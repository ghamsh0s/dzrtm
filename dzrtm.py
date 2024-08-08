import aiohttp
import asyncio
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import hashlib
from datetime import datetime, time
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)

# Telegram bot details
TELEGRAM_BOT_TOKEN = '6996028484:AAHESRCI7ekhF8ZfVlSXkjncn9CIUyKpZ_c'
TELEGRAM_CHAT_ID = '-1002243740808'
CHECK_INTERVAL = 5  # Time between checks in seconds

# Product page URL for arrangement checking
PRODUCT_URL = "https://www.dzrt.com/ar/our-products.html"

# List of product URLs to monitor and their corresponding image URLs
PRODUCT_URLS = [
    "https://www.dzrt.com/en/spicy-zest.html",
    "https://www.dzrt.com/en/haila.html",
    "https://www.dzrt.com/en/samra.html",
    "https://www.dzrt.com/en/tamra.html",
    "https://www.dzrt.com/en/edgy-mint.html",
    "https://www.dzrt.com/en/icy-rush.html",
    "https://www.dzrt.com/en/seaside-frost.html",
    "https://www.dzrt.com/en/garden-mint.html",
    "https://www.dzrt.com/en/highland-berries.html",
    "https://www.dzrt.com/en/mint-fusion.html",
    "https://www.dzrt.com/en/purple-mist.html"
]

PRODUCT_PHOTOS = {
    "https://www.dzrt.com/en/spicy-zest.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/s/p/spicy_zest_3mg_vue04.png",
    "https://www.dzrt.com/en/haila.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/1/5/153a9e23be648dc7153a9e23be648dc7haila__2810mg_29-view4_6_11zon_1.png",
    "https://www.dzrt.com/en/samra.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/s/a/samra__10mg_-view4_1_11zon_1.png",
    "https://www.dzrt.com/en/tamra.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/t/a/tamra__6mg_-view4_3_11zon_1.png",
    "https://www.dzrt.com/en/edgy-mint.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/e/d/edgy_mint_6mg_vue04.png",
    "https://www.dzrt.com/en/icy-rush.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/i/c/icy_rush_10mg_vue04_1.png",
    "https://www.dzrt.com/en/seaside-frost.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/s/e/seaside_frost_10mg_vue04_1.png",
    "https://www.dzrt.com/en/garden-mint.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/g/a/garden_mint_6mg_vue04_1.png",
    "https://www.dzrt.com/en/highland-berries.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/h/i/highland_berries_6mg_vue04_1.png",
    "https://www.dzrt.com/en/mint-fusion.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/m/i/mint_fusion_6mg_vue04_1.png",
    "https://www.dzrt.com/en/purple-mist.html": "https://assets.dzrt.com/media/catalog/product/cache/40c318bf2c9222cf50b132326f5e69e5/p/u/purple_mist_3mg_vue04-20230707.png"
}

# Variable to store the previous product arrangement hash and alert flag
previous_arrangement_hash = None
alert_sent = False

async def send_telegram_message(message, product_name=None, stock_status=None, photo_url=None, product_url=None):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        logging.info("Sending message to Telegram channel...")

        if product_name and stock_status and photo_url and product_url:
            keyboard = [
                [
                    InlineKeyboardButton("🔗 رابط المنتج", url=product_url),
                    InlineKeyboardButton("🔗 رابط السلة", url="https://www.dzrt.com/ar/onestepcheckout.html")
                ],
                [
                    InlineKeyboardButton("🔗 إعادة الطلب", url="https://www.dzrt.com/ar/sales/order/history/"),
                    InlineKeyboardButton("🔗 صفحة الدفع", url="https://www.dzrt.com/ar/onestepcheckout.html")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = (
                f"حالة التوفر: {stock_status}\n"
                
            )
            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=photo_url,
                caption=message,
                reply_markup=reply_markup
            )
        else:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message
            )

        logging.info("Message sent successfully")
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

