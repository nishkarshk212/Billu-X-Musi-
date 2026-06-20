# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of LilyMusic


import time
import psutil
import asyncio

from pyrogram import filters, types
from Lily import app, anon, boot, config, lang
from Lily.helpers import buttons


@app.on_message(filters.command(["alive", "ping"]) & ~app.bl_users)
@lang.language()
async def _ping(_, m: types.Message):
    start = time.time()
    sent = await m.reply_text(m.lang["pinging"])
    
    # Optimize system stats collection with parallel execution
    get_time = lambda s: (lambda r: (f"{r[-1]}, " if r[-1][:-4] != "0" else "") + ":".join(reversed(r[:-1])))([f"{v}{u}" for v, u in zip([s%60, (s//60)%60, (s//3600)%24, s//86400], ["s", "m", "h", "days"])])
    uptime = get_time(int(time.time() - boot))
    
    # Collect system stats in parallel for faster response
    cpu_task = asyncio.create_task(asyncio.to_thread(psutil.cpu_percent, interval=0))
    mem_task = asyncio.create_task(asyncio.to_thread(psutil.virtual_memory))
    disk_task = asyncio.create_task(asyncio.to_thread(psutil.disk_usage, "/"))
    ping_task = asyncio.create_task(anon.ping())
    
    # Wait for all tasks to complete
    cpu, mem, disk, ping_latency = await asyncio.gather(cpu_task, mem_task, disk_task, ping_task)
    
    latency = round((time.time() - start) * 1000, 2)
    await sent.edit_media(
        media=types.InputMediaPhoto(
            media=config.PING_IMG,
            caption=m.lang["ping_pong"].format(
                latency,
                uptime,
                cpu,
                mem.percent,
                disk.percent,
                ping_latency,
            ),
            has_spoiler=True,
        ),
        reply_markup=buttons.ping_markup(m.lang["support"]),
    )
