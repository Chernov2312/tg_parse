__all__ = (
    'get_reactions',
    'transcribe_audio_locally',
)
import os

from faster_whisper import WhisperModel

model = WhisperModel('tiny', device='cpu', compute_type='int8')


def get_reactions(message):
    reactions_data = {}
    if message.reactions and message.reactions.results:
        for count in message.reactions.results:
            if hasattr(count.reaction, 'emoticon'):
                emoji = count.reaction.emoticon
                reactions_data[emoji] = count.count
    return reactions_data


def transcribe_audio_locally(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""

    try:
        # 1. Вызываем метод без какой-либо распаковки.
        result = model.transcribe(
            file_path,
            beam_size=5,
            language='ru',
        )

        # 2. Безопасно проверяем, что вернулся корректный кортеж/объект
        if not result or not isinstance(result, tuple) or len(result) == 0:
            print(
                f"Предупреждение: Whisper вернул пустой результат для {file_path} (возможно, нет аудиодорожки)"
            )
            return ""

        # 3. Извлекаем генератор сегментов
        segments = result[0]

        # 4. Собираем текст
        text_segments = [segment.text for segment in segments]
        full_text = ' '.join(text_segments).strip()

        return full_text

    except Exception as e:
        print(
            f'Критическая ошибка локального Whisper на файле {file_path}: {e}',
        )
        # Возвращаем СТРОГО пустую строку.
        # Если вернуть текст ошибки вроде "[Ошибка]", ваш основной скрипт посчитает это успешным текстом.
        return ""
