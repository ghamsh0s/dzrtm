import aiohttp
import asyncio
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import logging
from datetime import datetime, time, timedelta
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)

# Replace these with your actual bot token and chat ID
TELEGRAM_BOT_TOKEN = '6996028484:AAHESRCI7ekhF8ZfVlSXkjncn9CIUyKpZ_c'
TELEGRAM_CHAT_ID = '-1002243740808'
CHECK_INTERVAL = 5  # Time between checks in seconds

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

# URL for the main product page to monitor arrangement changes
PRODUCT_PAGE_URL = "https://www.dzrt.com/en/our-products.html"

async def send_telegram_message(product_name, stock_status, photo_url, product_url):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        logging.info(f"Sending message for product: {product_name}")

        # Create inline keyboard buttons in pairs
        keyboard = [
            [
                InlineKeyboardButton("رابط المنتج", url=product_url),
                InlineKeyboardButton("عرض السلة", url="https://www.dzrt.com/en/checkout/cart/")
            ],
            [
                InlineKeyboardButton("إعادة الطلب", url="https://www.dzrt.com/en/sales/order/history/"),
                InlineKeyboardButton("صفحة الدفع", url="https://www.dzrt.com/en/onestepcheckout.html")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Prepare the message
        message = (
            f"Product: {product_name}\n"
            f"Stock Status: {stock_status}\n"
            f"Photo:\n{photo_url}"
        )

        # Send the message
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo_url,
            caption=message,
            reply_markup=reply_markup
        )
        logging.info("Message sent successfully")
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

async def send_arrangement_change_alert():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        logging.info("Sending arrangement change alert")
        message = "تم تغيير ترتيب المنتجات. هذا يشير إلى أن بعض المنتجات ستكون متاحة قريبًا."
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info("Arrangement change alert sent successfully")
    except Exception as e:
        logging.error(f"Failed to send arrangement change alert: {e}")

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

async def check_product_arrangement():
    async with aiohttp.ClientSession() as session:
        try:
            logging.info(f"Checking product arrangement for URL: {PRODUCT_PAGE_URL}")
            async with session.get(PRODUCT_PAGE_URL) as response:
                logging.info(f"HTTP response status: {response.status}")
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    products = soup.select('li.product-item')  # Adjust the selector as needed
                    product_ids = [product['data-product-id'] for product in products]
                    logging.info(f"Product arrangement: {product_ids}")
                    return product_ids
                else:
                    logging.error(f"Failed to retrieve the product page. Status code: {response.status}")
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
    previous_arrangement = None

    # Set timezone for Saudi Arabia
    saudi_tz = pytz.timezone('Asia/Riyadh')

    while True:
        # Check stock for individual products
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
                                stock_status="متوفر" if "In stock" in stock_status else "غير متوفر",
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

        # Get current time in Saudi Arabia
        now_saudi = datetime.now(saudi_tz).time()

        # Check product arrangement only between 12 PM and 6 PM Saudi Arabia time
        if time(12, 0) <= now_saudi <= time(18, 0):
            current_arrangement = await check_product_arrangement()
            if current_arrangement:
                if previous_arrangement is None:
                    # First check, just update the arrangement
                    previous_arrangement = current_arrangement
                else:
                    if current_arrangement != previous_arrangement:
                        # Arrangement has changed, send an alert
                        logging.info("Product arrangement has changed, sending alert...")
                        await send_arrangement_change_alert()
                        previous_arrangement = current_arrangement
                    else:
                        logging.info("No change in product arrangement.")

        # Wait before checking again
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(monitor_stock())
