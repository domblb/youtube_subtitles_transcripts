import os
import json
import logging
import argparse
import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Load YouTube API key from .env file
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@"
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="

if not YOUTUBE_API_KEY:
    raise ValueError("YouTube API key not found. Please set it in the .env file.")

# Function to setup logging
def setup_logging(log_level, log_format, log_file, console_logging):
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = log_levels.get(log_level.upper(), logging.INFO)
    
    log_format_plain = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_format_json = json.dumps({
        "time": "%(asctime)s",
        "name": "%(name)s",
        "level": "%(levelname)s",
        "message": "%(message)s"
    })
    
    log_format_str = log_format_json if log_format == 'json' else log_format_plain
    
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=level, format=log_format_str, filename=log_file, filemode='a')
    
    if console_logging:
        console = logging.StreamHandler()
        console.setLevel(level)
        formatter = logging.Formatter(log_format_str)
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
    
    # Suppress specific module warnings
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
    logging.getLogger('google.auth.compute_engine._metadata').setLevel(logging.ERROR)
    logging.getLogger('google.auth._default').setLevel(logging.ERROR)

# Function to create YouTube API client
def get_youtube_client():
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Function to get the channel ID from channel name
def get_channel_id(channel_name):
    url = "https://www.youtube.com/@" + channel_name
    r = requests.get(url)
    logging.debug(f"Fetching channel ID from URL: {url}")
    if r.status_code != 200:
        logging.error(f"Failed to fetch channel page. Status code: {r.status_code}")
        raise Exception(f"Failed to fetch channel page. Status code: {r.status_code}")
    text = r.text
    channel_id = text.split("youtube.com/channel/")[1].split('">')[0]
    logging.debug(f"Channel ID: {channel_id}")
    return channel_id

# Function to fetch video IDs of the videos in the uploads playlist of a channel
def fetch_video_ids(youtube, channel_name, max_videos, include_shorts):
    channel_id = get_channel_id(channel_name)
    base_url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "contentDetails", "id": channel_id, "key": YOUTUBE_API_KEY}
    
    try:
        response = requests.get(base_url, params=params)
        response = json.loads(response.content)
    except HttpError as e:
        logging.error(f"An HTTP error occurred: {e}")
        return []

    if "items" not in response or not response["items"]:
        raise Exception(f"No playlist found for {channel_name}")

    playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    videos = []
    next_page_token = None

    print("Scanning channel for videos...")

    while True:
        playlist_items_response = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        logging.debug(f"Playlist items response: {playlist_items_response}")

        for video in playlist_items_response["items"]:
            if include_shorts or 'shorts' not in video["snippet"]["title"].lower():
                videos.append({
                    "ID": video["snippet"]["resourceId"]["videoId"],
                    "Title": video["snippet"]["title"],
                    "Date": video["snippet"]["publishedAt"]
                })

        next_page_token = playlist_items_response.get("nextPageToken")

        if not next_page_token or len(videos) >= max_videos:
            break

    print(f"Discovered {len(videos)} videos.")
    logging.debug(f"Fetched videos: {videos}")
    return videos[:max_videos]

# Function to normalize the video title for filenames
def normalize_title(title):
    title = re.sub(r'[^\w\s-]', '', title).strip().lower()
    title = re.sub(r'[-\s]+', '-', title)
    return title

