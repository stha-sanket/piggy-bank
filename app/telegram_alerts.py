import requests
import time
from datetime import datetime

class TelegramAnomalyDetector:
    def __init__(self, bot_token, chat_id=None):
        self.bot_token = bot_token
        self.chat_id = chat_id or 8109579077  # Your chat ID
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_alert_time = 0
        self.alert_cooldown = 300  # 5 minutes between alerts
        self.min_weight_for_alert = 0.05  # Avoid alerts when piggy bank is nearly empty

    def send_message(self, message):
        """Send message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            print(f"SENDING TELEGRAM MESSAGE: {message[:r100]}...")
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✓ Telegram message sent successfully!")
                return True
            else:
                print(f"✗ Telegram error {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Telegram send error: {e}")
            return False

    def update_weight(self, current_weight, old_weight):
        """Check for weight decrease > 0.016g (more than 2 Rs.2 coins) and send alert"""
        # Ignore very small weights to avoid false alerts when empty
        if old_weight < self.min_weight_for_alert:
            return False

        weight_drop = old_weight - current_weight

        # Only trigger if weight dropped by MORE than 0.016g
        if weight_drop > 0.016:
            current_time = time.time()
            # Cooldown check
            if current_time - self.last_alert_time < self.alert_cooldown:
                remaining = int(self.alert_cooldown - (current_time - self.last_alert_time))
                print(f"Alert on cooldown. Next alert in {remaining}s")
                return False

            print(f"⚠️ WEIGHT DROP > 0.016g DETECTED: {weight_drop:.3f}g "
                  f"({old_weight:.3f}g → {current_weight:.3f}g)")

            self.trigger_alert(current_weight, old_weight, weight_drop)
            self.last_alert_time = current_time
            return True
        else:
            # Optional: log small changes or increases for debugging
            if weight_drop > 0:
                print(f"Small drop: {weight_drop:.3f}g (not enough for alert)")
            elif current_weight > old_weight:
                print(f"Weight increase: {old_weight:.3f}g → {current_weight:.3f}g")
            return False

    def trigger_alert(self, current_weight, previous_weight, drop_grams):
        """Send Telegram alert when >2 Rs.2 coins are potentially removed"""
        coins_missing = int(drop_grams / 0.008)  # Each Rs.2 coin = 0.008g
        value_lost = coins_missing * 2

        message = (
            f"🚨 <b>PIGGY BANK ALERT!</b> 🚨\n\n"
            f"⚠️ <b>Significant coin removal detected!</b>\n\n"
            f"📊 <b>Details:</b>\n"
            f"• Previous weight: <b>{previous_weight:.3f}g</b>\n"
            f"• Current weight: <b>{current_weight:.3f}g</b>\n"
            f"• Weight lost: <b>{drop_grams:.3f}g</b>\n"
            f"• Estimated Rs.2 coins removed: <b>{coins_missing}</b>\n"
            f"• Estimated value taken: <b>₹{value_lost}</b>\n\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🔔 Someone may have taken coins — check the piggy bank!"
        )

        self.send_message(message)

# Global instance (keep your real token safe!)
telegram_bot = TelegramAnomalyDetector(
    bot_token="8490596910:AAE58m8yP4pZ-lqimsmMhbADPe2rdcWRot8"
)  