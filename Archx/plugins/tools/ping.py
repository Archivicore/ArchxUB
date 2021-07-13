# Copyright (C) 2020-2021

from datetime import datetime

from Archx import Archx, Message


@Archx.on_cmd("ping", about={
    'header': "check how long it takes to ping your userbot",
    'flags': {'-a': "average ping"}}, group=-1)
async def pingme(message: Message):
    start = datetime.now()
    await message.edit('`Pong!`')
    end = datetime.now()
    m_s = (end - start).microseconds / 1000
    await message.edit(f"**Pong!**\n`{m_s} ms`")
