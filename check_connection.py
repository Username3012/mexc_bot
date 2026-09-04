import os
import sys
from dotenv import load_dotenv
import ccxt
import time

# Добавляем папку src в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

load_dotenv()

print("=" * 60)
print("ПРОВЕРКА ПОДКЛЮЧЕНИЯ К РЕАЛЬНОЙ БИРЖЕ MEXC")
print("=" * 60)

# Проверяем наличие ключей
api_key = os.getenv("EXCHANGE_API_KEY")
secret = os.getenv("EXCHANGE_SECRET")
exchange_name = os.getenv("EXCHANGE_NAME", "mexc")
sandbox_mode = os.getenv("SANDBOX_MODE", "false").lower() == "true"

print(f"Биржа: {exchange_name}")
print(f"Режим песочницы (sandbox): {sandbox_mode}")
print(f"API Key: {api_key[:10]}... (длина: {len(api_key) if api_key else 0})")
print(f"Secret: {secret[:10]}... (длина: {len(secret) if secret else 0})")
print()

if not api_key or not secret or api_key == "your_testnet_api_key_here":
    print("❌ ОШИБКА: Ключи не заполнены в файле .env!")
    print("   Откройте .env и вставьте свои ключи от реальной биржи MEXC")
    print("   API ключи нужно создавать на сайте: https://www.mexc.com/")
    exit()

print("✅ Ключи найдены")

# Пробуем подключиться
try:
    print("\n🔄 Подключаемся к реальной бирже MEXC...")
    
    # СОЗДАЕМ КЛИЕНТ ДЛЯ РЕАЛЬНОЙ БИРЖИ (НЕ TESTNET!)
    exchange = ccxt.mexc({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',  # Только спот-торговля
        }
    })
    
    # ВАЖНО: НЕ включаем sandbox для реальной биржи!
    # exchange.set_sandbox_mode(False) - не нужно, по умолчанию False
    
    print("✅ Клиент создан (реальная биржа)")
    print(f"   Режим sandbox: {exchange.sandbox if hasattr(exchange, 'sandbox') else 'false'}")
    
    # Пробуем получить баланс
    print("\n🔄 Проверяем баланс...")
    balance = exchange.fetch_balance()
    
    usdt_balance = balance['total'].get('USDT', 0)
    btc_balance = balance['total'].get('BTC', 0)
    
    print("\n✅ ПОДКЛЮЧЕНИЕ К РЕАЛЬНОЙ БИРЖЕ УСПЕШНО!")
    print(f"   Баланс USDT: {usdt_balance:.2f}")
    print(f"   Баланс BTC: {btc_balance:.8f}")
    print()
    
    if usdt_balance < 10:
        print(f"⚠️ ВНИМАНИЕ: У вас всего {usdt_balance:.2f} USDT")
        print("   Для торговли нужно минимум 10 USDT")
        print("   Пополните баланс на бирже")
    else:
        print(f"✅ Баланс достаточен для торговли (минимум 10 USDT)")
    
    # Пробуем получить цену BTC
    print("\n🔄 Проверяем цену BTC...")
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"   Цена BTC: ${ticker['last']:,.2f}")
    print(f"   24ч объем: ${ticker['quoteVolume']:,.0f}")
    
    print("\n" + "=" * 60)
    print("✅ ВСЕ РАБОТАЕТ! Бот готов к запуску на РЕАЛЬНОЙ бирже.")
    print("=" * 60)
    print()
    print("⚠️ ПРЕДУПРЕЖДЕНИЕ:")
    print("   - Бот будет торговать РЕАЛЬНЫМИ деньгами")
    print("   - Убедитесь, что в .env стоит TEST_MODE=live")
    print("   - Начните с 10-50 USDT для теста")
    
except ccxt.AuthenticationError as e:
    print(f"\n❌ ОШИБКА АУТЕНТИФИКАЦИИ:")
    print(f"   {str(e)}")
    print()
    print("Возможные причины:")
    print("1. Неправильные ключи API (скопируйте заново с mexc.com)")
    print("2. Ключи созданы на testnet, а не на реальной бирже")
    print("3. Ключи имеют неправильные права (нужны Read + Trade)")
    print("4. Ключи просрочены или отозваны")
    
except ccxt.BadSymbol as e:
    print(f"\n❌ ОШИБКА: Символ не найден")
    print(f"   {str(e)}")
    
except Exception as e:
    print(f"\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ:")
    print(f"   {str(e)}")
    print()
    print("Возможные причины:")
    print("1. Нет интернет-соединения")
    print("2. Биржа недоступна (проверьте сайт mexc.com)")
    print("3. VPN или прокси блокируют соединение")
    print("4. Неправильное имя биржи в .env (должно быть EXCHANGE_NAME=mexc)")
    
print()
input("Нажмите Enter для выхода...")