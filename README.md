# YouTube Transcripts Downloader

This Python script downloads video transcriptions from a specified YouTube channel or video using the YouTube Data API v3. 
The script supports fetching subtitles in specified languages, including or excluding YouTube Shorts, detailed logging, and various other user-defined parameters.

## Features

- Fetch video IDs from a YouTube channel's uploads playlist.
- Download transcriptions for specified videos or channels.
- Supports multiple languages for subtitles.
- Option to include or exclude YouTube Shorts.
- Detailed logging in plain text or JSON format.
- Force download of the first available subtitle if the requested language is not found.
- Handles API rate limits and timeouts.

## Requirements

- Python 3.6 or higher
- `google-api-python-client`
- `requests`
- `python-dotenv`

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/youtube-transcript-downloader.git
   cd youtube-transcript-downloader
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies:**
   ```bash
   pip install google-api-python-client requests python-dotenv
   ```

4. **Create a `.env` file in the project directory and add your YouTube API key:**
   ```env
   YOUTUBE_API_KEY=your_youtube_api_key_here
   ```
   Procedure to obtain a youtube API Key : https://sohitmishra.medium.com/how-to-obtain-a-youtube-api-key-for-your-project-edc89877783a
   
## Usage

The script provides several command-line arguments to customize its behavior. Below are some example usages:

1. **Download transcriptions for the latest 5 videos from a channel in French:**
   ```bash
   python script.py -c "channel_name" -d "save_folder" -l fr 
   ```

2. **Download transcription for a specific video in English, including time codes:**
   ```bash
   python script.py -v "video_id" -d transcriptions -l en --time-codes 
   ```

3. **List available subtitles, number of videos, and the date of the most recent video from a channel:**
   ```bash
   python script.py -c Finary -d finary -l fr --list
   ```

### Command-line Arguments

- `--channel` or `-c`: The YouTube channel ID or URL. Required unless `--video-id` is provided.
- `--video-id` or `-v`: The YouTube video ID. Required unless `--channel` is provided.
- `--destination-directory` or `-d`: The directory where transcriptions will be saved. Required.
- `--max-number-of-videos` or `-m`: The maximum number of videos to download transcriptions for. Default is 5.
- `--languages-of-subtitles` or `-l`: Comma-separated list of languages for subtitles (e.g., `en,fr,es`). Default is system locale settings.
- `--format` or `-f`: Format for saving transcriptions. Options are `plain_text` or `json`. Default is `plain_text`.
- `--time-codes` or `-t`: Include time codes in the transcriptions. Disabled by default.
- `--rate-limit` or `-r`: API rate limit in calls per second. Default is 5.
- `--timeout` or `-T`: Timeout for API calls in seconds. Default is 10 seconds.
- `--log-level` or `-L`: Set the logging level. Options are `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Default is `INFO`.
- `--log-format` or `-F`: Format for logging output. Options are `plain_text` or `json`. Default is `plain_text`.
- `--list`: List available subtitles, number of videos, and date of the most recent video.
- `--include-shorts`: Include YouTube Shorts in the download.
- `--force-download`: Force download the first available subtitle if the requested language is not found.

## Logging

- The script creates a log file in the destination directory with the format `log_YYYYMMDD_HHMMSS.log`.
- Logging levels include `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.
- Log format options include `plain_text` and `json`.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or issues, please open an issue on the [GitHub repository](https://github.com/yourusername/youtube-transcript-downloader/issues).

---

Feel free to modify the content as needed, especially the repository URLs and any other specific details.
