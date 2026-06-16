import json
import os
import time
import requests

WR_FILE = "wr_data.json"


def load_wr():

    if os.path.exists(WR_FILE):

        try:

            with open(
                WR_FILE,
                "r"
            ) as f:

                return json.load(f)

        except:

            return []

    return []


def save_wr(data):

    with open(
        WR_FILE,
        "w"
    ) as f:

        json.dump(
            data,
            f,
            indent=4
        )


def get_price(symbol):

    try:

        url = (
            "https://fapi.binance.com"
            "/fapi/v1/ticker/price"
            f"?symbol={symbol}"
        )

        response = requests.get(
            url,
            timeout=3
        )

        data = response.json()

        return float(
            data["price"]
        )

    except:

        return None


def save_signal(
    symbol,
    signal_type,
    setup_type="None"
):

    data = load_wr()

    entry_price = (
        get_price(symbol)
    )

    if entry_price is None:
        return

    signal = {

        "symbol":
        symbol,

        "type":
        signal_type,

        "setup":
        setup_type,

        "entry":
        entry_price,

        "time":
        time.time(),

        "checked_1h":
        False,

        "checked_4h":
        False,

        "checked_24h":
        False
    }

    data.append(signal)

    save_wr(data)

    print(
        f"📝 WR kayıt: "
        f"{symbol}"
    )


def check_wr():

    print(
        "📝 WR kontrol "
        "başladı..."
    )

    data = load_wr()

    # ⚡ Son 300 kayıt
    data = data[-300:]

    now = time.time()

    updated = False

    price_cache = {}

    print(
        f"📝 WR kayıt sayısı: "
        f"{len(data)}"
    )

    for i, signal in enumerate(data):

        try:

            symbol = signal.get(
                "symbol"
            )

            if not symbol:
                continue

            # ✅ Hepsi tamamlandıysa geç
            if (
                signal.get(
                    "checked_1h"
                )
                and signal.get(
                    "checked_4h"
                )
                and signal.get(
                    "checked_24h"
                )
            ):
                continue

            print(
                f"🔍 "
                f"{i+1}/"
                f"{len(data)} "
                f"{symbol}"
            )

            entry = signal.get(
                "entry"
            )

            # ⚡ Cache sistemi
            if (
                symbol
                in price_cache
            ):

                current_price = (
                    price_cache[
                        symbol
                    ]
                )

            else:

                current_price = (
                    get_price(
                        symbol
                    )
                )

                price_cache[
                    symbol
                ] = (
                    current_price
                )

            if (
                current_price
                is None
            ):
                continue

            pnl = (
                (
                    current_price
                    - entry
                )
                / entry
            ) * 100

            age = (
                now
                - signal[
                    "time"
                ]
            )

            # 1H
            if (
                age >= 3600
                and not signal.get(
                    "checked_1h"
                )
            ):

                signal[
                    "result_1h"
                ] = round(
                    pnl,
                    2
                )

                signal[
                    "checked_1h"
                ] = True

                updated = True

                print(
                    f"📝 1H "
                    f"{symbol} "
                    f"{pnl:+.2f}%"
                )

            # 4H
            if (
                age >= 14400
                and not signal.get(
                    "checked_4h"
                )
            ):

                signal[
                    "result_4h"
                ] = round(
                    pnl,
                    2
                )

                signal[
                    "checked_4h"
                ] = True

                updated = True

                print(
                    f"📝 4H "
                    f"{symbol} "
                    f"{pnl:+.2f}%"
                )

            # 24H
            if (
                age >= 86400
                and not signal.get(
                    "checked_24h"
                )
            ):

                signal[
                    "result_24h"
                ] = round(
                    pnl,
                    2
                )

                signal[
                    "checked_24h"
                ] = True

                updated = True

                print(
                    f"📝 24H "
                    f"{symbol} "
                    f"{pnl:+.2f}%"
                )

        except Exception as e:

            print(
                f"❌ WR hata "
                f"{symbol}: "
                f"{e}"
            )

    if updated:

        save_wr(data)

        print(
            "✅ WR "
            "güncellendi"
        )

    print(
        "✅ WR geçti"
    )