# Function to fetch and save transcript using youtube_transcript_api
def fetch_and_save_transcript(video_id, video_title, video_date, languages, dest_dir, format, include_timecodes):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    except Exception as e:
        logging.error(f"An error occurred while fetching transcript for video {video_id}: {e}")
        print(f"No subtitles found for video {video_title}")
        return False

    normalized_title = normalize_title(video_title)
    date_str = datetime.strptime(video_date, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d')
    file_extension = 'json' if format == 'json' else 'txt'
    file_name = f"{normalized_title}-{date_str}.{file_extension}"
    file_path = os.path.join(dest_dir, file_name)
    with open(file_path, 'w', encoding='utf-8') as file:
        if format == 'json':
            json.dump({'title': video_title, 'transcript': transcript}, file, ensure_ascii=False, indent=4)
        else:
            file.write(f"Title: {video_title}\n\n")
            for line in transcript:
                if include_timecodes:
                    file.write(f"{line['start']} - {line['text']}\n")
                else:
                    file.write(f"{line['text']}\n")
    
    print(f"Downloaded transcription for video {video_id} ({video_title})")
    logging.info(f"Downloaded transcription for video {video_id} ({video_title})")
    return True

# Main function to handle command-line arguments and orchestrate the script's functionality
def main():
    parser = argparse.ArgumentParser(description="Download YouTube video transcriptions.")
    parser.add_argument('--channel', '-c', help="The YouTube channel ID or URL.")
    parser.add_argument('--video-id', '-v', help="The YouTube video ID.")
    parser.add_argument('--destination-directory', '-d', required=True, help="The directory where transcriptions will be saved.")
    parser.add_argument('--max-number-of-videos', '-m', type=int, default=5, help="The maximum number of videos to download transcriptions for. Default is 5.")
    parser.add_argument('--languages-of-subtitles', '-l', required=True, help="Comma-separated list of languages for subtitles (e.g., [en,fr,es]). Default is system locale settings.")
    parser.add_argument('--format', '-f', default='plain_text', choices=['plain_text', 'json'], help="Format for saving transcriptions. Default is plain_text.")
    parser.add_argument('--time-codes', '-t', action='store_true', help="Include time codes in the transcriptions. Disabled by default.")
    parser.add_argument('--rate-limit', '-r', type=int, default=5, help="API rate limit in calls per second. Default is 5.")
    parser.add_argument('--timeout', '-T', type=int, default=10, help="Timeout for API calls in seconds. Default is 10 seconds.")
    parser.add_argument('--log-level', '-L', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level. Default is INFO.")
    parser.add_argument('--log-format', '-F', default='plain_text', choices=['plain_text', 'json'], help="Format for logging output. Default is plain_text.")
    parser.add_argument('--list', action='store_true', help="List available subtitles, number of videos, and date of the most recent video.")
    parser.add_argument('--include-shorts', action='store_true', help="Include YouTube Shorts in the download.")
    parser.add_argument('--force-download', action='store_true', help="Force download the first available subtitle if the requested language is not found.")
    parser.add_argument('--console-log', action='store_true', help="Output log messages to console as well as log file.")

    args = parser.parse_args()
    
    if not args.channel and not args.video_id:
        parser.error("You must specify either a channel ID/URL or a video ID.")
    
    if args.channel and args.video_id:
        parser.error("You cannot specify both a channel ID/URL and a video ID.")
    
    # Setup logging
    dest_dir = Path(args.destination_directory)
    log_file = dest_dir / f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    setup_logging(args.log_level, args.log_format, log_file, args.console_log)

    youtube = get_youtube_client()
    
    if args.channel:
        channel_name = args.channel.lstrip('@')
        
        # Check if channel exists
        try:
            channel_id = get_channel_id(channel_name)
        except Exception as e:
            full_url = YOUTUBE_CHANNEL_URL + channel_name
            logging.error(f"The channel does not exist: {args.channel}\nURL: {full_url}")
            print(f"The channel does not exist: {args.channel}\nURL: {full_url}")
            return
        
        # Create destination directory if it doesn't exist
        dest_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Destination directory created: {dest_dir}")
        print(f"Destination directory created: {dest_dir}")

        # Fetch video IDs
        try:
            videos = fetch_video_ids(youtube, channel_name, args.max_number_of_videos, args.include_shorts)
            logging.debug(f"Fetched video IDs: {videos}")
        except Exception as e:
            logging.error(f"Failed to fetch video IDs: {e}")
            return
        
        if args.list:
            print(f"Discovered {len(videos)} videos.")
            print("Listing available subtitles and video information...")
            for video in videos:
                print(f"ID: {video['ID']}, Title: {video['Title']}, Date: {video['Date']}")
            logging.info(f"Available subtitles: {videos}")
            logging.info(f"Number of videos: {len(videos)}")
            most_recent_date = videos[0]['Date'] if videos else 'N/A'
            logging.info(f"Most recent video date: {most_recent_date}")
            return
        
        # Download transcriptions
        print(f"Starting to download transcriptions for {len(videos)} videos.")
        languages = args.languages_of_subtitles.strip('[]').split(',')
        for video in videos:
            fetch_and_save_transcript(video['ID'], video['Title'], video['Date'], languages, dest_dir, args.format, args.time_codes)
    elif args.video_id:
        # Create destination directory if it doesn't exist
        dest_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Destination directory created: {dest_dir}")
        print(f"Destination directory created: {dest_dir}")

        # Download transcription for a single video
        languages = args.languages_of_subtitles.strip('[]').split(',')
        fetch_and_save_transcript(args.video_id, args.video_id, datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), languages, dest_dir, args.format, args.time_codes)

if __name__ == '__main__':
    main()
