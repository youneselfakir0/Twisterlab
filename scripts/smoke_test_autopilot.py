import asyncio
import logging
from twisterlab.services.trading.scanner_service import ScannerService
from twisterlab.config.settings import Settings
from unittest.mock import MagicMock, AsyncMock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_autopilot_trigger():
    print("--- Phase 12: Smoke Test Auto-Pilot Trigger ---")
    settings = Settings()
    scanner = ScannerService(settings)
    
    # Mocking components to avoid real network/DB calls during this logic check
    scanner.kucoin.fetch_candles = AsyncMock(return_value=[[0,0,100,0,0,0]] * 100) # Mock price 100
    
    # Mock Signal with High Confidence (0.95)
    mock_signal = MagicMock()
    mock_signal.direction = "LONG"
    mock_signal.confidence = 0.95
    mock_signal.strategy_name = "mean_reversion_v1"
    mock_signal.indicator_data = {}
    mock_signal.rationale = "Mock High Confidence"
    
    from twisterlab.utils.trading.strategy_engine import StrategyFactory
    StrategyFactory.get_strategy = MagicMock(return_value=MagicMock(generate_signal=MagicMock(return_value=mock_signal)))
    
    # Mock Execution
    scanner.execution.execute_market_order = AsyncMock(return_value=MagicMock(id=999))
    
    # 1. Trigger evaluation for Mean Reversion (which is Auto-Pilot: True)
    scan_config = {"symbol": "SOL/USDT", "strategy": "mean_reversion_v1", "timeframe": "15min", "auto_pilot": True, "confidence_threshold": 0.8}
    
    print("Evaluating Mean Reversion scan with Confidence 0.95...")
    await scanner._evaluate_scan(scan_config)
    
    # 2. Verify execute_market_order was called
    if scanner.execution.execute_market_order.called:
        print("✅ SUCCESS: Auto-Pilot triggered execution successfully.")
    else:
        print("❌ FAILURE: Auto-Pilot did NOT trigger execution.")

if __name__ == "__main__":
    asyncio.run(test_autopilot_trigger())
