import logging
import json
import time
import ccxt.async_support as ccxt
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from twisterlab.database.models.trading import LiveOrderRecord, ExecutionAuditLog
from twisterlab.config.settings import Settings

logger = logging.getLogger(__name__)

class ExecutionGatewayService:
    """
    Live Broker Execution Gateway using CCXT.
    Phase 6: Transition layer for secure multi-exchange connectivity.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._exchange = None
        
    async def _get_exchange(self) -> Any:
        """Initialize and return the CCXT exchange instance (Spot or Futures)."""
        if self._exchange:
            return self._exchange
            
        params = {
            'apiKey': self.settings.kucoin_api_key,
            'secret': self.settings.kucoin_secret,
            'password': self.settings.kucoin_passphrase,
            'enableRateLimit': True,
            'options': {
                'adjustForTimeDifference': True,
                'fetchCurrencies': False
            }
        }
        
        # Select exchange class
        if self.settings.kucoin_market_type.lower() == "futures":
            self._exchange = ccxt.kucoinfutures(params)
            sandbox_url = 'https://api-sandbox-futures.kucoin.com' # CCXT default Futures Sandbox
        else:
            self._exchange = ccxt.kucoin(params)
            sandbox_url = 'https://openapi-sandbox.kucoin.com' # Spot Sandbox

        if self.settings.kucoin_is_sandbox:
            # Manually set sandbox endpoint to bypass CCXT validation issues
            if isinstance(self._exchange.urls['api'], dict):
                self._exchange.urls['api']['public'] = sandbox_url
                self._exchange.urls['api']['private'] = sandbox_url
            else:
                self._exchange.urls['api'] = sandbox_url
            
            # Set sandbox mode flag without calling the potentially failing set_sandbox_mode()
            self._exchange.sandbox = True
            logger.info(f"ExecutionGateway: KuCoin ({self.settings.kucoin_market_type}) Sandbox Mode forced manually.")
            
            # For futures sandbox, mock the currencies fetch if it fails
            if self.settings.kucoin_market_type.lower() == "futures":
                 self._exchange.options['fetchCurrencies'] = False
        
        # Trigger time sync and market loading
        try:
            # Manual time sync as system clock is drifiting (+30s detected)
            logger.info(f"ExecutionGateway: Attempting manual time sync via public endpoint...")
            import httpx
            time_url = 'https://api-futures.kucoin.com/api/v1/timestamp' if self.settings.kucoin_market_type == "futures" else 'https://api.kucoin.com/api/v1/timestamp'
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(time_url)
                if resp.status_code == 200:
                    server_time = resp.json().get('data')
                    local_time = int(time.time() * 1000)
                    self._exchange.options['timeDifference'] = local_time - server_time
                    logger.info(f"ExecutionGateway: Manual time sync successful. Offset: {self._exchange.options['timeDifference']}ms")
            
            await self._exchange.load_markets()
        except Exception as e:
            logger.error(f"ExecutionGateway: Failed to load markets/sync time: {e}")
            
        return self._exchange


    async def fetch_balance(self, db: AsyncSession) -> Dict[str, Any]:
        """Fetch private account balances and audit the call."""
        if self.settings.kucoin_is_sandbox and not self.settings.kucoin_api_key:
            logger.info("ExecutionGateway: Returning simulated balance for Sandbox fallback (no keys).")
            return {
                "USDT": 10000.0,
                "free": {"USDT": 10000.0},
                "used": {"USDT": 0.0},
                "total": {"USDT": 10000.0}
            }

        exchange = await self._get_exchange()
        t0 = time.time()
        
        try:
            balance = await exchange.fetch_balance()
            await self._audit(db, "fetch_balance", {}, balance, "success", t0)
            return balance
        except Exception as e:
            await self._audit(db, "fetch_balance", {}, {"error": str(e)}, "error", t0)
            logger.error(f"ExecutionGateway: Balance fetch failed: {e}")
            raise

    async def execute_market_order(self, 
        db: AsyncSession, 
        symbol: str, 
        side: str, 
        amount: float, 
        signal_id: Optional[int] = None,
        strategy_name: Optional[str] = None, # Added for Phase 9
        atr: Optional[float] = None, # Added for Phase 10
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        is_entry: bool = True,
        request_id: Optional[str] = None
    ) -> LiveOrderRecord:
        """
        Submits a market order to the exchange and tracks it in the DB.
        Includes dual-layer idempotency checks (DB query and Client Order ID).
        """
        # 1. DB-Level Idempotency Check
        if request_id:
            stmt = select(LiveOrderRecord).where(LiveOrderRecord.request_id == request_id)
            existing_res = await db.execute(stmt)
            existing_order = existing_res.scalar_one_or_none()
            if existing_order:
                logger.warning(f"ExecutionGateway: Order with request_id '{request_id}' already exists. Status: {existing_order.status}. Returning existing record (idempotency safety).")
                return existing_order

        if signal_id is not None:
            stmt = select(LiveOrderRecord).where(
                LiveOrderRecord.signal_id == signal_id,
                LiveOrderRecord.status.in_(["filled", "submitted", "open"])
            )
            existing_res = await db.execute(stmt)
            existing_order = existing_res.scalar_one_or_none()
            if existing_order:
                logger.warning(f"ExecutionGateway: Order with signal_id {signal_id} is already active/filled. Returning existing record (idempotency safety).")
                return existing_order

        # 2. Create PENDING record
        order_rec = LiveOrderRecord(
            signal_id=signal_id,
            request_id=request_id,
            strategy_name=strategy_name,
            symbol=symbol,
            side=side,
            amount=amount,
            stop_loss=stop_loss,
            take_profit=take_profit,
            atr_at_entry=atr,
            status="pending"
        )
        db.add(order_rec)
        await db.commit()
        await db.refresh(order_rec)

        t0 = time.time()
        req_params = {"symbol": symbol, "side": side, "amount": amount, "type": "market"}
        
        try:
            # 3. Deterministic Client Order ID (clientOid) for exchange deduplication
            client_oid = request_id
            if not client_oid and signal_id is not None:
                import hashlib
                client_oid = hashlib.md5(f"twisterlab_{signal_id}".encode()).hexdigest()

            # 4. Execute on Exchange (or simulation if keys missing)
            if self.settings.kucoin_is_sandbox and not self.settings.kucoin_api_key:
                logger.info("ExecutionGateway: SIMULATION MODE ACTIVE - Faking fill.")
                res = {
                    "id": f"sim-{int(time.time())}",
                    "average": 65000.0, # Simple fallback for simulation
                    "price": 65000.0,
                    "status": "closed",
                    "amount": amount
                }
            else:
                exchange = await self._get_exchange()
                params = {}
                if client_oid:
                    params["clientOid"] = client_oid
                res = await exchange.create_market_order(symbol, side.lower(), amount, params=params)
            
            # 5. Update Record
            order_rec.exchange_id = str(res.get('id', 'unknown'))
            order_rec.status = "filled"
            order_rec.price_filled = float(res.get('average', res.get('price', 0)))
            order_rec.is_active = is_entry # Only entries count for active exposure monitoring
            
            await self._audit(db, "create_market_order", req_params, res, "success", t0)
            logger.info(f"ExecutionGateway: Filled {side} {amount} {symbol} at {order_rec.price_filled}")
            
        except Exception as e:
            order_rec.status = "rejected"
            order_rec.is_active = False
            order_rec.error_message = str(e)
            await self._audit(db, "create_market_order", req_params, {"error": str(e)}, "error", t0)
            logger.error(f"ExecutionGateway: Order failed for {symbol}: {e}")
            
        await db.commit()
        return order_rec

    async def emergency_halt(self, db: AsyncSession):
        """
        Kill Switch: Cancels all open orders on the exchange and marks active positions as halted.
        """
        exchange = await self._get_exchange()
        t0 = time.time()
        try:
            res = await exchange.cancel_all_orders()
            
            # Mark all active orders as no longer active in our exposure count
            from sqlalchemy import update
            stmt = update(LiveOrderRecord).where(LiveOrderRecord.is_active == True).values(
                is_active=False,
                closed_at=datetime.now(timezone.utc),
                status="halted"
            )
            await db.execute(stmt)
            await db.commit()

            await self._audit(db, "emergency_halt", {"action": "cancel_all"}, res, "success", t0)
            logger.warning("ExecutionGateway: EMERGENCY HALT TRIGGERED - Exposure reset.")
            return res
        except Exception as e:
            if db: await self._audit(db, "emergency_halt", {"action": "cancel_all"}, {"error": str(e)}, "error", t0)
            raise

    async def _audit(self, db: AsyncSession, action: str, req: dict, res: dict, status: str, t0: float):
        """Helper to log immutable API history."""
        latency = (time.time() - t0) * 1000
        log = ExecutionAuditLog(
            action=action,
            request_data=json.dumps(req),
            response_data=json.dumps(res),
            status=status,
            latency_ms=latency
        )
        db.add(log)
        await db.commit()
        
    async def close(self):
        """Close exchange connections."""
        if self._exchange:
            await self._exchange.close()
