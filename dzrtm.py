import aiohttp
import asyncio
from bs4 import BeautifulSoup
from telegram import Bot
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Replace these with your actual bot token and chat ID
TELEGRAM_BOT_TOKEN = '6996028484:AAHESRCI7ekhF8ZfVlSXkjncn9CIUyKpZ_c'
TELEGRAM_CHAT_ID = '-1002243740808'
CHECK_INTERVAL = 5  # Time between checks in seconds

# List of product URLs to monitor
PRODUCT_URLS = [
    "https://www.dzrt.com/en/haila.html",
    "https://www.dzrt.com/en/samra.html",
    "https://www.dzrt.com/en/tamra.html",
    "https://www.dzrt.com/en/highland-berries.html",
    "https://www.dzrt.com/en/purple-mist.html",
    "https://www.dzrt.com/en/icy-rush.html",
    "https://www.dzrt.com/en/seaside-frost.html",
    "https://www.dzrt.com/en/mint-fusion.html",
    "https://www.dzrt.com/en/spicy-zest.html",
    "https://www.dzrt.com/en/edgy-mint.html",
    "https://www.dzrt.com/en/garden-mint.html"
]

async def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        logging.info(f"Sending message: {message}")
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info("Message sent successfully")
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

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
                            f"Product at {product_url} stock status changed to: {stock_status}"
                        )
                        previous_statuses[product_url] = stock_status
                    else:
                        logging.info(f"No change in stock status for {product_url}.")
            else:
                logging.warning(f"Could not retrieve stock status for {product_url}.")
        
        # Wait before checking again
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(monitor_stock())
