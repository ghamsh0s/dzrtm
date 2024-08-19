import requests
from bs4 import BeautifulSoup
import time
import pytz
from datetime import datetime
from telegram import Bot

# Constants
LOGIN_URL = 'https://www.dzrt.com/en/customer/account/loginPost/'
CART_URL = 'https://www.dzrt.com/en/checkout/cart/'
EMAIL = 'nssr4k@gmail.com'
PASSWORD = '116366'
TELEGRAM_BOT_TOKEN = '7057170144:AAFrHvf0JlS1wulR_V3bzi92rf_-r1vEHV0'
TELEGRAM_CHAT_ID = '-1002243740808'

# Initialize session
session = requests.Session()

# Headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.104 Safari/537.36',
    'Referer': LOGIN_URL,
}

# Function to login
def login():
    login_data = {
        'login[username]': EMAIL,
        'login[password]': PASSWORD,
    }
    response = session.post(LOGIN_URL, data=login_data, headers=headers)
    
    # Check if login was successful by looking for a unique element on the dashboard page
    if "dashboard" in response.url or "customer/account" in response.url:
        return True
    else:
        print("Login failed. Response URL:", response.url)
        return False

# Function to check cart page for the specific message
def check_cart():
    response = session.get(CART_URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    no_source_items_msg = "There are no source items with the in stock status"
    out_of_stock_msg = "This product is out of stock."

    no_source_items_present = soup.find(string=no_source_items_msg)
    out_of_stock_present = soup.find(string=out_of_stock_msg)

    # Debugging output
    print("No source items present:", bool(no_source_items_present))
    print("Out of stock message present:", bool(out_of_stock_present))

    # Check if "There are no source items with the in stock status" disappears
    # and "This product is out of stock" remains
    return out_of_stock_present and not no_source_items_present

# Function to send Telegram notification
def send_telegram_notification(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# Function to run the script within the specified time range
def monitor():
    sa_tz = pytz.timezone('Asia/Riyadh')
    while True:
        now = datetime.now(sa_tz)
        if 12 <= now.hour < 24:  # 12 PM to 12 AM Saudi Arabia time
            if not login():
                print("Login failed, retrying in 1 minute...")
                time.sleep(60)
                continue
            
            if check_cart():
                send_telegram_notification("Alert: The product is expected to be in stock soon.")
                print("Notification sent.")
                time.sleep(600)  # Wait 10 minutes before checking again
            else:
                print("No changes detected.")
            
            time.sleep(60)  # Wait 1 minute before checking again
        else:
            print("Outside monitoring hours. Sleeping for 1 hour.")
            time.sleep(3600)  # Sleep for 1 hour before re-checking

# Start monitoring
monitor()
