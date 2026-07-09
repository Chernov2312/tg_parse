import json
import os
from datetime import datetime, timedelta

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
            if isinstance(data, dict):
                return data.get('posts', [])
            return data
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
    lines.append(
        '📚 <b>НАВИГАЦИЯ ПО ПОЛЕЗНЫМ МАТЕРИАЛАМ (ЗА ПОСЛЕДНИЙ ГОД)</b>'
    )
    lines.append('')

    if df_high_useful.empty:
        lines.append('😔 Пока нет полезных постов за последний год.')
        return '\n'.join(lines)

    for cat_name, cat_group in df_high_useful.groupby('category'):
        lines.append('───────────────────')
        lines.append(f'<b>{cat_name}</b>')

        top_10_in_category = cat_group.head(10)

        for _, row in top_10_in_category.iterrows():
            url = row.get('url', '#')
            subcategory = str(row.get('subcategory', ''))
            rubric = str(row.get('rubric', ''))

            sub_ok = subcategory and subcategory.strip() not in (
                '—',
                'nan',
                '',
            )
            rub_ok = rubric and rubric.strip() not in ('—', 'nan', '')

            if sub_ok and rub_ok:
                text = f'{subcategory} | {rubric}'
            elif sub_ok:
                text = subcategory
            elif rub_ok:
                text = rubric
            else:
                text = f'Пост №{row.get("id", "?")}'

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
        df[df['usefulness'] >= 7].copy()
        if 'usefulness' in df.columns
        else pd.DataFrame()
    )

    if not df_high.empty and 'date' in df_high.columns:
        df_high['datetime_parsed'] = pd.to_datetime(
            df_high['date'], errors='coerce'
        )
        one_year_ago = datetime.now() - timedelta(days=365)
        df_high = df_high[df_high['datetime_parsed'] >= one_year_ago]

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
    MAX_LENGTH = 3900

    if len(report_text) <= MAX_LENGTH:
        msg_text = await client.send_message(
            CHAT_ID, report_text, parse_mode='html', link_preview=False
        )
        new_message_ids.append(msg_text.id)
    else:
        print(
            f'Текст навигации слишком длинный ({len(report_text)} симв.). Разбиваем на части...'
        )
        lines = report_text.split('\n')
        current_chunk = []
        current_length = 0

        for line in lines:
            if current_length + len(line) + 1 > MAX_LENGTH:
                chunk_text = '\n'.join(current_chunk)
                msg_text = await client.send_message(
                    CHAT_ID, chunk_text, parse_mode='html', link_preview=False
                )
                new_message_ids.append(msg_text.id)
                current_chunk = [line]
                current_length = len(line)
            else:
                current_chunk.append(line)
                current_length += len(line) + 1

        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            msg_text = await client.send_message(
                CHAT_ID, chunk_text, parse_mode='html', link_preview=False
            )
            new_message_ids.append(msg_text.id)

    for col in df.select_dtypes(include=['object', 'string']).columns:
        df[col] = df[col].apply(
            lambda x: (
                str(x)[:32700] + '... [Обрезано из-за лимита Excel]'
                if isinstance(x, str) and len(x) > 32767
                else x
            )
        )

    excel_path = 'temporary_report.xlsx'
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Все посты')
        worksheet = writer.sheets['Все посты']
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            worksheet.column_dimensions[col_letter].width = min(
                max(max_len + 3, 10), 50
            )

    caption = f'📊 Полный архив отчетов обновлен: {datetime.now().strftime("%d.%m.%Y %H:%M")}'
    msg_file = await client.send_file(CHAT_ID, excel_path, caption=caption)
    new_message_ids.append(msg_file.id)

    if os.path.exists(excel_path):
        os.remove(excel_path)

    state['last_message_ids'] = new_message_ids
    save_state(state)
    print(f'Новые сообщения отправлены. ID: {new_message_ids}')
