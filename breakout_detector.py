import requests
import pandas as pd
import json
import os
import time

from telegram_sender import send_message
from config import SETUPS_TOPIC

from confirm_manager import (
    add_signal
)

from wr_manager import (
    save_signal
)


COOLDOWN_FILE = (
    "breakout_cooldown.json"
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
            f"❌ Veri çekme "
            f"hatası: {e}"
        )

        return None


def analyze_breakout(
    symbol
):

    try:

        df = get_klines(
            symbol=symbol,
            interval="15m"
        )

        if (
            df is None
            or len(df) < 50
        ):
            return

        df["ema20"] = (
            df["close"]
            .ewm(span=20)
            .mean()
        )

        df["ema50"] = (
            df["close"]
            .ewm(span=50)
            .mean()
        )

        last = (
            df.iloc[-1]
        )

        previous = (
            df.iloc[-15:-1]
        )

        recent_high = (
            previous[
                "high"
            ].max()
        )

        recent_low = (
            previous[
                "low"
            ].min()
        )

        avg_volume = (
            previous[
                "volume"
            ].mean()
        )

        volume_ok = (
            last["volume"]
            > avg_volume * 1.3
        )

        breakout_type = None
        direction = None
        score = 5

        # 📈 LONG BREAKOUT
        if (
            last["close"]
            > recent_high
            and
            last["open"]
            < recent_high
            and
            last["ema20"]
            > last["ema50"]
        ):

            breakout_type = (
                "📈 BREAKOUT"
            )

            direction = (
                "long"
            )

            score += 2

        # 📉 SHORT BREAKDOWN
        elif (
            last["close"]
            < recent_low
            and
            last["open"]
            > recent_low
            and
            last["ema20"]
            < last["ema50"]
        ):

            breakout_type = (
                "📉 BREAKDOWN"
            )

            direction = (
                "short"
            )

            score += 2

        else:
            return

        if volume_ok:
            score += 2

        if score < 7:
            return

        cooldowns = (
            load_cooldown()
        )

        now = (
            time.time()
        )

        if symbol in cooldowns:

            if (
                now
                - cooldowns[
                    symbol
                ]
                < 3600
            ):
                return

        cooldowns[
            symbol
        ] = now

        save_cooldown(
            cooldowns
        )

        try:

            ticker = (
                requests.get(
                    "https://fapi.binance.com"
                    "/fapi/v1/ticker/24hr"
                    f"?symbol={symbol}"
                ).json()
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

        entry_price = (
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
{breakout_type}

${coin} {emoji}{daily_change:+.2f}%

🎯 Score: {score}/10
💰 Fiyat: {entry_price:.4f}
⏰ 15M

📈 {tv_link}

🗣️ Pars:
“Babaaa zinciri kırmış 😈🚀”
"""

        add_signal(
            symbol,
            "breakout",
            direction,
            breakout_type
        )

        save_signal(
            symbol,
            "breakout",
            breakout_type
        )

        send_message(
            message,
            SETUPS_TOPIC
        )

        print(
            f"💥 Breakout: "
            f"{symbol}"
        )

    except Exception as e:

        print(
            f"❌ Breakout "
            f"{symbol}: {e}"
        )