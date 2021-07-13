# pylint: disable=missing-module-docstring

import os

from Archx import Archx


async def _worker() -> None:
    chat_id = int(os.environ.get("CHAT_ID") or 0)
    type_ = 'unofficial' if os.path.exists("../Archx/plugins/unofficial") else 'main'
    await Archx.send_message(chat_id, f'`{type_} build completed !`')

if __name__ == "__main__":
    Archx.begin(_worker())
    print('Archx test has been finished!')
