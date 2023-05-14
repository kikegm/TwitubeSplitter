import os

import telebot
from audio_processing import AudioProcessor
from tqdm import tqdm
from time import sleep
from dotenv import load_dotenv


class TelegramBot:
    """
    This class handles the operations of a Telegram bot that processes and sends audio files.
    """
    def __init__(self, token):
        """
        Initializes the Telegram bot with the given token, an instance of the AudioProcessor,
        and sets up the progress bar emojis and message.
        """
        self.bot = telebot.TeleBot(token)
        self.audio_processor = AudioProcessor()
        self.progress_emojis = ["⬜"] * 10  # Progress bar representation as emojis
        self.progress_message = None  # Message instance used for updating the progress bar

    def send_progress(self, chat_id, progress):
        """
        Updates or sends a new progress message in the chat with the given progress value.
        """
        progress_emoji = "🟩"
        filled_progress = int(progress * 10)
        progress_bars = self.progress_emojis[:]
        for i in range(filled_progress):
            progress_bars[i] = progress_emoji
        progress_text = "".join(progress_bars)
        if self.progress_message:
            # If a progress message already exists, edit it
            self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=self.progress_message.message_id,
                text=progress_text
            )
        else:
            # If no progress message exists, send a new one
            self.progress_message = self.bot.send_message(chat_id, progress_text)

    def send_files_via_telegram(self, chat_id, folder):
        """
        Sends all the audio files in the given folder to the specified chat in Telegram.
        """
        for file_name in os.listdir(folder):
            file_path = os.path.join(folder, file_name)
            with open(file_path, 'rb') as audio_file:
                audio_size = os.path.getsize(file_path)

                with tqdm(total=audio_size, unit='B', unit_scale=True, desc=file_name) as pbar:
                    success = False
                    attempts = 0
                    while not success and attempts < 3:
                        try:
                            self.bot.send_audio(chat_id, audio_file, timeout=600)
                            success = True
                        except telebot.apihelper.ApiException as e:
                            attempts += 1
                            if attempts < 10:
                                sleep(5)
                                print(f"Failed to send {file_name}. Retrying...")
                            else:
                                print(f"Failed to send {file_name} after {attempts} attempts.")
                                raise e
                        else:
                            pbar.update(audio_size)

    def start(self):
        """
        Starts the Telegram bot, setting up message handlers for different types of messages.
        """
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            self.bot.reply_to(message, "Welcome to the Audio Downloader Bot. Send me a video URL to download the audio.")

        @self.bot.message_handler(func=lambda message: True)
        def process_message(message):
            """
            Processes a message from a chat, downloading and splitting audio from a URL,
            then sending the audio files to the chat. Updates progress in the chat throughout.
            """
            chat_id = message.chat.id
            url = message.text

            try:
                self.progress_message = None
                self.send_progress(chat_id, 0.1)
                song_title, webm_file = self.audio_processor.download_audio(url)
                self.send_progress(chat_id, 0.2)
                duration = self
                self.audio_processor.get_audio_duration(webm_file)
                self.send_progress(chat_id, 0.3)
                self.audio_processor.createSubAudios(duration, song_title, webm_file)
                self.send_progress(chat_id, 0.6)
                self.audio_processor.remove_files(webm_file)
                self.send_progress(chat_id, 0.8)
                self.send_files_via_telegram(chat_id, song_title)
                self.send_progress(chat_id, 1.0)
            except Exception as e:
                # In case of any error during the process, send a message to the chat with the error
                self.bot.send_message(chat_id, f"An error occurred: {e}")

        self.bot.polling()  # Start polling for messages

if __name__ == '__main__':
    load_dotenv()  # Load environment variables from a .env file
    bot = TelegramBot(os.environ.get("TELEGRAM_BOT_TOKEN"))  # Create a Telegram bot instance with the token from the environment variables
    bot.start()  # Start the Telegram bot
