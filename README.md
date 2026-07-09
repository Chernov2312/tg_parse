# Парсер телеграм каналов
## Основные возможности

- Категоризация всех tg сообщений

---

### Предварительные требования

- [Python 3.12+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

### Установка и запуск

1. Клонирование репозитория

```bash
git clone https://github.com/Chernov2312/tg_parse
```

2. Переход в папку проекта

```bash
cd tg_parse
```

3. Создание виртуального окружения

Linux/macOS

```bash
python3 -m venv venv
```

Windows (PowerShell)

```powershell
python -m venv venv
```

4. Активация виртуального окружения

Linux/macOS

```bash
source venv/bin/activate
```

Windows (PowerShell)

```powershell
.\venv\Scripts\Activate.ps1
```

5. Установка зависимостей

Для запуска проекта

```bash
pip install -r requirements/prod.txt
```

6. Настройка переменных окружения

Linux/macOS

```bash
cp .env.example .env
```

Windows (PowerShell)

```powershell
Copy-Item .env.example .env
```

7. Запуск парсера

```bash
python main.py
```

---

#### Запуск парсера

+ Перед запуском обязательно наличие VPN для работы телеграма
+ Скачиваем в cmd для перевода аудио в текст
```bash
winget install Gyan.FFmpeg
```

**1. Создаём tg сессию**
Для этого вводите то, что требуется

**2. ВВодим номер канала, который мы хотим спарсить**

После этого ожидаем сообщение в личном чате.

---

#### Установка зависимостей

Для разработки

```bash
pip install -r requirements/dev.txt
```

Для запуска тестов

```bash
pip install -r requirements/test.txt
```

---

#### Запуск тестов

Проверка flake8

```bash
flake8
```

Проверка black

```bash
black --check .
```


---

###### Структура проекта
```
Tg_parse/
├── parse/                # парсинг чатов
├── config/               # Конфигурация проекта
├── deepseek/             # Категоризация с использованием  нейросети deepseek
├── requirements/         # Зависимости
├── tg/                   # Отправка exel в tg
├── main.py               # Запуск
├── .env.example          # Пример переменных окружения
├── .flake8
├── pyproject.toml
├── .gitignore
├── .gitlab-ci.yml
└── README.md
```

---

###### Разработчики

```
Чернов Макс
```
---

<small>© 2026 Max</small>