import hashlib
import os
import re
import subprocess
import unicodedata

import ffmpeg
from moviepy.video.io.VideoFileClip import AudioFileClip
from pytube import YouTube
import requests
from bs4 import BeautifulSoup


def shorten_title(title, max_length=50):
    """
    Shortens the title of a file if it's too long
    """
    if len(title) <= max_length:
        return title
    short_title = title[:max_length]
    hash_object = hashlib.sha1(title.encode('utf-8'))
    hex_dig = hash_object.hexdigest()[:10]
    return f"{short_title}_{hex_dig}"


class AudioProcessor:
    def __init__(self):
        pass

    def download_audio(self, url):
        """
        Downloads the audio of the given video URL
        """
        if "youtube.com" in url:
            return self.download_audio_youtube(url)
        elif "twitch.tv" in url:
            return self.download_audio_twitch(url)
        else:
            raise Exception("Sorry, this script only supports downloading audio from YouTube and Twitch.")

    def download_audio_youtube(self, url):
        """
        Downloads the audio from YouTube of the given video URL
        """
        yt = YouTube(url)
        stream = yt.streams.get_audio_only()
        stream.download()
        mp4_file = stream.get_file_path()

        song_title = self.clean_title(re.sub(r'[^\w\s-]', '', yt.title).strip().replace(' ', '_'))
        song_title = shorten_title(song_title)

        clip = AudioFileClip(mp4_file)

        return song_title, clip, mp4_file

    def convert_audio(self, song_title, clip, mp4_file):
        """
        Converts the downloaded audio file to mp3 format
        """
        song_file_path = f"{song_title}.mp3"
        clip.write_audiofile(song_file_path)

    def create_sub_audios(self, song_title, clip):
        """
        Splits the downloaded audio file into sub-audios
        """
        sub_audios_dir = song_title
        os.makedirs(sub_audios_dir, exist_ok=True)

        duration = clip.duration
        max_duration = 30 * 60
        num_sub_audios = int(duration / max_duration) + 1
        sub_audio_duration = int(duration / num_sub_audios)

        for i in range(num_sub_audios):
            start_time = i * sub_audio_duration
            end_time = (i + 1) * sub_audio_duration
            if end_time > duration:
                end_time = duration
            sub_audio = clip.subclip(start_time, end_time)
            sub_audio_file_path = os.path.join(sub_audios_dir, f"{song_title}_{i + 1}.mp3")
            sub_audio.write_audiofile(os.path.abspath(sub_audio_file_path))

        clip.close()
        print("Audio has been downloaded and split in sub-audios.")

    def remove_audios(self, song_title, mp4_file):
        """
        Deletes the downloaded audio files
        """
        mp3_file = f"{song_title}.mp3"
        self.remove_files(mp4_file, mp3_file)

    def remove_files(self, *file_paths):
        """
        Deletes a list of files
        """
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)
    def convert_video_to_audio(self, song_title, mp4_file):
        """
        Converts the downloaded video file to mp3 format
        """
        song_file_path = f"{song_title}.mp3"
        (
            ffmpeg
            .input(mp4_file)
            .output(song_file_path)
            .run()
        )

    def download_audio_twitch(self, url):
        """
        Downloads the audio from Twitch of the given video URL
        """
        title = self.scrap_twitch_video_title(url)
        vod_path = f"./{title}.mp4"
        if not os.path.exists(vod_path):
            subprocess.call(["streamlink", url, "audio", "-o", vod_path, "--stream-segment-threads=8", "--hls-live-edge=6",
                         "--stream-segment-timeout=5",])

        mp3_path = f"./{title}.mp3"
        if not os.path.exists(mp3_path):
            self.convert_video_to_audio(title, vod_path)

        print("Audio has been downloaded.")
        print("Video file has been deleted.")

        clip = AudioFileClip(mp3_path)

        return title, clip, vod_path

    def scrap_twitch_video_title(self, url):
        """
        Gets the title of the Twitch video from the webpage
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
        Cleans the title of special characters
        """
        title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode('utf-8')
        title = re.sub(r'[^\w\s\-]+', '', title).strip().replace(' ', '_')
        title = shorten_title(title)

        return title