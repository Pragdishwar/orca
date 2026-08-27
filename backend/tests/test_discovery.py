import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.app.core.discovery import DatasetDiscoveryAgent, DiscoveryDecisionLog, DiscoveryResult
from backend.app.models.source_registry import SourceRegistry

@pytest.mark.asyncio
async def test_discovery_tier_1_priority():
    mock_session = AsyncMock()
    
    tier1_mosdac = SourceRegistry(
        source_id="mosdac_01",
        provider="MOSDAC",
        spatial_coverage="Kerala",
        variables={"available": ["wave", "wind"]},
        priority_tier=1,
        access_status="UNKNOWN"
    )
    
    tier2_copernicus = SourceRegistry(
        source_id="copernicus_01",
        provider="Copernicus",
        spatial_coverage="Kerala",
        variables={"available": ["wave", "wind"]},
        priority_tier=2,
        access_status="UNKNOWN"
    )
    
    # Return out of order to verify sorting algorithm
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [tier2_copernicus, tier1_mosdac]
    mock_session.execute.return_value = mock_result
    
    agent = DatasetDiscoveryAgent(session=mock_session)
    
    with patch.object(agent, '_attempt_connection', new_callable=AsyncMock) as mock_conn:
        mock_conn.return_value = True
        
        result = await agent.discover_sources(["wave"], "Kerala")
        
        assert result.log.chosen_source == "MOSDAC"
        assert result.log.priority_tier == 1
        assert result.log.fallback_occurred is False
        # Ensures MOSDAC was evaluated before Copernicus
        assert result.log.candidates_considered == ["MOSDAC", "Copernicus"]

@pytest.mark.asyncio
async def test_discovery_fallback_to_tier_2():
    mock_session = AsyncMock()
    
    tier1_bhuvan = SourceRegistry(
        source_id="bhuvan_01",
        provider="Bhuvan",
        spatial_coverage="Kerala",
        variables={"available": ["wave", "wind"]},
        priority_tier=1,
        access_status="UNKNOWN"
    )
    
    tier2_nasa = SourceRegistry(
        source_id="nasa_01",
        provider="NASA",
        spatial_coverage="Kerala",
        variables={"available": ["wave", "wind"]},
        priority_tier=2,
        access_status="UNKNOWN"
    )
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [tier1_bhuvan, tier2_nasa]
    mock_session.execute.return_value = mock_result
    
    agent = DatasetDiscoveryAgent(session=mock_session)
    
    async def mock_attempt(source):
        # Tier 1 fails, Tier 2 succeeds
        return source.priority_tier != 1
        
    with patch.object(agent, '_attempt_connection', side_effect=mock_attempt):
        result = await agent.discover_sources(["wave"], "Kerala")
        
        assert result.log.chosen_source == "NASA"
        assert result.log.priority_tier == 2
        assert result.log.fallback_occurred is True
        
        assert tier1_bhuvan.access_status == "SUBSTITUTED"
        assert tier2_nasa.access_status == "CONNECTED"
