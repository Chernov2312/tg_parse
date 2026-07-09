__all__ = ('create_messages_json',)
import asyncio
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

    os.makedirs('downloads/audio', exist_ok=True)

    unsaved_count = 0
    SAVE_EVERY_N_MESSAGES = 50

    async for message in client.iter_messages(target_channel):
        msg_id_str = str(message.id)

        if msg_id_str in data:
            continue

        if isinstance(target_channel, str):
            clean_channel = target_channel.lstrip('@')
            post_url = f'https://t.me/{clean_channel}/{message.id}'
        else:
            clean_id = str(target_channel).replace('-100', '')
            post_url = f'https://t.mec/{clean_id}/{message.id}'

        text_content = ''
        audio_text = ''
        video_text = ''

        if message.text:
            text_content = message.text

        if message.media and isinstance(message.media, MessageMediaDocument):
            mime = message.media.document.mime_type or ''
            if 'audio' in mime or 'ogg' in mime:
                ext = '.ogg' if 'ogg' in mime else '.mp3'
                audio_path = f'downloads/audio/{message.id}{ext}'

                print(f'Скачиваем аудио для поста {message.id}...')
                await client.download_media(message=message, file=audio_path)

                print(
                    f'Локально расшифровываем аудио для поста {message.id}...',
                )
                try:
                    loop = asyncio.get_running_loop()
                    audio_text = await loop.run_in_executor(
                        None,
                        transcribe_audio_locally,
                        audio_path,
                    )
                except Exception as e:
                    print(f'Ошибка расшифровки поста {message.id}: {e}')
                finally:
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
            elif 'video' in mime:
                if 'mp4' in mime:
                    ext = '.mp4'
                elif 'webm' in mime:
                    ext = '.webm'
                elif 'quicktime' in mime:
                    ext = '.mov'
                else:
                    ext = '.mp4'

                video_path = f'downloads/video/{message.id}{ext}'

                print(f'Скачиваем видео для поста {message.id}...')
                await client.download_media(message=message, file=video_path)

                print(
                    f'Локально расшифровываем видео (извлекаем текст)'
                    f' для поста {message.id}...',
                )
                try:
                    loop = asyncio.get_running_loop()
                    video_text = await loop.run_in_executor(
                        None,
                        transcribe_audio_locally,
                        video_path,
                    )
                    print(f'Текст из видео {message.id} успешно получен!')

                except Exception as e:
                    print(f'Ошибка расшифровки видео-поста {message.id}: {e}')
                finally:
                    if os.path.exists(video_path):
                        os.remove(video_path)

        if audio_text:
            if text_content:
                text_content = (
                    f'{text_content}\n\n[Расшифровка аудио]:\n{audio_text}'
                )
            else:
                text_content = audio_text

        if video_text:
            if text_content:
                text_content = (
                    f'{text_content}\n\n[Расшифровка видео]:\n{video_text}'
                )
            else:
                text_content = video_text

        if text_content or message.reactions:
            reactions = (
                get_reactions(message)
                if 'get_reactions' in globals()
                else None
            )

            data[msg_id_str] = {
                'text': text_content,
                'url': post_url,
                'date': message.date.isoformat() if message.date else None,
                'reactions': reactions,
            }

            unsaved_count += 1

        if unsaved_count >= SAVE_EVERY_N_MESSAGES:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(
                f'Промежуточное сохранение: записано {unsaved_count}'
                f' новых сообщений (всего в базе: {len(data)}).',
            )
            unsaved_count = 0

    if unsaved_count > 0:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(
            f'Финальное сохранение: записан остаток '
            f'из {unsaved_count} сообщений.',
        )

    print(f'Обработка завершена. Всего сообщений в {filename}: {len(data)}')
