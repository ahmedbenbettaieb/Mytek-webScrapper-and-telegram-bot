import os
import logging
import time
from dbConnection import get_db_connection
import telebot
from telebot import types
import telebot.apihelper 
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conn = get_db_connection()
cursor = conn.cursor()

API_TOKEN = os.getenv("API_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

telebot.apihelper.READ_TIMEOUT = 60  
telebot.apihelper.CONNECT_TIMEOUT = 30  

print("Bot started")


# Retry mechanism for sending messages
def send_message_with_retries(chat_id, text, retries=3, delay=5):
    for i in range(retries):
        try:
            bot.send_message(chat_id, text)
            return
        except Exception as e:
            logger.error(
                f"Attempt {i + 1} failed. Retrying in {delay} seconds... Error: {e}"
            )
            time.sleep(delay)
    raise Exception("All retries failed!")


# Command: /start
@bot.message_handler(commands=["start"])
def start(message):
    logger.info(f"User {message.from_user.id} issued /start command")
    send_message_with_retries(
        message.chat.id,
        "Welcome! Use the following commands:\n"
        "/pcs - Search for PCs\n"
        "/budget - Search for PCs within a price range",
    )


# Command: /budget
@bot.message_handler(commands=["budget"])
def budget(message):
    try:
        args = message.text.split()[1:]
        if len(args) != 2:
            send_message_with_retries(
                message.chat.id,
                "Please provide a min and max price. Example: /budget 1000 2000",
            )
            return

        min_price = float(args[0])
        max_price = float(args[1])
        logger.info(
            f"User {message.from_user.id} searched for PCs with price range: {min_price}-{max_price}"
        )

        cursor.execute(
            "SELECT * FROM pcs WHERE price BETWEEN %s AND %s", (min_price, max_price)
        )
        results = cursor.fetchall()

        if not results:
            send_message_with_retries(
                message.chat.id, "No PCs found within that price range."
            )
            return

        response = f"Here are the PCs between {min_price} TND and {max_price} TND:\n\n"
        for row in results:
            pc_info = (
                f"Name: {row[3]}\n"
                f"Price: {row[1]} TND\n"
                f"Reference: {row[2]}\n"
                f"Description: {row[4]}\n"
                f"Availability: {row[5]}\n\n"
            )
            if len(response) + len(pc_info) > 4096:  # Telegram message length limit
                send_message_with_retries(message.chat.id, response)
                response = pc_info
            else:
                response += pc_info

        if response:
            send_message_with_retries(message.chat.id, response)
    except ValueError:
        send_message_with_retries(
            message.chat.id, "Please enter valid numbers for prices"
        )
    except Exception as e:
        logger.error(f"Error in /budget command: {e}")
        send_message_with_retries(message.chat.id, f"An error occurred: {e}")


# Command: /pcs
@bot.message_handler(commands=["pcs"])
def pcs(message):
    try:
        cursor.execute("SELECT * FROM pcs")
        results = cursor.fetchall()

        if not results:
            send_message_with_retries(message.chat.id, "No PCs found.")
            return

        response = "Available PCs:\n\n"
        for row in results:
            pc_info = (
                f"Name: {row[3]}\n" f"Price: {row[1]} TND\n" f"Reference: {row[2]}\n\n"
            )
            if len(response) + len(pc_info) > 4096:
                send_message_with_retries(message.chat.id, response)
                response = pc_info
            else:
                response += pc_info

        if response:
            send_message_with_retries(message.chat.id, response)
    except Exception as e:
        logger.error(f"Error in /pcs command: {e}")
        send_message_with_retries(message.chat.id, f"An error occurred: {e}")


# Handle unknown commands
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    logger.info(
        f"User {message.from_user.id} sent an unrecognized message: {message.text}"
    )
    send_message_with_retries(
        message.chat.id,
        "Sorry, I don't understand that command. Use /start to see available commands.",
    )


# Start the bot
if __name__ == "__main__":
    try:
        logger.info("Starting bot...")
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Cleanup
        cursor.close()
        conn.close()
        logger.info("Bot stopped.")
