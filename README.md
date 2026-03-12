# Path Index (MVP)

`pathi` — утилита для поиска системных путей по алиасам, ключевым словам и частям пути.

## Что реализовано

- Индексация путей из переменных окружения
- Индексация директорий из `PATH`
- Пользовательские алиасы через `aliases.json`
- В индекс попадают только существующие директории (не файлы и не отдельные объекты)
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

## Установка через pipx (глобальная команда `pathi`)

Если нужно, чтобы `pathi` была доступна глобально (вне конкретного venv), используйте `pipx`.

На дистрибутивах с PEP 668 (например, Arch) команда
`python3 -m pip install --user pipx` может падать с `externally-managed-environment`.
В этом случае сначала установите `pipx` через пакетный менеджер:

```bash
# Arch
sudo pacman -S python-pipx

# Debian/Ubuntu
sudo apt install pipx

# Fedora
sudo dnf install pipx
```

После этого:

```bash
pipx ensurepath
# перезапустите терминал
pipx install /полный/путь/к/EnvPathShortcutTool
```

Если `pipx` всё ещё не установлен и у вас НЕ PEP668-окружение, можно использовать fallback:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Пример для вашего случая:

```bash
pipx install ~/Sources/EnvPathShortcutTool-main
```

Обновить установленную версию после `git pull`:

```bash
pipx upgrade pathindex
```

Удалить:

```bash
pipx uninstall pathindex
```

## Использование

```bash
pathi index
pathi search conf
pathi pseudo /home/user/.config/nvim
pathi alias add projects /home/user/projects
pathi open nvim
pathi env sync --source alias --normalize --file ~/.config/pathi/environment --rebuild
```

### Экспорт индекса в переменные окружения

Чтобы превращать записи индекса в переменные среды (например, для быстрого доступа к `$STEAM`),
используйте:

```bash
pathi env sync --source alias --normalize --print-only
```

Для записи в файл окружения:

```bash
pathi env sync --source alias --normalize --file /etc/environment
```

> Для `/etc/environment` обычно требуются права root (запуск через `sudo`).
> В файл добавляется/обновляется только блок, помеченный как `pathi managed`.

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
