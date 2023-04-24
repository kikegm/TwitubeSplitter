# Import necessary libraries
import os
import telebot
from audio_processing import AudioProcessor
from tqdm import tqdm
from time import sleep
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TelegramBot:
    def __init__(self):
        # Initialize the Telegram bot and AudioProcessor objects
        self.bot = telebot.TeleBot(os.environ.get("TELEGRAM_BOT_TOKEN"))
        self.audio_processor = AudioProcessor()
        self.progress_message = None

    def send_progress(self, chat_id: int, progress: float):
        """
        Sends a progress bar to the chat identified by `chat_id` with the percentage of `progress` completed.
        If a previous progress message exists, it will be edited instead of sending a new message.
        """
        progress_text = self._generate_progress_bar(progress)
        if self.progress_message:
            self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=self.progress_message.message_id,
                text=progress_text
            )
        else:
            self.progress_message = self.bot.send_message(chat_id, progress_text)

    @staticmethod
    def _generate_progress_bar(progress: float, total_bars: int = 10) -> str:
        """
        Generates a progress bar string with a specified number of `total_bars` and a percentage of `progress`.
        """
        progress_emoji = "🟩"
        empty_bar_emoji = "⬜"
        filled_bars = int(progress * total_bars)
        progress_bars = [progress_emoji] * filled_bars + [empty_bar_emoji] * (total_bars - filled_bars)
        return "".join(progress_bars)

    def send_files_via_telegram(self, chat_id, folder):
        """
        Sends all audio files in the specified `folder` to the chat identified by `chat_id` using Telegram's
        `send_audio()` method. A progress bar is displayed for each file being sent.
        """
        for file_name in os.listdir(folder):
            file_path = os.path.join(folder, file_name)
            with open(file_path, 'rb') as audio_file:
                # Get the size of the file for the progress bar
                audio_size = os.path.getsize(file_path)

                # Display a progress bar for sending the file
                with tqdm(total=audio_size, unit='B', unit_scale=True, desc=file_name) as pbar:
                    success = False
                    attempts = 0
                    while not success and attempts < 3:
                        try:
                            # Send the audio file to the chat
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
                            # Update the progress bar as the file is sent
                            pbar.update(audio_size)

    def process_audio(self, chat_id, url):
        """
        Downloads the audio from the specified `url`, converts it to a compatible format, creates sub-audios from it,
        removes the original audio file, and sends the resulting files to the chat identified by `chat_id`. Progress
        bars are displayed for each step of the process.
        """
        try:
            song_title, clip, mp4_file = self.audio_processor.download_audio(url)
                        # Send progress update after downloading audio
            self.send_progress(chat_id, 0.2)

            # Convert audio to a compatible format
            self.audio_processor.convert_audio(song_title, clip, mp4_file)
            self.send_progress(chat_id, 0.4)

            # Create sub-audios from the main audio file
            self.audio_processor.create_sub_audios(song_title, clip)
            self.send_progress(chat_id, 0.8)

            # Remove the original audio file
            self.audio_processor.remove_audios(song_title, mp4_file)

            # Send resulting audio files to the chat
            self.send_files_via_telegram(chat_id, song_title)
        except Exception as e:
            raise e

    def _register_message_handlers(self):
        """
        Registers message handlers for the bot. The '/start' and '/help' commands will trigger the `send_welcome()`
        function, while all other messages will trigger the `process_message()` function.
        """
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            self.bot.reply_to(message,
                              "Welcome to the Audio Downloader Bot. Send me a video URL to download the audio.")

        @self.bot.message_handler(func=lambda message: True)
        def process_message(message):
            chat_id = message.chat.id
            url = message.text

            try:
                # Send initial progress message
                self.progress_message = None
                self.send_progress(chat_id, 0.0)

                # Process the audio from the URL
                self.process_audio(chat_id, url)

                # Send final progress message
                self.send_progress(chat_id, 1.0)
            except Exception as e:
                if str(e) == "'streamingData'":
                    # Retry up to 3 times if a 'streamingData' error occurs
                    max_attempts = 3
                    attempts = 0
                    while attempts < max_attempts:
                        attempts += 1
                        sleep(5)
                        try:
                            self.process_audio(chat_id, url)
                            break
                        except Exception as e:
                            if attempts == max_attempts:
                                self.bot.send_message(chat_id, f"An error occurred: {e}")
                else:
                    # Send error message to chat if an exception occurs
                    self.bot.send_message(chat_id, f"An error occurred: {e}")

    def start(self):
        """
        Starts the Telegram bot and registers message handlers.
        """
        self._register_message_handlers()
        self.bot.polling()


if __name__ == '__main__':
    # Create a new instance of the TelegramBot class and start the bot
    bot = TelegramBot()
    bot.start()

