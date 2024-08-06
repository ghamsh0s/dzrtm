import aiohttp
import asyncio
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import logging
from datetime import datetime, time
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)

# Replace these with your actual bot token and chat ID
TELEGRAM_BOT_TOKEN = '6996028484:AAHESRCI7ekhF8ZfVlSXkjncn9CIUyKpZ_c'
TELEGRAM_CHAT_ID = '-1002243740808'
CHECK_INTERVAL = 2  # Time between checks for product stock in seconds
CART_CHECK_INTERVAL = 600  # Time to refresh the cart page in seconds (10 minutes)

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

# Cart page URL and login details
LOGIN_URL = 'https://www.dzrt.com/en/customer/account/login/'
CART_URL = 'https://www.dzrt.com/en/checkout/cart/'
LOGIN_EMAIL = 'nssr4k@gmail.com'
LOGIN_PASSWORD = '201Sa405'

# Messages to check for on the cart page
MISSING_PRODUCT_MESSAGES = [
    "There are no source items with the in stock status",
    "This product is out of stock."
]

async def send_telegram_message(message, product_name=None, stock_status=None, photo_url=None, product_url=None):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        logging.info("Sending message to Telegram channel...")

        if product_name and stock_status and photo_url and product_url:
            keyboard = [
                [
                    InlineKeyboardButton("رابط المنتج", url=product_url),
                    InlineKeyboardButton("عرض السلة", url=CART_URL)
                ],
                [
                    InlineKeyboardButton("إعادة الطلب", url="https://www.dzrt.com/en/sales/order/history/"),
                    InlineKeyboardButton("صفحة الدفع", url="https://www.dzrt.com/en/onestepcheckout.html")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = (
                f"حالة التوفر: {stock_status}\n"
                f"صورة المنتج:\n{photo_url}"
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

async def login(session):
    login_payload = {
        'login[username]': LOGIN_EMAIL,
        'login[password]': LOGIN_PASSWORD
    }
    async with session.post(LOGIN_URL, data=login_payload) as response:
        if response.status == 200:
            logging.info("Login successful.")
        else:
            logging.error(f"Login failed with status code: {response.status}")

async def check_cart(session):
    async with session.get(CART_URL) as response:
        if response.status == 200:
            html_content = await response.text()
            soup = BeautifulSoup(html_content, 'html.parser')
            cart_info = soup.get_text(strip=True)
            logging.debug(cart_info)  # Debug: Print the entire cart text

            # Check if any of the predefined messages are present
            if any(message in cart_info for message in MISSING_PRODUCT_MESSAGES):
                logging.info("Products are still out of stock.")
            else:
                logging.info("Predefined messages not found in the cart.")
                await send_telegram_message(
                    "ربما تتوفر المنتجات قريبا , كونوا على استعداد"
                )
        else:
            logging.error(f"Failed to retrieve the cart page. Status code: {response.status}")

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
        logging.info("Starting stock check loop...")
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
                                product_name=product_url.split('/')[-1].replace('.html', '').title(),  # Extract and format product name
                                stock_status="متوفر" if stock_status == "In stock" else "غير متوفر",
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

async def monitor_cart_and_stock():
    async with aiohttp.ClientSession() as session:
        await login(session)  # Perform login

        while True:
            logging.info("Checking if within monitoring hours...")
            if is_within_time_range():
                logging.info("Within monitoring hours. Checking cart and stock...")
                await check_cart(session)  # Check cart page
                await monitor_stock()  # Check stock status
            else:
                logging.info("Outside of monitoring hours. Sleeping for 1 hour.")
                await asyncio.sleep(3600)  # Sleep for 1 hour if outside the time range

            await asyncio.sleep(CART_CHECK_INTERVAL)  # Wait before checking the cart page again

if __name__ == "__main__":
    asyncio.run(monitor_cart_and_stock())
