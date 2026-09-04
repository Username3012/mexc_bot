import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ExchangeConfig:
    api_key: str
    secret: str
    exchange_name: str = "mexc"
    sandbox_mode: bool = True

@dataclass
class StrategyConfig:
    symbol: str = "BTC/USDT"
    timeframe: str = "1m"
    fast_ema: int = 50
    slow_ema: int = 200
    rsi_period: int = 7
    volume_spike: float = 1.5

@dataclass
class RiskConfig:
    max_risk_per_trade: float = 0.005
    daily_loss_limit: float = 0.03
    min_notional: float = 10.0

@dataclass
class DatabaseConfig:
    url: str = "sqlite:///trading_bot.db"

@dataclass
class LoggingConfig:
    level: str = "INFO"
    json_format: bool = False
    log_file: str = "test_run.log"

@dataclass
class AppConfig:
    exchange: ExchangeConfig
    strategy: StrategyConfig
    risk: RiskConfig
    database: DatabaseConfig
    logging: LoggingConfig
    poll_interval: int = 5

def load_config():
    return AppConfig(
        exchange=ExchangeConfig(
            api_key=os.getenv("EXCHANGE_API_KEY", ""),
            secret=os.getenv("EXCHANGE_SECRET", ""),
            exchange_name=os.getenv("EXCHANGE_NAME", "mexc"),
            sandbox_mode=os.getenv("SANDBOX_MODE", "true").lower() == "true"
        ),
        strategy=StrategyConfig(
            symbol=os.getenv("TRADING_SYMBOL", "BTC/USDT"),
            timeframe=os.getenv("TIMEFRAME", "1m")
        ),
        risk=RiskConfig(
            max_risk_per_trade=float(os.getenv("MAX_RISK_PER_TRADE", "0.005")),
            daily_loss_limit=float(os.getenv("DAILY_LOSS_LIMIT", "0.03"))
        ),
        database=DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")
        ),
        logging=LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            json_format=os.getenv("LOG_JSON", "false").lower() == "true"
        ),
        poll_interval=int(os.getenv("POLL_INTERVAL", "5"))
    )