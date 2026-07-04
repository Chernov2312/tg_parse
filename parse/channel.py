__all__ = ('get_channel',)
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty


async def get_channel(client: TelegramClient):
    chats = []
    last_date = None
    size_chats = 200
    channels = []

    result = await client(
        GetDialogsRequest(
            offset_date=last_date,
            offset_id=0,
            offset_peer=InputPeerEmpty(),
            limit=size_chats,
            hash=0,
        ),
    )
    chats.extend(result.chats)
    for chat in chats:
        try:
            if chat.broadcast:
                channels.append(chat)
        except AttributeError:
            continue
    print('Выберите номер группы из перечня:')
    i = 0
    for g in channels:
        print(str(i) + '- ' + g.title)
        i += 1

    g_index = input('Введите нужную цифру: ')

    target_channel = channels[int(g_index)]
    if getattr(target_channel, 'username', None):
        return target_channel.username
    return target_channel.id
