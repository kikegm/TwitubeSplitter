# TwitubeSplitter

This is a Telegram bot that allows users to download audio from YouTube and Twitch videos, convert the audio to mp3 format, and split it into sub-audios. The bot then sends the sub-audios to the user via Telegram.

The bot was created to help people who listen to podcasts or other long-form audio content but don't have the ability to skip forward or backward easily on their current MP3 player, particularly those who listen at work. By splitting the audio into smaller sub-audios, users can more easily skip forward or backward to find the content they want to listen to, without the need for a device with advanced playback controls.
## Requirements

- Python 3.11
- `ffmpeg` executable in PATH
- Telegram bot token (create one [here](https://core.telegram.org/bots#3-how-do-i-create-a-bot))
- `pytube`, `beautifulsoup4`, `moviepy`, `tqdm`, and `python-dotenv` Python packages (can be installed via pip)

## Usage

1. Clone the repository: `git clone https://github.com/username/audio-downloader-bot.git`
2. Install the required packages: `pip install -r requirements.txt`
3. Create a `.env` file in the project directory with the following content:

    ```
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
    ```

4. Run the bot: `python main.py`

## Commands

- `/start` or `/help`: Displays the welcome message and instructions.
- Send a video URL to the bot: Downloads the audio from the video, converts it to mp3, splits it into sub-audios, and sends them to the user via Telegram.

## License

This project is licensed under the MIT License.
