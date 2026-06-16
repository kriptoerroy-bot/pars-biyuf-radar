import requests
import json
import os
import time

from telegram_sender import send_message
from config import WHALE_TOPIC

from confirm_manager import (
    add_signal
)

from wr_manager import (
    save_signal
)


COOLDOWN_FILE = (
    "whale_cooldown.json"
)


def load_json(file_name):

    if os.path.exists(
        file_name
    ):

        try:

            with open(
                file_name,
                "r"
            ) as f:

                return json.load(f)

        except:
            return {}

    return {}


def save_json(
    file_name,
    data
):

    with open(
        file_name,
        "w"
    ) as f:

        json.dump(
            data,
            f
        )


def get_recent_trades(
    symbol
):

    url = (
        "https://fapi.binance.com"
        "/fapi/v1/trades"
        f"?symbol={symbol}"
        "&limit=1000"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        return response.json()

    except:

        return []


def analyze_whale(
    symbol
):

    trades = (
        get_recent_trades(
            symbol
        )
    )

    if not trades:
        return

    buy_volume = 0
    sell_volume = 0

    recent_buy = 0
    recent_sell = 0

    for i, trade in enumerate(
        trades
    ):

        qty = float(
            trade["qty"]
        )

        price = float(
            trade["price"]
        )

        usd_value = (
            qty * price
        )

        is_buy = (
            not trade[
                "isBuyerMaker"
            ]
        )

        if is_buy:

            buy_volume += (
                usd_value
            )

        else:

            sell_volume += (
                usd_value
            )

        if i >= 800:

            if is_buy:

                recent_buy += (
                    usd_value
                )

            else:

                recent_sell += (
                    usd_value
                )

    net_flow = (
        buy_volume
        - sell_volume
    )

    if abs(
        net_flow
    ) < 25000:

        return

    cooldowns = (
        load_json(
            COOLDOWN_FILE
        )
    )

    now = time.time()

    if symbol in cooldowns:

        last_alert = (
            cooldowns[
                symbol
            ]
        )

        if (
            now
            - last_alert
            < 900
        ):
            return

    cooldowns[
        symbol
    ] = now

    save_json(
        COOLDOWN_FILE,
        cooldowns
    )

    whale_abs = abs(
        net_flow
    )

    if whale_abs >= 10000000:

        whale_text = (
            "🐳 GOD MODE"
        )

    elif whale_abs >= 1000000:

        whale_text = (
            "🚀 MEGA WHALE"
        )

    elif whale_abs >= 500000:

        whale_text = (
            "🔥 BIG WHALE"
        )

    elif whale_abs >= 100000:

        whale_text = (
            "🟢 STRONG WHALE"
        )

    else:

        whale_text = (
            "🟡 MINI WHALE"
        )

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

    if net_flow > 0:

        if (
            daily_change > 1
            and recent_buy
            > recent_sell * 1.5
        ):

            whale_comment = (
                "🟢 Güçlü alım baskısı"
            )

            details = (
                "📌 Agresif market alımı\n"
                "📌 Momentum devam edebilir\n"
                "📌 Alıcı baskın"
            )

            pars = (
                "“Baba biri topluyor 😈”"
            )

        elif (
            daily_change < 0.5
        ):

            whale_comment = (
                "🟣 Sessiz toplama"
            )

            details = (
                "📌 Fiyat sakin\n"
                "📌 Satış emiliyor\n"
                "📌 Güç birikiyor olabilir"
            )

            pars = (
                "“Baba sessiz sessiz topluyorlar 👀”"
            )

        else:

            whale_comment = (
                "🟡 Karışık akış"
            )

            details = (
                "📌 Alım var\n"
                "📌 Satış baskısı da hissediliyor\n"
                "📌 Fake move riski"
            )

            pars = (
                "“Baba dikkat, karışık ortam 😈”"
            )

    else:

        whale_comment = (
            "🔴 Güçlü satış baskısı"
        )

        details = (
            "📌 Satıcı baskın\n"
            "📌 Alımlar emiliyor\n"
            "📌 Dump riski olabilir"
        )

        pars = (
            "“Baba biri mal boşaltıyor olabilir 😈”"
        )

    coin_name = symbol.replace(
        "USDT",
        ""
    )

    if whale_abs >= 1_000_000:

        net_text = (
            f"${whale_abs/1_000_000:.2f}M"
        )

    elif whale_abs >= 1000:

        net_text = (
            f"${whale_abs/1000:.0f}K"
        )

    else:

        net_text = (
            f"${whale_abs:.0f}"
        )

    tv_symbol = symbol.replace(
        "USDT",
        "USDT.P"
    )

    tv_link = (
        "https://www.tradingview.com/chart/"
        f"?symbol=BINANCE:{tv_symbol}"
    )

    flow_title = (
        "🐋 NET ALIM"
        if net_flow > 0
        else "🐋 NET SATIŞ"
    )

    sign = (
        "+"
        if net_flow > 0
        else "-"
    )

    message = f"""
${coin_name} {emoji}{daily_change:+.2f}% 🐋

{flow_title}:
{sign}{net_text}

{whale_text}

🧠 Whale Yorumu:
{whale_comment}

{details}

📈 {tv_link}

🗣️ Pars:
{pars}
"""

    direction = (
        "long"
        if net_flow > 0
        else "short"
    )

    add_signal(
        symbol,
        "whale",
        direction
    )

    save_signal(
        symbol,
        "whale"
    )

    send_message(
        message,
        WHALE_TOPIC
    )

    print(
        f"🐋 Whale: "
        f"{symbol}"
    )