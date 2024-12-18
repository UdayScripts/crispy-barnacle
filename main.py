import telebot
import requests
import os
import math
from telebot.types import Message
from keep_alive import keep_alive
keep_alive()

# Replace with your bot token and channel username
BOT_TOKEN = "8142385461:AAFUCFo0ngYrMsGovyquODaFJ5cvd0kgSLQ"
CHANNEL_USERNAME = "@tbdatabase"

bot = telebot.TeleBot(BOT_TOKEN)


def progress_bar(progress, total):
    """Generate a progress bar string."""
    percentage = progress / total * 100
    completed = math.ceil(percentage / 5)
    return f"[{'█' * completed}{' ' * (20 - completed)}] {percentage:.2f}%"


@bot.message_handler(commands=["start"])
def welcome_message(message: Message):
    """Send a welcome message on /start command."""
    bot.reply_to(
        message,
        (
            "Welcome to the TeraBox Video Downloader Bot!\n"
            "You can send me a TeraBox link to download videos.\n\n"
            "To download, just send a TeraBox link or use:\n"
            "`/download <TeraBox URL>`",
        ),
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["download"])
def download_video_command(message: Message):
    """Handle the /download command."""
    args = message.text.split(" ", 1)
    if len(args) < 2:
        bot.reply_to(message, "Please provide the TeraBox URL. Usage: /download <URL>")
        return
    download_video(message, args[1])


@bot.message_handler(func=lambda message: True)
def handle_text(message: Message):
    """Automatically detect TeraBox links and start downloading."""
    text = message.text.strip()
    if text.startswith("http") and "terabox" in text:
        download_video(message, text)
    else:
        bot.reply_to(message, "Please send a valid TeraBox link to download.")


def download_video(message: Message, terabox_url: str):
    """Download the video from the given TeraBox URL."""
    chat_id = message.chat.id
    api_url = f"https://terabox.udayscriptsx.workers.dev/?url={terabox_url}"

    msg = bot.send_message(chat_id, "Fetching video information...")

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        file_name = data["file_name"]
        download_link = data["direct_link"]
        file_size = data["size"]

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text=f"Downloading video: *{file_name}* ({file_size})",
            parse_mode="Markdown",
        )

        # Download video
        with open(file_name, "wb") as file:
            response = requests.get(download_link, stream=True)
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    bar = progress_bar(downloaded, total_size)
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg.message_id,
                        text=f"Downloading: {bar} ({downloaded / (1024 * 1024):.2f}/{total_size / (1024 * 1024):.2f} MB)",
                    )

        # Upload to channel
        with open(file_name, "rb") as video:
            bot.send_video(
                chat_id=CHANNEL_USERNAME,
                video=video,
                caption=f"Here is the video: *{file_name}* ({file_size})",
                parse_mode="Markdown",
            )

        # Send to user
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text="Sending video to you...",
        )
        with open(file_name, "rb") as video:
            bot.send_video(
                chat_id=chat_id,
                video=video,
                caption=f"Here is the video: *{file_name}* ({file_size})",
                parse_mode="Markdown",
            )

        # Cleanup
        os.remove(file_name)

    except requests.exceptions.RequestException as e:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text=f"Failed to fetch video: {str(e)}",
        )
    except Exception as e:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text=f"An error occurred: {str(e)}",
        )


if __name__ == "__main__":
    bot.polling()
