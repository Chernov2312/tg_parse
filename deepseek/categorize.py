__all__ = ('categorize_posts',)
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

from config import PromptType, settings


def _send_to_ai(chunk_posts: list, prompt: str) -> list:
    system_instruction = (
        f'{prompt}\n'
        'ВАЖНО: Ответь СТРОГО в формате JSON. Никакого лишнего текста,'
        ' пояснений или markdown-разметки (без ```json).'
    )
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url='https://api.deepseek.com',
    )

    chunk_json_str = json.dumps({'posts': chunk_posts}, ensure_ascii=False)

    response = client.chat.completions.create(
        model='deepseek-v4-pro',
        messages=[
            {'role': 'system', 'content': system_instruction},
            {
                'role': 'user',
                'content': f'Входной JSON для анализа:\n{chunk_json_str}',
            },
        ],
        stream=False,
        response_format={'type': 'json_object'},
    )

    ai_output = response.choices[0].message.content.strip()
    parsed_res = json.loads(ai_output)
    return parsed_res.get('posts', parsed_res)


def save_progress(posts_list: list, filename: str):
    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump({'posts': posts_list}, outfile, ensure_ascii=False, indent=4)


def process_json_with_ai(
    all_posts: dict,
    existing_posts: list,
    chunk_size: int = 5,
    max_workers: int = 10,
    max_retries: int = 3,
) -> list:
    if not all_posts:
        return existing_posts

    final_processed_posts = list(existing_posts)
    keys = list(all_posts.keys())
    total_posts = len(all_posts)

    chunks_to_send = []
    for i in range(0, total_posts, chunk_size):
        keys_data = keys[i : i + chunk_size]
        chunk = [all_posts[val] for val in keys_data]
        chunks_to_send.append(chunk)

    print(
        f'Осталось постов для анализа: {total_posts}.'
        f' Нарезано на {len(chunks_to_send)} пачек. '
        f'Запуск параллельной обработки в {max_workers} потоков...',
    )

    def safe_send_to_ai(chunk, prompt_type, chunk_idx):
        for attempt in range(1, max_retries + 1):
            try:
                result = _send_to_ai(chunk, prompt_type)
                return result
            except Exception as err:
                print(
                    f' [Попытка {attempt}/{max_retries}] Ошибка в пачке'
                    f' {chunk_idx + 1}: {err}',
                )
                if attempt < max_retries:
                    time.sleep(2)
        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                safe_send_to_ai,
                chunks_to_send[idx],
                PromptType.CATEGORY.value,
                idx,
            ): idx
            for idx in range(len(chunks_to_send))
        }

        for future in as_completed(futures):
            idx = futures[future]
            try:
                processed_chunk = future.result()

                if processed_chunk is not None:
                    final_processed_posts.extend(processed_chunk)
                    print(
                        f' -> Пачка {idx + 1}/{len(chunks_to_send)}'
                        ' успешно обработана.',
                    )

                    save_progress(
                        final_processed_posts, 'processed_messages.json',
                    )
                else:
                    print(
                        f' КРИТИЧЕСКАЯ ОШИБКА: Пачка {idx + 1} пропущена после'
                        f'{max_retries} попыток.',
                    )

            except Exception as critical_err:
                print(
                    f' Непредвиденная ошибка при чтении потока '
                    f'{idx + 1}: {critical_err}',
                )

    return final_processed_posts


def categorize_posts():
    with open('messages.json', 'r', encoding='utf-8') as file:
        data = json.loads(file.read())

    processed_data_list = []

    try:
        with open('processed_messages.json', 'r', encoding='utf-8') as file:
            processed_file_content = json.loads(file.read())
            processed_data_list = processed_file_content.get('posts', [])

        for post in processed_data_list:
            post_id = post.get('id')
            if post_id in data:
                del data[post_id]
    except Exception as e:
        print('Обработка начата с нуля (файл прогресса не найден или пуст)', e)

    final_list = process_json_with_ai(data, existing_posts=processed_data_list)

    save_progress(final_list, 'processed_messages.json')
    print(
        '\nВсе текстовые посты обработаны'
        '. Результат в processed_messages.json',
    )
