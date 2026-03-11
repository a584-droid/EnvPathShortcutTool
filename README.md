# Path Index (MVP)

`pathi` — утилита для поиска системных путей по алиасам, ключевым словам и частям пути.

## Что реализовано

- Индексация путей из переменных окружения
- Индексация директорий из `PATH`
- Пользовательские алиасы через `aliases.json`
- SQLite-хранилище индекса
- Поиск по `name`, `keywords`, `path`
- Преобразование абсолютного пути в псевдопуть (`$VAR/...`) по самому длинному префиксу
- CLI-интерфейс

## Установка (локально)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Использование

```bash
pathi index
pathi search conf
pathi pseudo /home/user/.config/nvim
pathi alias add projects /home/user/projects
pathi open nvim
```

## Хранилище

По умолчанию:

- Linux: `~/.local/share/pathindex`
- macOS: `~/Library/Application Support/pathindex`
- Windows: `%APPDATA%/pathindex`

Файлы:

- `index.sqlite`
- `aliases.json`
- `cache.json` (зарезервирован)

## Архитектура

```
pathindex/
 ├── collectors.py     # env/path сборщики
 ├── storage.py        # SQLite и aliases.json
 ├── search.py         # поиск и pseudo-path
 ├── actions.py        # действия (open/copy)
 └── cli.py            # CLI
```

## Ограничения MVP

- Без GUI
- Без rofi/fzf интеграции
- Без глобального сканирования файловой системы
