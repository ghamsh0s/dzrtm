import aiohttp
import asyncio
from bs4 import BeautifulSoup
from telegram import Bot

# Replace these with your actual bot token and chat ID
TELEGRAM_BOT_TOKEN = '6996028484:AAHESRCI7ekhF8ZfVlSXkjncn9CIUyKpZ_c'
TELEGRAM_CHAT_ID = '-1002243740808'  # Your channel ID
CHECK_INTERVAL = 60  # Time between checks in seconds

async def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    print(f"Sending message: {message}")  # Debugging information
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    print("Message sent successfully")  # Debugging information

async def check_stock(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    print(soup.prettify())  # Print the HTML content for debugging
                    stock_info = soup.find("div", class_="stock unavailable")
                    if stock_info:
                        stock_text = stock_info.find("span").text
                        print(f"Stock status found: {stock_text}")  # Debugging information
                        return stock_text
                    else:
                        print("Stock status element not found.")
                        return None
                else:
                    print(f"Failed to retrieve the page. Status code: {response.status}")
                    return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

async def monitor_stock():
    product_url = "https://www.dzrt.com/en/purple-mist.html"
    previous_status = None

    while True:
        stock_status = await check_stock(product_url)
        if stock_status:
            if "Back In Stock Soon" not in stock_status:
                if previous_status == "Back In Stock Soon":
                    print("Product is back in stock, sending message...")  # Debugging information
                    await send_telegram_message(f"Product is back in stock! Check it out: {product_url}")
                previous_status = "In Stock"
            else:
                previous_status = "Back In Stock Soon"
        else:
            print("Could not retrieve stock status.")
        
        # Wait before checking again
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(monitor_stock())
