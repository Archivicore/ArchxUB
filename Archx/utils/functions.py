import codecs
import pickle
from asyncio import gather, get_running_loop
from datetime import datetime, timedelta
from io import BytesIO
from math import atan2, cos, radians, sin, sqrt
from random import randint
from re import findall
from time import time

import aiofiles
import aiohttp
import speedtest
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pyrogram.types import Message
from wget import download

async def get_http_status_code(url: str) -> int:
    async with aiohttp.ClientSession() as resp:
        return resp.status

def get_urls_from_text(text: str) -> bool:
    regex = r"""(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]
                [.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(
                \([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\
                ()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))""".strip()
    return [x[0] for x in findall(regex, text)]
