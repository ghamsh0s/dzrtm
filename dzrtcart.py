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

def log(message):
    print(f"{datetime.now()}: {message}")

def handle_age_verification():
    try:
        age_modal = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.modal#modal-age-verification'))
        )
        log("Age verification pop-up detected.")
        time.sleep(2)
        yes_button = age_modal.find_element(By.XPATH, "//button[contains(text(), 'Yes I am')]")
        yes_button.click()
        log("Clicked 'Yes I am' button.")
        WebDriverWait(driver, 5).until(EC.invisibility_of_element(age_modal))
        log("Age verification modal closed.")
    except Exception as e:
        log("No age verification pop-up found or failed to handle: " + str(e))

def login():
    driver.get(LOGIN_URL)
    log("Navigated to login page.")
    handle_age_verification()

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "login[username]"))
        )
        username_field.send_keys(EMAIL)

        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "login[password]"))
        )
        password_field.send_keys(PASSWORD)

        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "send2"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        driver.execute_script("arguments[0].click();", login_button)
        log("Clicked login button.")

        max_wait_time = 20
        poll_interval = 1
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            try:
                cart_counter = driver.find_element(By.CSS_SELECTOR, 'span.counter-number')
                cart_count = cart_counter.text.strip()

                if cart_count.isdigit() and int(cart_count) > 0:
                    log("Login successful based on mini cart counter.")
                    return True
            except:
                pass

            time.sleep(poll_interval)
            elapsed_time += poll_interval

        log("Login failed: Mini cart counter did not show a valid number within the time limit.")
        return False

    except Exception as e:
        log("Login failed: " + str(e))
        return False

def check_cart():
    driver.get(CART_URL)
    time.sleep(5)
    log("Navigated to cart page.")

    no_source_items_present = driver.find_elements(By.XPATH, "//*[contains(text(), 'There are no source items')]")
    out_of_stock_present = driver.find_elements(By.XPATH, "//*[contains(text(), 'This product is out of stock')]")

    log("No source items message found: " + str(bool(no_source_items_present)))
    log("Out of stock message found: " + str(bool(out_of_stock_present)))

    return out_of_stock_present and not no_source_items_present

def send_telegram_notification(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    log("Telegram notification sent.")

def monitor():
    logged_in = False
    while True:
        if not logged_in:
            logged_in = login()
            if not logged_in:
                log("Login failed, retrying in 1 minute...")
                time.sleep(60)
                continue

        if check_cart():
            send_telegram_notification("Alert: The product is expected to be in stock soon.")
            log("Notification sent.")
            time.sleep(600)
        else:
            log("No changes detected.")

        driver.refresh()
        time.sleep(60)

# Start monitoring
monitor()
