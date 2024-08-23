from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
from telegram import Bot
from datetime import datetime
import pytz
import asyncio
from webdriver_manager.chrome import ChromeDriverManager

# Constants
LOGIN_URL = 'https://www.dzrt.com/en/customer/account/login/'
CART_URL = 'https://www.dzrt.com/en/checkout/cart/'
EMAIL = 'nssr4k@gmail.com'
PASSWORD = '116366'
TELEGRAM_BOT_TOKEN = '7057170144:AAFrHvf0JlS1wulR_V3bzi92rf_-r1vEHV0'
TELEGRAM_CHAT_ID = '-1002243740808'

# Setup Selenium with Chrome
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-notifications")

def setup_driver():
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def log(message):
    print(f"{datetime.now()}: {message}")

def handle_age_verification(driver):
    try:
        age_modal = WebDriverWait(driver, 20).until(
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

def login(driver):
    driver.get(LOGIN_URL)
    log("Navigated to login page.")
    handle_age_verification(driver)

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

        # Check for successful login by verifying mini cart counter
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

def is_logged_in(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, 'span.counter-number')
        log("Already logged in.")
        return True
    except:
        log("Not logged in.")
        return False

def check_cart(driver):
    driver.get(CART_URL)
    time.sleep(5)
    log("Navigated to cart page.")

    product_elements = driver.find_elements(By.CSS_SELECTOR, '#shopping-cart-table > tbody > tr.item-info > td.col.item > div')

    alert_sent = False

    for product in product_elements:
        try:
            product_name = product.find_element(By.CSS_SELECTOR, 'strong.product-item-name a').text.strip()
        except Exception as e:
            product_name = "Unknown Product"
            log(f"Failed to get product name: {str(e)}")

        try:
            strength_element = product.find_element(By.CSS_SELECTOR, 'dl > dd')
            strength = strength_element.text.strip()
        except Exception as e:
            strength = "Unknown Strength"
            log(f"Failed to get product strength: {str(e)}")

        try:
            red_messages = product.find_elements(By.CSS_SELECTOR, 'div.cart.item.message.error div')
            message_texts = [message.text.strip() for message in red_messages]
        except Exception as e:
            log(f"Failed to get red error messages: {str(e)}")
            message_texts = []

        log(f"Product '{product_name}' (Strength: {strength}) messages: {message_texts}")

        if len(message_texts) == 1 and message_texts[0] == "This product is out of stock.":
            log(f"Product '{product_name}' (Strength: {strength}) meets the alert condition.")
            asyncio.run(send_telegram_notification(f"Alert: The product '{product_name}' with strength '{strength}' is almost in stock. Only the message 'This product is out of stock' is present."))
            alert_sent = True

    if not alert_sent:
        log("No products met the alert condition.")

    log("Check completed.")

async def send_telegram_notification(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        log("Telegram notification sent.")
    except Exception as e:
        log(f"Failed to send Telegram notification: {str(e)}")

def monitor():
    driver = setup_driver()
    try:
        while True:
            if not is_logged_in(driver):
                if not login(driver):
                    log("Login failed, retrying in 1 minute...")
                    time.sleep(60)
                    continue

            check_cart(driver)
            time.sleep(600)  # Wait for 10 minutes before next check

            driver.refresh()
            log("Page refreshed to avoid log off.")
    finally:
        driver.quit()

# Start monitoring
monitor()
