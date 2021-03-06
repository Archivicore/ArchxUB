# Copyright (C) 2020-2021

from Archx import Archx, Message


@Archx.on_cmd("cancel", about={'header': "Reply this to message you want to cancel"})
async def cancel_(message: Message):
    replied = message.reply_to_message
    if replied:
        replied.cancel_the_process()
        await message.edit(
            "`added your request to the cancel list`", del_in=5)
    else:
        await message.err("reply to the message you want to cancel")
