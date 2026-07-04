import asyncio

from telethon.sync import TelegramClient, events

from config import settings
from deepseek.categorize import categorize_posts
from parse import channel_post_handler, create_messages_json, get_channel
from tg.send_report import send_interactive_report

__all__ = ()

client = TelegramClient(
    settings.PHONE,
    settings.API_ID,
    settings.API_HASH,
    lang_code='ru',
    system_lang_code='ru-RU',
)


def run_sync_ai_tasks():
    categorize_posts()


async def main():
    await client.connect()
    channel = await get_channel(client)
    await create_messages_json(client=client, target_channel=channel)
    await asyncio.to_thread(run_sync_ai_tasks)
    await send_interactive_report(client=client)
    client.add_event_handler(
        channel_post_handler,
        events.NewMessage(chats=channel),
    )

    await client.run_until_disconnected()


if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
