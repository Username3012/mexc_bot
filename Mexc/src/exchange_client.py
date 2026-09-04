import asyncio
import math
import ccxt
from config import ExchangeConfig

class ExchangeClient:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.exchange = None
        self._init_exchange()
    
    def _init_exchange(self):
        exchange_class = getattr(ccxt, self.config.exchange_name)
        self.exchange = exchange_class({
            'apiKey': self.config.api_key,
            'secret': self.config.secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        if self.config.sandbox_mode:
            self.exchange.set_sandbox_mode(True)
        self.logger.info("exchange_initialized", exchange=self.config.exchange_name)
    
    async def fetch_ohlcv(self, symbol, timeframe, limit=100):
        return await asyncio.to_thread(
            self.exchange.fetch_ohlcv, symbol, timeframe, limit=limit
        )
    
    async def fetch_ticker(self, symbol):
        result = await asyncio.to_thread(self.exchange.fetch_ticker, symbol)
        return {'last': result['last']}
    
    async def fetch_balance(self):
        return await asyncio.to_thread(self.exchange.fetch_balance)
    
    async def create_order(self, symbol, side, order_type, amount, price=None):
        market = self.exchange.market(symbol)
        precision = market['precision']['amount']
        amount = math.floor(amount / precision) * precision
        
        return await asyncio.to_thread(
            self.exchange.create_order, symbol, order_type, side, amount, price
        )