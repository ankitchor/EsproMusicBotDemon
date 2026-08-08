import asyncio

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from EsproMusic import YouTube, app
from EsproMusic.core.call import Loy
from EsproMusic.misc import SUDOERS, db
from EsproMusic.utils.database import (
    get_active_chats,
    get_lang,
    get_upvote_count,
    is_active_chat,
    is_Music_playing,
    is_nonadmin_chat,
    Music_off,
    Music_on,
    set_loop,
)
from EsproMusic.utils.decorators.language import languageCB
from EsproMusic.utils.formatters import seconds_to_min
from EsproMusic.utils.inline import close_markup, stream_markup, stream_markup_timer
from EsproMusic.utils.stream.autoclear import auto_clean
from EsproMusic.utils.thumbnails import get_thumb
from config import (
    BANNED_USERS,
    SUPPORT_CHAT,
    SOUNCLOUD_IMG_URL,
    STREAM_IMG_URL,
    TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL,
    adminlist,
    confirmer,
    votemode,
)
from strings import get_string

checker = {}
upvoters = {}


@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()

    try:
        callback_request = callback_data.split(None, 1)[1]
        command, chat = callback_request.split("|")
    except (IndexError, ValueError):
        return await CallbackQuery.answer(
            "Invalid callback data.",
            show_alert=True,
        )

    counter = None

    if "_" in str(chat):
        bet = chat.split("_", 1)
        chat = bet[0]
        counter = bet[1]

    try:
        chat_id = int(chat)
    except (TypeError, ValueError):
        return await CallbackQuery.answer(
            "Invalid chat ID.",
            show_alert=True,
        )

    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(
            _["general_5"],
            show_alert=True,
        )

    mention = CallbackQuery.from_user.mention

    # =========================
    # UPVOTE
    # =========================
    if command == "UpVote":
        if chat_id not in votemode:
            votemode[chat_id] = {}

        if chat_id not in upvoters:
            upvoters[chat_id] = {}

        voters = upvoters[chat_id].get(CallbackQuery.message.id)

        if not voters:
            upvoters[chat_id][CallbackQuery.message.id] = []

        vote = votemode[chat_id].get(CallbackQuery.message.id)

        if vote is None:
            votemode[chat_id][CallbackQuery.message.id] = 0

        if (
            CallbackQuery.from_user.id
            in upvoters[chat_id][CallbackQuery.message.id]
        ):
            upvoters[chat_id][CallbackQuery.message.id].remove(
                CallbackQuery.from_user.id
            )

            votemode[chat_id][CallbackQuery.message.id] -= 1

        else:
            upvoters[chat_id][CallbackQuery.message.id].append(
                CallbackQuery.from_user.id
            )

            votemode[chat_id][CallbackQuery.message.id] += 1

        upvote = await get_upvote_count(chat_id)

        get_upvotes = int(
            votemode[chat_id][CallbackQuery.message.id]
        )

        if get_upvotes >= upvote:
            votemode[chat_id][CallbackQuery.message.id] = upvote

            try:
                exists = confirmer[chat_id][CallbackQuery.message.id]
                current = db[chat_id][0]
            except Exception:
                return await CallbackQuery.edit_message_text(
                    "ғᴀɪʟᴇᴅ."
                )

            try:
                if current["vidid"] != exists["vidid"]:
                    return await CallbackQuery.edit_message_text(
                        _["admin_35"]
                    )

                if current["file"] != exists["file"]:
                    return await CallbackQuery.edit_message_text(
                        _["admin_35"]
                    )

            except Exception:
                return await CallbackQuery.edit_message_text(
                    _["admin_36"]
                )

            try:
                await CallbackQuery.edit_message_text(
                    _["admin_37"].format(upvote)
                )
            except Exception:
                pass

            command = counter
            mention = "ᴜᴘᴠᴏᴛᴇs"

        else:
            if (
                CallbackQuery.from_user.id
                in upvoters[chat_id][CallbackQuery.message.id]
            ):
                await CallbackQuery.answer(
                    _["admin_38"],
                    show_alert=True,
                )
            else:
                await CallbackQuery.answer(
                    _["admin_39"],
                    show_alert=True,
                )

            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=f"👍 {get_upvotes}",
                            callback_data=(
                                f"ADMIN  UpVote|"
                                f"{chat_id}_{counter}"
                            ),
                        )
                    ]
                ]
            )

            await CallbackQuery.answer(
                _["admin_40"],
                show_alert=True,
            )

            return await CallbackQuery.edit_message_reply_markup(
                reply_markup=upl
            )

    # =========================
    # ADMIN CHECK
    # =========================
    else:
        is_non_admin = await is_nonadmin_chat(
            CallbackQuery.message.chat.id
        )

        if not is_non_admin:
            if CallbackQuery.from_user.id not in SUDOERS:
                admins = adminlist.get(
                    CallbackQuery.message.chat.id
                )

                if not admins:
                    return await CallbackQuery.answer(
                        _["admin_13"],
                        show_alert=True,
                    )

                if CallbackQuery.from_user.id not in admins:
                    return await CallbackQuery.answer(
                        _["admin_14"],
                        show_alert=True,
                    )

    # =========================
    # PAUSE
    # =========================
    if command == "Pause":
        if not await is_Music_playing(chat_id):
            return await CallbackQuery.answer(
                _["admin_1"],
                show_alert=True,
            )

        await CallbackQuery.answer()

        await Music_off(chat_id)
        await Loy.pause_stream(chat_id)

        await CallbackQuery.message.reply_text(
            _["admin_2"].format(mention),
            reply_markup=close_markup(_),
        )

    # =========================
    # RESUME
    # =========================
    elif command == "Resume":
        if await is_Music_playing(chat_id):
            return await CallbackQuery.answer(
                _["admin_3"],
                show_alert=True,
            )

        await CallbackQuery.answer()

        await Music_on(chat_id)
        await Loy.resume_stream(chat_id)

        await CallbackQuery.message.reply_text(
            _["admin_4"].format(mention),
            reply_markup=close_markup(_),
        )

    # =========================
    # STOP / END
    # =========================
    elif command in ("Stop", "End"):
        await CallbackQuery.answer()

        await Loy.stop_stream(chat_id)
        await set_loop(chat_id, 0)

        await CallbackQuery.message.reply_text(
            _["admin_5"].format(mention),
            reply_markup=close_markup(_),
        )

        try:
            await CallbackQuery.message.delete()
        except Exception:
            pass

    # =========================
    # SKIP / REPLAY
    # =========================
    elif command in ("Skip", "Replay"):
        check = db.get(chat_id)

        if not check:
            return await CallbackQuery.answer(
                _["admin_1"],
                show_alert=True,
            )

        if command == "Skip":
            txt = (
                f"➻ sᴛʀᴇᴀᴍ sᴋɪᴩᴩᴇᴅ 🎄\n"
                f"│ \n"
                f"└ʙʏ : {mention} 🥀"
            )

            popped = None

            try:
                popped = check.pop(0)

                if popped:
                    await auto_clean(popped)

                if not check:
                    await CallbackQuery.edit_message_text(
                        txt
                    )

                    await CallbackQuery.message.reply_text(
                        text=_["admin_6"].format(
                            mention,
                            CallbackQuery.message.chat.title,
                        ),
                        reply_markup=close_markup(_),
                    )

                    try:
                        return await Loy.stop_stream(chat_id)
                    except Exception:
                        return

            except Exception:
                try:
                    await CallbackQuery.edit_message_text(
                        txt
                    )

                    await CallbackQuery.message.reply_text(
                        text=_["admin_6"].format(
                            mention,
                            CallbackQuery.message.chat.title,
                        ),
                        reply_markup=close_markup(_),
                    )

                    return await Loy.stop_stream(chat_id)

                except Exception:
                    return

        else:
            txt = (
                f"➻ sᴛʀᴇᴀᴍ ʀᴇ-ᴘʟᴀʏᴇᴅ 🎄\n"
                f"│ \n"
                f"└ʙʏ : {mention} 🥀"
            )

        await CallbackQuery.answer()

        try:
            queued = check[0]["file"]
            title = check[0]["title"].title()
            user = check[0]["by"]
            duration = check[0]["dur"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
        except (KeyError, IndexError, TypeError):
            return await CallbackQuery.message.reply_text(
                "❌ Song data not found."
            )

        status = (
            True
            if str(streamtype) == "video"
            else None
        )

        db[chat_id][0]["played"] = 0

        exis = check[0].get("old_dur")

        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0

        # =========================
        # LIVE STREAM
        # =========================
        if "live_" in queued:
            n, link = await YouTube.video(
                videoid,
                True,
            )

            if n == 0:
                return await CallbackQuery.message.reply_text(
                    text=_["admin_7"].format(title),
                    reply_markup=close_markup(_),
                )

            try:
                image = await YouTube.thumbnail(
                    videoid,
                    True,
                )
            except Exception:
                image = None

            try:
                await Loy.skip_stream(
                    chat_id,
                    link,
                    video=status,
                    image=image,
                )
            except Exception:
                return await CallbackQuery.message.reply_text(
                    _["call_6"]
                )

            button = stream_markup(
                _,
                chat_id,
            )

            img = await get_thumb(videoid)

            run = await CallbackQuery.message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    duration,
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

            await CallbackQuery.edit_message_text(
                txt,
                reply_markup=close_markup(_),
            )

        # =========================
        # VIDEO FILE
        # =========================
        elif "vid_" in queued:
            mystic = await CallbackQuery.message.reply_text(
                _["call_7"],
                disable_web_page_preview=True,
            )

            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=status,
                )
            except Exception:
                return await mystic.edit_text(
                    _["call_6"]
                )

            try:
                image = await YouTube.thumbnail(
                    videoid,
                    True,
                )
            except Exception:
                image = None

            try:
                await Loy.skip_stream(
                    chat_id,
                    file_path,
                    video=status,
                    image=image,
                )
            except Exception:
                return await mystic.edit_text(
                    _["call_6"]
                )

            button = stream_markup(
                _,
                chat_id,
            )

            img = await get_thumb(videoid)

            run = await CallbackQuery.message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    duration,
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

            await CallbackQuery.edit_message_text(
                txt,
                reply_markup=close_markup(_),
            )

            try:
                await mystic.delete()
            except Exception:
                pass

        # =========================
        # INDEX STREAM
        # =========================
        elif "index_" in queued:
            try:
                await Loy.skip_stream(
                    chat_id,
                    videoid,
                    video=status,
                )
            except Exception:
                return await CallbackQuery.message.reply_text(
                    _["call_6"]
                )

            button = stream_markup(
                _,
                chat_id,
            )

            run = await CallbackQuery.message.reply_photo(
                photo=STREAM_IMG_URL,
                caption=_["stream_2"].format(user),
                reply_markup=InlineKeyboardMarkup(button),
            )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

            await CallbackQuery.edit_message_text(
                txt,
                reply_markup=close_markup(_),
            )

        # =========================
        # TELEGRAM / SOUNDCLOUD / OTHER
        # =========================
        else:
            if videoid in ("telegram", "soundcloud"):
                image = None
            else:
                try:
                    image = await YouTube.thumbnail(
                        videoid,
                        True,
                    )
                except Exception:
                    image = None

            try:
                await Loy.skip_stream(
                    chat_id,
                    queued,
                    video=status,
                    image=image,
                )
            except Exception:
                return await CallbackQuery.message.reply_text(
                    _["call_6"]
                )

            if videoid == "telegram":
                button = stream_markup(
                    _,
                    chat_id,
                )

                run = await CallbackQuery.message.reply_photo(
                    photo=(
                        TELE
