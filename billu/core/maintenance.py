# ALONE-CODER
import asyncio
import os
import sys
import shutil
from pathlib import Path
from billu import logger, db

async def auto_cache_clear():
    """
    Periodic task to clear old cache entries every 24 hours.
    """
    # 24 hours in seconds
    interval = 24 * 60 * 60
    
    while True:
        await asyncio.sleep(interval)
        
        logger.info("Starting scheduled 24-hour cache clearing...")
        
        try:
            # Clear old query cache from MongoDB
            deleted_count = await db.clear_old_cache(hours=24)
            logger.info(f"Cleared {deleted_count} old cache entries from MongoDB.")
        except Exception as e:
            logger.error(f"Error clearing MongoDB cache: {e}")
        
        # Clear local cache directory
        cache_dir = Path("cache")
        if cache_dir.exists():
            try:
                for item in cache_dir.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    except Exception as e:
                        logger.error(f"Error clearing cache item {item}: {e}")
                logger.info("Local cache directory cleared.")
            except Exception as e:
                logger.error(f"Error clearing local cache: {e}")
        
        logger.info("24-hour cache clearing completed.")

async def auto_maintenance():
    """
    Periodic task to clear cache and restart the bot every 7 days.
    """
    # 7 days in seconds
    interval = 7 * 24 * 60 * 60
    
    while True:
        await asyncio.sleep(interval)
        
        logger.info("Starting scheduled 7-day maintenance...")
        
        # 1. Clear Local Cache & Downloads
        for directory in ["cache", "downloads"]:
            dir_path = Path(directory)
            if dir_path.exists():
                for item in dir_path.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    except Exception as e:
                        logger.error(f"Error clearing {item}: {e}")
        
        logger.info("Local cache and downloads cleared.")
        
        # 2. Restart the bot
        # This will replace the current process with a new one
        logger.info("Scheduled restart initiated...")
        os.execl(sys.executable, sys.executable, "-m", "Lily")
