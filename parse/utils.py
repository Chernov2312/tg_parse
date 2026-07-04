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
        return '[Ошибка: аудиофайл не найден]'

    try:
        segments, _ = model.transcribe(
            file_path,
            beam_size=5,
            language='ru',
        )
        text_segments = [segment.text for segment in segments]
        full_text = ' '.join(text_segments).strip()

        if not full_text:
            return '[Аудиозапись пуста или голос не различим]'

        return full_text

    except Exception as e:
        print(
            f'Критическая ошибка локального Whisper на файле {file_path}: {e}',
        )
        return f'[Не удалось обработать аудио локально: {e}]'
