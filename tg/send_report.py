__all__ = ('send_interactive_report',)
import json
import os

import pandas as pd
from openpyxl.utils import get_column_letter
from telethon import TelegramClient

CHAT_ID = 'me'
STATE_FILE = 'report_state.json'


def load_classified_posts(filename: str) -> list:
    if not os.path.exists(filename):
        print(f'Файл {filename} не найден.')
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('posts', [])
    except Exception as e:
        print(f'Ошибка чтения файла {filename}: {e}')
        return []


async def send_interactive_report(client: TelegramClient):
    text_posts = load_classified_posts('processed_messages.json')
    all_posts = text_posts

    valid_posts = [p for p in all_posts if 'error' not in p]

    if not valid_posts:
        print('Нет успешных данных для формирования Excel-отчета.')
        return

    rows = []
    for post in valid_posts:
        try:
            post_id_clean = int(post.get('id'))
        except (ValueError, TypeError):
            post_id_clean = post.get('id')

        raw_date = post.get('date', 'Не указана')
        clean_date = (
            raw_date.replace('T', ' ').split('+')[0]
            if 'T' in raw_date
            else raw_date
        )

        rows.append(
            {
                'ID Поста': post_id_clean,
                'Ссылка на пост': post.get(
                    'url',
                    f'https://t.me{post_id_clean}',
                ),
                'Категория': post.get('category', 'Без категории'),
                'Подкатегория': post.get('subcategory', '—'),
                'Рубрика': post.get('rubric', '—'),
                'Полезность (1-10)': post.get('usefulness', 0),
                'Важность': post.get('importance', 'средняя'),
                'Текст поста': post.get('text', '—'),
                'Дата публикации': clean_date,
            },
        )

    df = pd.DataFrame(rows)
    importance_weight = {'высокая': 3, 'средняя': 2, 'низкая': 1}
    df['_weight'] = df['Важность'].map(importance_weight)
    df = df.sort_values(
        by=['Категория', 'Полезность (1-10)', '_weight'],
        ascending=[True, False, False],
    )
    df = df.drop(columns=['_weight'])

    excel_filename = 'анализ_каналов_report.xlsx'
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Анализ контента')
        worksheet = writer.sheets['Анализ контента']
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            worksheet.column_dimensions[col_letter].width = max(
                max_len + 3,
                12,
            )

    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as sf:
                state = json.load(sf)
                old_msg_id = state.get('last_message_id')

                if old_msg_id:
                    print(
                        f'[Telethon] Удаляем старое сообщение с'
                        f' отчетом (ID: {old_msg_id}) из чата...',
                    )
                    await client.delete_messages(
                        entity=CHAT_ID,
                        message_ids=old_msg_id,
                    )
        except Exception as delete_err:
            print(
                f'[Предупреждение] Не удалось удалить'
                f' старое сообщение: {delete_err}',
            )

    print('Отправка свежего Excel-файла в Telegram...')
    try:
        total_posts = len(df)
        caption_text = (
            '📊 **Обновленный Контент-анализ**\n'
            '━━━━━━━━━━━━━━━━━━━━\n'
            ' База данных обновлена после выхода нового поста.\n'
            f' Всего отсортировано постов в таблице: **{total_posts}**\n'
        )

        new_message = await client.send_file(
            entity=CHAT_ID,
            file=excel_filename,
            caption=caption_text,
            parse_mode='md',
        )
        print('Новый отчет успешно доставлен!')

        with open(STATE_FILE, 'w', encoding='utf-8') as sf:
            json.dump(
                {'last_message_id': new_message.id},
                sf,
                ensure_ascii=False,
                indent=4,
            )

        if os.path.exists(excel_filename):
            os.remove(excel_filename)

    except Exception as e:
        print(f'Не удалось отправить файл отчета в Telegram: {e}')
