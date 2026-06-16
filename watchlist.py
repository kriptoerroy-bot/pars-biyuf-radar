import requests
import pandas as pd
import json
import os

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

from telegram_sender import send_message
from config import WATCHLIST_TOPIC

from confirm_manager import add_signal
from wr_manager import save_signal


COUNTER_FILE = "watchlist_counter.json"


def load_counter():

    if os.path.exists(
        COUNTER_FILE
    ):

        with open(
            COUNTER_FILE,
            "r"
        ) as f:

            return json.load(
                f
            )

    return {}


def save_counter(data):

    with open(
        COUNTER_FILE,
        "w"
    ) as f:

        json.dump(
            data,
            f
        )


def get_usdt_futures_pairs():

    url = (
        "https://fapi.binance.com/"
        "fapi/v1/exchangeInfo"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        data = response.json()

        usdt_pairs = []

        for symbol in data[
            "symbols"
        ]:

            symbol_name = symbol[
                "symbol"
            ]

            if (
                symbol[
                    "quoteAsset"
                ]
                == "USDT"
                and
                symbol[
                    "status"
                ]
                == "TRADING"
                and
                symbol[
                    "contractType"
                ]
                == "PERPETUAL"
                and "_"
                not in symbol_name
            ):

                usdt_pairs.append(
                    symbol_name
                )

        print(
            f"✅ "
            f"{len(usdt_pairs)} "
            f"coin bulundu"
        )

        return sorted(
            usdt_pairs
        )

    except Exception as e:

        print(
            "❌ Coin çekme hatası:",
            e
        )

        return []


def get_klines(
    symbol,
    interval="1m",
    limit=100
):

    url = (
        "https://fapi.binance.com"
        "/fapi/v1/klines"
        f"?symbol={symbol}"
        f"&interval={interval}"
        f"&limit={limit}"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        data = response.json()

        df = pd.DataFrame(
            data
        )

        df = df.iloc[:, :6]

        df.columns = [
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]

        for col in [
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]:

            df[col] = (
                df[col]
                .astype(float)
            )

        return df

    except Exception as e:

        print(
            f"❌ {symbol} veri hatası:",
            e
        )

        return None


def analyze_watchlist(
    symbol
):

    df = get_klines(
        symbol
    )

    if (
        df is None
        or len(df)
        < 50
    ):
        return

    ema20 = (
        EMAIndicator(
            df["close"],
            window=20
        )
        .ema_indicator()
    )

    rsi = (
        RSIIndicator(
            df["close"],
            window=14
        )
        .rsi()
    )

    last_price = (
        df["close"]
        .iloc[-1]
    )

    prev_price = (
        df["close"]
        .iloc[-2]
    )

    last_volume = (
        df["volume"]
        .iloc[-1]
    )

    avg_volume = (
        df["volume"]
        .tail(20)
        .mean()
    )

    trend_ok = (
        last_price >
        ema20.iloc[-1]
    )

    volume_ok = (
        last_volume >
        avg_volume * 1.7
    )

    momentum_ok = (
        last_price >
        prev_price
    )

    rsi_ok = (
        rsi.iloc[-1]
        < 78
    )

    price_change = (
        (
            last_price -
            prev_price
        )
        /
        prev_price
    ) * 100

    speed_ok = (
        price_change > 0.7
    )

    score = 0

    if trend_ok:
        score += 1

    if volume_ok:
        score += 2

    if momentum_ok:
        score += 1

    if rsi_ok:
        score += 1

    if speed_ok:
        score += 2

    if score >= 4:

        try:

            ticker_url = (
                "https://fapi.binance.com/"
                "fapi/v1/ticker/24hr"
                f"?symbol={symbol}"
            )

            ticker = (
                requests.get(
                    ticker_url,
                    timeout=10
                )
                .json()
            )

            daily_change = (
                float(
                    ticker[
                        "priceChangePercent"
                    ]
                )
            )

        except:

            daily_change = 0

        change_emoji = (
            "🟢"
            if daily_change >= 0
            else "🔴"
        )

        coin_name = (
            symbol.replace(
                "USDT",
                ""
            )
        )

        counters = (
            load_counter()
        )

        if (
            coin_name
            not in counters
        ):

            counters[
                coin_name
            ] = 0

        counters[
            coin_name
        ] += 1

        signal_count = (
            counters[
                coin_name
            ]
        )

        save_counter(
            counters
        )

        power_text = ""

        if (
            signal_count >= 2
        ):

            power_text = (
                "\n🔥 Güç toplanıyor olabilir"
            )

        tv_symbol = (
            symbol.replace(
                "USDT",
                "USDT.P"
            )
        )

        tv_link = (
            "https://www.tradingview.com/chart/"
            f"?symbol=BINANCE:{tv_symbol}"
        )

        message = f"""
${coin_name} {change_emoji}{daily_change:+.2f}% 🛰️{signal_count}

💰 {last_price:.4f}

⚡ Momentum: {price_change:.2f}%
📊 Score: {score}/7
📈 Volume Spike: {last_volume / avg_volume:.1f}x

📈 {tv_link}

🗣️ Pars:
“Baba burada hareket kokusu var 👀🚀”
{power_text}
"""

        add_signal(
            symbol,
            "watchlist",
            "long"
        )

        save_signal(
            symbol,
            "watchlist"
        )

        send_message(
            message,
            WATCHLIST_TOPIC
        )