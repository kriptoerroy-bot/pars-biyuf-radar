from flask import Flask
import threading
import os
import time
from datetime import datetime

from watchlist import (
    get_usdt_futures_pairs,
    analyze_watchlist
)

from strong_signal import (
    analyze_strong_signal
)

from whale_detector import (
    analyze_whale
)

from setup_turtle import (
    analyze_turtle
)

from breakout_detector import (
    analyze_breakout
)

from sniper_break import (
    analyze_sniper_break
)

from market_pulse import (
    analyze_market_pulse
)

from wr_tracker import (
    check_wr,
    load_wr
)

from telegram_sender import (
    send_message
)

from config import (
    WR_TOPIC
)

# =========================
# FLASK (RENDER KEEP ALIVE)
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running 😎"


def run_web():
    port = int(os.environ.get("PORT", 10000))

    print(
        f"🌐 Flask başladı PORT={port}",
        flush=True
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


threading.Thread(
    target=run_web,
    daemon=True
).start()

# =========================
# BOT
# =========================

print(
    "🚀 BOT AÇILDI 😎",
    flush=True
)

last_report_day = None


while True:

    try:

        print(
            "⭐ Market Pulse kontrol ediliyor...",
            flush=True
        )

        analyze_market_pulse()

        print(
            "✅ Market Pulse geçti",
            flush=True
        )

    except Exception as e:

        print(
            f"❌ Market Pulse hata: {e}",
            flush=True
        )

    try:

        print(
            "📝 WR kontrol ediliyor...",
            flush=True
        )

        check_wr()

        print(
            "✅ WR geçti",
            flush=True
        )

    except Exception as e:

        print(
            f"❌ WR hata: {e}",
            flush=True
        )

    # =========================
    # GÜN SONU RAPOR
    # =========================

    try:

        print(
            "🔥 Report kontrol",
            flush=True
        )

        current_time = datetime.now()

        if (
            current_time.hour == 23
            and current_time.minute >= 59
        ):

            today = current_time.strftime(
                "%Y-%m-%d"
            )

            if last_report_day != today:

                print(
                    "🔥 Gün sonu raporu çalışıyor",
                    flush=True
                )

                data = load_wr()

                completed = [
                    x for x in data
                    if x.get("checked_24h")
                ]

                total = len(completed)

                wins = len([
                    x for x in completed
                    if x.get(
                        "result_24h",
                        0
                    ) > 0
                ])

                losses = total - wins

                wr = (
                    (wins / total) * 100
                    if total > 0
                    else 0
                )

                avg_pnl = 0

                if total > 0:

                    avg_pnl = round(
                        sum([
                            x.get(
                                "result_24h",
                                0
                            )
                            for x in completed
                        ]) / total,
                        2
                    )

                report = (
                    "📊 <b>GÜN SONU WR RAPORU</b>\n\n"
                    f"🎯 Toplam Signal: {total}\n"
                    f"✅ Kazanan: {wins}\n"
                    f"❌ Kaybeden: {losses}\n"
                    f"📈 WR: %{wr:.2f}\n"
                    f"💰 Ort. PNL: {avg_pnl}%"
                )

                send_message(
                    report,
                    WR_TOPIC
                )

                print(
                    "📊 Gün sonu raporu gönderildi",
                    flush=True
                )

                last_report_day = today

        print(
            "✅ Report geçti",
            flush=True
        )

    except Exception as e:

        print(
            f"❌ Report hata: {e}",
            flush=True
        )

    # =========================
    # COIN LIST
    # =========================

    try:

        print(
            "🚀 Tarama başladı...",
            flush=True
        )

        coins = (
            get_usdt_futures_pairs()
        )

        print(
            f"📊 {len(coins)} coin bulundu",
            flush=True
        )

    except Exception as e:

        print(
            f"❌ Coin çekme hata: {e}",
            flush=True
        )

        time.sleep(30)
        continue

    # =========================
    # ANALYZE COINS
    # =========================

    for i, coin in enumerate(coins):

        try:

            print(
                f"🔍 {i+1}/{len(coins)} {coin}",
                flush=True
            )

            analyze_watchlist(coin)
            analyze_strong_signal(coin)
            analyze_whale(coin)
            analyze_turtle(coin)
            analyze_breakout(coin)
            analyze_sniper_break(coin)

        except Exception as e:

            print(
                f"❌ Hata {coin}: {e}",
                flush=True
            )

    print(
        "✅ Tarama tamamlandı",
        flush=True
    )

    print(
        "⏳ 2 dakika bekleniyor...\n",
        flush=True
    )

    time.sleep(120)
