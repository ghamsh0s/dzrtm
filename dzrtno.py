import aiohttp
import asyncio
from bs4 import BeautifulSoup
from telegram import Bot
import logging
import hashlib
from datetime import datetime, time
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)

# Telegram bot details
TELEGRAM_BOT_TOKEN = '7207906313:AAGsj1zHZeCK6NDd87pPqfbYOcae5OrWdWw'
TELEGRAM_CHAT_ID = '-1002243740808'
CHECK_INTERVAL = 5  # Time between checks in seconds

# Product page URL
PRODUCT_URL = "https://www.dzrt.com/en/our-products.html"

# Headers to mimic a browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Variables to track product arrangements and daily notifications
previous_arrangement_hash = None
last_notification_date = None

async def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        logging.info("Sending message to Telegram channel...")
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info("Message sent successfully")
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

async def check_page():
    global previous_arrangement_hash, last_notification_date

    # Get current Saudi Arabia time
    tz = pytz.timezone('Asia/Riyadh')
    sa_time = datetime.now(tz)

    # Check if current time is between 12 PM and 12 AM
    if not time(12, 0) <= sa_time.time() < time(23, 59):
        logging.info("Outside monitoring hours.")
        return

    # Check if we already sent a notification today
    if last_notification_date is not None and last_notification_date.date() == sa_time.date():
        logging.info("Notification already sent today. Ignoring further changes.")
        return

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        try:
            logging.info(f"Checking page for URL: {PRODUCT_URL}")
            async with session.get(PRODUCT_URL) as response:
                logging.info(f"HTTP response status: {response.status}")
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract the part of the page where products are listed
                    products_section = soup.select_one('div.products')
                    if products_section:
                        # Convert the products section to a string and calculate its hash
                        current_arrangement_hash = hashlib.md5(products_section.prettify().encode('utf-8')).hexdigest()
                        
                        # Compare with the previous hash
                        if previous_arrangement_hash is None:
                            previous_arrangement_hash = current_arrangement_hash
                            logging.info("Initial product arrangement saved.")
                        elif current_arrangement_hash != previous_arrangement_hash:
                            logging.info("Product arrangement has changed.")
                            await send_telegram_message(f"ربما تتوفر المنتجات قريبا تسجيل دخول وتحديث الصفحة")
                            previous_arrangement_hash = current_arrangement_hash
                            last_notification_date = sa_time  # Update the last notification date
                        else:
                            logging.info("No change in product arrangement.")
                    else:
                        logging.error("Product section not found on the page.")
                else:
                    logging.error(f"Failed to retrieve the page. Status code: {response.status}")
        except aiohttp.ClientError as e:
            logging.error(f"Client error occurred: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

async def monitor_page():
    while True:
        await check_page()
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(monitor_page())
