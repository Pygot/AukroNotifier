# Author: https://github.com/Pygot
#
# This software is provided "as is" without any warranty.
# For inquiries or issues, please create an issue on the repository.

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import timedelta, datetime
from selenium import webdriver
from requests import post
from logger import log_it
from time import sleep

import traceback
import config
import re

options = webdriver.ChromeOptions()
options.add_argument("--blink-settings=imagesEnabled=false")
# -*- #
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
# -*- #

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def get_error(e) -> str:
    tb = traceback.extract_tb(e.__traceback__)
    filename, line, _, text = tb[-1]
    log_it(f"In {filename}, line {line}: {text} | {e}", 2)


def scroll_down() -> None:
    max_scroll_height = driver.execute_script("return document.body.scrollHeight") - 234
    log_it(f"Max scroll height: {max_scroll_height} pixels")
    log_it("Scrolling down...")

    current_scroll_position = driver.execute_script("return window.pageYOffset")

    while current_scroll_position < max_scroll_height:
        try:
            element = driver.find_element(By.TAG_NAME, "mat-dialog-container")
            element.find_element(By.CLASS_NAME, "material-icons").click()
        except: pass

        driver.execute_script("window.scrollBy(0, 1000);")  # 1000 Recommended

        sleep(0.125)

        current_scroll_position = driver.execute_script("return window.pageYOffset")


def convert_time_to_timedelta(time_str):
    days = 0
    hours = 0
    minutes = 0

    day_match = re.search(r'(\d+)\s*(den|dny|d)', time_str)
    if day_match:
        days = int(day_match.group(1))

    hour_match = re.search(r'(\d+)\s*(hodin|hodina|h)', time_str)
    if hour_match:
        hours = int(hour_match.group(1))

    minute_match = re.search(r'(\d+)\s*(minut|minuta|m)', time_str)
    if minute_match:
        minutes = int(minute_match.group(1))

    return timedelta(days=days, hours=hours, minutes=minutes)


def send_text(text: str, link: str, image: str) -> None:
    try:
        text = text.split("\n")
        text.pop(0)
        title = text.pop(1)
        if title == "Žádný příhoz": title = "N/A"

        auctioneer_index = [i for i, val in enumerate(text) if val == "account_circle"]

        try:
            auctioneer_index = auctioneer_index[0] + 1
            auctioneer = text[auctioneer_index]
            text.pop(auctioneer_index)
            text.pop(auctioneer_index - 1)
        except IndexError: auctioneer = "N/A"

        # TIME CHECK

        time_left = None
        for i, val in enumerate(text):
            time_left = convert_time_to_timedelta(val)
            if time_left:
                text.pop(i)
                text.pop(i - 1)
                break

        result_time = time_left - config.MAX_TIME_LEFT_TO_NOTICE

        time_message = None
        if "access_time" in text:
            time_message = "Less than 5 minutes"
        elif result_time <= timedelta(seconds=0):
            time_message = datetime.now() + time_left
            time_message = f"<t:{int(time_message.timestamp())}:R>"

        # PRICE CHECK

        price = None
        for i, val in enumerate(text):
            if " Kč" in val:
                try:
                    price = float(val.replace(" ", "").replace("Kč", "").replace(",", "."))
                    text.pop(i)
                except: continue
                break

        if time_message and price and price <= float(config.MAX_PRICE_PER_AUCTION):
            footer = text.pop(0)

            embed = {
                "username": auctioneer,
                "embeds": [
                    {
                        "title": title,
                        "description": f"Time left: {time_message}\nPrice: ``{price} Kč``\nLink: {link}",
                        "color": 5763719,  # https://gist.github.com/thomasbnt/b6f455e2c7d743b796917fa3c205f812
                        "footer": {"text": footer},
                        "timestamp": datetime.now().isoformat(),
                        "thumbnail": {
                            "url": image
                        }
                    }
                ]
            }

            response = post(config.WEBHOOK, json=embed)

            if response.status_code != 204:
                log_it(f"Failed to send auction: {response.status_code}, {response.text} | {title}", 2)
            else:
                log_it("Successfully sent auction!")
        else:
            log_it(f"Auction ({title}) does not meet config requirements, skipping | Price: {price if price else 'N/A'}")

    except Exception as e: get_error(e)


def list_auctions(url: str) -> list:
    try:
        log_it(f"Loading - {url}")
        driver.get(url)
        log_it(f"Sleeping - {url}")
        WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
        log_it(f"Scrolling down - {url}")
        scroll_down()

        elements = driver.find_elements(By.TAG_NAME, "auk-advanced-item-card")

        for element in elements:
            link = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            image = element.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
            send_text(element.text, link, image)

    except Exception as e: get_error(e)
    finally: driver.quit()


def run():
    try:
        sleep_time = config.MAX_TIME_LEFT_TO_NOTICE.total_seconds() + 1
        while True:
            list_auctions(config.AUKRO_URL)
            log_it(f"Done, sleeping {sleep_time} seconds")
            sleep(sleep_time)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()