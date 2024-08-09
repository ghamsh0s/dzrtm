import sqlite3
from datetime import datetime

# Path to your SQLite database file
DATABASE_PATH = 'C:/Users/abuze/OneDrive/Desktop/dzrtm/subscriptions.db'

def create_table():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    # Drop existing tables if they exist
    cursor.execute('DROP TABLE IF EXISTS user_subscriptions')
    cursor.execute('DROP TABLE IF EXISTS subscription_codes')
    cursor.execute('DROP TABLE IF EXISTS invitation_links')

    # Create subscription_codes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_codes (
            code TEXT PRIMARY KEY,
            period TEXT,
            is_used INTEGER NOT NULL CHECK (is_used IN (0, 1)), -- Use INTEGER for Boolean values
            user_id INTEGER,
            invitation_link TEXT,
            date_used TEXT, -- Ensure date format is consistent
            FOREIGN KEY (user_id) REFERENCES user_subscriptions (user_id)
        )
    ''')

    # Create user_subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            user_id INTEGER PRIMARY KEY,
            subscription_code TEXT,
            expiration_date TEXT, -- Ensure date format is consistent
            FOREIGN KEY (subscription_code) REFERENCES subscription_codes (code)
        )
    ''')

    # Create invitation_links table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invitation_links (
            link TEXT PRIMARY KEY,
            user_id INTEGER,
            expiration_date TEXT, -- Ensure date format is consistent
            FOREIGN KEY (user_id) REFERENCES user_subscriptions (user_id)
        )
    ''')

    # Optional: Add indexes to improve query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscription_code ON subscription_codes (code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON user_subscriptions (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invitation_link ON invitation_links (link)')

    connection.commit()
    connection.close()

if __name__ == "__main__":
    create_table()
    print("Database setup completed successfully.")
