"""
RealTraderAgent - The Scalping Expert (Accountable)
Phase 5-C: Persistence & Performance Metrics
"""

import logging
from typing import List, Dict, Any, Optional

from twisterlab.agents.core.base import (
    CoreAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)
from twisterlab.utils.trading.kucoin_client import KuCoinPublicClient
from twisterlab.utils.trading.indicators import IndicatorEngine
from twisterlab.utils.trading.strategy_engine import StrategyFactory
from twisterlab.utils.trading.risk_engine import RiskEngine
from twisterlab.services.trading.journal_service import JournalService
from twisterlab.services.trading.execution_service import ExecutionGatewayService
from twisterlab.services.trading.risk_guard_service import RiskGuardService
from twisterlab.config.settings import Settings
from twisterlab.api.schemas.trading import LiveOrderResponse
from twisterlab.database.models.trading import LiveOrderRecord

logger = logging.getLogger(__name__)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class RealTraderAgent(CoreAgent):
    """
    Agent specialized in cryptocurrency market analysis and signal generation.
    Phase 6: Includes secure live execution gateway with risk guards.
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = Settings()
        self._kucoin = KuCoinPublicClient()
        self._indicators = IndicatorEngine()
        self._risk = RiskEngine()
        self._journal = JournalService()
        self._execution = ExecutionGatewayService(self._settings)
        self._risk_guard = RiskGuardService(self._settings)

    @property
    def name(self) -> str:
        return "trader"

    @property
    def description(self) -> str:
        return "Generates signals, manages paper trades, and provides a secure Live Execution Gateway (Accountable)."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="analyze_market",
                description="Fetch and analyze KuCoin market data for a specific symbol",
                handler="handle_analyze_market",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("symbol", ParamType.STRING, "Trading pair (e.g. BTC-USDT)", required=True),
                    CapabilityParam("timeframe", ParamType.STRING, "Interval (1min, 5min, 15min, 1hour)", required=False, default="1hour"),
                ],
            ),
            AgentCapability(
                name="generate_trade_signal",
                description="Generate a High-Probability Trade Signal and log it to the journal.",
                handler="handle_generate_signal",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("symbol", ParamType.STRING, "Trading pair (e.g. BTC-USDT)", required=True),
                    CapabilityParam("timeframe", ParamType.STRING, "Interval (1min, 5min, 15min)", required=False, default="5min"),
                    CapabilityParam("strategy", ParamType.STRING, "Named strategy (e.g. scalp_v1)", required=False, default="scalp_v1"),
                ],
            ),
            AgentCapability(
                name="execute_paper_trade",
                description="Open a simulated paper trade from a generated signal ID.",
                handler="handle_execute_paper_trade",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("signal_id", ParamType.INTEGER, "The ID of the signal to execute", required=True),
                ],
            ),
            AgentCapability(
                name="close_paper_trade",
                description="Close an active paper trade with a simulated exit price.",
                handler="handle_close_paper_trade",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("trade_id", ParamType.INTEGER, "The ID of the trade to close", required=True),
                    CapabilityParam("exit_price", ParamType.NUMBER, "Simulated price at exit", required=True),
                    CapabilityParam("reason", ParamType.STRING, "Reason for closing (tp_hit, sl_hit, manual)", required=False, default="manual"),
                ],
            ),
            AgentCapability(
                name="get_trading_metrics",
                description="Retrieve aggregated performance metrics for the trading journal.",
                handler="handle_get_metrics",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("strategy", ParamType.STRING, "Filter by strategy name", required=False),
                ],
            ),
            AgentCapability(
                name="request_live_execution",
                description="[PHASE 6] Execute a REAL live trade on the exchange (Subject to $5 Micro-Cap).",
                handler="handle_request_live_execution",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("signal_id", ParamType.INTEGER, "The ID of the signal to execute", required=True),
                    CapabilityParam("confirm_live", ParamType.BOOLEAN, "Must be true to acknowledge real fund usage", required=True),
                ],
            ),
            AgentCapability(
                name="get_live_balances",
                description="[PHASE 6] Fetch real private account balances from the broker.",
                handler="handle_get_live_balances",
                capability_type=CapabilityType.QUERY,
            )
        ]

    async def handle_analyze_market(self, symbol: str, timeframe: str = "1hour") -> AgentResponse:
        """Lightweight analysis (Phase 5-A logic maintained)."""
        candles = await self._kucoin.fetch_candles(symbol, interval=timeframe, limit=100)
        if not candles:
            return AgentResponse(success=False, error=f"Could not fetch data for {symbol}")
            
        closes = [c[2] for c in candles]
        ema_20 = self._indicators.calculate_ema(closes, 20)
        ema_50 = self._indicators.calculate_ema(closes, 50)
        rsi = self._indicators.calculate_rsi(closes, 14)
        vwap = self._indicators.calculate_vwap(candles)
        
        last_close = closes[-1]
        last_rsi = rsi[-1] if rsi else 50
        
        trend = "Bullish" if (ema_20 and ema_50 and ema_20[-1] > ema_50[-1]) else "Bearish"
        
        return AgentResponse(success=True, data={
            "symbol": symbol,
            "timeframe": timeframe,
            "trend": trend,
            "rsi": round(last_rsi, 2),
            "price": last_close,
            "vwap": round(vwap[-1], 2) if vwap else 0
        })

    async def handle_generate_signal(self, symbol: str, timeframe: str = "5min", strategy: str = "scalp_v1") -> AgentResponse:
        """
        Advanced Signal Generation with Persistent Logging (Phase 5-C).
        """
        # 1. Determine Higher Timeframe (HTF)
        htf_map = {"1min": "5min", "5min": "15min", "15min": "1hour"}
        htf_timeframe = htf_map.get(timeframe, "1hour")
        
        # 2. Fetch Data (LTF + HTF)
        ltf_candles = await self._kucoin.fetch_candles(symbol, interval=timeframe, limit=300)
        htf_candles = await self._kucoin.fetch_candles(symbol, interval=htf_timeframe, limit=300)
        
        if not ltf_candles:
            return AgentResponse(success=False, error=f"Failed to fetch LTF candles for {symbol}")
            
        # 3. Generate Signal
        strategy_impl = StrategyFactory.get_strategy(strategy)
        signal = strategy_impl.generate_signal(ltf_candles, htf_candles)
        signal.symbol = symbol
        signal.timeframe = timeframe
        
        # 4. Fetch ATR for Risk info
        atr_series = self._indicators.calculate_atr(ltf_candles, 14)
        last_atr = atr_series[-1] if atr_series else 0.0
        entry_price = ltf_candles[-1][2]
        
        risk_levels = self._risk.calculate_levels(
            entry_price=entry_price,
            atr=last_atr,
            direction=signal.direction
        )
        
        # 5. Build Comprehensive Data Object
        data = {
            "symbol": symbol,
            "strategy": strategy,
            "timeframe": timeframe,
            "signal": signal.direction,
            "confidence": signal.confidence,
            "entry_price": entry_price,
            "risk_management": risk_levels,
            "technical_confluence": signal.indicator_data,
            "rationale": signal.rationale,
            "summary": f"[{signal.direction}] Setup detected on {symbol} ({timeframe})."
        }
        
        # 6. PERSIST SUCCESSFUL SIGNAL
        # We log everything that isn't NO_TRADE, or even NO_TRADE if we want full audit.
        # Let's log persistent signal records for everything.
        signal_id = await self._journal.log_signal(data)
        data["signal_id"] = signal_id
        
        return AgentResponse(success=True, data=data)

    async def handle_execute_paper_trade(self, signal_id: int) -> AgentResponse:
        """Opens a paper trade based on a stored signal."""
        res = await self._journal.open_trade(signal_id)
        if not res["success"]:
            return AgentResponse(success=False, error=res.get("error"))
        return AgentResponse(success=True, data=res)

    async def handle_close_paper_trade(self, trade_id: int, exit_price: float, reason: str = "manual") -> AgentResponse:
        """Closes an open paper trade and reports PnL."""
        res = await self._journal.close_trade(trade_id, exit_price, reason)
        if not res["success"]:
            return AgentResponse(success=False, error=res.get("error"))
        return AgentResponse(success=True, data=res)

    async def handle_get_metrics(self, strategy: Optional[str] = None) -> AgentResponse:
        """Retrieves performance KPIs."""
        metrics = await self._journal.get_metrics(strategy)
        return AgentResponse(success=True, data=metrics)

    async def handle_request_live_execution(self, signal_id: int, confirm_live: bool = False, request_id: Optional[str] = None) -> AgentResponse:
        """
        [PHASE 6] Gatekeeper for real fund execution.
        """
        if not confirm_live:
            return AgentResponse(success=False, error="Confirmation required for live execution.")

        from twisterlab.database.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            # 1. Fetch the signal
            signal = await self._journal.get_signal(signal_id)
            if not signal:
                return AgentResponse(success=False, error=f"Signal {signal_id} not found.")

            # 2. Risk Validation (hard $5 cap)
            entry_price = signal.entry_price
            safe_amount = self._risk_guard.get_micro_size_recommendation(entry_price)
            
            # Use structured RiskGuardResult
            risk_res = await self._risk_guard.validate_order(
                db, signal.symbol, signal.direction, safe_amount, entry_price
            )
            
            if not risk_res.approved:
                return AgentResponse(success=False, error=f"RiskGuard Rejection: {risk_res.reason} ({risk_res.risk_code})")

            # 3. Execution via Gateway
            try:
                order_rec = await self._execution.execute_market_order(
                    db, 
                    signal.symbol, 
                    signal.direction, 
                    safe_amount, 
                    signal_id,
                    strategy_name=signal.strategy_name, # Added for Phase 9
                    atr=signal.atr, # Added for Phase 10
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    request_id=request_id
                )
                # Manually extract fields to avoid lazy-loading/greenlet errors on detached objects
                data = {
                    "id": order_rec.id,
                    "symbol": order_rec.symbol,
                    "side": order_rec.side,
                    "amount": order_rec.amount,
                    "price_requested": order_rec.price_requested,
                    "price_filled": order_rec.price_filled,
                    "status": order_rec.status,
                    "is_active": order_rec.is_active,
                    "created_at": order_rec.created_at,
                    "closed_at": order_rec.closed_at,
                    "stop_loss": order_rec.stop_loss,
                    "take_profit": order_rec.take_profit
                }
                return AgentResponse(success=True, data=data)
            except Exception as e:
                logger.error(f"TraderAgent: Live execution failed: {e}")
                return AgentResponse(success=False, error=str(e))

    async def handle_emergency_halt(self, db: AsyncSession) -> AgentResponse:
        """Kill Switch handler."""
        try:
            res = await self._execution.emergency_halt(db)
            return AgentResponse(success=True, data={"message": "System halted, all orders canceled.", "details": res})
        except Exception as e:
            return AgentResponse(success=False, error=str(e))

    async def handle_get_risk_status(self, db: AsyncSession) -> AgentResponse:
        """Risk status summary handler."""
        status = await self._risk_guard.get_risk_status(db)
        return AgentResponse(success=True, data=status)

    async def handle_get_profit_analytics(self, db: AsyncSession, strategy: Optional[str] = None) -> AgentResponse:
        """New: Dashboard PnL analytics with real-time unrealized calc (Phase 9 Final)."""
        # 1. Fetch active symbols to get prices
        stmt = select(LiveOrderRecord.symbol).where(LiveOrderRecord.is_active == True).distinct()
        res = await db.execute(stmt)
        active_symbols = res.scalars().all()
        
        # 2. Fetch prices (using a simulated fallback if needed via CCXT)
        prices = {}
        if active_symbols:
            try:
                # We reuse the simulated价格 feed if sandbox + no keys
                if self._settings.kucoin_is_sandbox and not self._settings.kucoin_api_key:
                    prices = {"BTC/USDT": 65000.0, "ETH/USDT": 3500.0, "SOL/USDT": 145.0, "BNB/USDT": 580.0}
                else:
                    exchange = await self._execution._get_exchange()
                    tickers = await exchange.fetch_tickers(active_symbols)
                    prices = {s: t['last'] for s, t in tickers.items() if 'last' in t}
            except Exception as e:
                logger.error(f"TraderAgent: Price fetch failed for analytics: {e}")
        
        # 3. Aggregated Analytics
        stats = await self._risk_guard.get_profit_analytics(db, prices, strategy=strategy)
        return AgentResponse(success=True, data=stats)

    async def handle_get_live_balances(self) -> AgentResponse:
        """Fetch real balances."""
        from twisterlab.database.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                balance = await self._execution.fetch_balance(db)
                return AgentResponse(success=True, data=balance)
            except Exception as e:
                return AgentResponse(success=False, error=str(e))

__all__ = ["RealTraderAgent"]
