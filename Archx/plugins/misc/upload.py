""" upload , rename and convert telegram files """

import os
import io
import re
import time
from datetime import datetime
from pathlib import Path

import stagger
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.errors.exceptions import FloodWait

from Archx import Archx, Config, Message
from Archx.utils import sort_file_name_key, progress, take_screen_shot, humanbytes
from Archx.utils.exceptions import ProcessCanceled
from Archx.plugins.misc.download import tg_download, url_download

LOGGER = Archx.getLogger(__name__)
CHANNEL = Archx.getCLogger(__name__)

LOGO_PATH = 'resources/Archx.png'


@Archx.on_cmd("rename", about={
    'header': "Rename telegram files",
    'flags': {
        '-d': "upload as document",
        '-wt': "without thumb"},
    'usage': "{tr}rename [flags] [new_name_with_extension] : reply to telegram media",
    'examples': "{tr}rename -d test.mp4"}, del_pre=True, check_downpath=True)
async def rename_(message: Message):
    """ ganti nama file telegram """
    if not message.filtered_input_str:
        await message.err("nama baru tidak ditemukan!")
        return
    await message.edit("`Mencoba untuk Mengganti Nama ...`")
    if message.reply_to_message and message.reply_to_message.media:
        await _handle_message(message)
    else:
        await message.err("balas ke media untuk mengganti namanya")


@Archx.on_cmd("convert", about={
    'header': "Convert telegram files",
    'usage': "reply {tr}convert to any media"}, del_pre=True, check_downpath=True)
async def convert_(message: Message):
    """ konversi file telegram """
    await message.edit("`Mencoba untuk Mengkonversi ...`")
    if message.reply_to_message and message.reply_to_message.media:
        message.text = '' if message.reply_to_message.document else ". -d"
        await _handle_message(message)
    else:
        await message.err("balas ke media untuk mengubahnya")


@Archx.on_cmd("upload", about={
    'header': "Upload files to telegram",
    'flags': {
        '-d': "upload as document",
        '-wt': "without thumb"},
    'usage': "{tr}upload [flags] [file or folder path | link]",
    'examples': [
        "{tr}upload -d https://speed.hetzner.de/100MB.bin | test.bin",
        "{tr}upload downloads/test.mp4"]}, del_pre=True, check_downpath=True)
async def upload_to_tg(message: Message):
    """ unggah ke telegram """
    path_ = message.filtered_input_str
    if not path_:
        await message.err("Masukan tidak ditemukan!")
        return
    is_url = re.search(r"(?:https?|ftp)://[^|\s]+\.[^|\s]+", path_)
    del_path = False
    if is_url:
        del_path = True
        try:
            path_, _ = await url_download(message, path_)
        except ProcessCanceled:
            await message.edit("`Proses Dibatalkan!`", del_in=5)
            return
        except Exception as e_e:  # pylint: disable=broad-except
            await message.err(str(e_e))
            return
    if "|" in path_:
        path_, file_name = path_.split("|")
        path_ = path_.strip()
        if os.path.isfile(path_):
            new_path = os.path.join(Config.DOWN_PATH, file_name.strip())
            os.rename(path_, new_path)
            path_ = new_path
    try:
        string = Path(path_)
    except IndexError:
        await message.err("sintaks yang salah")
    else:
        await message.delete()
        await upload_path(message, string, del_path)


async def _handle_message(message: Message) -> None:
    try:
        dl_loc, _ = await tg_download(message, message.reply_to_message)
    except ProcessCanceled:
        await message.edit("`Proses Dibatalkan!`", del_in=5)
    except Exception as e_e:  # pylint: disable=broad-except
        await message.err(str(e_e))
    else:
        await message.delete()
        await upload(message, Path(dl_loc), True)


async def upload_path(message: Message, path: Path, del_path: bool):
    file_paths = []
    if path.exists():
        def explorer(_path: Path) -> None:
            if _path.is_file() and _path.stat().st_size:
                file_paths.append(_path)
            elif _path.is_dir():
                for i in sorted(_path.iterdir(), key=lambda a: sort_file_name_key(a.name)):
                    explorer(i)
        explorer(path)
    else:
        path = path.expanduser()
        str_path = os.path.join(*(path.parts[1:] if path.is_absolute() else path.parts))
        for p in Path(path.root).glob(str_path):
            file_paths.append(p)
    current = 0
    for p_t in file_paths:
        current += 1
        try:
            await upload(message, p_t, del_path, f"{current}/{len(file_paths)}")
        except FloodWait as f_e:
            time.sleep(f_e.x)  # asyncio sleep ?
        if message.process_is_canceled:
            break


