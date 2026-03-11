# Архитектура проекта Path Index

## Модули

- `pathindex.collectors`
  - сбор путей из ENV
  - сбор путей из `PATH`
  - подготовка ключевых слов
- `pathindex.storage`
  - создание директории данных
  - SQLite-таблица `entries`
  - чтение/запись `aliases.json`
- `pathindex.search`
  - поиск через SQL LIKE
  - преобразование абсолютного пути в псевдопуть
- `pathindex.actions`
  - открытие пути в системном файловом менеджере
  - копирование в буфер обмена
  - открытие терминала
- `pathindex.cli`
  - команды пользователя (`index/search/open/copy/pseudo/alias`)

## Поток данных

1. `pathi index`
2. collectors читают источники
3. storage очищает и заполняет SQLite
4. `pathi search <query>` выполняет поиск
5. действия над top-результатом (`open/copy/terminal`)
