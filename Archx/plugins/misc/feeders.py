from asyncio import get_event_loop, sleep
from time import time

from pyrogram import filters
from pyrogram.types import Message

from Archx import Archx, Message, Config, logging, get_collection, pool
from Archx.utils.functions import (get_http_status_code,
                                 get_urls_from_text)
from Archx.utils.rss import Feed

RSS_COLLECTION = get_collection("RSS_FEEDS")

""" RSS DB """
async def add_rss_feed(chat_id: int, url: str, last_title: str):
    return await RSS_COLLECTION.update_one(
        {"chat_id": chat_id},
        {"$set": {"url": url, "last_title": last_title}},
        upsert=True,
    )

async def remove_rss_feed(chat_id: int):
    return await RSS_COLLECTION.delete_one({"chat_id": chat_id})

async def update_rss_feed(chat_id: int, last_title: str):
    return await RSS_COLLECTION.update_one(
        {"chat_id": chat_id},
        {"$set": {"last_title": last_title}},
        upsert=True,
    )

async def is_rss_active(chat_id: int) -> bool:
    return await RSS_COLLECTION.find_one({"chat_id": chat_id})

async def get_rss_feeds() -> list:
    feeds = RSS_COLLECTION.find({"chat_id": {"$exists": 1}})
    feeds = await feeds.to_list(length=10000000)
    if not feeds:
        return
    data = []
    for feed in feeds:
        data.append(
            dict(
                chat_id=feed["chat_id"],
                url=feed["url"],
                last_title=feed["last_title"],
            )
        )
    return data

async def get_rss_feeds_count() -> int:
    feeds = RSS_COLLECTION.find({"chat_id": {"$exists": 1}})
    feeds = await feeds.to_list(length=10000000)
    return len(feeds)


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
