# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of LilyMusic
#ALONE-CODER

import time
import logging
import static_ffmpeg
static_ffmpeg.add_paths()
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


__version__ = "3.0.1"

from config import Config

config = Config()
config.check()
tasks = []
boot = time.time()

from billu.core.bot import Bot
app = Bot()

from billu.core.dir import ensure_dirs
ensure_dirs()

from billu.core.userbot import Userbot
userbot = Userbot()

from billu.core.mongo import MongoDB
db = MongoDB()

from billu.core.lang import Language
lang = Language()

from billu.core.telegram import Telegram
from billu.core.youtube import YouTube
from billu.core.xbit import XBitAPI
from billu.core.nexgen import NexGenBotsAPI
tg = Telegram()
yt = YouTube()
xbit = XBitAPI()
nexgen = NexGenBotsAPI()

from billu.helpers import Queue
queue = Queue()

from billu.core.calls import TgCall
anon = TgCall()


async def stop() -> None:
    logger.info("Stopping...")
    for task in tasks:
        task.cancel()
        try:
            await task
        except:
            pass

    await app.exit()
    await userbot.exit()
    await db.close()

    logger.info("Stopped.\n")
