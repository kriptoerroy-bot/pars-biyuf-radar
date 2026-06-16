import requests
import time

from tradingview_ta import (
    TA_Handler,
    Interval
)

from telegram_sender import (
    send_message
)

from config import (
    MARKET_TOPIC
)

# ==========================
# CONFIG
# ==========================

COINGECKO_URL = (
    "https://api.coingecko.com"
    "/api/v3/global"
)

# breakout botunda kullanmak için
market_score = 0
market_mode = "UNKNOWN"


# ==========================
# TRADINGVIEW ANALYSIS
# ==========================

def get_tv_analysis(
    symbol,
    interval
):

    try:

        handler = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange="BINANCE",
            interval=interval
        )

        return (
            handler
            .get_analysis()
        )

    except Exception as e:

        print(
            f"TV Error "
            f"{symbol}: {e}"
        )

        return None


def trend_score(
    summary_1h,
    summary_4h,
    max_score
):

    score = 0

    text = "🔴 Weak"

    r1 = summary_1h.get(
        "RECOMMENDATION",
        "NEUTRAL"
    )

    r4 = summary_4h.get(
        "RECOMMENDATION",
        "NEUTRAL"
    )

    # Strong bullish
    if (
        r1 == "BUY"
        and
        r4 == "BUY"
    ):

        score = max_score

        text = (
            "🟢 Strong"
        )

    # Mixed
    elif (
        r1 == "BUY"
        or
        r4 == "BUY"
    ):

        score = int(
            max_score * 0.6
        )

        text = (
            "🟡 Mixed"
        )

    return (
        score,
        text,
        r1,
        r4
    )


# ==========================
# MARKET CAP DATA
# ==========================

def get_market_data():

    try:

        data = requests.get(
            COINGECKO_URL,
            timeout=10
        ).json()["data"]

        total_cap = (
            data["total_market_cap"]
            ["usd"]
        )

        btc_dom = (
            data["market_cap_percentage"]
            ["btc"]
        )

        eth_dom = (
            data["market_cap_percentage"]
            ["eth"]
        )

        usdt_dom = (
            data["market_cap_percentage"]
            ["usdt"]
        )

        btc_cap = (
            total_cap
            * btc_dom
            / 100
        )

        eth_cap = (
            total_cap
            * eth_dom
            / 100
        )

        total2 = (
            total_cap
            - btc_cap
        )

        total3 = (
            total2
            - eth_cap
        )

        return {
            "btc_dom": btc_dom,
            "usdt_dom": usdt_dom,
            "total2": total2,
            "total3": total3
        }

    except Exception as e:

        print(
            f"Market Data "
            f"Error: {e}"
        )

        return None


# ==========================
# TREND CHECK
# ==========================

def get_direction(
    current,
    previous
):

    if current > previous:

        return (
            "🟢 Strengthening",
            True
        )

    elif current == previous:

        return (
            "🟡 Neutral",
            False
        )

    return (
        "🔴 Weakening",
        False
    )


# ==========================
# MAIN ANALYSIS
# ==========================

def analyze_market_pulse():

    global market_score
    global market_mode
   

    try:

        score = 0

        # ==================
        # BTC
        # ==================

        btc_1h = get_tv_analysis(
            "BTCUSDT",
            Interval.INTERVAL_1_HOUR
        )

        btc_4h = get_tv_analysis(
            "BTCUSDT",
            Interval.INTERVAL_4_HOURS
        )

        btc_score, btc_text, _, _ = (
            trend_score(
                btc_1h.summary,
                btc_4h.summary,
                25
            )
        )

        score += btc_score

        # ==================
        # ETH
        # ==================

        eth_1h = get_tv_analysis(
            "ETHUSDT",
            Interval.INTERVAL_1_HOUR
        )

        eth_4h = get_tv_analysis(
            "ETHUSDT",
            Interval.INTERVAL_4_HOURS
        )

        eth_score, eth_text, _, _ = (
            trend_score(
                eth_1h.summary,
                eth_4h.summary,
                20
            )
        )

        score += eth_score

        # ==================
        # MARKET DATA
        # ==================

        current = (
            get_market_data()
        )

        time.sleep(2)

        previous = (
            get_market_data()
        )

        btc_dom = (
            current["btc_dom"]
        )

        usdt_dom = (
            current["usdt_dom"]
        )

        # BTC.D
        btcd_text, btcd_ok = (
            get_direction(
                previous["btc_dom"],
                btc_dom
            )
        )

        if btcd_ok:
            score += 15

        # USDT.D
        usdt_text, usdt_ok = (
            get_direction(
                usdt_dom,
                previous["usdt_dom"]
            )
        )

        if usdt_ok:
            score += 15

        # TOTAL2
        total2_text, total2_ok = (
            get_direction(
                current["total2"],
                previous["total2"]
            )
        )

        if total2_ok:
            score += 15

        # TOTAL3
        total3_text, total3_ok = (
            get_direction(
                current["total3"],
                previous["total3"]
            )
        )

        if total3_ok:
            score += 10

        market_score = score

        # ==================
        # MARKET MODE
        # ==================

        if score >= 76:

            market_mode = (
                "🟢 ALTCOIN ATTACK"
            )

        elif score >= 56:

            market_mode = (
                "🟡 SELECTIVE ATTACK"
            )

        elif score >= 36:

            market_mode = (
                "🟠 CAUTION MODE"
            )

        else:

            market_mode = (
                "🔴 DEFENSIVE MODE"
            )

        # ==================
        # COMMENT
        # ==================

        comments = []

        if btc_score >= 20:
            comments.append(
                "BTC güçlü."
            )
        else:
            comments.append(
                "BTC tam güçlü değil."
            )

        if eth_score >= 15:
            comments.append(
                "ETH marketi destekliyor."
            )
        else:
            comments.append(
                "ETH zayıf."
            )

        if total3_ok:
            comments.append(
                "Altcoin momentumu olumlu."
            )

        if usdt_ok:
            comments.append(
                "Risk iştahı güçlü."
            )

        if score < 40:
            comments.append(
                "Yeni girişlerde dikkat."
            )

        comment = (
            " ".join(comments)
        )

        # ==================
        # MESSAGE
        # ==================

        message = f"""
⭐ MARKET PULSE

{market_mode}

₿ BTC:
{btc_text}

⟠ ETH:
{eth_text}

📊 BTC.D:
{btc_dom:.2f}%
{btcd_text}

💵 USDT.D:
{usdt_dom:.2f}%
{usdt_text}

📈 TOTAL2:
{total2_text}

🚀 TOTAL3:
{total3_text}

🧠 Pulse Score:
{score}/100

💬 Market Yorumu:
{comment}
"""

        send_message(
            message,
            MARKET_TOPIC
        )

        print(
            "⭐ Market Pulse sent"
        )

    except Exception as e:

        print(
            f"❌ Market Pulse: {e}"
        )