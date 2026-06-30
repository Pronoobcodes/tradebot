from app.telegram.notifier import send_message
from app.telegram.formatter import format_startup

def test():
    print("Testing Telegram connection...")
    success = send_message("🧪 *Test Message*\nIf you see this, the Telegram bot is working correctly!")
    if success:
        print("Message sent successfully!")
    else:
        print("Failed to send message. Please check your .env file credentials.")

if __name__ == "__main__":
    test()
