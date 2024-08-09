import sqlite3
import time
import random
import string
from datetime import datetime, timedelta
import requests
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

# Store user state
user_state = {}

# Bot and channel configuration
BOT_TOKEN = '6996028484:AAHESRCI7ekhF8ZfVlSXkjncn9CIUyKpZ_c'
CHANNEL_ID = '-1002243740808'

bot = Bot(token=BOT_TOKEN)

# Function to get database connection
def get_db_connection():
    try:
        conn = sqlite3.connect('subscriptions.db', timeout=10)
        return conn
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")
        time.sleep(1)  # Wait for 1 second before retrying
        return get_db_connection()

# Function to execute database queries
def execute_query(query, params=(), fetchone=False, fetchall=False):
    result = None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        else:
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    return result

# Function to handle the /start command
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🔗 Free 3-day Trial", callback_data='free_trial')],
        [InlineKeyboardButton("🔑 Enter Code", callback_data='enter_code')],
        [InlineKeyboardButton("🕒 Subscription Period", callback_data='subscription_period')],
        [InlineKeyboardButton("🛒 Store", url='https://ezdzrt.com/')],
        [InlineKeyboardButton("📞 Contact Support", url='https://t.me/2128302750')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome! Please choose an option:', reply_markup=reply_markup)

# Function to generate a Telegram channel invite link
def generate_invite_link(chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/exportChatInviteLink"
    payload = {'chat_id': chat_id}
    response = requests.post(url, json=payload)
    result = response.json()
    if result['ok']:
        return result['result']
    else:
        return None

# Function to revoke a Telegram channel invite link
def revoke_invitation_link(link):
    try:
        bot.revoke_chat_invite_link(CHANNEL_ID, link)
        print(f"Revoked invitation link: {link}")
    except Exception as e:
        print(f"Failed to revoke the invitation link: {e}")

# Function to check if a user has already used the 3-day trial
def has_used_trial(user_id):
    return execute_query("SELECT expiration_date FROM user_subscriptions WHERE user_id = ? AND subscription_code = 'TRIAL'", (user_id,), fetchone=True) is not None

# Function to delete the trial subscription record
def delete_trial_subscription(user_id):
    execute_query("DELETE FROM user_subscriptions WHERE user_id = ? AND subscription_code = 'TRIAL'", (user_id,))

# Function to handle button presses
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    user_id = update.effective_user.id

    if callback_data == 'free_trial':
        if has_used_trial(user_id):
            delete_trial_subscription(user_id)
        invitation_link = generate_invite_link(CHANNEL_ID)
        if invitation_link:
            save_invitation_link(user_id, invitation_link)
            await query.edit_message_text(text=f"Here is your new channel invitation link: {invitation_link}")
            save_trial_subscription(user_id)
        else:
            await query.edit_message_text(text="There was an error generating your invitation link.")
    elif callback_data == 'enter_code':
        user_state[update.effective_user.id] = 'awaiting_code'
        await query.edit_message_text(text="Please enter your subscription code.")
    elif callback_data == 'subscription_period':
        subscription = get_user_subscription(update.effective_user.id)
        if subscription:
            expiration_date = subscription[0]
            if is_subscription_active(expiration_date):
                await query.edit_message_text(text=f"Your subscription is valid until {expiration_date}.")
            else:
                await query.edit_message_text(text="Your subscription has expired.")
        else:
            await query.edit_message_text(text="You do not have an active subscription.")
    elif callback_data.startswith('inspect_code_'):
        code = callback_data.split('_')[2]
        details = get_code_details(code)
        if details:
            message = (
                f"Code: {details[0]}\n"
                f"Status: {'Used' if details[1] else 'Available'}\n"
                f"Period: {details[2]}\n"
                f"User ID: {details[3]}\n"
                f"Invitation Link: {details[4]}\n"
                f"Date Used: {details[5]}\n"
            )
            await query.edit_message_text(text=message)
        else:
            await query.edit_message_text(text="No details found for this code.")
    elif callback_data == 'inspect_code':
        await query.edit_message_text(text="Please enter the code to inspect.")
    elif callback_data == 'generate_codes':
        num_codes = 10
        codes_generated = []
        for _ in range(num_codes):
            code = generate_code()
            invitation_link = generate_invite_link(CHANNEL_ID)
            execute_query("INSERT OR REPLACE INTO subscription_codes (code, period, is_used, user_id, invitation_link, date_used) VALUES (?, 'temporary', 0, NULL, ?, NULL)", (code, invitation_link))
            codes_generated.append(code)
        await query.edit_message_text(text=f"Generated {num_codes} subscription codes:\n" + "\n".join(codes_generated))
    elif callback_data == 'check_codes':
        codes = execute_query("SELECT * FROM subscription_codes", fetchall=True)
        if codes:
            message = "All Codes:\n"
            for code in codes:
                message += f"Code: {code[0]}, Status: {'Used' if code[2] else 'Available'}\n"
            await query.edit_message_text(text=message)
        else:
            await query.edit_message_text(text="No codes found.")
    elif callback_data == 'show_used_codes':
        used_codes = execute_query("SELECT * FROM subscription_codes WHERE is_used = 1", fetchall=True)
        if used_codes:
            message = "Used Codes:\n"
            for code in used_codes:
                message += f"Code: {code[0]}\n"
            await query.edit_message_text(text=message)
        else:
            await query.edit_message_text(text="No used codes found.")
    elif callback_data == 'delete_trial':
        delete_trial_subscription(user_id)
        await query.edit_message_text(text="All trial subscriptions have been deleted.")

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in user_state and user_state[user_id] == 'awaiting_code':
        code = update.message.text.strip()
        if verify_code(code):
            invitation_link = get_invitation_link(code)
            if not invitation_link:
                invitation_link = generate_invite_link(CHANNEL_ID)
                save_invitation_link(user_id, invitation_link)
                update_invitation_link_for_code(code, invitation_link)
            if invitation_link and is_invitation_link_valid(invitation_link):
                await update.message.reply_text(f"Your code is valid! Here is your channel invitation link: {invitation_link}")
                mark_code_as_used(code, user_id)
                await bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
                await bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
                create_subscription(user_id, code)
            else:
                await update.message.reply_text("Your code is valid, but the invitation link is expired or invalid.")
        else:
            await update.message.reply_text("Invalid code. Please try again.")
        del user_state[user_id]

def verify_code(code):
    result = execute_query("SELECT is_used FROM subscription_codes WHERE code = ?", (code,), fetchone=True)
    return result and result[0] == 0

def get_invitation_link(code):
    result = execute_query("SELECT invitation_link FROM subscription_codes WHERE code = ?", (code,), fetchone=True)
    return result[0] if result else None

def save_trial_subscription(user_id):
    expiration_date = datetime.now() + timedelta(days=3)
    execute_query("INSERT INTO user_subscriptions (user_id, subscription_code, expiration_date) VALUES (?, 'TRIAL', ?)", (user_id, expiration_date))

def save_invitation_link(user_id, link):
    execute_query("INSERT OR REPLACE INTO invitation_links (user_id, link) VALUES (?, ?)", (user_id, link))

def update_invitation_link_for_code(code, link):
    execute_query("UPDATE subscription_codes SET invitation_link = ? WHERE code = ?", (link, code))

def is_invitation_link_valid(link):
    # Implement logic to verify if the link is still valid
    return True

def create_subscription(user_id, code):
    expiration_date = datetime.now() + timedelta(days=30) # Set a 30-day subscription period
    execute_query("INSERT INTO user_subscriptions (user_id, subscription_code, expiration_date) VALUES (?, ?, ?)", (user_id, code, expiration_date))

def mark_code_as_used(code, user_id):
    execute_query("UPDATE subscription_codes SET is_used = 1, user_id = ?, date_used = ? WHERE code = ?", (user_id, datetime.now(), code))

def get_user_subscription(user_id):
    return execute_query("SELECT expiration_date FROM user_subscriptions WHERE user_id = ?", (user_id,), fetchone=True)

def is_subscription_active(expiration_date):
    return datetime.strptime(expiration_date, "%Y-%m-%d %H:%M:%S") > datetime.now()

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def get_code_details(code):
    return execute_query("SELECT code, is_used, period, user_id, invitation_link, date_used FROM subscription_codes WHERE code = ?", (code,), fetchone=True)

async def admin(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🔑 Generate Codes", callback_data='generate_codes')],
        [InlineKeyboardButton("🔍 Check Codes", callback_data='check_codes')],
        [InlineKeyboardButton("📋 Show Used Codes", callback_data='show_used_codes')],
        [InlineKeyboardButton("❌ Delete Trial Subscriptions", callback_data='delete_trial')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Admin menu:', reply_markup=reply_markup)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('admin', admin))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(button))
    
    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
