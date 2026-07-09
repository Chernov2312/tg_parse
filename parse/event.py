__all__ = ('channel_post_handler',)
import asyncio
import json
import os

from deepseek.categorize import categorize_posts
from tg.send_report import send_interactive_report


def save_to_json(target_channel, message):
    data = {}
    filename = 'messages.json'
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass

    if isinstance(target_channel, str):
        post_url = f'https://t.me/{target_channel}/{message.id}'
    else:
        clean_id = str(target_channel).replace('-100', '')
        post_url = f'https://t.mec/{clean_id}/{message.id}'

    data[str(message.id)] = {
        'text': message.text,
        'url': post_url,
        'date': message.date.isoformat() if message.date else None,
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def channel_post_handler(event):
    message = event.message
    if message.text:
        chat = await event.get_chat()
        channel_identifier = (
            chat.username if getattr(chat, 'username', None) else event.chat_id
        )
        await asyncio.to_thread(save_to_json, channel_identifier, message)
        await asyncio.to_thread(categorize_posts)
        await send_interactive_report(client=event.client)
