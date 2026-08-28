"""Dataset discovery: choose a source per variable from the registry (SRS 5.2).

FR-06 requires selection to happen at query time by ranking registry
candidates, not by mapping a query type to a fixed source, and FR-09 requires
an Indian/ISRO source to be attempted before any non-Indian substitute for
every variable one covers. Both fall out of resolving each variable
independently in tier order.
"""
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.source_registry import SourceRegistry

logger = logging.getLogger(__name__)


class DiscoveryDecisionLog(BaseModel):
    candidates_considered: List[str]
    chosen_source: Optional[str]
    priority_tier: Optional[int]
    reason: str
    fallback_occurred: bool
    failed: List[str] = []
    per_variable: List[Dict[str, Any]] = []


class DiscoveryResult(BaseModel):
    selected_sources: List[SourceRegistry]
    log: DiscoveryDecisionLog

    model_config = {"arbitrary_types_allowed": True}


def _variables_of(src: SourceRegistry) -> List[str]:
    v = src.variables
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return v.get("available", list(v.keys()))
    return []


class DatasetDiscoveryAgent:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _attempt_connection(self, source: SourceRegistry) -> bool:
        """Whether this source can actually serve data right now.

        The registry records the outcome of the real access attempt made during
        ETL (SRS 9.1 step 2). A source recorded as ATTEMPTED or SUBSTITUTED did
        not yield data - typically because it needs credentials this build does
        not hold - so it is not selectable, and the fall-through is logged
        rather than hidden. In production this becomes a live health probe.
        """
        return source.access_status == "CONNECTED"

    async def discover_sources(self, required_variables: List[str],
                               region: str) -> DiscoveryResult:
        stmt = select(SourceRegistry).where(SourceRegistry.spatial_coverage == region)
        candidates = list((await self.session.execute(stmt)).scalars().all())

        per_variable: List[Dict[str, Any]] = []
        chosen_by_var: Dict[str, SourceRegistry] = {}
        considered_order: List[str] = []
        all_failed: List[str] = []
        fallback_occurred = False

        for var in required_variables:
            covering = sorted(
                [c for c in candidates if var in _variables_of(c)],
                key=lambda s: (s.priority_tier, s.provider),
            )
            names = [c.provider for c in covering]
            for n in names:
                if n not in considered_order:
                    considered_order.append(n)

            chosen: Optional[SourceRegistry] = None
            failed: List[str] = []
            for src in covering:
                if await self._attempt_connection(src):
                    chosen = src
                    src.access_status = "CONNECTED"
                    self.session.add(src)
                    break
                failed.append(src.provider)
                # Only ever a downgrade: a source is never promoted to
                # CONNECTED by a failed probe.
                if src.access_status != "SUBSTITUTED":
                    logger.warning("Tier %s source %s did not connect for '%s'; falling through.",
                                   src.priority_tier, src.provider, var)
                    src.access_status = "SUBSTITUTED"
                    self.session.add(src)

            if failed:
                fallback_occurred = True
                all_failed.extend(f for f in failed if f not in all_failed)
            if chosen is not None:
                chosen_by_var[var] = chosen

            per_variable.append({
                "variable": var,
                "candidates": [{"provider": c.provider, "priority_tier": c.priority_tier,
                                "access_status": c.access_status} for c in covering],
                "chosen": chosen.provider if chosen else None,
                "chosen_source_id": chosen.source_id if chosen else None,
                "priority_tier": chosen.priority_tier if chosen else None,
                "attempted_first": names[0] if names else None,
                "failed": failed,
            })

        selected: List[SourceRegistry] = []
        for src in chosen_by_var.values():
            if src not in selected:
                selected.append(src)
        selected.sort(key=lambda s: (s.priority_tier, s.provider))

        primary = selected[0] if selected else None
        reason = self._reason(required_variables, per_variable, primary, all_failed)

        try:
            await self.session.commit()
        except Exception:  # pragma: no cover - a read-only probe must not 500 a query
            logger.exception("Could not persist registry access_status updates.")

        return DiscoveryResult(
            selected_sources=selected,
            log=DiscoveryDecisionLog(
                candidates_considered=considered_order,
                chosen_source=primary.provider if primary else None,
                priority_tier=primary.priority_tier if primary else None,
                reason=reason,
                fallback_occurred=fallback_occurred,
                failed=all_failed,
                per_variable=per_variable,
            ),
        )

    @staticmethod
    def _reason(required: List[str], per_variable: List[Dict[str, Any]],
                primary: Optional[SourceRegistry], failed: List[str]) -> str:
        if primary is None:
            return (f"No registry source covering {', '.join(required)} could be reached "
                    f"for this region.")
        unresolved = [p["variable"] for p in per_variable if not p["chosen"]]
        parts = [f"{primary.provider} (tier {primary.priority_tier}) selected as the primary "
                 f"source for {', '.join(required)}."]
        if failed:
            parts.append(f"Tier-1 candidate(s) {', '.join(failed)} were attempted first, per "
                         f"R-8, and did not connect; the substitution is recorded rather than "
                         f"hidden.")
        if unresolved:
            parts.append(f"No source available for: {', '.join(unresolved)}.")
        return " ".join(parts)
