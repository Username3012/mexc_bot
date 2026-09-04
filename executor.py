import asyncio
from datetime import datetime
import pandas as pd

class ScalpingExecutor:
    def __init__(self, exchange_client, strategy, risk_manager, storage, logger, symbols):
        self.exchange = exchange_client
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.storage = storage
        self.logger = logger
        self.symbols = symbols
        self.active_positions = {}
        self.processing_symbols = set()
    
    async def process_symbol(self, symbol, balance):
        if symbol in self.processing_symbols:
            return
        self.processing_symbols.add(symbol)
        
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, '1m', 100)
            if not ohlcv or len(ohlcv) < 30:
                return
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            ticker = await self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            if symbol in self.active_positions:
                self.risk_manager.update_open_positions(symbol, [self.active_positions[symbol]])
            else:
                self.risk_manager.update_open_positions(symbol, [])
            
            if not self.risk_manager.can_open_position(symbol):
                return
            
            signal = self.strategy.generate_signal(df)
            if signal['signal'] == 'HOLD':
                return
            
            volatility = df['high'].iloc[-20:].std() / df['close'].iloc[-1]
            position_size = self.risk_manager.calculate_position_size(
                balance, current_price, volatility
            )
            
            if position_size is None:
                return
            
            side = 'buy' if signal['signal'] == 'BUY' else 'sell'
            
            order = await self.exchange.create_order(
                symbol, side, 'market', position_size.amount
            )
            
            self.active_positions[symbol] = {
                'order_id': order['id'],
                'side': side,
                'entry_price': order['price'],
                'amount': position_size.amount,
                'stop_loss': position_size.stop_loss,
                'take_profit': position_size.take_profit,
                'opened_at': datetime.utcnow()
            }
            
            self.logger.info(
                "order_executed",
                symbol=symbol, side=side, price=order['price'],
                amount=position_size.amount, sl=position_size.stop_loss,
                tp=position_size.take_profit
            )
            
        finally:
            self.processing_symbols.remove(symbol)
    
    async def monitor_positions(self):
        for symbol, position in list(self.active_positions.items()):
            ticker = await self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            if current_price <= position['stop_loss']:
                await self.close_position(symbol, "STOP_LOSS")
            elif current_price >= position['take_profit']:
                await self.close_position(symbol, "TAKE_PROFIT")
    
    async def close_position(self, symbol, reason):
        if symbol not in self.active_positions:
            return
        
        position = self.active_positions[symbol]
        side = 'sell' if position['side'] == 'buy' else 'buy'
        ticker = await self.exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        order = await self.exchange.create_order(symbol, side, 'market', position['amount'])
        
        pnl = (current_price - position['entry_price']) * position['amount']
        if position['side'] == 'sell':
            pnl = -pnl
        
        self.logger.info(
            "position_closed", symbol=symbol, reason=reason,
            entry=position['entry_price'], exit=current_price, pnl=pnl
        )
        
        del self.active_positions[symbol]
        self.risk_manager.daily_pnl += pnl
        return True
    
    async def close_all_positions(self):
        for symbol in list(self.active_positions.keys()):
            await self.close_position(symbol, "EMERGENCY")