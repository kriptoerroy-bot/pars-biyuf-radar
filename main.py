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

from datetime import (
    datetime
)

import time


print(
    "🚀 BOT AÇILDI 😎"
)

last_report_day = None


while True:

    try:

        print(
            "⭐ Market Pulse kontrol ediliyor..."
        )

        analyze_market_pulse()

        print(
            "✅ Market Pulse geçti"
        )

    except Exception as e:

        print(
            f"❌ Market Pulse hata: {e}"
        )

    try:

        print(
            "📝 WR kontrol ediliyor..."
        )

        check_wr()

        print(
            "✅ WR geçti"
        )

    except Exception as e:

        print(
            f"❌ WR hata: {e}"
        )

    # 📊 GÜN SONU REPORT
    try:

        print(
            "🔥 Report kontrol"
        )

        current_time = (
            datetime.now()
        )

        if (
            current_time.hour == 23
            and current_time.minute >= 59
        ):

            today = (
                current_time.strftime(
                    "%Y-%m-%d"
                )
            )

            if (
                last_report_day
                != today
            ):

                print(
                    "🔥 Gün sonu raporu çalışıyor"
                )

                data = (
                    load_wr()
                )

                completed = [

                    x for x
                    in data

                    if x.get(
                        "checked_24h"
                    )
                ]

                total = len(
                    completed
                )

                wins = len([

                    x for x
                    in completed

                    if x.get(
                        "result_24h",
                        0
                    ) > 0
                ])

                losses = (
                    total
                    - wins
                )

                wr = (

                    (
                        wins
                        / total
                    ) * 100

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

                            for x
                            in completed

                        ])

                        / total,

                        2
                    )

                report = (

                    "📊 "
                    "<b>GÜN SONU WR RAPORU</b>\n\n"

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
                    "📊 Gün sonu raporu gönderildi"
                )

                last_report_day = (
                    today
                )

        print(
            "✅ Report geçti"
        )

    except Exception as e:

        print(
            f"❌ Report hata: {e}"
        )

    try:

        print(
            "🚀 Tarama başladı..."
        )

        coins = (
            get_usdt_futures_pairs()
        )

        print(
            f"📊 {len(coins)} coin bulundu"
        )

    except Exception as e:

        print(
            f"❌ Coin çekme hata: {e}"
        )

        time.sleep(30)
        continue

    for i, coin in enumerate(coins):

        try:

            print(
                f"🔍 {i+1}/{len(coins)} {coin}"
            )

            # ⚡ WATCHLIST
            analyze_watchlist(
                coin
            )

            # 🔥 STRONG
            analyze_strong_signal(
                coin
            )

            # 🐋 WHALE
            analyze_whale(
                coin
            )

            # 🐢 TURTLE
            analyze_turtle(
                coin
            )

            # 💥 BREAKOUT
            analyze_breakout(
                coin
            )

            # 🚀 SNIPER BREAK
            analyze_sniper_break(
                coin
            )

        except Exception as e:

            print(
                f"❌ Hata {coin}: {e}"
            )

    print(
        "✅ Tarama tamamlandı"
    )

    print(
        "⏳ 2 dakika bekleniyor...\n"
    )

    time.sleep(
        120
    )

from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()
