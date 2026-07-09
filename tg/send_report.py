__all__ = ()
import json
import os
from datetime import datetime

import pandas as pd
from openpyxl.utils import get_column_letter
from telethon import TelegramClient

__all__ = ('send_interactive_report',)

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


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state: dict):
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f'Ошибка сохранения состояния: {e}')


def build_top_text(df_high_useful: pd.DataFrame) -> str:
    lines = []
    lines.append('📚 <b>НАВИГАЦИЯ ПО ПОЛЕЗНЫМ МАТЕРИАЛАМ</b>')
    lines.append('')

    if df_high_useful.empty:
        lines.append('😔 Пока нет постов с высокой полезностью.')
        return '\n'.join(lines)

    for cat_name, cat_group in df_high_useful.groupby('Категория'):
        lines.append('───────────────────')
        lines.append(f'<b>{cat_name}</b>')

        top_10_in_category = cat_group.head(10)

        for _, row in top_10_in_category.iterrows():
            url = row.get('Ссылка на пост', '#')
            subcategory = str(row.get('Подкатегория', ''))
            rubric = str(row.get('Рубрика', ''))

            sub_ok = (
                subcategory and subcategory != '—' and subcategory != 'nan'
            )
            rub_ok = rubric and rubric != '—' and rubric != 'nan'

            if sub_ok and rub_ok:
                text = f'{subcategory} | {rubric}'
            elif sub_ok:
                text = subcategory
            elif rub_ok:
                text = rubric
            else:
                text = f'Пост №{row.get("ID Поста", "?")}'

            if len(str(text)) > 80:
                text = str(text)[:77] + '...'

            lines.append(f'🔹 <a href="{url}">{text}</a>')

    return '\n'.join(lines)


async def send_interactive_report(client: TelegramClient):
    posts = load_classified_posts('processed_messages.json')
    if not posts:
        print('Нет данных для отправки.')
        return

    df = pd.DataFrame(posts)

    df_high = (
        df[df['Полезность'] == 'Высокая']
        if 'Полезность' in df.columns
        else pd.DataFrame()
    )

    state = load_state()
    old_messages = state.get('last_message_ids', [])

    if old_messages:
        print(f'Удаление старых сообщений: {old_messages}')
        try:
            await client.delete_messages(
                CHAT_ID,
                [int(m_id) for m_id in old_messages],
            )
        except Exception as e:
            print(f'Не удалось удалить некоторые сообщения: {e}')

    new_message_ids = []

    report_text = build_top_text(df_high)
    msg_text = await client.send_message(
        CHAT_ID,
        report_text,
        parse_mode='html',
        link_preview=False,
    )
    new_message_ids.append(msg_text.id)

    excel_path = 'temporary_report.xlsx'
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Все посты')
        worksheet = writer.sheets['Все посты']
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            worksheet.column_dimensions[col_letter].width = max(
                max_len + 3,
                10,
            )

    caption = '📊 Полный отчет обновлен:'
    f' {datetime.now().strftime("%d.%m.%Y %H:%M")}'
    msg_file = await client.send_file(CHAT_ID, excel_path, caption=caption)
    new_message_ids.append(msg_file.id)

    if os.path.exists(excel_path):
        os.remove(excel_path)

    state['last_message_ids'] = new_message_ids
    save_state(state)
    print(f'Новые сообщения отправлены. ID: {new_message_ids}')
