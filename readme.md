# Smart Piggy Bank

A smart piggy bank that tracks the number of coins deposited and sends Telegram alerts for unauthorized withdrawals. This project uses an Arduino with a load cell to weigh the coins and a Flask web application to display the data and manage savings goals.

## Features

- **Real-time Coin Counting:** Tracks the number of Rs. 2 coins in the piggy bank based on weight.
- **Telegram Alerts:** Sends a Telegram notification when a significant weight drop is detected, indicating a possible unauthorized withdrawal.
- **Savings Goals:** Set and track savings goals with images.
- **Web Interface:** A simple web interface to view the current weight, number of coins, and savings goals.
- **API Endpoints:** Provides API endpoints for current data, system info, and testing.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.x
- Arduino IDE
- A Telegram Bot Token and Chat ID

### Hardware Setup

1.  **Arduino:**
    *   Connect the load cell and HX711 amplifier to your Arduino.
    *   Upload the `arduino/arduino.ino` sketch to your Arduino.
    *   Use the `arduino/calibration.ino` sketch to calibrate your load cell. Note the calibration factor and update it in `arduino.ino`.
2.  **Connections:**
    *   Connect the Arduino to your computer via USB.

### Software Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/piggy-bank.git
    cd piggy-bank
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your Telegram Bot:**
    *   Create a new Telegram bot using the BotFather.
    *   Get your Bot Token and Chat ID.
    *   Update the `bot_token` and `chat_id` in `app/telegram_alerts.py`.

5.  **Initialize the databases:**
    ```bash
    python3 app/database.py
    ```

## Usage

1.  **Run the Flask application:**
    ```bash
    python3 app/main.py
    ```

2.  **Open your browser and navigate to:**
    *   **Dashboard:** `http://localhost:5000`
    *   **Goals:** `http://localhost:5000/goals`
    *   **API Help:** `http://localhost:5000/help`

## File Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py           # Flask application
│   ├── database.py       # Database connection and functions
│   ├── serial_reader.py  # Reads data from the Arduino
│   ├── telegram_alerts.py# Sends Telegram alerts
│   ├── static/           # Static files (CSS, images)
│   └── templates/        # HTML templates
├── arduino/
│   ├── arduino.ino       # Main Arduino sketch
│   └── calibration.ino   # Sketch for calibrating the load cell
├── data/
│   ├── coin_tracker.db   # SQLite database for weight readings
│   └── goals.db          # SQLite database for savings goals
├── .gitignore
├── readme.md
└── requirements.txt
```

## Coin Weights

-   **Rs. 1 Coin:** (0.006g)
-   **Rs. 2 Coin:** (0.008g)
