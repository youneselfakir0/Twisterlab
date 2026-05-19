import pytest
import time
from unittest.mock import AsyncMock, MagicMock
from twisterlab.services.trading.execution_service import ExecutionGatewayService
from twisterlab.config.settings import Settings
from twisterlab.database.models.trading import LiveOrderRecord
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_execution_gateway_idempotency_request_id():
    """Verify that ExecutionGatewayService does not place duplicate orders for the same request_id."""
    settings = Settings()
    settings.kucoin_is_sandbox = True
    settings.kucoin_api_key = ""  # Trigger simulation mode
    
    gateway = ExecutionGatewayService(settings)
    mock_db = AsyncMock(spec=AsyncSession)
    
    # First execution: no existing record in DB
    mock_result_empty = MagicMock()
    mock_result_empty.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result_empty
    
    order_1 = await gateway.execute_market_order(
        db=mock_db,
        symbol="BTC-USDT",
        side="BUY",
        amount=0.01,
        signal_id=42,
        request_id="req-unique-999"
    )
    
    assert order_1.status == "filled"
    assert order_1.request_id == "req-unique-999"
    assert order_1.signal_id == 42
    
    # Reset mock counters to isolate the second execution
    mock_db.add.reset_mock()
    
    # Second execution: mock DB query finding the existing record
    mock_result_exists = MagicMock()
    mock_result_exists.scalar_one_or_none.return_value = order_1
    mock_db.execute.return_value = mock_result_exists
    
    order_2 = await gateway.execute_market_order(
        db=mock_db,
        symbol="BTC-USDT",
        side="BUY",
        amount=0.01,
        signal_id=42,
        request_id="req-unique-999"
    )
    
    # Assert it returns the existing order record (idempotency enforced)
    assert order_2 is order_1
    # Mock DB add should NOT be called during early return
    assert mock_db.add.call_count == 0


@pytest.mark.asyncio
async def test_execution_gateway_idempotency_signal_id():
    """Verify that ExecutionGatewayService prevents double buying if signal_id is already filled."""
    settings = Settings()
    settings.kucoin_is_sandbox = True
    settings.kucoin_api_key = ""  # Trigger simulation mode
    
    gateway = ExecutionGatewayService(settings)
    mock_db = AsyncMock(spec=AsyncSession)
    
    # First execution: no existing record
    mock_result_empty = MagicMock()
    mock_result_empty.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result_empty
    
    order_1 = await gateway.execute_market_order(
        db=mock_db,
        symbol="ETH-USDT",
        side="BUY",
        amount=0.1,
        signal_id=101,
        request_id="first-attempt-req"
    )
    
    assert order_1.status == "filled"
    assert order_1.signal_id == 101
    
    # Reset mock counters to isolate the second execution
    mock_db.add.reset_mock()
    
    # Second execution attempt (with a different request_id but same signal_id)
    # Mock DB query to return no request_id match, but return signal_id match on the second query
    # Since mock_db.execute.return_value is queried sequentially, we can use side_effect
    mock_res_no_req = MagicMock()
    mock_res_no_req.scalar_one_or_none.return_value = None  # No request_id match
    
    mock_res_signal = MagicMock()
    mock_res_signal.scalar_one_or_none.return_value = order_1  # Signal_id match
    
    mock_db.execute.side_effect = [mock_res_no_req, mock_res_signal]
    
    order_2 = await gateway.execute_market_order(
        db=mock_db,
        symbol="ETH-USDT",
        side="BUY",
        amount=0.1,
        signal_id=101,
        request_id="second-attempt-req"
    )
    
    assert order_2 is order_1
    assert mock_db.add.call_count == 0
