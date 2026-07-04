__all__ = ('create_messages_json',)
import json
import os

from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument

from parse.utils import get_reactions, transcribe_audio_locally


async def create_messages_json(client: TelegramClient, target_channel):
    filename = 'messages.json'
    data = {}

    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f'Файл {filename} поврежден, создаем новую базу.')
            data = {}

    async for message in client.iter_messages(target_channel):
        if str(message.id) in data:
            continue

        if isinstance(target_channel, str):
            post_url = f'https://t.me/{target_channel}/{message.id}'
        else:
            clean_id = str(target_channel).replace('-100', '')
            post_url = f'https://t.me/c/{clean_id}/{message.id}'

        text_content = ''

        if message.text:
            text_content = message.text

        elif message.media and isinstance(message.media, MessageMediaDocument):
            mime = message.media.document.mime_type or ''
            if 'audio' in mime or 'ogg' in mime:
                ext = '.ogg' if 'ogg' in mime else '.mp3'
                audio_path = f'downloads/audio/{message.id}{ext}'

                print(f'Скачиваем аудио для поста {message.id}...')
                await client.download_media(message=message, file=audio_path)

                print(
                    f'Локально расшифровываем аудио для поста {message.id}...',
                )
                text_content = transcribe_audio_locally(audio_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)

        if text_content:
            data[str(message.id)] = {
                'text': text_content,
                'url': post_url,
                'reactions': get_reactions(message),
                'date': message.date.isoformat() if message.date else None,
            }

    if data:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    return data
