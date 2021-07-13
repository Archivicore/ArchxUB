# Copyright (C) 2020-2021 

from pyrogram.errors import MessageDeleteForbidden

from Archx import Archx, Message


@Archx.on_cmd("del", about={'header': "delete replied message"})
async def del_msg(message: Message):
    if Archx.dual_mode:
        u_msg_ids = []
        b_msg_ids = []
        o_msg_ids = []
        for m in filter(lambda _: _, (message, message.reply_to_message)):
            if m.from_user and m.from_user.id == Archx.id:
                u_msg_ids.append(m.message_id)
            elif m.from_user and m.from_user.id == Archx.bot.id:
                b_msg_ids.append(m.message_id)
            else:
                o_msg_ids.append(m.message_id)
        if u_msg_ids:
            await Archx.delete_messages(message.chat.id, u_msg_ids)
        if b_msg_ids:
            await Archx.bot.delete_messages(message.chat.id, b_msg_ids)
        for o_msg_id in o_msg_ids:
            try:
                await Archx.delete_messages(message.chat.id, o_msg_id)
            except MessageDeleteForbidden:
                try:
                    await Archx.bot.delete_messages(message.chat.id, o_msg_id)
                except MessageDeleteForbidden:
                    pass
    else:
        await message.delete()
        replied = message.reply_to_message
        if replied:
            await replied.delete()
