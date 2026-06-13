# 🚀 Automated Price Tracker with Telegram Alerts

A professional Python-based web scraping system that monitors product prices in real-time, stores price history using an SQLite database, and sends instant notification alerts directly to a Telegram channel/chat when a price change is detected.

## ✨ Features
* *Automated Web Scraping:* Extracts product prices dynamically using BeautifulSoup and requests.
* *Local Database Storage:* Keeps a structured price history utilizing SQLite3 for trend analysis.
* *Smart Notifications:* Integrates with the Telegram Bot API to send instant cellular alerts only when a price change actually occurs.
* *Secure Architecture:* Built with environment variables (.env) to decouple sensitive API tokens and credentials from the core logic.
* *Task Scheduling:* Runs seamlessly in the background as a local service checking prices based on customizable intervals.

## 🛠️ Tech Stack
* *Language:* Python
* *Libraries:* BeautifulSoup4, Requests, Python-dotenv, Schedule, SQLite3

## 📦 Installation & Setup
1. Clone the repository.
2. Install dependencies: pip install -r requirements.txt
3. Configure your Telegram Token and Chat ID in a .env file.
4. Run the engine: python tracker.py
