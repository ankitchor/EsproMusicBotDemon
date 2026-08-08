import asyncio
import os
import re
from typing import Union, Optional
import httpx

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from EsproMusic.utils.formatters import time_to_seconds

# ================= CONFIG =================

API_BASE_URL = "https://shrutibots.site"
SHRUTI_API_KEY = "ShrutiBotsL0zQEKsazSrYS2LWsIQW"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ================= UTILS =================

def time_to_seconds(time_str):
    if not time_str or not isinstance(time_str, str):
        return 0
    try:
        parts = time_str.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(parts[0])
    except:
        return 0


async def api_prepare(video_id: str, media_type: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{API_BASE_URL}/download",
                params={"url": video_id, "type": media_type},
            )
            if r.status_code != 200:
                return None
            return r.json().get("download_token")
    except:
        return None


async def api_stream(video_id: str, token: str, media_type: str, out_file: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "GET",
                f"{API_BASE_URL}/stream/{video_id}",
                params={"type": media_type},
                headers={"X-Download-Token": token},
            ) as r:
                if r.status_code != 200:
                    return False

                with open(out_file, "wb") as f:
                    async for chunk in r.aiter_bytes(16384):
                        f.write(chunk)
        return True
    except:
        return False


# ================= YOUTUBE API =================

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    # ---------------- BASIC ----------------

    async def exists(self, link: str, videoid=False):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message: Message) -> Union[str, None]:
        messages = [message]
        if message.reply_to_message:
            messages.append(message.reply_to_message)

        for msg in messages:
            if msg.entities:
                for e in msg.entities:
                    if e.type == MessageEntityType.URL:
                        text = msg.text or msg.caption
                        return text[e.offset : e.offset + e.length]
            if msg.caption_entities:
                for e in msg.caption_entities:
                    if e.type == MessageEntityType.TEXT_LINK:
                        return e.url
        return None

    # ---------------- SEARCH ----------------

    async def _search_first(self, query: str):
        def _search():
            s = VideosSearch(query, limit=1)
            r = s.result()
            if not r or not r.get("result"):
                return None
            v = r["result"][0]
            return {
                "id": v["id"],
                "title": v["title"],
                "duration": v.get("duration", "0:00"),
                "url": v["link"],
            }

        return await asyncio.to_thread(_search)

    # ---------------- DETAILS ----------------

    async def details(self, link: str, videoid=False):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        r = await self._search_first(link)
        if not r:
            return None, None, 0, None, None

        vid = r["id"]
        dur = r["duration"]
        return (
            r["title"],
            dur,
            time_to_seconds(dur),
            f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            vid,
        )

    async def title(self, link: str, videoid=False):
        r = await self._search_first(link)
        return r["title"] if r else None

    async def duration(self, link: str, videoid=False):
        r = await self._search_first(link)
        return r["duration"] if r else None

    async def thumbnail(self, link: str, videoid=False):
        r = await self._search_first(link)
        return f"https://i.ytimg.com/vi/{r['id']}/hqdefault.jpg" if r else None

    # ---------------- TRACK ----------------

    async def track(self, link: str, videoid=False):
        r = await self._search_first(link)
        if not r:
            return None, None

        vid = r["id"]
        return (
            {
                "title": r["title"],
                "link": r["url"],
                "vidid": vid,
                "duration_min": r["duration"],
                "thumb": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            },
            vid,
        )

    # ---------------- DOWNLOAD ----------------

    async def download(
        self,
        link: str,
        mystic,
        video=False,
        videoid=False,
        **kwargs,
    ):
        try:
            if videoid:
                link = self.base + link

            link = link.split("&")[0]
            vid = (
                link.split("v=")[-1].split("&")[0]
                if "v=" in link
                else link.split("/")[-1]
            )

            media_type = "video" if video else "audio"
            ext = "mp4" if video else "mp3"
            out_file = os.path.join(DOWNLOAD_DIR, f"{vid}.{ext}")

            # STEP 1: PREPARE
            token = await api_prepare(vid, media_type)
            if not token:
                return None, None

            # STEP 2: STREAM
            ok = await api_stream(vid, token, media_type, out_file)
            if not ok or not os.path.exists(out_file):
                return None, None

            return out_file, False

        except Exception as e:
            print(f"[DOWNLOAD ERROR] {e}")
            return None, NoneTrue
