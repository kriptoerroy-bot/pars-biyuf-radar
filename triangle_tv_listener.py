from flask import Flask, request, jsonify
from telegram_sender import send_message
import os
import threading

# Environment variables
TRIANGLE_TOPIC = int(os.getenv("TRIANGLE_TOPIC", 7000))
PATTERN_TOPIC = int(os.getenv("PATTERN_TOPIC", 7001))

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():

    try:
        data = request.json

        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON"
            }), 400

        signal_type = data.get("type")

        symbol = data.get("symbol", "UNKNOWN")
        side = data.get("side", "")
        tf = data.get("timeframe", "")
        strength = data.get("strength", "")
        entry = data.get("entry", "")
        sl = data.get("sl", "")
        tp1 = data.get("tp1", "")
        tp2 = data.get("tp2", "")
        tp3 = data.get("tp3", "")
        tv_link = data.get("tv_link", "")

        # TRIANGLE BREAKOUT
        if signal_type == "triangle_breakout":

            emoji = "🟢" if side == "LONG" else "🔴"

            text = (
                f"{emoji} <b>{symbol} {side}</b>\n\n"
                f"📐 Triangle Breakout\n"
                f"⚡ Güç: {strength}\n\n"
                f"📍 <b>Entry:</b> {entry}\n\n"
                f"🎯 TP1: {tp1}\n"
                f"🎯 TP2: {tp2}\n"
                f"🎯 TP3: {tp3}\n\n"
                f"🛑 SL: {sl}\n\n"
                f"⏰ TF: {tf}\n\n"
                f'📊 <a href="{tv_link}">TradingView Aç</a>'
            )

            send_message(
                text,
                TRIANGLE_TOPIC
            )

        # TP HIT
        elif signal_type == "tp_hit":

            target = data.get(
                "target",
                "TP"
            )

            text = (
                f"🎯 <b>{symbol} "
                f"{target} HIT</b>\n\n"
                f"SL → Break Even"
            )

            send_message(
                text,
                TRIANGLE_TOPIC
            )

        # SL HIT
        elif signal_type == "sl_hit":

            text = (
                f"🛑 <b>{symbol} "
                f"STOP LOSS HIT</b>"
            )

            send_message(
                text,
                TRIANGLE_TOPIC
            )

        # CLASSIC PATTERN
        elif signal_type == "classic_pattern":

            pattern = data.get(
                "pattern",
                ""
            )

            emoji = (
                "🟢"
                if side == "LONG"
                else "🔴"
            )

            text = (
                f"{emoji} "
                f"<b>{symbol}</b>\n\n"
                f"📊 {pattern}\n"
                f"📍 {side}\n"
                f"⏰ TF: {tf}"
            )

            send_message(
                text,
                PATTERN_TOPIC
            )

        return jsonify({
            "status": "ok"
        })

    except Exception as e:

        print(
            "WEBHOOK ERROR:",
            e
        )

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


def start_tv_listener():

    thread = threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=5000,
            debug=False,
            use_reloader=False
        )
    )

    thread.daemon = True
    thread.start()

    print(
        "✅ TV Listener başladı"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
