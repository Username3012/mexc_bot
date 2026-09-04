import asyncio
from datetime import datetime
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class PaperPosition:
    symbol: str
    side: str
    entry_price: float
    amount: float
    stop_loss: float
    take_profit: float
    opened_at: datetime
    exit_price: Optional[float] = None
    pnl: float = 0.0
    status: str = "open"

@dataclass
class PaperTrade:
    timestamp: datetime
    symbol: str
    signal: str
    price: float
    amount: float
    reason: str
    success: bool
    metadata: dict = field(default_factory=dict)

class PaperTrader:
    def __init__(self, exchange_client, strategy, risk_manager, logger,
                 initial_balance=1000, symbols=None):
        self.exchange = exchange_client
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.logger = logger
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.symbols = symbols or ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        self.positions = {}
        self.trades = []
        self.daily_pnl = 0.0
    
    async def process_symbol(self, symbol):
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, '1m', 100)
            if not ohlcv or len(ohlcv) < 30:
                return
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            ticker = await self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            if symbol in self.positions:
                position = self.positions[symbol]
                if current_price <= position.stop_loss:
                    await self.close_position(symbol, "STOP_LOSS", current_price)
                    return
                if current_price >= position.take_profit:
                    await self.close_position(symbol, "TAKE_PROFIT", current_price)
                    return
            
            if not self.risk_manager.can_open_position(symbol):
                return
            
            signal = self.strategy.generate_signal(df)
            if signal['signal'] == 'HOLD':
                return
            
            volatility = df['high'].iloc[-20:].std() / df['close'].iloc[-1]
            position_size = self.risk_manager.calculate_position_size(
                self.current_balance, current_price, volatility
            )
            
            if position_size is None:
                return
            
            side = signal['signal'].lower()
            slippage = current_price * 0.002 if 'BTC' not in symbol else current_price * 0.001
            execution_price = current_price + slippage if side == 'buy' else current_price - slippage
            
            position = PaperPosition(
                symbol=symbol, side=side, entry_price=execution_price,
                amount=position_size.amount, stop_loss=position_size.stop_loss,
                take_profit=position_size.take_profit, opened_at=datetime.utcnow()
            )
            
            self.positions[symbol] = position
            self.current_balance -= execution_price * position_size.amount
            
            self.trades.append(PaperTrade(
                timestamp=datetime.utcnow(), symbol=symbol, signal=side.upper(),
                price=execution_price, amount=position_size.amount,
                reason=signal.get('reason', 'unknown'), success=True
            ))
            
            self.logger.info(
                "paper_position_opened", symbol=symbol, side=side,
                entry=execution_price, amount=position_size.amount,
                balance=self.current_balance
            )
            
        except Exception as e:
            self.logger.error("paper_trading_error", symbol=symbol, error=str(e))
    
    async def close_position(self, symbol, reason, price):
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        if position.side == 'buy':
            pnl = (price - position.entry_price) * position.amount
        else:
            pnl = (position.entry_price - price) * position.amount
        
        position.exit_price = price
        position.pnl = pnl
        position.status = "closed"
        
        self.current_balance += price * position.amount + pnl
        self.daily_pnl += pnl
        
        self.trades.append(PaperTrade(
            timestamp=datetime.utcnow(), symbol=symbol, signal="CLOSE",
            price=price, amount=position.amount, reason=reason,
            success=pnl > 0, metadata={'pnl': pnl}
        ))
        
        self.logger.info(
            "paper_position_closed", symbol=symbol, reason=reason,
            entry=position.entry_price, exit=price, pnl=pnl,
            balance=self.current_balance
        )
        
        del self.positions[symbol]
    
    async def close_all_positions(self):
        for symbol in list(self.positions.keys()):
            ticker = await self.exchange.fetch_ticker(symbol)
            await self.close_position(symbol, "EMERGENCY", ticker['last'])
    
    def get_stats(self):
        closed = [t for t in self.trades if t.signal == 'CLOSE']
        if not closed:
            return {'total_trades': 0}
        
        wins = sum(1 for t in closed if t.success)
        pnls = [t.metadata.get('pnl', 0) for t in closed if t.metadata]
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.current_balance,
            'total_pnl': sum(pnls),
            'total_pnl_percent': (sum(pnls) / self.initial_balance) * 100,
            'total_trades': len(closed),
            'winning_trades': wins,
            'losing_trades': len(closed) - wins,
            'win_rate': (wins / len(closed) * 100) if closed else 0,
            'avg_profit': sum([p for p in pnls if p > 0]) / wins if wins > 0 else 0,
            'avg_loss': sum([p for p in pnls if p < 0]) / (len(closed) - wins) if (len(closed) - wins) > 0 else 0
        }