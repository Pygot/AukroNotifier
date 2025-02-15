from datetime import timedelta

WEBHOOK = "DISCORD_WEBHOOK"
AUKRO_URL = "https://aukro.cz/pocitace-a-hry-aukce-bazar?sort=endingTime:ASC&attr_48=val_1,3,6"
MAX_TIME_LEFT_TO_NOTICE = timedelta(hours=2, minutes=5)
MAX_PRICE_PER_AUCTION = 500  # Kč
