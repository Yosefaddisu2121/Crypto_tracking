import sqlite3
import asyncio
import time
from datetime import datetime
from pycoingecko import CoinGeckoAPI
from telegram import Bot

# Telegram Bot Token
BOT_TOKEN = "7845638676:AAFdbpt4JtqCsDWVi10SqnXjfG26mUYhWBg"

# Initialize CoinGecko API
cg = CoinGeckoAPI()

# Crypto price targets
targets = {
    "bitcoin": 65000,
    "ethereum": 4000,
    "possum": 0.00095
}

# Database setup
def update_db():
    """Create or update the database structure."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            subscription TEXT DEFAULT 'free',
            last_alert TEXT DEFAULT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def get_users():
    """Fetch all users from the database."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id, subscription, last_alert FROM users")
    users = cursor.fetchall()
    
    conn.close()
    return users

def can_receive_alert(user_id, subscription, last_alert):
    """Check if a free user is allowed to receive an alert today."""
    if subscription == "premium":
        return True  # Premium users get unlimited alerts

    if last_alert:
        last_alert_date = datetime.strptime(last_alert, "%Y-%m-%d")
        if last_alert_date.date() == datetime.now().date():
            return False  # Free user already received an alert today

    return True

def update_last_alert(user_id):
    """Update the last alert time for free users."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("UPDATE users SET last_alert = ? WHERE user_id = ?", (today_date, user_id))
    
    conn.commit()
    conn.close()

async def send_telegram_message(user_id, message):
    """Send a message to a Telegram user."""
    bot = Bot(token=BOT_TOKEN)

    try:
        await bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        print(f"Telegram error: {e}")

async def price_tracking():
    """Check crypto prices and send alerts based on user subscription."""
    while True:
        users = get_users()  # Get all users
        met_targets = {}

        for crypto, target_price in targets.items():
            try:
                response = cg.get_price(ids=crypto, vs_currencies="usd")
                current_price = response[crypto]["usd"]
                
                if current_price >= target_price:
                    met_targets[crypto] = current_price

            except Exception as e:
                print(f"Error fetching {crypto} price: {e}")

        if met_targets:
            for user_id, subscription, last_alert in users:
                if can_receive_alert(user_id, subscription, last_alert):
                    message_body = "🎉 Congrats, you made some money!\n\n"
                    for crypto, current_price in met_targets.items():
                        message_body += f"{crypto.capitalize()}\n"
                        message_body += f"Current price: ${current_price}\n"
                        message_body += f"Target price: ${targets[crypto]}\n\n"

                    await send_telegram_message(user_id, message_body)

                    if subscription == "free":
                        update_last_alert(user_id)  # Mark alert as sent for free users

        await asyncio.sleep(20)  # Wait before checking again

def add_user(user_id, subscription="free"):
    """Add a new user to the database with a default 'free' subscription."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO users (user_id, subscription) VALUES (?, ?)", (user_id, subscription))

    conn.commit()
    conn.close()

def is_premium(user_id):
    """Check if a user has a premium subscription."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT subscription FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] == "premium" if result else False

def update_to_premium(user_id):
    """Upgrade a user to premium status."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET subscription = 'premium' WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

def downgrade_to_free(user_id):
    """Downgrade a premium user back to free (e.g., after subscription expiry)."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET subscription = 'free' WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_db()  # Ensure database is set up
    asyncio.run(price_tracking())
