import json
import os
import requests
import time


WR_FILE = "wr_data.json"


def load_wr():

    if os.path.exists(
        WR_FILE
    ):

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

        data = requests.get(
            url,
            timeout=10
        ).json()

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

    data.append(
        signal
    )

    save_wr(data)

    print(
        f"📝 WR kayıt: "
        f"{symbol}"
    )