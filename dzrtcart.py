from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from telegram import Bot
from datetime import datetime
import pytz
from webdriver_manager.chrome import ChromeDriverManager

# Constants
LOGIN_URL = 'https://www.dzrt.com/en/customer/account/login/'
CART_URL = 'https://www.dzrt.com/en/checkout/cart/'
EMAIL = 'nssr4k@gmail.com'
PASSWORD = '116366'
TELEGRAM_BOT_TOKEN = '7057170144:AAFrHvf0JlS1wulR_V3bzi92rf_-r1vEHV0'
TELEGRAM_CHAT_ID = '-1002243740808'

# Setup Selenium with visible Chrome
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
# Uncomment the following line if you want to run headless
# chrome_options.add_argument("--headless")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def handle_age_verification():
    try:
        # Wait explicitly for the pop-up to appear with a longer timeout
        age_modal = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.modal#modal-age-verification'))
        )
        print("Age verification pop-up detected.")
        
        # Once the pop-up is detected, wait a little more to ensure it is fully loaded
        time.sleep(2)
        
        # Click the "Yes I am" button to proceed
        yes_button = age_modal.find_element(By.XPATH, "//button[contains(text(), 'Yes I am')]")
        yes_button.click()
        print("Clicked 'Yes I am' button.")
        
        # Wait until the modal is no longer visible
        WebDriverWait(driver, 5).until(EC.invisibility_of_element(age_modal))
        print("Age verification modal closed.")
        
    except Exception as e:
        print("No age verification pop-up found or failed to handle:", e)

def login():
    driver.get(LOGIN_URL)

    # Handle age verification pop-up if present
    handle_age_verification()

    try:
        # Wait for the page to fully load before interacting
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Enter email and password
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "login[username]"))
        )
        username_field.send_keys(EMAIL)

        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "login[password]"))
        )
        password_field.send_keys(PASSWORD)

        # Wait for the login button to be clickable
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "send2"))
        )

        # Scroll the button into view and click it using JavaScript to avoid click interception
        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        driver.execute_script("arguments[0].click();", login_button)

        # Wait for the mini cart counter to load and show a valid number
        max_wait_time = 20  # Total time to wait for the cart counter (in seconds)
        poll_interval = 1    # Check every 1 second
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            try:
                cart_counter = driver.find_element(By.CSS_SELECTOR, 'span.counter-number')
                cart_count = cart_counter.text.strip()

                if cart_count.isdigit() and int(cart_count) > 0:
                    print("Login successful based on mini cart counter.")
                    return True
            except:
                pass

            # Wait for a second before checking again
            time.sleep(poll_interval)
            elapsed_time += poll_interval

        # If we exit the loop, it means the counter was not detected in time
        print("Login failed: Mini cart counter did not show a valid number within the time limit.")
        return False

    except Exception as e:
        print(f"Login failed: {e}")
        return False

def check_cart():
    driver.get(CART_URL)
    time.sleep(5)  # Ensure all elements load

    # Look for the "No source items" and "Out of stock" messages
    no_source_items_present = driver.find_elements(By.XPATH, "//*[contains(text(), 'There are no source items')]")
    out_of_stock_present = driver.find_elements(By.XPATH, "//*[contains(text(), 'This product is out of stock')]")

    # Debugging output
    print("No source items message found:", bool(no_source_items_present))
    print("Out of stock message found:", bool(out_of_stock_present))

    return out_of_stock_present and not no_source_items_present

def send_telegram_notification(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def monitor():
    sa_tz = pytz.timezone('Asia/Riyadh')
    logged_in = False
    while True:
        now = datetime.now(sa_tz)
        if 12 <= now.hour < 24:  # 12 PM to 12 AM Saudi Arabia time
            if not logged_in:
                logged_in = login()
                if not logged_in:
                    print("Login failed, retrying in 1 minute...")
                    time.sleep(60)
                    continue

            if check_cart():
                send_telegram_notification("Alert: The product is expected to be in stock soon.")
                print("Notification sent.")
                time.sleep(600)  # Wait 10 minutes before checking again
            else:
                print("No changes detected.")
            
            # Refresh page to keep session alive
            driver.refresh()
            time.sleep(60)  # Wait 1 minute before checking again
        else:
            print("Outside monitoring hours. Sleeping for 1 hour.")
            time.sleep(3600)  # Sleep for 1 hour before re-checking

# Start monitoring
monitor()
