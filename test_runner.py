import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Добавляем папку src в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from exchange_client import ExchangeClient
from logging_config import configure_logging, console_print
from paper_trader import PaperTrader
from strategy import ScalpingStrategy
from risk_manager import ScalpingRiskManager
from test_analyzer import TestAnalyzer


class TestRunner:
    def __init__(self):
        console_print("=" * 60, "START")
        console_print("ЗАПУСК БОТА ДЛЯ РЕАЛЬНОЙ ТОРГОВЛИ", "START")
        console_print("=" * 60, "START")
        
        console_print("Шаг 1: Загрузка конфигурации...", "INFO")
        load_dotenv()
        self.config = load_config()
        console_print("✅ Конфигурация загружена", "INFO")
        
        console_print("Шаг 2: Настройка логирования...", "INFO")
        self.logger = configure_logging(
            level="INFO", 
            json_format=False,
            log_file="live_trading.log"
        )
        console_print("✅ Логирование настроено", "INFO")
        
        console_print("Шаг 3: Подключение к бирже MEXC...", "INFO")
        self.exchange = ExchangeClient(self.config.exchange, self.logger)
        console_print("✅ Подключение к бирже установлено", "INFO")
        
        symbols_env = os.getenv("TEST_SYMBOLS", "BTC/USDT")
        self.test_symbols = [s.strip() for s in symbols_env.split(",")]
        console_print(f"✅ Торгуемые символы: {self.test_symbols}", "INFO")
        
        console_print("Шаг 4: Инициализация стратегии...", "INFO")
        self.strategy = ScalpingStrategy(
            ema_period=int(os.getenv("EMA_PERIOD", 50)),
            rsi_period=int(os.getenv("RSI_PERIOD", 14)),
            volume_spike=float(os.getenv("VOLUME_SPIKE", 1.8)),
            lookback_levels=int(os.getenv("LOOKBACK_LEVELS", 50)),
            min_trend_strength=float(os.getenv("MIN_TREND_STRENGTH", 0.3)),
            historical_bars=int(os.getenv("HISTORICAL_BARS", 200))
        )
        console_print("✅ Стратегия инициализирована", "INFO")
        
        console_print("Шаг 5: Инициализация риск-менеджера...", "INFO")
        self.risk_manager = ScalpingRiskManager(
            config=self.config.risk,
            logger=self.logger,
            max_concurrent_positions=int(os.getenv("MAX_CONCURRENT_POSITIONS", 1)),
            sl_percent=float(os.getenv("SL_PERCENT", 0.015)),
            tp_percent=float(os.getenv("TP_PERCENT", 0.025))
        )
        console_print("✅ Риск-менеджер инициализирован", "INFO")
        
        self.initial_balance = float(os.getenv("INITIAL_BALANCE", 10))
        console_print(f"✅ Начальный баланс: ${self.initial_balance:.2f}", "INFO")
        
        console_print("Шаг 6: Инициализация трейдера...", "INFO")
        self.paper_trader = PaperTrader(
            exchange_client=self.exchange,
            strategy=self.strategy,
            risk_manager=self.risk_manager,
            logger=self.logger,
            initial_balance=self.initial_balance,
            symbols=self.test_symbols
        )
        console_print("✅ Трейдер инициализирован", "INFO")
        
        self.analyzer = TestAnalyzer()
        
        # Проверяем режим торговли
        test_mode = os.getenv("TEST_MODE", "paper")
        self.is_live = test_mode == "live"
        
        console_print("=" * 60, "INFO")
        if self.is_live:
            console_print("⚠️  РЕЖИМ РЕАЛЬНОЙ ТОРГОВЛИ (LIVE)!", "WARNING")
            console_print(f"   Начальный баланс: ${self.initial_balance:.2f}", "INFO")
            console_print("   ВНИМАНИЕ: Бот будет торговать реальными деньгами!", "WARNING")
        else:
            console_print("📊 РЕЖИМ БУМАЖНОЙ ТОРГОВЛИ (PAPER)", "INFO")
        console_print("=" * 60, "INFO")
        
        self.test_duration_hours = float(os.getenv("TEST_DURATION_HOURS", 24))
        console_print(f"⏱️  Тест будет идти {self.test_duration_hours:.1f} часов", "INFO")
        console_print("🚀 ЗАПУСК!", "INFO")
        console_print("")
    
    async def run_test(self):
        console_print("⏳ Начинаем торговлю...", "INFO")
        
        end_time = datetime.utcnow() + timedelta(hours=self.test_duration_hours)
        iteration = 0
        last_report_time = datetime.utcnow()
        
        while datetime.utcnow() < end_time:
            iteration += 1
            
            try:
                # Обрабатываем каждый символ
                for symbol in self.test_symbols:
                    await self.paper_trader.process_symbol(symbol)
                
                # Проверяем позиции
                if iteration % 10 == 0:
                    now = datetime.utcnow()
                    if (now - last_report_time).seconds >= 60:  # Раз в минуту
                        console_print(
                            f"📊 Статус: итерация {iteration}, "
                            f"позиций: {len(self.paper_trader.positions)}, "
                            f"баланс: ${self.paper_trader.current_balance:.2f}, "
                            f"сделок: {len(self.paper_trader.trades)}",
                            "INFO"
                        )
                        last_report_time = now
                
                await asyncio.sleep(int(os.getenv("POLL_INTERVAL", 60)))
                
            except KeyboardInterrupt:
                console_print("⏹️  Остановка по запросу пользователя", "WARNING")
                break
            except Exception as e:
                console_print(f"❌ Ошибка: {str(e)}", "ERROR")
                await asyncio.sleep(10)
        
        console_print("⏰ Тест завершен!", "INFO")
        console_print("Закрываем все позиции...", "INFO")
        await self.paper_trader.close_all_positions()
        
        # Генерируем отчет
        self.generate_report()
    
    def generate_report(self):
        console_print("Генерация отчета...", "INFO")
        stats = self.paper_trader.get_stats()
        report = self.analyzer.generate_report(stats)
        
        os.makedirs("results", exist_ok=True)
        with open("results/report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        console_print("=" * 60, "INFO")
        console_print("📊 ОТЧЕТ О ТОРГОВЛЕ", "INFO")
        console_print("=" * 60, "INFO")
        print(report)
        console_print("=" * 60, "INFO")
        console_print(f"✅ Отчет сохранен в: results/report.txt", "INFO")


async def main():
    try:
        runner = TestRunner()
        await runner.run_test()
    except Exception as e:
        console_print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", "ERROR")
        import traceback
        traceback.print_exc()
    
    console_print("👋 Бот остановлен", "INFO")
    input("\nНажмите Enter для выхода...")


if __name__ == "__main__":
    asyncio.run(main())