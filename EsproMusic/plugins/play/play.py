import random
import string

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall

import config
from EsproMusic import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app
from EsproMusic.core.call import Loy
from EsproMusic.utils import seconds_to_min, time_to_seconds
from EsproMusic.utils.channelplay import get_channeplayCB
from EsproMusic.utils.decorators.language import languageCB
from EsproMusic.utils.decorators.play import PlayWrapper
from EsproMusic.utils.formatters import formats
from EsproMusic.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from EsproMusic.utils.logger import play_logs
from EsproMusic.utils.stream.stream import stream
from config import BANNED_USERS, lyrical


@app.on_message(
    filters.command(
        [
            "play",
            "vplay",
            "cplay",
            "cvplay",
            "playforce",
            "vplayforce",
            "cplayforce",
            "cvplayforce",
        ]
    )
    & filters.group
    & ~BANNED_USERS
)
@PlayWrapper
async def play_commnd(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    mystic = await message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )

    plist_id = None
    slider = None
    plist_type = None
    spotify = None

    user_id = message.from_user.id
    user_name = message.from_user.first_name

    audio_telegram = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )

    video_telegram = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )

    # =========================================================
    # TELEGRAM AUDIO
    # =========================================================

    if audio_telegram:
        if audio_telegram.file_size > 104857600:
            return await mystic.edit_text(_["play_5"])

        duration_min = seconds_to_min(audio_telegram.duration)

        if audio_telegram.duration > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(
                    config.DURATION_LIMIT_MIN,
                    app.mention,
                )
            )

        file_path = await Telegram.get_filepath(audio=audio_telegram)

        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(
                audio_telegram,
                audio=True,
            )

            dur = await Telegram.get_duration(
                audio_telegram,
                file_path,
            )

            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = (
                    e
                    if ex_type == "AssistantErr"
                    else _["general_2"].format(ex_type)
                )
                return await mystic.edit_text(err)

            return await mystic.delete()

        return

    # =========================================================
    # TELEGRAM VIDEO
    # =========================================================

    elif video_telegram:
        if message.reply_to_message.document:
            try:
                ext = video_telegram.file_name.split(".")[-1]

                if ext.lower() not in formats:
                    return await mystic.edit_text(
                        _["play_7"].format(
                            f"{' | '.join(formats)}"
                        )
                    )
            except Exception:
                return await mystic.edit_text(
                    _["play_7"].format(
                        f"{' | '.join(formats)}"
                    )
                )

        if video_telegram.file_size > config.TG_VIDEO_FILESIZE_LIMIT:
            return await mystic.edit_text(_["play_8"])

        file_path = await Telegram.get_filepath(
            video=video_telegram
        )

        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)

            file_name = await Telegram.get_filename(
                video_telegram
            )

            dur = await Telegram.get_duration(
                video_telegram,
                file_path,
            )

            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=True,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = (
                    e
                    if ex_type == "AssistantErr"
                    else _["general_2"].format(ex_type)
                )
                return await mystic.edit_text(err)

            return await mystic.delete()

        return

    # =========================================================
    # URL PLAY
    # =========================================================

    elif url:

        # =====================================================
        # YOUTUBE
        # =====================================================

        if await YouTube.exists(url):

            if "playlist" in url:
                try:
                    details = await YouTube.playlist(
                        url,
                        config.PLAYLIST_FETCH_LIMIT,
                        message.from_user.id,
                    )
                except Exception:
                    return await mystic.edit_text(_["play_3"])

                if not details:
                    return await mystic.edit_text(_["play_3"])

                streamtype = "playlist"
                plist_type = "yt"

                if "=" in url:
                    if "&" in url:
                        plist_id = (
                            url.split("=")[1]
                            .split("&")[0]
                        )
                    else:
                        plist_id = url.split("=")[1]
                else:
                    return await mystic.edit_text(_["play_3"])

                img = config.PLAYLIST_IMG_URL
                cap = _["play_9"]

            else:
                try:
                    details, track_id = await YouTube.track(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])

                # FIX: YouTube.track() can return None
                if not details:
                    return await mystic.edit_text(
                        "❌ Song details nahi mil paayi.\n"
                        "Please dusra YouTube link try karein."
                    )

                streamtype = "youtube"

                img = details.get("thumb")

                cap = _["play_10"].format(
                    details.get("title", "Unknown"),
                    details.get("duration_min") or "Live",
                )

        # =====================================================
        # SPOTIFY
        # =====================================================

        elif await Spotify.valid(url):

            spotify = True

            if (
                not config.SPOTIFY_CLIENT_ID
                and not config.SPOTIFY_CLIENT_SECRET
            ):
                return await mystic.edit_text(
                    "» sᴘᴏᴛɪғʏ ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ʏᴇᴛ.\n\n"
                    "ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
                )

            if "track" in url:
                try:
                    details, track_id = await Spotify.track(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])

                if not details:
                    return await mystic.edit_text(_["play_3"])

                streamtype = "youtube"
                img = details.get("thumb")

                cap = _["play_10"].format(
                    details.get("title", "Unknown"),
                    details.get("duration_min") or "Live",
                )

            elif "playlist" in url:
                try:
                    details, plist_id = await Spotify.playlist(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])

                if not details:
                    return await mystic.edit_text(_["play_3"])

                streamtype = "playlist"
                plist_type = "spplay"
                img = config.SPOTIFY_PLAYLIST_IMG_URL

                cap = _["play_11"].format(
                    app.mention,
                    message.from_user.mention,
                )

            elif "album" in url:
                try:
                    details, plist_id = await Spotify.album(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])

                if not details:
                    return await mystic.edit_text(_["play_3"])

                streamtype = "playlist"
                plist_type = "spalbum"
                img = config.SPOTIFY_ALBUM_IMG_URL

                cap = _["play_11"].format(
                    app.mention,
                    message.from_user.mention,
                )

            elif "artist" in url:
                try:
                    details, plist_id = await Spotify.artist(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])

                if not details:
                    return await mystic.edit_text(_["play_3"])

                streamtype = "playlist"
                plist_type = "spartist"
                img = config.SPOTIFY_ARTIST_IMG_URL

                cap = _["play_11"].format(
                    message.from_user.first_name
                )

            else:
                return await mystic.edit_text(_["play_15"])

        # =====================================================
        # APPLE MUSIC
        # =====================================================

        elif await Apple.valid(url):

            if "album" in url:
                try:
                    details, track_id = await Apple.track(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])

                if not details:
                    return await mystic.edit_text(_["play_3"])

                streamtype = "youtube"
                img = details.get("thumb")

                cap = _["play_10"].format(
                    details.get("title", "Unknown"),
                    details.get("duration_min") or "Live",
                )

            elif "playlist" in url:
                spotify = True

                try:
                    details, plist_id = await Apple.playlist(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])

                if not details:
                    return await mystic.edit_text(_["play_3"])

                streamtype = "playlist"
                plist_type = "apple"

                cap = _["play_12"].format(
                    app.mention,
                    message.from_user.mention,
                )

                img = url

            else:
                return await mystic.edit_text(_["play_3"])

        # =====================================================
        # RESSO
        # =====================================================

        elif await Resso.valid(url):

            try:
                details, track_id = await Resso.track(url)
            except Exception:
                return await mystic.edit_text(_["play_3"])

            if not details:
                return await mystic.edit_text(_["play_3"])

            streamtype = "youtube"
            img = details.get("thumb")

            cap = _["play_10"].format(
                details.get("title", "Unknown"),
                details.get("duration_min") or "Live",
            )

        # =====================================================
        # SOUNDCLOUD
        # =====================================================

        elif await SoundCloud.valid(url):

            try:
                details, track_path = await SoundCloud.download(url)
            except Exception:
                return await mystic.edit_text(_["play_3"])

            if not details:
                return await mystic.edit_text(_["play_3"])

            duration_sec = details.get("duration_sec") or 0

            if duration_sec > config.DURATION_LIMIT:
                return await mystic.edit_text(
                    _["play_6"].format(
                        config.DURATION_LIMIT_MIN,
                        app.mention,
                    )
                )

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="soundcloud",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__

                err = (
                    e
                    if ex_type == "AssistantErr"
                    else _["general_2"].format(ex_type)
                )

                return await mystic.edit_text(err)

            return await mystic.delete()

        # =====================================================
        # M3U8 / INDEX LINK
        # =====================================================

        else:
            try:
                await Loy.stream_call(url)

            except NoActiveGroupCall:
                await mystic.edit_text(_["black_9"])

                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=_["play_17"],
                )

            except Exception as e:
                return await mystic.edit_text(
                    _["general_2"].format(
                        type(e).__name__
                    )
                )

            await mystic.edit_text(_["str_2"])

            try:
                await stream(
                    _,
                    mystic,
                    message.from_user.id,
                    url,
                    chat_id,
                    message.from_user.first_name,
                    message.chat.id,
                    video=video,
                    streamtype="index",
                    forceplay=fplay,
                )

            except Exception as e:
                ex_type = type(e).__name__

                err = (
                    e
                    if ex_type == "AssistantErr"
                    else _["general_2"].format(ex_type)
                )

                return await mystic.edit_text(err)

            return await play_logs(
                message,
                streamtype="M3u8 or Index Link",
            )

    # =========================================================
    # SEARCH QUERY
    # =========================================================

    else:

        if len(message.command) < 2:
            buttons = botplaylist_markup(_)

            return await mystic.edit_text(
                _["play_18"],
                reply_markup=InlineKeyboardMarkup(buttons),
            )

        slider = True

        query = message.text.split(None, 1)[1]

        if "-v" in query:
            query = query.replace("-v", "")

        try:
            details, track_id = await YouTube.track(query)
        except Exception:
            return await mystic.edit_text(_["play_3"])

        # FIX: prevent NoneType error
        if not details:
            return await mystic.edit_text(
                "❌ Song nahi mila.\n"
                "Please song ka naam dobara try karein."
            )

        streamtype = "youtube"

    # =========================================================
    # DIRECT PLAY
    # =========================================================

    if str(playmode) == "Direct":

        if not plist_type:

            # FIX: details can be None
            duration_min = (
                details.get("duration_min")
                if details
                else None
            )

            if duration_min:

                try:
                    duration_sec = time_to_seconds(
                        duration_min
                    )
                except Exception:
                    duration_sec = 0

                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit_text(
                        _["play_6"].format(
                            config.DURATION_LIMIT_MIN,
                            app.mention,
                        )
                    )

            else:
                buttons = livestream_markup(
                    _,
                    track_id,
                    user_id,
                    "v" if video else "a",
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )

                return await mystic.edit_text(
                    _["play_13"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

        try:
            await stream(
                _,
                mystic,
                user_id,
                details,
                chat_id,
                user_name,
                message.chat.id,
                video=video,
                streamtype=streamtype,
                spotify=spotify,
                forceplay=fplay,
            )

        except Exception as e:
            ex_type = type(e).__name__

            err = (
                e
                if ex_type == "AssistantErr"
                else _["general_2"].format(ex_type)
            )

            return await mystic.edit_text(err)

        await mystic.delete()

        return await play_logs(
            message,
            streamtype=streamtype,
        )

    # =========================================================
    # NON DIRECT PLAY
    # =========================================================

    else:

        if plist_type:

            ran_hash = "".join(
                random.choices(
                    string.ascii_uppercase
                    + string.digits,
                    k=10,
                )
            )

            lyrical[ran_hash] = plist_id

            buttons = playlist_markup(
                _,
                ran_hash,
                message.from_user.id,
                plist_type,
                "c" if channel else "g",
                "f" if fplay else "d",
            )

            await mystic.delete()

            await message.reply_photo(
                photo=img,
                caption=cap,
                reply_markup=InlineKeyboardMarkup(
                    buttons
                ),
            )

            return await play_logs(
                message,
                streamtype=f"Playlist : {plist_type}",
            )

        else:

            if slider:

                buttons = slider_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    query,
                    0,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )

                await mystic.delete()

                duration = (
                    details.get("duration_min")
                    or "Live"
                )

                await message.reply_photo(
                    photo=details.get("thumb"),
                    caption=_["play_10"].format(
                        details.get(
                            "title",
                            "Unknown",
                        ).title(),
                        duration,
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        buttons
                    ),
                )

                return await play_logs(
                    message,
                    streamtype="Searched on Youtube",
                )

            else:

                buttons = track_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )

                await mystic.delete()

                await message.reply_photo(
                    photo=img,
                    caption=cap,
                    reply_markup=InlineKeyboardMarkup(
                        buttons
                    ),
                )

                return await play_logs(
                    message,
                    streamtype="URL Searched Inline",
                )


