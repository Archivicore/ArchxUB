from asyncio import get_event_loop, sleep
from time import time

from pyrogram import filters
from pyrogram.types import Message

from Archx import Archx, Message, Config, logging, get_collection, pool
from Archx.core.decorators.errors import capture_err
from Archx.utils.dbfunctions import (add_rss_feed, get_rss_feeds,
                                   is_rss_active, remove_rss_feed,
                                   update_rss_feed)
from Archx.utils.functions import (get_http_status_code,
                                 get_urls_from_text)
from Archx.utils.rss import Feed


async def rss_worker():
    print("[INFO]: RSS WORKER STARTED")
    while True:
        t1 = time()
        feeds = await get_rss_feeds()
        if not feeds:
            await sleep(Config.RSS_DELAY)
            continue
        for _feed in feeds:
            try:
                chat = _feed["chat_id"]
                url = _feed["url"]
                last_title = _feed.get("last_title")
                feed = Feed(url)
                if feed.title == last_title:
                    continue
                await app.send_message(
                    chat, feed.parsed(), disable_web_page_preview=True
                )
                await update_rss_feed(chat, feed.title)
            except Exception as e:
                print(str(e), f"RSS {chat}")
                pass
        t2 = time()
        if (t2 - t1) >= Config.RSS_DELAY:
            continue
        await sleep(Config.RSS_DELAY - (t2 - t1))


loop = get_event_loop()
loop.create_task(rss_worker())

@Archx.on_cmd("addrss", about={
    'header': "Add new RSSFeed Url to get regular Updates from it.",
    'usage': "{tr}addrss url"})
async def add_feed_func(msg: Message):
    if len(msg.command) != 2:
        return await msg.reply("Read 'RSS' section in help menu.")
    url = msg.text.split(None, 1)[1].strip()

    if not url:
        return await msg.reply("[ERROR]: Invalid Argument")

    urls = get_urls_from_text(url)
    if not urls:
        return await msg.reply("[ERROR]: Invalid URL")

    url = urls[0]
    status = await get_http_status_code(url)
    if status != 200:
        return await msg.reply("[ERROR]: Invalid Url")

    ns = "[ERROR]: This feed isn't supported."
    try:
        feed = Feed(url)
    except Exception:
        return await msg.reply(ns)
    if not feed:
        return await msg.reply(ns)

    chat_id = msg.chat.id
    if await is_rss_active(chat_id):
        return await msg.reply(
            "[ERROR]: You already have an RSS feed enabled."
        )
    try:
        await msg.reply(feed.parsed(), disable_web_page_preview=True)
    except Exception:
        return await msg.reply(ns)
    await add_rss_feed(chat_id, feed.url, feed.title)

@userge.on_cmd("delrss", about={
    'header': "Delete a existing Feed Url from Database.",
    'flags': {'-all': 'Delete All Urls.'},
    'usage': "{tr}delrss title"})
async def rm_feed_func(msg: Message):
    if await is_rss_active(msg.chat.id):
        await remove_rss_feed(msg.chat.id)
        await msg.reply("Removed RSS Feed")
    else:
        await msg.reply("There are no active RSS Feeds in this chat.")