async def check_page():
    global previous_arrangement_hash, alert_sent
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        try:
            logging.info(f"Checking page for URL: {PRODUCT_URL}")
            async with session.get(PRODUCT_URL) as response:
                logging.info(f"HTTP response status: {response.status}")
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract the part of the page where products are listed
                    products_section = soup.select_one('div.products')  # Adjust the selector to match the actual HTML
                    if products_section:
                        # Convert the products section to a string and calculate its hash
                        current_arrangement_hash = hashlib.md5(products_section.prettify().encode('utf-8')).hexdigest()
                        
                        # Compare with the previous hash
                        if previous_arrangement_hash is None:
                            previous_arrangement_hash = current_arrangement_hash
                            logging.info("Initial product arrangement saved.")
                        elif current_arrangement_hash != previous_arrangement_hash:
                            if not alert_sent:
                                logging.info("Product arrangement has changed.")
                                await send_telegram_message(f"The product arrangement has changed: {PRODUCT_URL}")
                                previous_arrangement_hash = current_arrangement_hash
                                alert_sent = True
                        else:
                            logging.info("No change in product arrangement.")
                            alert_sent = False
                    else:
                        logging.error("Product section not found on the page.")
                else:
                    logging.error(f"Failed to retrieve the page. Status code: {response.status}")
        except aiohttp.ClientError as e:
            logging.error(f"Client error occurred: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

async def check_stock(url):
    async with aiohttp.ClientSession() as session:
        try:
            logging.info(f"Checking stock for URL: {url}")
            async with session.get(url) as response:
                logging.info(f"HTTP response status: {response.status}")
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    logging.debug(soup.prettify())  # Debug: Print the entire HTML
                    stock_info = soup.select_one('div.stock > span')
                    if stock_info:
                        stock_text = stock_info.get_text(strip=True)
                        logging.info(f"Stock status found: {stock_text}")
                        return stock_text
                    else:
                        logging.info("Stock status element not found.")
                        return None
                else:
                    logging.error(f"Failed to retrieve the page. Status code: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            logging.error(f"Client error occurred: {e}")
            return None
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return None

async def monitor_stock():
    # Dictionary to keep track of previous stock statuses
    previous_statuses = {url: None for url in PRODUCT_URLS}

    while True:
        for product_url in PRODUCT_URLS:
            photo_url = PRODUCT_PHOTOS.get(product_url, None)  # Fetch the photo URL
            if photo_url:
                stock_status = await check_stock(product_url)
                if stock_status:
                    if previous_statuses[product_url] is None:
                        # First check, just update the status
                        previous_statuses[product_url] = stock_status
                    else:
                        if stock_status != previous_statuses[product_url]:
                            # Status has changed, send a notification
                            logging.info(f"Stock status changed for {product_url}, sending message...")
                            await send_telegram_message(
                                message=f"Product: {product_url.split('/')[-1].replace('.html', '').title()}\n"
                                        f"Status: {'Available' if stock_status == 'In stock' else 'Not Available'}",
                                product_name=product_url.split('/')[-1].replace('.html', '').title(),  # Extract and format product name
                                stock_status="✅ متوفر" if stock_status == "In stock" else "❌ غير متوفر",
                                photo_url=photo_url,
                                product_url=product_url
                            )
                            previous_statuses[product_url] = stock_status
                        else:
                            logging.info(f"No change in stock status for {product_url}.")
                else:
                    logging.warning(f"Could not retrieve stock status for {product_url}.")
            else:
                logging.warning(f"No photo URL found for {product_url}.")
        
        # Wait before checking again
        await asyncio.sleep(CHECK_INTERVAL)

def is_within_time_range():
    tz = pytz.timezone('Asia/Riyadh')  # Saudi Arabia time zone
    now = datetime.now(tz).time()
    start_time = time(12, 0)  # 12:00 PM
    end_time = time(20, 0)   # 8:00 PM
    return start_time <= now <= end_time

async def monitor_stock_only():
    while True:
        if is_within_time_range():
            await monitor_stock()  # Check stock status
            await check_page()     # Check page arrangement
        else:
            logging.info("Outside monitoring hours. Sleeping until next check.")
        await asyncio.sleep(CHECK_INTERVAL)  # Wait before next check

if __name__ == "__main__":
    asyncio.run(monitor_stock_only())