async def upload(message: Message, path: Path, del_path: bool = False,
                 extra: str = '', with_thumb: bool = True):
    if 'wt' in message.flags:
        with_thumb = False
    if path.name.lower().endswith(
            (".mkv", ".mp4", ".webm", ".m4v")) and ('d' not in message.flags):
        await vid_upload(message, path, del_path, extra, with_thumb)
    elif path.name.lower().endswith(
            (".mp3", ".flac", ".wav", ".m4a")) and ('d' not in message.flags):
        await audio_upload(message, path, del_path, extra, with_thumb)
    elif path.name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp")) and ('d' not in message.flags):
        await photo_upload(message, path, del_path, extra)
    else:
        await doc_upload(message, path, del_path, extra, with_thumb)


async def doc_upload(message: Message, path, del_path: bool = False,
                     extra: str = '', with_thumb: bool = True):
    str_path = str(path)
    sent: Message = await message.client.send_message(
        message.chat.id, f"`Mengunggah {str_path} sebagai dokumen ... {extra}`")
    start_t = datetime.now()
    thumb = None
    if with_thumb:
        thumb = await get_thumb(str_path)
    await message.client.send_chat_action(message.chat.id, "upload_document")
    try:
        msg = await message.client.send_document(
            chat_id=message.chat.id,
            document=str_path,
            thumb=thumb,
            caption=path.name,
            parse_mode="html",
            disable_notification=True,
            progress=progress,
            progress_args=(message, f"mengunggah {extra}", str_path)
        )
    except ValueError as e_e:
        await sent.edit(f"Melewatkan `{str_path}` disebabkan oleh {e_e}")
    except Exception as u_e:
        await sent.edit(str(u_e))
        raise u_e
    else:
        await sent.delete()
        await finalize(message, msg, start_t)
        if os.path.exists(str_path) and del_path:
            os.remove(str_path)


async def vid_upload(message: Message, path, del_path: bool = False,
                     extra: str = '', with_thumb: bool = True):
    str_path = str(path)
    thumb = None
    if with_thumb:
        thumb = await get_thumb(str_path)
    duration = 0
    metadata = extractMetadata(createParser(str_path))
    if metadata and metadata.has("duration"):
        duration = metadata.get("duration").seconds
    sent: Message = await message.client.send_message(
        message.chat.id, f"`Mengunggah {str_path} sebagai video ... {extra}`")
    start_t = datetime.now()
    await message.client.send_chat_action(message.chat.id, "upload_video")
    width = 0
    height = 0
    if thumb:
        t_m = extractMetadata(createParser(thumb))
        if t_m and t_m.has("width"):
            width = t_m.get("width")
        if t_m and t_m.has("height"):
            height = t_m.get("height")
    try:
        msg = await message.client.send_video(
            chat_id=message.chat.id,
            video=str_path,
            duration=duration,
            thumb=thumb,
            width=width,
            height=height,
            caption=path.name,
            parse_mode="html",
            disable_notification=True,
            progress=progress,
            progress_args=(message, f"mengunggah {extra}", str_path)
        )
    except ValueError as e_e:
        await sent.edit(f"Melewatkan `{str_path}` disebabkan oleh {e_e}")
    except Exception as u_e:
        await sent.edit(str(u_e))
        raise u_e
    else:
        await sent.delete()
        await remove_thumb(thumb)
        await finalize(message, msg, start_t)
        if os.path.exists(str_path) and del_path:
            os.remove(str_path)


