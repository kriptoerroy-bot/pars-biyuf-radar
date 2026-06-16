import requests
import pandas as pd
import json
import os
import time

from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange

from telegram_sender import (
    send_message
)

from config import (
    SNIPER_TOPIC
)

from confirm_manager import (
    add_signal
)

from wr_manager import (
    save_signal
)


COOLDOWN_FILE = (
    "sniper_cooldown.json"
)


def load_cooldown():

    if os.path.exists(
        COOLDOWN_FILE
    ):

        try:

            with open(
                COOLDOWN_FILE,
                "r"
            ) as f:

                return json.load(f)

        except:

            return {}

    return {}


def save_cooldown(data):

    with open(
        COOLDOWN_FILE,
        "w"
    ) as f:

        json.dump(
            data,
            f
        )


def get_klines(
    symbol,
    interval="15m",
    limit=120
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
            f"❌ Sniper veri "
            f"hatası: {e}"
        )

        return None


def analyze_sniper_break(
    symbol
):

    try:

        df = get_klines(
            symbol=symbol,
            interval="15m"
        )

        if (
            df is None
            or len(df) < 80
        ):
            return

        # EMA
        df["ema20"] = EMAIndicator(
            df["close"],
            window=20
        ).ema_indicator()

        df["ema50"] = EMAIndicator(
            df["close"],
            window=50
        ).ema_indicator()

        # ATR
        atr = AverageTrueRange(
            df["high"],
            df["low"],
            df["close"],
            window=14
        ).average_true_range()

        last = (
            df.iloc[-1]
        )

        # 🔥 DAHA ERKEN BREAKOUT
        previous = (
            df.iloc[-10:-1]
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

        # 🔥 Hacim filtresi yumuşatıldı
        volume_ok = (
            last["volume"]
            >
            avg_volume * 1.2
        )

        long_trend = (
            last["ema20"]
            >
            last["ema50"]
        )

        short_trend = (
            last["ema20"]
            <
            last["ema50"]
        )

        # Mum gücü
        candle_body = abs(
            last["close"]
            - last["open"]
        )

        candle_range = (
            last["high"]
            - last["low"]
        )

        body_ratio = (
            candle_body
            / candle_range
            if candle_range > 0
            else 0
        )

        strong_candle = (
            body_ratio > 0.55
        )

        sniper_type = None
        direction = None
        score = 5
       
        # 🚀 LONG SNIPER
        if (
            last["close"]
            > recent_high
            and
            last["high"]
            > recent_high
            and
            long_trend
            and
            volume_ok
            and
            strong_candle
        ):

            sniper_type = (
                "🚀 SNIPER LONG"
            )

            direction = (
                "long"
            )

            score += 5

        # 🔻 SHORT SNIPER
        elif (
            last["close"]
            < recent_low
            and
            last["low"]
            < recent_low
            and
            short_trend
            and
            volume_ok
            and
            strong_candle
        ):

            sniper_type = (
                "🔻 SNIPER SHORT"
            )

            direction = (
                "short"
            )

            score += 5

        else:
            return

        if score < 8:
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
                < 7200
            ):

                return

        cooldowns[
            symbol
        ] = now

        save_cooldown(
            cooldowns
        )

        try:

            ticker = requests.get(
                "https://fapi.binance.com"
                "/fapi/v1/ticker/24hr"
                f"?symbol={symbol}",
                timeout=10
            ).json()

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

        coin = symbol.replace(
            "USDT",
            ""
        )

        entry_price = (
            last["close"]
        )

        atr_value = (
            atr.iloc[-1]
        )

        # 🎯 DAHA MANTIKLI TP/SL
        if direction == "long":

            tp1 = (
                entry_price
                + atr_value * 1.2
            )

            tp2 = (
                entry_price
                + atr_value * 2.2
            )

            tp3 = (
                entry_price
                + atr_value * 3.5
            )

            sl = (
                entry_price
                - atr_value * 1.0
            )

        else:

            tp1 = (
                entry_price
                - atr_value * 1.2
            )

            tp2 = (
                entry_price
                - atr_value * 2.2
            )

            tp3 = (
                entry_price
                - atr_value * 3.5
            )

            sl = (
                entry_price
                + atr_value * 1.0
            )

        tv_symbol = symbol.replace(
            "USDT",
            "USDT.P"
        )

        tv_link = (
            "https://www.tradingview.com/chart/"
            f"?symbol=BINANCE:{tv_symbol}"
        )

        message = f"""
{sniper_type}

${coin} {emoji}{daily_change:+.2f}%

🎯 Score: {score}/10
💰 Giriş: {entry_price:.4f}

🎯 TP1: {tp1:.4f}
🎯 TP2: {tp2:.4f}
🎯 TP3: {tp3:.4f}

🛑 SL: {sl:.4f}

⏰ 15M

📈 {tv_link}

🗣️ Pars:
“Baba düşeni kırmışlar 😈🚀”
"""

        add_signal(
            symbol,
            "sniper",
            direction,
            sniper_type
        )

        save_signal(
            symbol,
            "sniper",
            sniper_type
        )

        send_message(
            message,
            SNIPER_TOPIC
        )

        print(
            f"🚀 Sniper: "
            f"{symbol}"
        )

    except Exception as e:

        print(
            f"❌ Sniper "
            f"{symbol}: {e}"
        )