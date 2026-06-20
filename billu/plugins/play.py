# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of LilyMusic
#ALONE-CODER

from pathlib import Path
import asyncio

from pyrogram import filters, types
from pyrogram.types import LinkPreviewOptions

from billu import anon, app, config, db, lang, queue, tg, yt, xbit, nexgen
from billu.helpers import buttons, utils, Track, Media
from billu.helpers._play import checkUB


def playlist_to_queue(chat_id: int, tracks: list, user_id: int = None) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        if user_id:
            track.user_id = user_id
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text

async def background_download(file: Media | Track, video: bool):
    try:
        if not file.file_path:
            ext = 'mp4' if video else 'mp3'
            fname = f"downloads/{file.id}.{ext}"
            if Path(fname).exists() and Path(fname).stat().st_size > 1024:
                file.file_path = fname
            else:
                print(f"Starting background download for {file.id} using NexGenBots...")
                file.file_path = await nexgen.download(file.id, video=video)
                if file.file_path:
                    print(f"Background download successful: {file.file_path}")
                else:
                    print(f"Background download failed for {file.id}")
    except Exception as e:
        print(f"Background download error: {e}")

@app.on_message(
    filters.command(["play", "playforce", "vplay", "vplayforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:
    sent = await m.reply_text(m.lang["play_searching"])
    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    if url:
        if "playlist" in url:
            await sent.edit_text(m.lang["playlist_fetch"])
            if config.NEXGENBOTS_API_TOKEN:
                tracks = await nexgen.playlist(config.PLAYLIST_LIMIT, mention, url, video)
            if not tracks and config.XBIT_API_TOKEN:
                tracks = await xbit.playlist(config.PLAYLIST_LIMIT, mention, url, video)
            if not tracks:
                tracks = await yt.playlist(
                    config.PLAYLIST_LIMIT, mention, url, video
                )

            if not tracks:
                return await sent.edit_text(m.lang["playlist_error"])

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            if config.NEXGENBOTS_API_TOKEN:
                file = await nexgen.search(url, sent.id, video=video)
            if not file and config.XBIT_API_TOKEN:
                file = await xbit.search(url, sent.id, video=video)
            if not file:
                file = await yt.search(url, sent.id, video=video)

        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        # Fast play: Check query cache
        cache = await db.get_query_cache(query)
        if cache:
            cache.pop("_id", None); file = Track(**cache)
            file.message_id = sent.id
        else:
            if config.NEXGENBOTS_API_TOKEN:
                file = await nexgen.search(query, sent.id, video=video)
            if not file and config.XBIT_API_TOKEN:
                file = await xbit.search(query, sent.id, video=video)
            if not file:
                file = await yt.search(query, sent.id, video=video)
            
            if file and isinstance(file, Track):
                # Save to query cache
                import dataclasses
                await db.save_query_cache(query, dataclasses.asdict(file))
        
        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    elif media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    if not file:
        return await sent.edit_text(m.lang["play_usage"])

    if file.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_text(
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    if await db.is_logger():
        await utils.play_log(m, file.title, file.duration)

    file.user = mention
    file.user_id = m.from_user.id
    if force:
        queue.force_add(m.chat.id, file)
    else:
        position = queue.add(m.chat.id, file)

        if position != 0 or await db.get_call(m.chat.id):
            await sent.edit_text(
                m.lang["play_queued"].format(
                    position,
                    file.url,
                    file.title,
                    file.duration,
                    m.from_user.mention,
                ),
                reply_markup=buttons.play_queued(
                    m.chat.id, file.id, m.lang["play_now"]
                ),
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
            # Start background download for queued item
            asyncio.create_task(background_download(file, video))
            
            if tracks:
                added = playlist_to_queue(m.chat.id, tracks, m.from_user.id)
                await app.send_message(
                    chat_id=m.chat.id,
                    text=m.lang["playlist_queued"].format(len(tracks)) + added,
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
            return

    if not file.file_path:
        ext = 'mp4' if video else 'mp3'
        fname = f"downloads/{file.id}.{ext}"
        if Path(fname).exists() and Path(fname).stat().st_size > 1024:
            file.file_path = fname
        else:
            await sent.edit_text(m.lang["play_downloading"])
            file.file_path = await nexgen.download(file.id, video=video)

        # Verify download
        if not file.file_path:
            queue.remove_current(m.chat.id)
            return await sent.edit_text(m.lang["error_no_file"].format(config.SUPPORT_CHAT))
        p = Path(file.file_path)
        if not p.exists() or p.stat().st_size == 0:
            queue.remove_current(m.chat.id)
            return await sent.edit_text(m.lang["error_no_file"].format(config.SUPPORT_CHAT))

    await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
    if not tracks:
        return
    added = playlist_to_queue(m.chat.id, tracks, m.from_user.id)
    await app.send_message(
        chat_id=m.chat.id,
        text=m.lang["playlist_queued"].format(len(tracks)) + added,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
