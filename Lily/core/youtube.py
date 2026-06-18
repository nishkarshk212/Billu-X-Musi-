# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of LilyMusic
# ALONE-CODER

import os
import re
import asyncio
import aiohttp
import random
import yt_dlp
from py_yt import Playlist, VideosSearch
from urllib.parse import quote
from Lily import logger
from Lily.helpers import Track, utils

DOWNLOAD_DIR = "downloads"


def seconds_to_time(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.api_base = "https://yt-api-two-plum.vercel.app"
        self.cookies = []
        self.checked = False
        self.cookie_dir = "Lily/cookies"
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

    def get_cookies(self):
        if not self.checked:
            if os.path.exists(self.cookie_dir):
                for file in os.listdir(self.cookie_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(f"{self.cookie_dir}/{file}")
            self.checked = True
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("Cookies are missing; downloads might fail.")
            return None
        return random.choice(self.cookies)

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Saving cookies from urls...")
        if not os.path.exists(self.cookie_dir):
            os.makedirs(self.cookie_dir)
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls):
                path = f"{self.cookie_dir}/cookie_{i}.txt"
                link = "https://batbin.me/api/v2/paste/" + url.split("/")[-1]
                try:
                    async with session.get(link) as resp:
                        resp.raise_for_status()
                        with open(path, "wb") as fw:
                            fw.write(await resp.read())
                except Exception as e:
                    logger.warning(f"Failed to save cookie from {url}: {e}")
        logger.info(f"Cookies saved in {self.cookie_dir}.")

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        # First try yt-api
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/search?query={quote(query)}&limit=1"
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    response_data = await resp.json()
                    if response_data.get("status") == "success" and "results" in response_data:
                        results = response_data["results"]
                        if results and len(results) > 0:
                            data = results[0]
                            duration_sec = int(data.get("duration", 0))
                            duration_str = seconds_to_time(data.get("duration", 0))
                            return Track(
                                id=data.get("id"),
                                channel_name=data.get("channel", ""),
                                duration=duration_str,
                                duration_sec=duration_sec,
                                message_id=m_id,
                                title=data.get("title", "")[:25],
                                thumbnail=data.get("thumbnail"),
                                url=data.get("url", ""),
                                view_count="",
                                video=video,
                            )
        except Exception as e:
            logger.warning(f"YouTube API search error: {e}")

        # Fallback to original py_yt search
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
            if results and results["result"]:
                data = results["result"][0]
                return Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name"),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    message_id=m_id,
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails", [{}])[-1].get("url", "").split("?")[0],
                    url=data.get("link"),
                    view_count=data.get("viewCount", {}).get("short"),
                    video=video,
                )
        except Exception as e:
            logger.warning(f"py_yt search error: {e}")

        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails", [{}])[-1].get("url", "").split("?")[0],
                    url=data.get("link", "").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception as e:
            logger.warning(f"Playlist fetch error: {e}")
        return tracks

    async def download(self, video_id: str, video: bool = False) -> str | None:
        if not video_id or len(video_id) < 11:
            return None

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        ext = "mp4" if video else "mp3"
        file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

        if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
            return file_path

        url = f"{self.base}{video_id}"

        # First try yt-api
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                download_url = f"{self.api_base}/download?url={quote(url)}"
                async with session.get(download_url) as resp:
                    resp.raise_for_status()
                    with open(file_path, "wb") as f:
                        f.write(await resp.read())
                if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
                    return file_path
        except Exception as e:
            logger.warning(f"YouTube API download error for {video_id}: {e}")

        # Fallback to yt-dlp
        cookie_file = self.get_cookies()

        ydl_opts = {
            "format": "bestvideo+bestaudio/best" if video else "bestaudio/best",
            "outtmpl": os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        }

        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        if not video:
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: self._run_ydl(url, ydl_opts))
            if info and os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
                return file_path
        except Exception as e:
            logger.warning(f"yt-dlp download error for {video_id}: {e}")

        # Cleanup partial files
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return None

    def _run_ydl(self, url: str, opts: dict) -> dict | None:
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                return ydl.extract_info(url, download=True)
            except Exception as e:
                logger.warning(f"yt-dlp extract error: {e}")
                return None
