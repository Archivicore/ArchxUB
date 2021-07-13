# Copyright (C) 2020-2021 

from Archx import Archx, Message, Config, versions, get_version


@Archx.on_cmd("repo", about={'header': "get repo link and details"})
async def see_repo(message: Message):
    """see repo"""
    output = f"""
**Hey**, __I am using__ 🔥 **Archx** 🔥

    __Durable as a Serge__

• **Archx version** : `{get_version()}`
• **license** : {versions.__license__}
• **copyright** : {versions.__copyright__}
• **repo** : [Archx]({Config.UPSTREAM_REPO})
"""
    await message.edit(output)
