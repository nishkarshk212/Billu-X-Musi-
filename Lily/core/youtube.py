# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License
# This file is part of LilyMusic
# ALONE-CODER

import os
import re
import asyncio
import aiohttp
from urllib.parse import quote
from Lily import logger
from Lily.helpers import Track, utils

DOWNLOAD_DIR = "downloads"


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.api_base = "https://yt-api-two-plum.vercel.app"
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/search?query={quote(query)}&limit=1"
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    results = await resp.json()
                    if results and len(results) > 0:
                        data = results[0]
                        return Track(
                            id=data.get("id"),
                            channel_name=data.get("channel", ""),
                            duration=data.get("duration", ""),
                            duration_sec=utils.to_seconds(data.get("duration", "")),
                            message_id=m_id,
                            title=data.get("title", "")[:25],
                            thumbnail=data.get("thumbnail", ""),
                            url=data.get("url", ""),
                            view_count=data.get("views", ""),
                            video=video,
                        )
        except Exception as e:
            logger.warning(f"YouTube search error: {e}")
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            pass
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

        try:
            async with aiohttp.ClientSession() as session:
                download_url = f"{self.api_base}/download?url={quote(url)}"
                async with session.get(download_url, timeout=300) as resp:
                    resp.raise_for_status()
                    with open(file_path, "wb") as f:
                        f.write(await resp.read())
                if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
                    return file_path
        except Exception as e:
            logger.warning(f"Download error for {video_id}: {e}")

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return None
