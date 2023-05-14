import hashlib
import os
import re
import subprocess
import unicodedata
import yt_dlp
import requests
from bs4 import BeautifulSoup


def shorten_title(title, max_length=50):
    """
    Truncate the title of a file if it's too long.
    """
    if len(title) <= max_length:
        return title
    short_title = title[:max_length]
    hash_object = hashlib.sha1(title.encode('utf-8'))
    hex_dig = hash_object.hexdigest()[:10]
    return f"{short_title}_{hex_dig}"




class AudioProcessor:
    # Desired duration of a sub_audio clip in seconds
    sub_audio_duration = 30 * 60

    def __init__(self):
        pass

    def download_audio(self, url):
        """
        Download audio from the video provided by the URL.
        """
        if "youtube.com" in url:
            return self.download_audio_youtube(url)
        elif "twitch.tv" in url:
            return self.download_video_twitch(url)
        else:
            raise Exception("Sorry, this script only supports downloading audio from YouTube and Twitch.")

    def download_audio_youtube(self, url):
        """
        Download YouTube audio from the video provided by the URL.
        """
        song_title = clip = None
        try:
            # First, fetch the video's info
            with yt_dlp.YoutubeDL({}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                song_title = self.clean_title(re.sub(r'[^\w\s-]', '', info_dict['title']).strip().replace(' ', '_'))
                song_title = shorten_title(song_title)

            # Then, download the audio and convert it to mp3 format
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{song_title}.webm',  # output filename includes the cleaned video's title
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            webm_file = f"{song_title}.webm"  # webm file named after the cleaned video's title
            return song_title, webm_file
        except Exception as e:
            print(f"An error occurred: {e}")

    def createSubAudios(self, duration, song_title, webm_file):
        """
        Splits the audio into multiple sub-audios based on specified duration.
        """
        num_sub_audios = int(duration / self.sub_audio_duration) + 1
        mp3_files = []
        # Create a folder to store sub-audios
        sub_audio_folder = os.path.join(os.getcwd(), f"{song_title}")
        os.makedirs(sub_audio_folder, exist_ok=True)
        for i in range(num_sub_audios):
            start_time = i * self.sub_audio_duration
            end_time = (i + 1) * self.sub_audio_duration
            if end_time > duration:
                end_time = duration
            mp3_file = os.path.join(sub_audio_folder, f"{song_title}_{i + 1}.mp3")
            self.convert_webm_to_mp3(webm_file, mp3_file, start_time, end_time)
            mp3_files.append(mp3_file)
        # Remove the webm file after creating all sub_audios
        self.remove_files(webm_file)
        return mp3_files

    def convert_webm_to_mp3(self, webm_file, mp3_file, start_time, end_time):
        """
        Converts the webm file to mp3 using ffmpeg
        """
        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', webm_file, '-ss', str(start_time), '-to', str(end_time),
                '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', '-threads', '8', mp3_file
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error in converting {webm_file} to {mp3_file}: {e}")

    def get_audio_duration(self, audio_file):
        """
        Get the duration of an audio file in seconds
        """
        try:
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                     'format=duration', '-of',
                                     'default=noprint_wrappers=1:nokey=1', audio_file],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout.strip()
            if not output:
                raise ValueError("Empty output received from ffprobe")

            duration = float(output)
            return duration
        except subprocess.CalledProcessError as e:
            print(f"Error in getting duration of {audio_file}: {e}")
            return None
        except ValueError as e:
            print(f"Error in converting ffprobe output to float: {e}")
            return None

    def convert_audio(self, song_title, clip):
        """
        Convert the downloaded audio file to mp3 format
        """
        song_file_path = f"{song_title}.mp3"
        clip.write_audiofile(song_file_path)

    def remove_audios(self, song_title, mp4_file):
        """
        Remove the downloaded audio files
        """
        mp3_file = f"{song_title}.mp3"
        self.remove_files(mp4_file, mp3_file)

    def remove_files(self, *file_paths):
        """
        Remove a list of files
        """
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

    def download_video_twitch(self, url):
        """
        Download the Twitch video provided by the URL
        """
        title = self.scrap_twitch_video_title(url)
        vod_path = f"./{title}.webm"
        if not os.path.exists(vod_path):
            subprocess.call(
                ["streamlink", url, "audio", "-o", vod_path, "--stream-segment-threads=8", "--hls-live-edge=6",
                 "--stream-segment-timeout=5", ])

        print("Video has been downloaded.")
        return title, vod_path

    def scrap_twitch_video_title(self, url):
        """
        Retrieve the title of the Twitch video from the web page
        """
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        meta_tag = soup.find('meta', {'property': 'og:title'})
        if meta_tag:
            full_title = meta_tag['content']
            title, description = full_title.rsplit(' - ', 1)
        else:
            title = 'Title not found'
        return self.clean_title(title)

    def clean_title(self, title):
        """
        Clean the title of special characters
        """
        title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode('utf-8')
        title = re.sub(r'[^\w\s\-]+', '', title).strip().replace(' ', '_')
        title = shorten_title(title)

        return title

if __name__ == '__main__':
        while True:
            # Prompt the user to enter a YouTube URL
            url = input("Enter a YouTube video URL to download the audio: ")

            # Create a new instance of the AudioProcessor class
            audio_processor = AudioProcessor()

            try:
                # Download the audio from the URL and create sub-audios
                song_title, *webm_file = audio_processor.download_audio(url)

                print("Audio has been downloaded and split into sub-audios.")
            except Exception as e:
                # If an exception occurs, send error message to console
                print(f"An error occurred: {e}")
