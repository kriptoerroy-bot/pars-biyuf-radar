import json
import os
import time
import requests

from telegram_sender import (
    send_message
)

from config import (
    CONFIRM_TOPIC
)


CONFIRM_FILE = (
    "confirm_signals.json"
)

COOLDOWN_FILE = (
    "confirm_cooldown.json"
)


def load_json(file):

    if os.path.exists(file):

        try:

            with open(
                file,
                "r"
            ) as f:

                return json.load(f)

        except:

            return {}

    return {}


def save_json(
    file,
    data
):

    with open(
        file,
        "w"
    ) as f:

        json.dump(
            data,
            f
        )


def add_signal(
    symbol,
    signal_type,
    direction=None,
    setup_detail=None
):

    signals = load_json(
        CONFIRM_FILE
    )

    cooldowns = load_json(
        COOLDOWN_FILE
    )

    now = time.time()

    if symbol not in signals:

        signals[symbol] = {}

    defaults = {

        "watchlist": False,
        "strong": False,
        "whale": False,
        "turtle": False,
        "breakout": False,
        "three_tap": False,
        "sniper": False,

        "watchlist_dir": None,
        "strong_dir": None,
        "whale_dir": None,
        "turtle_dir": None,
        "breakout_dir": None,
        "three_tap_dir": None,
        "sniper_dir": None,

        "setup_detail": None,
        "last_update": now
    }

    for key, value in defaults.items():

        if key not in signals[symbol]:

            signals[symbol][key] = value

    # Signal işle
    signals[
        symbol
    ][
        signal_type
    ] = True

    dir_key = (
        f"{signal_type}_dir"
    )

    if dir_key in signals[symbol]:

        signals[
            symbol
        ][
            dir_key
        ] = direction

    signals[
        symbol
    ][
        "last_update"
    ] = now

    if setup_detail:

        signals[
            symbol
        ][
            "setup_detail"
        ] = setup_detail

    data = signals[
        symbol
    ]

    # NORMAL MODÜL SAYISI
    module_count = sum([

        data["watchlist"],
        data["strong"],
        data["whale"],
        data["turtle"],
        data["breakout"],
        data["three_tap"]

    ])

    # SCORE
    score = 0

    if data["watchlist"]:
        score += 1

    if data["strong"]:
        score += 1

    if data["whale"]:
        score += 1

    if data["turtle"]:
        score += 1

    if data["breakout"]:
        score += 1

    if data["three_tap"]:
        score += 1

    # 🚀 SNIPER BOOST
    if data["sniper"]:
        score += 2

    # EN AZ 3 AYRI MODÜL
    if module_count >= 3:

        if symbol in cooldowns:

            if (
                now
                - cooldowns[
                    symbol
                ]
                < 3600
            ):

                save_json(
                    CONFIRM_FILE,
                    signals
                )

                return

        cooldowns[
            symbol
        ] = now

        save_json(
            COOLDOWN_FILE,
            cooldowns
        )

        coin = symbol.replace(
            "USDT",
            ""
        )

        setup_text = (
            data[
                "setup_detail"
            ]
            or
            "Yok"
        )

        # Güncel fiyat
        try:

            ticker = requests.get(
                "https://fapi.binance.com"
                "/fapi/v1/ticker/price"
                f"?symbol={symbol}",
                timeout=5
            ).json()

            current_price = float(
                ticker[
                    "price"
                ]
            )

        except:

            current_price = 0

        # Direction Count
        long_count = 0
        short_count = 0

        dirs = [

            data[
                "watchlist_dir"
            ],

            data[
                "strong_dir"
            ],

            data[
                "whale_dir"
            ],

            data[
                "turtle_dir"
            ],

            data[
                "breakout_dir"
            ],

            data[
                "three_tap_dir"
            ],

            data[
                "sniper_dir"
            ]

        ]

        for d in dirs:

            if d == "long":

                long_count += 1

            elif d == "short":

                short_count += 1

        # Alignment
        if (
            long_count >= 3
            and short_count == 0
        ):

            direction_text = (
                "🟢 FULL ALIGNMENT"
            )

            pars_text = (
                "“Baba ekip aynı "
                "tarafta 😈🚀”"
            )

        elif (
            short_count >= 3
            and long_count == 0
        ):

            direction_text = (
                "🔴 FULL SHORT ALIGNMENT"
            )

            pars_text = (
                "“Baba aşağı "
                "kokusu geliyor 😈📉”"
            )

        elif (
            long_count > 0
            and short_count > 0
        ):

            direction_text = (
                "⚠️ SIGNAL CONFLICT"
            )

            pars_text = (
                "“Baba ekip "
                "kavga ediyor 😈👀”"
            )

        else:

            direction_text = (
                "🟡 MIXED FLOW"
            )

            pars_text = (
                "“Baba ortam "
                "karışık 👀”"
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
💎 CONFIRM SIGNAL

${coin}

💰 Fiyat:
{current_price:.4f}

⚡ WATCHLIST {"✅" if data["watchlist"] else "❌"}
🔥 STRONG {"✅" if data["strong"] else "❌"}
🐋 WHALE {"✅" if data["whale"] else "❌"}
🐢 TURTLE {"✅" if data["turtle"] else "❌"}
💥 BREAKOUT {"✅" if data["breakout"] else "❌"}
🎯 THREE TAP {"✅" if data["three_tap"] else "❌"}
🚀 SNIPER {"✅" if data["sniper"] else "❌"}

📌 Setup:
{setup_text}

🧠 CONFIRM SCORE:
{score}/8

🟢 LONG: {long_count}
🔴 SHORT: {short_count}

{direction_text}

{"🚀 SNIPER BOOST" if data["sniper"] else ""}

📈 {tv_link}

🗣️ Pars:
{pars_text}
"""

        send_message(
            message,
            CONFIRM_TOPIC
        )

        print(
            f"💎 Confirm: "
            f"{symbol}"
        )

    save_json(
        CONFIRM_FILE,
        signals
    )