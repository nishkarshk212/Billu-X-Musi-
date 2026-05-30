# ALONE-CODER
import aiohttp

class XBitAPI:
    def __init__(self):
        from AloneX import config
        self.api_key = config.XBIT_API_TOKEN
        self.base_url = config.XBIT_API_URL

    async def get_info(self, vid_id: str):
        if not self.api_key:
            return None
        
        endpoint = f"{self.base_url}/info/{vid_id}"
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'success':
                            return data
        except Exception as e:
            print(f"Error fetching from XBit API: {e}")
        
        return None

    async def download(self, vid_id: str, video: bool = False):
        if self.api_key:
            data = await self.get_info(vid_id)
            if data:
                return data.get("video_url") if video else data.get("audio_url")
        
        from AloneX import yt
        return await yt.download(vid_id, video=video)
