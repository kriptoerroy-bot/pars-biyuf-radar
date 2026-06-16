import requests
import pandas as pd
import json
import os

from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

from telegram_sender import send_message
from config import SETUPS_TOPIC

from confirm_manager import (
    add_signal
)

from wr_manager import (
    save_signal
)


COOLDOWN_FILE = (
    "turtle_cooldown.json"
)


def load_cooldown():

    if os.path.exists(
        COOLDOWN_FILE
    ):

        with open(
            COOLDOWN_FILE,
            "r"
        ) as f:

            return json.load(f)

    return {}


def save_cooldown(data):

    with open(
        COOLDOWN_FILE,
        "w"
    ) as f:

        json.dump(data, f)


def get_klines(
    symbol,
    interval="15m",
    limit=60
):

    url = (
        "https://fapi.binance.com/"
        "fapi/v1/klines"
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
            f"❌ Turtle veri "
            f"hatası: {e}"
        )

        return None


def analyze_turtle(
    symbol
):

    try:

        df = get_klines(
            symbol
        )

        if df is None:
            return

        if len(df) < 50:
            return

        last = (
            df.iloc[-1]
        )

        ema20 = EMAIndicator(
            df["close"],
            window=20
        ).ema_indicator()

        ema50 = EMAIndicator(
            df["close"],
            window=50
        ).ema_indicator()

        rsi = RSIIndicator(
            df["close"],
            window=14
        ).rsi()

        current_rsi = (
            rsi.iloc[-1]
        )

        avg_volume = (
            df["volume"]
            .iloc[-21:-1]
            .mean()
        )

        volume_ok = (
            last["volume"]
            > avg_volume * 1.15
        )

        last_20_high = (
            df["high"]
            .iloc[-21:-1]
            .max()
        )

        last_20_low = (
            df["low"]
            .iloc[-21:-1]
            .min()
        )

        turtle_type = None
        direction = None
        score = 4

        # 🐢 LONG
        if (
            last["low"]
            < last_20_low
            and
            last["close"]
            > last_20_low
        ):

            turtle_type = (
                "🐢 LONG TURTLE"
            )

            direction = (
                "long"
            )

            score += 2

            if volume_ok:
                score += 1

            if (
                ema20.iloc[-1]
                >
                ema50.iloc[-1]
            ):
                score += 1

            if current_rsi < 45:
                score += 1

        # 🐢 SHORT
        elif (
            last["high"]
            > last_20_high
            and
            last["close"]
            < last_20_high
        ):

            turtle_type = (
                "🐢 SHORT TURTLE"
            )

            direction = (
                "short"
            )

            score += 2

            if volume_ok:
                score += 1

            if (
                ema20.iloc[-1]
                <
                ema50.iloc[-1]
            ):
                score += 1

            if current_rsi > 55:
                score += 1

        else:
            return

        if score < 6:
            return

        cooldown = (
            load_cooldown()
        )

        if symbol in cooldown:
            return

        cooldown[
            symbol
        ] = True

        save_cooldown(
            cooldown
        )

        try:

            ticker = (
                requests.get(
                    "https://fapi.binance.com"
                    "/fapi/v1/ticker/24hr"
                    f"?symbol={symbol}"
                ).json()
            )

            daily_change = float(
                ticker[
                    "priceChangePercent"
                ]
            )

        except:

            daily_change = 0

        emoji = (
            "🟢"
            if daily_change >= 0
            else "🔴"
        )

        coin = (
            symbol.replace(
                "USDT",
                ""
            )
        )

        price = (
            last["close"]
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
{turtle_type}

${coin} {emoji}{daily_change:+.2f}%

🎯 Score: {score}/10
💰 Fiyat: {price:.4f}
⏰ 15M

📈 {tv_link}

🗣️ Pars:
“Babaaa turtle uyandı 😎🐢”
"""

        add_signal(
            symbol,
            "turtle",
            direction,
            turtle_type
        )

        save_signal(
            symbol,
            "turtle",
            turtle_type
        )

        send_message(
            message,
            SETUPS_TOPIC
        )

        print(
            f"🐢 Turtle: "
            f"{symbol}"
        )

    except Exception as e:

        print(
            f"❌ Turtle "
            f"{symbol}: {e}"
        )