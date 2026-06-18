
# ALONE-CODER
import os
import aiohttp


class NexGenBotsAPI:
    def __init__(self):
        from Lily import config
        self.api_key = config.NEXGENBOTS_API_TOKEN
        self.base_url = config.NEXGENBOTS_API_URL
        self.video_url = config.VIDEO_API_URL

    async def get_info(self, vid_id: str):
        if not self.api_key or not vid_id or len(vid_id) < 11:
            return None

        endpoint = f"{self.base_url}/info/{vid_id}"
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'success':
                            return data
        except Exception as e:
            print(f"NexGenBots info error: {e}")

        return None

    async def search(self, query: str, message_id: int, video: bool = False):
        return None

    async def playlist(self, limit: int, mention: str, url: str, video: bool = False):
        return None

    async def download(self, vid_id: str, video: bool = False):
        path = f"downloads/{vid_id}.{'mp4' if video else 'mp3'}"
        if os.path.exists(path) and os.path.getsize(path) > 1024:
            return path

        if self.api_key:
            data = await self.get_info(vid_id)
            if data:
                url = data.get("video_url") if video else data.get("audio_url")
                if url:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                                if response.status == 200:
                                    with open(path, "wb") as f:
                                        async for chunk in response.content.iter_chunked(1024 * 256):
                                            f.write(chunk)
                                    if os.path.exists(path) and os.path.getsize(path) > 1024:
                                        return path
                                    else:
                                        print(f"NexGenBots: downloaded file too small for {vid_id}")
                                        if os.path.exists(path):
                                            os.remove(path)
                                else:
                                    print(f"NexGenBots stream failed: status {response.status} for {vid_id}")
                    except Exception as e:
                        print(f"NexGenBots download error: {e}")
                        if os.path.exists(path):
                            try:
                                os.remove(path)
                            except:
                                pass
                else:
                    print(f"NexGenBots: no stream URL for {vid_id}")
            else:
                print(f"NexGenBots: info fetch failed for {vid_id}")

        print(f"Falling back to XBit or yt-dlp for {vid_id}...")
        from Lily import xbit, yt
        xbit_path = await xbit.download(vid_id, video=video)
        if xbit_path:
            return xbit_path
        return await yt.download(vid_id, video=video)
