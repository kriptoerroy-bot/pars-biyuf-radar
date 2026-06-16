import json
import os
import time

from telegram_sender import send_message
from config import SERI_TOPIC


SIGNAL_FILE = "seri_signals.json"

WINDOW = 5400  # 90 dk


def load_signals():

    if os.path.exists(
        SIGNAL_FILE
    ):

        with open(
            SIGNAL_FILE,
            "r"
        ) as f:

            return json.load(f)

    return {}


def save_signals(data):

    with open(
        SIGNAL_FILE,
        "w"
    ) as f:

        json.dump(data, f)


def add_signal(
    symbol,
    signal_name,
    price,
    timeframe="15M",
    daily_change=0
):

    try:

        data = load_signals()

        now = time.time()

        if symbol not in data:

            data[symbol] = []

        # eski kayıtları sil
        data[symbol] = [

            s for s in data[symbol]

            if now - s["time"] < WINDOW
        ]

        # yeni sinyal ekle
        data[symbol].append({

            "signal": signal_name,
            "time": now
        })

        signals = list(set([
            s["signal"]
            for s in data[symbol]
        ]))

        signal_count = len(
            signals
        )

        save_signals(data)

        # 3+ farklı sinyal
        if signal_count < 3:
            return

        emoji = (
            "🟢"
            if daily_change >= 0
            else "🔴"
        )

        coin = symbol.replace(
            "USDT",
            ""
        )

        signal_icons = {

            "watchlist": "⚡",
            "strong": "🔥",
            "whale": "🐋",
            "turtle": "🐢",
            "breakout": "💥"
        }

        icons = ""

        for s in signals:

            if s in signal_icons:
                icons += (
                    signal_icons[s]
                )

        message = f"""
🚨 SERİ

${coin} {emoji}{daily_change:+.2f}%

📊 {signal_count}x Sinyal

{icons}

💰 {price}
⏰ {timeframe}
"""

        send_message(
            message,
            SERI_TOPIC
        )

        print(
            f"🚨 SERİ: "
            f"{symbol}"
        )

        # spam önleme
        data[symbol] = []

        save_signals(
            data
        )

    except Exception as e:

        print(
            f"❌ SERİ "
            f"{symbol}: {e}"
        )