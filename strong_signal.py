import requests
import pandas as pd

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

from telegram_sender import send_message
from config import STRONG_SIGNAL_TOPIC

from confirm_manager import (
    add_signal
)

from wr_manager import (
    save_signal
)


def get_klines(
    symbol,
    interval="15m",
    limit=100
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

    except:

        return None


def check_breakout_tf(
    symbol,
    interval,
    lookback=20
):

    try:

        df = get_klines(
            symbol=symbol,
            interval=interval,
            limit=100
        )

        if (
            df is None
            or len(df) < 50
        ):
            return False

        df["ema20"] = EMAIndicator(
            df["close"],
            window=20
        ).ema_indicator()

        df["ema50"] = EMAIndicator(
            df["close"],
            window=50
        ).ema_indicator()

        last = (
            df.iloc[-1]
        )

        previous = (
            df.iloc[
                -lookback:-1
            ]
        )

        recent_high = (
            previous[
                "high"
            ].max()
        )

        breakout = (
            last["close"]
            > recent_high
        )

        trend_ok = (
            last["ema20"]
            >
            last["ema50"]
        )

        return (
            breakout
            and trend_ok
        )

    except:

        return False


def analyze_strong_signal(
    symbol
):

    try:

        df = get_klines(
            symbol
        )

        if (
            df is None
            or len(df) < 50
        ):
            return

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

        last_price = (
            df["close"]
            .iloc[-1]
        )

        prev_price = (
            df["close"]
            .iloc[-2]
        )

        momentum = (
            (
                last_price
                - prev_price
            )
            / prev_price
        ) * 100

        last_volume = (
            df["volume"]
            .iloc[-1]
        )

        avg_volume = (
            df["volume"]
            .iloc[-20:]
            .mean()
        )

        trend_ok = (
            ema20.iloc[-1]
            >
            ema50.iloc[-1]
        )

        volume_ok = (
            last_volume
            >
            avg_volume * 1.4
        )

        rsi_ok = (
            rsi.iloc[-1]
            > 52
            and
            rsi.iloc[-1]
            < 72
        )

        momentum_ok = (
            momentum > 0.45
        )

        score = 0

        # NORMAL STRONG SCORE
        if trend_ok:
            score += 2

        if volume_ok:
            score += 3

        if rsi_ok:
            score += 2

        if momentum_ok:
            score += 3

        # MULTI TF BREAKOUT
        break_15m = check_breakout_tf(
            symbol,
            "15m"
        )

        break_4h = check_breakout_tf(
            symbol,
            "4h"
        )

        break_1d = check_breakout_tf(
            symbol,
            "1d"
        )

        break_2d = check_breakout_tf(
            symbol,
            "2d"
        )

        if break_15m:
            score += 1

        if break_4h:
            score += 2

        if break_1d:
            score += 3

        if break_2d:
            score += 4

        if score < 7:
            return

        try:

            ticker_url = (
                "https://fapi.binance.com/"
                "fapi/v1/ticker/24hr"
                f"?symbol={symbol}"
            )

            ticker = requests.get(
                ticker_url,
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

        tv_symbol = symbol.replace(
            "USDT",
            "USDT.P"
        )

        tv_link = (
            "https://www.tradingview.com/chart/"
            f"?symbol=BINANCE:{tv_symbol}"
        )

        tf_strength = 0

        if break_15m:
            tf_strength += 1

        if break_4h:
            tf_strength += 1

        if break_1d:
            tf_strength += 1

        if break_2d:
            tf_strength += 1

        if tf_strength >= 3:

            pars_text = (
                "“Babaaa burada "
                "canavar güç var 😈🚀”"
            )

        elif tf_strength >= 2:

            pars_text = (
                "“Babaaa güç "
                "toplanıyor 😈🔥”"
            )

        else:

            pars_text = (
                "“Babaaa burada "
                "güç var 😈🔥”"
            )

        message = f"""
🔥 STRONG SIGNAL

${coin} {emoji}{daily_change:+.2f}%

🎯 Score: {score}/20
💰 {last_price:.4f}

⚡ 15M {"✅" if break_15m else "❌"}
⚡ 4H {"✅" if break_4h else "❌"}
🔥 1D {"✅" if break_1d else "❌"}
👑 2D {"✅" if break_2d else "❌"}

📈 {tv_link}

🗣️ Pars:
{pars_text}
"""

        add_signal(
            symbol,
            "strong",
            "long"
        )

        save_signal(
            symbol,
            "strong"
        )

        send_message(
            message,
            STRONG_SIGNAL_TOPIC
        )

        print(
            f"🔥 Strong: "
            f"{symbol}"
        )

    except Exception as e:

        print(
            f"❌ Strong "
            f"{symbol}: {e}"
        )