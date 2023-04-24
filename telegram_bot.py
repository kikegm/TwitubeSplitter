import os

import telebot
from audio_processing import AudioProcessor
from tqdm import tqdm
from time import sleep
from dotenv import load_dotenv
load_dotenv()
class TelegramBot:
    def __init__(self):
        self.bot = telebot.TeleBot(os.environ.get("TELEGRAM_BOT_TOKEN"))
        self.audio_processor = AudioProcessor()
        self.progress_message = None

    def send_progress(self, chat_id: int, progress: float):
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
        progress_emoji = "🟩"
        empty_bar_emoji = "⬜"
        filled_bars = int(progress * total_bars)
        progress_bars = [progress_emoji] * filled_bars + [empty_bar_emoji] * (total_bars - filled_bars)
        return "".join(progress_bars)

    def send_files_via_telegram(self, chat_id, folder):
        """
        Envia los archivos de audio al chat de Telegram
        """
        for file_name in os.listdir(folder):
            file_path = os.path.join(folder, file_name)
            with open(file_path, 'rb') as audio_file:
                # Obtener el tamaño del archivo
                audio_size = os.path.getsize(file_path)

                # Crear una barra de progreso
                with tqdm(total=audio_size, unit='B', unit_scale=True, desc=file_name) as pbar:
                    success = False
                    attempts = 0
                    while not success and attempts < 3:
                        try:
                            # Enviar el archivo de audio al chat
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
                            # Actualizar la barra de progreso
                            pbar.update(audio_size)

    def process_audio(self, chat_id, url):
        try:
            song_title, clip, mp4_file = self.audio_processor.download_audio(url)
            self.send_progress(chat_id, 0.2)
            self.audio_processor.convert_audio(song_title, clip, mp4_file)
            self.send_progress(chat_id, 0.4)
            self.audio_processor.create_sub_audios(song_title, clip)
            self.send_progress(chat_id, 0.8)
            self.audio_processor.remove_audios(song_title, mp4_file)
            self.send_files_via_telegram(chat_id, song_title)
        except Exception as e:
            raise e

    def _register_message_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            self.bot.reply_to(message,
                              "Welcome to the Audio Downloader Bot. Send me a video URL to download the audio.")

        @self.bot.message_handler(func=lambda message: True)
        def process_message(message):
            chat_id = message.chat.id
            url = message.text

            try:
                self.progress_message = None
                self.send_progress(chat_id, 0.0)
                self.process_audio(chat_id, url)
                self.send_progress(chat_id, 1.0)
            except Exception as e:
                if str(e) == "'streamingData'":
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
                    self.bot.send_message(chat_id, f"An error occurred: {e}")
    def start(self):
        self._register_message_handlers()
        self.bot.polling()


if __name__ == '__main__':
    bot = TelegramBot()
    bot.start()
