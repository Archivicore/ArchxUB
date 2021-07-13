# pylint: disable=invalid-name, missing-module-docstring

import os
import asyncio

from pyrogram import Client
from pyrogram.errors import UserIsBot
from dotenv import load_dotenv

if os.path.isfile("config.env"):
    load_dotenv("config.env")


async def genStrSession() -> None:  # pylint: disable=missing-function-docstring
    async with Client(
        "Archx",
        api_id=int(os.environ.get("API_ID") or input("Enter Telegram APP ID: ")),
        api_hash=os.environ.get("API_HASH") or input("Enter Telegram API HASH: "),
    ) as Archx:
        print("\nprocessing...")
        doneStr = "sent to saved messages!"
        try:
            await Archx.send_message(
                "me", f"#Archx #HU_STRING_SESSION\n\n```{await Archx.export_session_string()}```"
            )
        except UserIsBot:
            doneStr = "successfully printed!"
            print(await Archx.export_session_string())
        print(f"Done !, session string has been {doneStr}")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(genStrSession())
