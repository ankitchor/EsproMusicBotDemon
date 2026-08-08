import asyncio

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from EsproMusic import YouTube, app
from EsproMusic.misc import SUDOERS
from EsproMusic.utils.database import (
    get_assistant,
    get_cmode,
    get_lang,
    get_playmode,
    get_playtype,
    is_active_chat,
    is_maintenance,
)
from EsproMusic.utils.inline import botplaylist_markup
from config import PLAYLIST_IMG_URL, SUPPORT_CHAT, adminlist
from strings import get_string

links = {}


def PlayWrapper(command):
    async def wrapper(client, message):

        # =====================================================
        # LANGUAGE
        # =====================================================

        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
        except Exception:
            language = "en"
            _ = get_string(language)

        # =====================================================
        # USER CHECK
        # =====================================================

        if not message.from_user:
            return

        # =====================================================
        # ANONYMOUS ADMIN CHECK
        # =====================================================

        if message.sender_chat:
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ʜᴏᴡ ᴛᴏ ғɪx ?",
                            callback_data="LoymousAdmin",
                        ),
                    ]
                ]
            )

            return await message.reply_text(
                _["general_3"],
                reply_markup=upl,
            )

        # =====================================================
        # MAINTENANCE
        # =====================================================

        try:
            maintenance = await is_maintenance()
        except Exception:
            maintenance = False

        if maintenance is False:

            if message.from_user.id not in SUDOERS:
                return await message.reply_text(
                    text=(
                        f"{app.mention} "
                        "ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ, "
                        f"ᴠɪsɪᴛ <a href={SUPPORT_CHAT}>"
                        "sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a> "
                        "ғᴏʀ ᴋɴᴏᴡɪɴɢ ᴛʜᴇ ʀᴇᴀsᴏɴ."
                    ),
                    disable_web_page_preview=True,
                )

        # =====================================================
        # DELETE COMMAND
        # =====================================================

        try:
            await message.delete()
        except Exception:
            pass

        # =====================================================
        # REPLY AUDIO
        # =====================================================

        audio_telegram = (
            (
                message.reply_to_message.audio
                or message.reply_to_message.voice
            )
            if message.reply_to_message
            else None
        )

        # =====================================================
        # REPLY VIDEO
        # =====================================================

        video_telegram = (
            (
                message.reply_to_message.video
                or message.reply_to_message.document
            )
            if message.reply_to_message
            else None
        )

        # =====================================================
        # YOUTUBE URL
        # =====================================================

        try:
            url = await YouTube.url(message)
        except Exception:
            url = None

        # =====================================================
        # NO QUERY / NO REPLY
        # =====================================================

        if (
            audio_telegram is None
            and video_telegram is None
            and url is None
        ):

            if len(message.command) < 2:

                if "stream" in message.command:
                    return await message.reply_text(
                        _["str_1"]
                    )

                buttons = botplaylist_markup(_)

                return await message.reply_photo(
                    photo=PLAYLIST_IMG_URL,
                    caption=_["play_18"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

        # =====================================================
        # CHANNEL PLAY
        # =====================================================

        try:
            command_name = message.command[0].lower()
        except Exception:
            command_name = "play"

        if command_name.startswith("c"):

            try:
                chat_id = await get_cmode(
                    message.chat.id
                )
            except Exception:
                chat_id = None

            if chat_id is None:
                return await message.reply_text(
                    _["setting_7"]
                )

            try:
                chat = await app.get_chat(chat_id)
            except Exception:
                return await message.reply_text(
                    _["cplay_4"]
                )

            channel = chat.title

        else:
            chat_id = message.chat.id
            channel = None

        # =====================================================
        # PLAY MODE
        # =====================================================

        try:
            playmode = await get_playmode(
                message.chat.id
            )
        except Exception:
            playmode = "Direct"

        # =====================================================
        # PLAY TYPE
        # =====================================================

        try:
            playty = await get_playtype(
                message.chat.id
            )
        except Exception:
            playty = "Everyone"

        # =====================================================
        # ADMIN / EVERYONE CHECK
        # =====================================================

        if playty != "Everyone":

            if message.from_user.id not in SUDOERS:

                admins = adminlist.get(
                    message.chat.id
                )

                if not admins:
                    return await message.reply_text(
                        _["admin_13"]
                    )

                if message.from_user.id not in admins:
                    return await message.reply_text(
                        _["play_4"]
                    )

        # =====================================================
        # VIDEO MODE
        # =====================================================

        # FIX:
        # Old code used message.command[0][1].
        # This can cause IndexError for /play.
        # Now it is completely safe.

        video = None

        try:

            if command_name.startswith("v"):
                video = True

            elif "-v" in (message.text or ""):
                video = True

            elif len(command_name) > 1:
                if command_name[1] == "v":
                    video = True

        except Exception:
            video = None

        # =====================================================
        # FORCE PLAY
        # =====================================================

        if command_name.endswith("e"):

            try:
                active = await is_active_chat(
                    chat_id
                )
            except Exception:
                active = False

            if not active:
                return await message.reply_text(
                    _["play_16"]
                )

            fplay = True

        else:
            fplay = None

        # =====================================================
        # ASSISTANT CHECK
        # =====================================================

        try:
            active_chat = await is_active_chat(
                chat_id
            )
        except Exception:
            active_chat = False

        if not active_chat:

            # -------------------------------------------------
            # GET ASSISTANT
            # -------------------------------------------------

            try:
                userbot = await get_assistant(
                    chat_id
                )
            except Exception as e:
                return await message.reply_text(
                    _["call_3"].format(
                        app.mention,
                        type(e).__name__,
                    )
                )

            if not userbot:
                return await message.reply_text(
                    _["call_1"]
                )

            # -------------------------------------------------
            # CHECK ASSISTANT MEMBER
            # -------------------------------------------------

            try:

                try:
                    get = await app.get_chat_member(
                        chat_id,
                        userbot.id,
                    )

                except ChatAdminRequired:
                    return await message.reply_text(
                        _["call_1"]
                    )

                if (
                    get.status
                    == ChatMemberStatus.BANNED
                    or get.status
                    == ChatMemberStatus.RESTRICTED
                ):

                    return await message.reply_text(
                        _["call_2"].format(
                            app.mention,
                            userbot.id,
                            userbot.name,
                            userbot.username,
                        )
                    )

            except UserNotParticipant:

                # =================================================
                # INVITE LINK
                # =================================================

                if chat_id in links:

                    invitelink = links[chat_id]

                else:

                    # -------------------------------------------------
                    # PUBLIC GROUP
                    # -------------------------------------------------

                    if message.chat.username:

                        invitelink = (
                            message.chat.username
                        )

                        try:
                            await userbot.resolve_peer(
                                invitelink
                            )
                        except Exception:
                            pass

                    # -------------------------------------------------
                    # PRIVATE GROUP
                    # -------------------------------------------------

                    else:

                        try:
                            invitelink = (
                                await app.export_chat_invite_link(
                                    chat_id
                                )
                            )

                        except ChatAdminRequired:
                            return await message.reply_text(
                                _["call_1"]
                            )

                        except Exception as e:
                            return await message.reply_text(
                                _["call_3"].format(
                                    app.mention,
                                    type(e).__name__,
                                )
                            )

                # =================================================
                # FIX INVITE LINK
                # =================================================

                if invitelink.startswith(
                    "https://t.me/+"
                ):

                    invitelink = invitelink.replace(
                        "https://t.me/+",
                        "https://t.me/joinchat/",
                    )

                # =================================================
                # JOIN MESSAGE
                # =================================================

                myu = await message.reply_text(
                    _["call_4"].format(
                        app.mention
                    )
                )

                # =================================================
                # JOIN ASSISTANT
                # =================================================

                try:

                    await asyncio.sleep(1)

                    await userbot.join_chat(
                        invitelink
                    )

                except InviteRequestSent:

                    try:

                        await app.approve_chat_join_request(
                            chat_id,
                            userbot.id,
                        )

                    except Exception as e:

                        return await message.reply_text(
                            _["call_3"].format(
                                app.mention,
                                type(e).__name__,
                            )
                        )

                    await asyncio.sleep(3)

                    try:
                        await myu.edit(
                            _["call_5"].format(
                                app.mention
                            )
                        )
                    except Exception:
                        pass

                except UserAlreadyParticipant:
                    pass

                except Exception as e:

                    return await message.reply_text(
                        _["call_3"].format(
                            app.mention,
                            type(e).__name__,
                        )
                    )

                # =================================================
                # SAVE LINK
                # =================================================

                links[chat_id] = invitelink

                # =================================================
                # RESOLVE CHAT
                # =================================================

                try:
                    await userbot.resolve_peer(
                        chat_id
                    )
                except Exception:
                    pass

            except Exception as e:

                return await message.reply_text(
                    _["call_3"].format(
                        app.mention,
                        type(e).__name__,
                    )
                )

        # =====================================================
        # CALL PLAY COMMAND
        # =====================================================

        try:

            return await command(
                client,
                message,
                _,
                chat_id,
                video,
                channel,
                playmode,
                url,
                fplay,
            )

        except Exception as e:

            # IMPORTANT:
            # This prevents wrapper from silently hiding
            # the actual exception.

            error_type = type(e).__name__

            try:
                return await message.reply_text(
                    f"❌ **Play Error:** `{error_type}`\n\n"
                    f"`{str(e)[:1000]}`"
                )
            except Exception:
                return

    return wrapper
