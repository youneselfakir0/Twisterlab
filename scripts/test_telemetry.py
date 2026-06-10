import asyncio
import logging
import time
from twisterlab.database.session import AsyncSessionLocal
from twisterlab.services.trading.stop_manager_service import StopManagerService
from twisterlab.services.trading.execution_service import ExecutionGatewayService
from twisterlab.config.settings import Settings
from twisterlab.database.models.trading import LiveOrderRecord
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelemetryTest")

async def test_telemetry():
    settings = Settings()
    # Force simulation mode
    settings.kucoin_is_sandbox = True
    settings.kucoin_api_key = ""
    
    execution = ExecutionGatewayService(settings)
    stop_manager = StopManagerService(settings, execution)
    
    async with AsyncSessionLocal() as db:
        logger.info("1. Creating Entry Order...")
        order = await execution.execute_market_order(
            db, "BTC/USDT", "buy", 0.001, signal_id=99,
            stop_loss=60000, take_profit=75000
        )
        # Force entry price for easy math
        order.price_filled = 65000.0
        await db.commit()
        await db.refresh(order)
        
        logger.info(f"Order #{order.id} opened at {order.price_filled}")
        
        logger.info("2. Triggering TSL Exit at 66500...")
        # Simulate StopManager behavior manually for speed
        await stop_manager._trigger_exit(db, order, exit_price=66500, reason="TSL_EXIT")
        await db.commit()
        await db.refresh(order)
        
        logger.info(f"Order #{order.id} closed. Status: {order.status}")
        logger.info(f"PnL: {order.realized_pnl} USD")
        logger.info(f"Reason: {order.exit_reason}")
        
        assert order.status == "closed"
        assert order.realized_pnl > 0
        assert order.exit_reason == "tsl_exit"
        
        logger.info("\u2705 TELEMETRY TEST PASSED!")

if __name__ == "__main__":
    asyncio.run(test_telemetry())