async def audio_upload(message: Message, path, del_path: bool = False,
                       extra: str = '', with_thumb: bool = True):
    title = None
    artist = None
    thumb = None
    duration = 0
    str_path = str(path)
    file_size = humanbytes(os.stat(str_path).st_size)
    if with_thumb:
        try:
            album_art = stagger.read_tag(str_path)
            if album_art.picture and not os.path.lexists(Config.THUMB_PATH):
                bytes_pic_data = album_art[stagger.id3.APIC][0].data
                bytes_io = io.BytesIO(bytes_pic_data)
                image_file = Image.open(bytes_io)
                image_file.save("album_cover.jpg", "JPEG")
                thumb = "album_cover.jpg"
        except stagger.errors.NoTagError:
            pass
        if not thumb:
            thumb = await get_thumb(str_path)
    metadata = extractMetadata(createParser(str_path))
    if metadata and metadata.has("title"):
        title = metadata.get("title")
    if metadata and metadata.has("artist"):
        artist = metadata.get("artist")
    if metadata and metadata.has("duration"):
        duration = metadata.get("duration").seconds
    sent: Message = await message.client.send_message(
        message.chat.id, f"`Mengunggah {str_path} sebagai audio ... {extra}`")
    start_t = datetime.now()
    await message.client.send_chat_action(message.chat.id, "upload_audio")
    try:
        msg = await message.client.send_audio(
            chat_id=message.chat.id,
            audio=str_path,
            thumb=thumb,
            caption=f"{path.name} [ {file_size} ]",
            title=title,
            performer=artist,
            duration=duration,
            parse_mode="html",
            disable_notification=True,
            progress=progress,
            progress_args=(message, f"mengunggah {extra}", str_path)
        )
    except ValueError as e_e:
        await sent.edit(f"Melewatkan `{str_path}` disebabkan oleh {e_e}")
    except Exception as u_e:
        await sent.edit(str(u_e))
        raise u_e
    else:
        await sent.delete()
        await finalize(message, msg, start_t)
        if os.path.exists(str_path) and del_path:
            os.remove(str_path)
    finally:
        if os.path.lexists("album_cover.jpg"):
            os.remove("album_cover.jpg")


async def photo_upload(message: Message, path, del_path: bool = False, extra: str = ''):
    str_path = str(path)
    sent: Message = await message.client.send_message(
        message.chat.id, f"`Mengunggah {path.name} sebagai foto ... {extra}`")
    start_t = datetime.now()
    await message.client.send_chat_action(message.chat.id, "upload_photo")
    try:
        msg = await message.client.send_photo(
            chat_id=message.chat.id,
            photo=str_path,
            caption=path.name,
            parse_mode="html",
            disable_notification=True,
            progress=progress,
            progress_args=(message, f"mengunggah {extra}", str_path)
        )
    except ValueError as e_e:
        await sent.edit(f"Melewatkan `{str_path}` disebabkan oleh {e_e}")
    except Exception as u_e:
        await sent.edit(str(u_e))
        raise u_e
    else:
        await sent.delete()
        await finalize(message, msg, start_t)
        if os.path.exists(str_path) and del_path:
            os.remove(str_path)


async def get_thumb(path: str = ''):
    if os.path.exists(Config.THUMB_PATH):
        return Config.THUMB_PATH
    if path:
        types = (".jpg", ".webp", ".png")
        if path.endswith(types):
            return None
        file_name = os.path.splitext(path)[0]
        for type_ in types:
            thumb_path = file_name + type_
            if os.path.exists(thumb_path):
                if type_ != ".jpg":
                    new_thumb_path = f"{file_name}.jpg"
                    Image.open(thumb_path).convert('RGB').save(new_thumb_path, "JPEG")
                    os.remove(thumb_path)
                    thumb_path = new_thumb_path
                return thumb_path
        metadata = extractMetadata(createParser(path))
        if metadata and metadata.has("duration"):
            return await take_screen_shot(
                path, metadata.get("duration").seconds)
    if os.path.exists(LOGO_PATH):
        return LOGO_PATH
    return None


async def remove_thumb(thumb: str) -> None:
    if (thumb and os.path.exists(thumb)
            and thumb != LOGO_PATH and thumb != Config.THUMB_PATH):
        os.remove(thumb)


async def finalize(message: Message, msg: Message, start_t):
    await CHANNEL.fwd_msg(msg)
    await message.client.send_chat_action(message.chat.id, "cancel")
    if message.process_is_canceled:
        await message.edit("`Proses Dibatalkan!`", del_in=5)
    else:
        end_t = datetime.now()
        m_s = (end_t - start_t).seconds
        await message.edit(f"Diunggah dalam {m_s} detik", del_in=10)
