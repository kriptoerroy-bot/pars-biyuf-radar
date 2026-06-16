import requests
import pandas as pd
import json
import os
import time

from ta.trend import EMAIndicator

from telegram_sender import (
    send_message
)

from config import (
    SETUPS_TOPIC
)

from confirm_manager import (
    add_signal
)

from wr_manager import (
    save_signal
)


COOLDOWN_FILE = (
    "three_tap_cooldown.json"
)


def load_cooldown():

    if os.path.exists(
        COOLDOWN_FILE
    ):

        with open(
            COOLDOWN_FILE,
            "r"
        ) as f:

            return json.load(
                f
            )

    return {}


def save_cooldown(
    data
):

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
    limit=80
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


def analyze_three_tap(
    symbol
):

    try:

        df = get_klines(
            symbol
        )

        if (
            df is None
            or len(df)
            < 50
        ):
            return

        last = (
            df.iloc[-1]
        )

        previous = (
            df.iloc[-25:-1]
        )

        ema20 = (
            EMAIndicator(
                df["close"],
                window=20
            )
            .ema_indicator()
        )

        ema50 = (
            EMAIndicator(
                df["close"],
                window=50
            )
            .ema_indicator()
        )

        avg_volume = (
            previous[
                "volume"
            ]
            .mean()
        )

        volume_ok = (
            last["volume"]
            >
            avg_volume * 1.2
        )

        resistance = (
            previous[
                "high"
            ]
            .max()
        )

        support = (
            previous[
                "low"
            ]
            .min()
        )

        tolerance = 0.003

        resistance_hits = sum(

            abs(
                previous["high"]
                - resistance
            )
            / resistance
            <
            tolerance

        )

        support_hits = sum(

            abs(
                previous["low"]
                - support
            )
            / support
            <
            tolerance

        )

        three_tap_type = None
        direction = None
        score = 5
        pars_text = ""

        # LONG
        if (
            resistance_hits >= 2
            and
            last["close"]
            >= resistance * 0.997
        ):

            three_tap_type = (
                "🎯 LONG THREE TAP"
            )

            direction = (
                "long"
            )

            score += 2

            if (
                ema20.iloc[-1]
                >
                ema50.iloc[-1]
            ):
                score += 1

            if volume_ok:
                score += 1

            pars_text = (
                "“Baba kapıyı "
                "3 kere zorladı "
                "😈🚀”"
            )

        # SHORT
        elif (
            support_hits >= 2
            and
            last["close"]
            <= support * 1.003
        ):

            three_tap_type = (
                "🎯 SHORT THREE TAP"
            )

            direction = (
                "short"
            )

            score += 2

            if (
                ema20.iloc[-1]
                <
                ema50.iloc[-1]
            ):
                score += 1

            if volume_ok:
                score += 1

            pars_text = (
                "“Baba zemin "
                "çatlıyor "
                "😈📉”"
            )

        else:
            return

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
{three_tap_type}

${coin} {emoji}{daily_change:+.2f}%

🔨 3. test algılandı
🎯 Score: {score}/10
💰 Fiyat: {price:.4f}
⏰ 15M

📈 {tv_link}

🗣️ Pars:
{pars_text}
"""

        add_signal(
            symbol,
            "three_tap",
            direction,
            three_tap_type
        )

        save_signal(
            symbol,
            "three_tap",
            three_tap_type
        )

        send_message(
            message,
            SETUPS_TOPIC
        )

        print(
            f"🎯 Three Tap: "
            f"{symbol}"
        )

    except Exception as e:

        print(
            f"❌ Three Tap "
            f"{symbol}: {e}"
        )