# =============================================================
# MUSIC STREAM CALLBACK
# =============================================================

@app.on_callback_query(
    filters.regex("MusicStream") & ~BANNED_USERS
)
@languageCB
async def play_Music(client, CallbackQuery, _):

    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]

    vidid, user_id, mode, cplay, fplay = callback_request.split(
        "|"
    )

    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(
                _["playcb_1"],
                show_alert=True,
            )
        except Exception:
            return

    try:
        chat_id, channel = await get_channeplayCB(
            _,
            cplay,
            CallbackQuery,
        )
    except Exception:
        return

    user_name = CallbackQuery.from_user.first_name

    try:
        await CallbackQuery.message.delete()
        await CallbackQuery.answer()
    except Exception:
        pass

    mystic = await CallbackQuery.message.reply_text(
        _["play_2"].format(channel)
        if channel
        else _["play_1"]
    )

    try:
        details, track_id = await YouTube.track(
            vidid,
            True,
        )
    except Exception:
        return await mystic.edit_text(_["play_3"])

    # FIX: details None check
    if not details:
        return await mystic.edit_text(
            "❌ Song details nahi mil paayi.\n"
            "Please dobara try karein."
        )

    duration_min = details.get("duration_min")

    if duration_min:

        try:
            duration_sec = time_to_seconds(
                duration_min
            )
        except Exception:
            duration_sec = 0

        if duration_sec > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(
                    config.DURATION_LIMIT_MIN,
                    app.mention,
                )
            )

    else:
        buttons = livestream_markup(
            _,
            track_id,
            CallbackQuery.from_user.id,
            mode,
            "c" if cplay == "c" else "g",
            "f" if fplay else "d",
        )

        return await mystic.edit_text(
            _["play_13"],
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None

    try:
        await stream(
            _,
            mystic,
            CallbackQuery.from_user.id,
            details,
            chat_id,
            user_name,
            CallbackQuery.message.chat.id,
            video,
            streamtype="youtube",
            forceplay=ffplay
