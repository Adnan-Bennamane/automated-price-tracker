import os
import sqlite3
import logging
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import schedule

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))
DB_FILE = os.getenv("DB_FILE", "price_history.db")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("tracker.log"),
        logging.StreamHandler()
    ]
)

def init_db():
    """Initializes the SQLite database and creates the price history table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                url TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

def get_latest_price(url):
    """Retrieves the last recorded price for the given URL from the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT price FROM price_history WHERE url = ? ORDER BY timestamp DESC LIMIT 1",
            (url,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        return None
    except Exception as e:
        logging.error(f"Error querying latest price from database: {e}")
        return None

def save_price(url, price):
    """Saves a new price record to the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO price_history (url, price) VALUES (?, ?)",
            (url, price)
        )
        conn.commit()
        conn.close()
        logging.info(f"Saved price {price} to database for {url}")
    except Exception as e:
        logging.error(f"Error saving price to database: {e}")

def scrape_price(url):
    """Scrapes the product price from books.toscrape.com."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Books.toscrape.com product detail pages have the price in a paragraph with class 'price_color'
        price_elem = soup.find("p", class_="price_color")
        if not price_elem:
            raise ValueError("Could not find price element on page.")
        
        # The price text looks like "£51.77" or "£12.34"
        price_text = price_elem.get_text().strip()
        
        # Clean price string and convert to float (remove £ symbol and any weird encoding characters)
        cleaned_price = price_text.replace("£", "").replace("Â", "").strip()
        price_float = float(cleaned_price)
        
        return price_float
    except Exception as e:
        logging.error(f"Error scraping price: {e}")
        return None

def send_telegram_message(message):
    """Sends a notification message via Telegram Bot API."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram configuration missing. Skipping notification.")
        return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info("Telegram notification sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

def check_price():
    """Scrapes the price, compares it with the database, and alerts if changed."""
    logging.info("Checking product price...")
    
    current_price = scrape_price(PRODUCT_URL)
    if current_price is None:
        logging.error("Could not retrieve current price. Skipping execution.")
        return

    previous_price = get_latest_price(PRODUCT_URL)
    
    if previous_price is None:
        # First time tracking this product
        logging.info(f"Initial price check. Setting base price: £{current_price}")
        save_price(PRODUCT_URL, current_price)
        send_telegram_message(
            f"<b>Price Tracker Started!</b>\n"
            f"URL: {PRODUCT_URL}\n"
            f"Initial Price: £{current_price}"
        )
    elif current_price != previous_price:
        logging.info(f"Price changed! Old: £{previous_price} -> New: £{current_price}")
        save_price(PRODUCT_URL, current_price)
        
        direction = "dropped" if current_price < previous_price else "increased"
        message = (
            f"🚨 <b>Price Alert!</b>\n"
            f"The price of the product has {direction}!\n"
            f"<b>Old Price:</b> £{previous_price}\n"
            f"<b>New Price:</b> £{current_price}\n"
            f"<b>Product Link:</b> <a href='{PRODUCT_URL}'>View Product</a>"
        )
        send_telegram_message(message)
    else:
        logging.info(f"No price change detected. Current price remains: £{current_price}")

def main():
    # Validate critical variables
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("TELEGRAM_TOKEN and TELEGRAM_CHAT_ID are not set in .env! Notifications will be disabled.")
    
    # Initialize DB
    init_db()
    
    # Run immediate check on start
    check_price()
    
    # Schedule subsequent checks
    logging.info(f"Scheduling price check every {CHECK_INTERVAL} minutes.")
    schedule.every(CHECK_INTERVAL).minutes.do(check_price)
    
    # Keep the schedule running
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Price tracker stopped by user.")

if __name__ == "__main__":
    main()
