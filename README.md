# VideoGrabber

A simple and user-friendly Python GUI application to download videos and audio from various online sources using [yt-dlp](https://github.com/yt-dlp/yt-dlp). Supports choosing video quality, selecting download folders, and shows live download progress and logs.

---

## Features

- Download videos from many supported sites (e.g., YouTube, Vimeo, etc.)
- Select desired video quality:
  - Best available
  - 1080p
  - 720p
  - 480p
  - Audio only (MP3)
- Choose custom download directory via a folder browser
- Real-time progress bar, download speed, and estimated time remaining
- View detailed log of download process
- Open folder containing downloaded file with one click after completion
- Bundled FFmpeg executable for audio extraction and video processing

---


**Clone the repository:**

Install dependencies:

pip install yt-dlp


## Structure

```text
VideoDownload/
├── ffmpeg/
│ └── ffmpeg.exe 
├── VideoDownload.py 
```