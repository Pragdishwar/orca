import logging
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.source_registry import SourceRegistry

logger = logging.getLogger(__name__)

class DiscoveryDecisionLog(BaseModel):
    candidates_considered: List[str]
    chosen_source: Optional[str]
    priority_tier: Optional[int]
    reason: str
    fallback_occurred: bool

class DiscoveryResult(BaseModel):
    selected_sources: List[SourceRegistry]
    log: DiscoveryDecisionLog
    
    model_config = {"arbitrary_types_allowed": True}

class DatasetDiscoveryAgent:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def _attempt_connection(self, source: SourceRegistry) -> bool:
        """
        Simulates an actual connection check. 
        In production, this attempts HTTP/FTP endpoints for health status.
        """
        return source.access_status != "OFFLINE"

    async def discover_sources(self, required_variables: List[str], region: str) -> DiscoveryResult:
        # Step 1: Query SourceRegistry for region match
        stmt = select(SourceRegistry).where(SourceRegistry.spatial_coverage == region)
        result = await self.session.execute(stmt)
        sources = result.scalars().all()
        
        valid_candidates = []
        for src in sources:
            src_vars = []
            if isinstance(src.variables, list):
                src_vars = src.variables
            elif isinstance(src.variables, dict):
                src_vars = src.variables.get('available', list(src.variables.keys()))
                
            # Must support all required variables
            if all(var in src_vars for var in required_variables):
                valid_candidates.append(src)
                
        # Step 2: Sort candidates strictly by priority_tier ASC (Tier 1 ISRO/Indian -> Tier 2 Foreign)
        valid_candidates.sort(key=lambda s: s.priority_tier)
        
        candidates_considered = [s.provider for s in valid_candidates]
        fallback_occurred = False
        selected_source = None
        reason = "No suitable sources found."
        
        # Step 3 & 4: Attempt connection adhering to Sovereign Priority (Rule R-8)
        for source in valid_candidates:
            success = await self._attempt_connection(source)
            if success:
                selected_source = source
                source.access_status = "CONNECTED"
                reason = f"Successfully connected to {source.provider} (Tier {source.priority_tier})."
                self.session.add(source)
                await self.session.commit()
                break
            else:
                source.access_status = "SUBSTITUTED"
                self.session.add(source)
                await self.session.commit()
                fallback_occurred = True
                logger.warning(f"Tier {source.priority_tier} source {source.provider} failed. Attempting fallback.")
                
        # Step 5: Construct structured decision log
        log = DiscoveryDecisionLog(
            candidates_considered=candidates_considered,
            chosen_source=selected_source.provider if selected_source else None,
            priority_tier=selected_source.priority_tier if selected_source else None,
            reason=reason,
            fallback_occurred=fallback_occurred
        )
        
        return DiscoveryResult(
            selected_sources=[selected_source] if selected_source else [],
            log=log
        )
