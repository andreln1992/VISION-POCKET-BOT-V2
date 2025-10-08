import os
import requests
import time
from datetime import datetime

# === CONFIG ===
API_KEY = os.getenv("FCS_API_KEY")
LICENSE = os.getenv("LICENSE_CODE", "FREE")
EMA_PERIOD = 10
RSI_PERIOD = 14
FREE_LIMIT = 50  # daily free signals

# === MAJOR FOREX PAIRS ===
CURRENCY_PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]

# === STORAGE ===
signal_count = 0


def get_market_data(symbol):
    """Fetch recent candle data for given pair"""
    try:
        pair_code = symbol.replace("/", "")
        url = f"https://fcsapi.com/api-v3/forex/candle?symbol={pair_code}&period=1m&access_key={API_KEY}"
        response = requests.get(url)
        data = response.json()
        if data.get("status"):
            return data["response"]
        else:
            print(f"⚠️ API Error for {symbol}: {data.get('msg')}")
            return None
    except Exception as e:
        print(f"❌ Connection error for {symbol}: {e}")
        return None


def calculate_ema(prices, period):
    """Simple EMA calculation"""
    k = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = price * k + ema * (1 - k)
    return ema


def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    if len(prices) < period:
        return 50
    gains = []
    losses = []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def generate_signal(symbol):
    """Generate signal for given currency pair"""
    global signal_count
    data = get_market_data(symbol)
    if not data:
        return

    closes = [float(c["c"]) for c in data[-RSI_PERIOD * 2 :]]
    ema = calculate_ema(closes, EMA_PERIOD)
    rsi = calculate_rsi(closes, RSI_PERIOD)
    last_close = closes[-1]

    signal = "HOLD"
    confidence = 60
    expiry = "1m"

    if last_close > ema and rsi < 70:
        signal = "BUY"
        confidence = round(70 + (70 - rsi) / 2, 2)
    elif last_close < ema and rsi > 30:
        signal = "SELL"
        confidence = round(70 + (rsi - 30) / 2, 2)

    signal_count += 1

    print(
        f"📈 {datetime.now().strftime('%H:%M:%S')} | {symbol:<8} | "
        f"{signal:<4} | RSI={rsi:.2f} | EMA={ema:.5f} | Conf={confidence}% | Expiry={expiry}"
    )


if __name__ == "__main__":
    print("🚀 Pocket Option Multi-Pair Signal Bot started...")
    print(f"License: {LICENSE}")
    print(f"Tracking {len(CURRENCY_PAIRS)} pairs...")

    while True:
        if LICENSE == "FREE" and signal_count >= FREE_LIMIT:
            print("⚠️ Free daily limit reached. Upgrade for unlimited access.")
            break

        for pair in CURRENCY_PAIRS:
            generate_signal(pair)
            time.sleep(2)  # avoid API overload

        print("⏳ Waiting 1 minute for next scan...\n")
        time.sleep(60)
