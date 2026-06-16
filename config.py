import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

WATCHLIST_TOPIC = int(os.getenv("WATCHLIST_TOPIC", 2))
SETUPS_TOPIC = int(os.getenv("SETUPS_TOPIC", 3))
WHALE_TOPIC = int(os.getenv("WHALE_TOPIC", 5))
MARKET_TOPIC = int(os.getenv("MARKET_TOPIC", 6))
STRONG_SIGNAL_TOPIC = int(os.getenv("STRONG_SIGNAL_TOPIC", 540))
CONFIRM_TOPIC = int(os.getenv("CONFIRM_TOPIC", 1078))
SNIPER_TOPIC = int(os.getenv("SNIPER_TOPIC", 3692))
SCALP_TOPIC = int(os.getenv("SCALP_TOPIC", 6113))
WR_TOPIC = int(os.getenv("WR_TOPIC", 1057))

TRIANGLE_TOPIC = int(os.getenv("TRIANGLE_TOPIC", 7000))
PATTERN_TOPIC = int(os.getenv("PATTERN_TOPIC", 7001))

WATCHLIST_TF = "5m"
BREAKOUT_TF = "15m"

COOLDOWN_MINUTES = 30
