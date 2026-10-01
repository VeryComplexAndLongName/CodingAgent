## Requirements

- Python 3.12+

# Global Copilot Instructions for Python Project
- Помести в `.gitignore` все файлы, которые не должны попадать в репозиторий (например, `.env`, `logs/`, `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`, `.Python`, `env/`, `.venv/`, `*.log`, `.ruff_cache`, `.mypy_cache`, `.pytest_cahe`, `ruff_cache`, `*.bak`, `*.egg-info/`).
- use uv to manage project, dependencies and virtual environments instead of pip.
- foresing two environment usage: development and production. Use `.env` file for development environment and environment variables for production.
- use `config.json` in repository root as the default runtime configuration file.
- prepare correct `.dockerignore` file to exclude unnecessary files from Docker image.
- для логировани, вывода любых сообщений и ошибок использовать только `loguru` вместо встроенного модуля `logging`.
- не использовать print() для вывода сообщений в консоль, использовать только `loguru`.
- Проект должен быть в формате src-layout, где исходный код находится в папке `src/`, а тесты в папке `tests/`.
- Use russian language for README.md, docstrings, comments and variable names. Use russian language for commit messages and issues.


## Preparation

Run the commands below to prepare the environment for the project:
1. Create a .vscode\settings.json file with the following content:
```json
{
  "python.pythonPath": ".venv/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "workbench.tree.indent": 24,
  "workbench.tree.renderIndentGuides": "always",
  "workbench.colorCustomizations": {
    "tree.indentGuidesStroke": "#bcb6b6"
  },
  "python.testing.unittestEnabled": false
}
```
2. Create .vscode\launch.json file with the following content:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "CLI",
            "type": "debugpy",
            "request": "launch",
            "module": "apps.cli",
            "cwd": "${workspaceFolder}",
            "justMyCode": false,
            "console": "integratedTerminal",
            "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
            "envFile": "${workspaceFolder}/.env",
            "python.terminal.useEnvFile": true            
        },
        {
            "name": "API",
            "type": "debugpy",
            "request": "launch",
            "module": "apps.api",
            "cwd": "${workspaceFolder}",
            "justMyCode": false,
            "console": "integratedTerminal",
            "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
            "envFile": "${workspaceFolder}/.env",
            "python.terminal.useEnvFile": true
        },
        {
            "name": "Gateway",
            "type": "debugpy",
            "request": "launch",
            "module": "apps.gateway",
            "cwd": "${workspaceFolder}",
            "justMyCode": false,
            "console": "integratedTerminal",
            "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
            "envFile": "${workspaceFolder}/.env",
            "python.terminal.useEnvFile": true
        }
    ]
}
```
3. python -m pip install --upgrade pip
4. python -m venv .venv
5. .venv/Scripts/activate (Windows) or source .venv/bin/activate (Linux/Mac)
6. python -m pip install uv[all] --upgrade
7. uv init
8. uv add ruff mypy pytest loguru uvicorn pydantic python-dotenv sqlalchemy alembic fastapi requests


## Code Style

- Следовать стандарту PEP8.
- Максимальная длина строки: 100 символов.
- Имена функций и переменных — snake_case.
- Имена классов — PascalCase.
- Константы — UPPER_SNAKE_CASE.
- Использовать type hints во всех публичных функциях.
- Использовать f-строки вместо format().

# Python Coding Instructions

- keep a single entry point in main.py as if __main__ to run the application.
- use `argparse` for command-line argument parsing.
- Use Principles: SRP, OCP, LSP, ISP, DIP, DRY, KISS, YAGNI, Law of Demeter, GRASP.
- Use Hexagonal/Clean Architecture.
- Give preference `asyncio` if it is applicable
- Use concurrent.futures.ProcessPoolExecutor for CPU-bound tasks
- Use concurrent.futures.ThreadPoolExecutor если очень нужно, но предпочтение всегда за `asyncio`

## Project Structure

- Объявления моделей — в `models/`.
- Логика приложения — в `services/`.
- Утилиты — в `utils/`.
- Общие функции — в `common/`.
- Тесты — в `tests/`, тесты должны быть написаны без использования классов (`class`), обязатьно наличие `conftest.py`.
- Конфигурации — в файле в папке `config/` или `.env`, если нужно использовать секреты (если используется dotenv).
- Если проект CLI, backend или сервис — использовать `main.py` как точку входа.
- Если проект CLI, backend или сервис — использовать `config/app.json` для конфигурации приложения.
- Если проект CLI, backend или сервис — использовать `logs/` для логов приложения.
- Если проект CLI, backend или сервис — использовать `requirements.txt` и `pyproject.toml` для зависимостей.
- Если проект CLI, backend или сервис — использовать `README.md` для документации.
- Если проект CLI, backend или сервис — использовать `Dockerfile` и `docker-compose.yml` для контейнеризации при необходимости.
- Все CLI-утилиты должны быть в `cli/`. Каждая задача должна иметь свою папку и иметь точку входа в своём собственном `main.py`.

## Documentation

- Все публичные функции и классы должны иметь docstring в формате Google-style.
- Для модулей с нетривиальной логикой — краткое описание в начале файла.
- Если функция сложная — добавлять примеры использования.
- `README.md` должен содержать общее описание приложения/проекта.
- `README.md` должен содержать инструкцию по запуску и примеры использования.
- `README.md` должен содержать информацию о зависимостях и их установке.
- `README.md` должен содержать информацию о том, как запускать тесты и проверять покрытие.
- `README.md` должен содержать информацию о том, как запускать приложение и использовать его функции.

## Error Handling

- Исключения должны быть информативными и специфичными.
- Не подавлять исключения без необходимости.
- Внешние ошибки должны оборачиваться в кастомные исключения проекта.
- Исключения должны быть осмысленными: `InvalidConfigError`, `CommandExecutionError`, и т.д.

## Logging

- Логи должны писаться в файл `logs/app.log` и выводиться в консоль.
- Формат логов: `%(asctime)s - %(levelname)s - %(message)s`.
- Использовать подходящие цвета в консольном выводе для разных 
  - уровней логов
  - времени
  - loglevel
- Не использовать логирование внутри чистых функций.

## Dependencies

- Все зависимости должны быть перечислены в `requirements.txt` и `pyproject.toml`.
- Не добавлять тяжёлые библиотеки без необходимости.
- Если есть выбор — использовать стандартную библиотеку.
- Program initial version is stored in `pyproject.toml`, do not store version in code. Initial version value is: 0.1.0

## Testing

- Все тесты должны быть в папке `tests/`.
- Использовать pytest.
- Покрывать тестами:
  - smoke-тесты
  - unit-тесты
  - бизнес‑логику
  - обработку ошибок
  - edge-cases
  - e2e (end-to-end) сценарии, если это CLI, backend или сервис.
- Не мокать стандартную библиотеку без необходимости.
- Тесты должны быть изолированными и повторяемыми.

## Code Quality

- Предпочитать чистые функции.
- Избегать циклических зависимостей.
- Разделять бизнес-логику и ввод/вывод.
- Использовать dataclasses, если структура данных неизменяема.
- Отдавать предпочтение `pydantic` для всех структур данных, для валидации данных.
- Не смешивать слои приложения в одном модуле.

## Performance

- Не оптимизировать преждевременно.
- Если требуется оптимизация — добавлять комментарий с объяснением.
- Использовать генераторы вместо списков, если это снижает память.
- Использовать асинхронные функции, если это повышает производительность.
- Использовать `asyncio` для асинхронного ввода/вывода, если это необходимо.
- Использовать `concurrent.futures` для параллельного выполнения задач, если это необходимо.
- Использовать `multiprocessing` для CPU-bound задач, если это необходимо.
- Использовать `threading` для I/O-bound задач, если это необходимо, но избегать сложных гонок данных и отдавать предпочтение `asyncio` по возможности.

## Security

- Не хранить секреты в коде.
- Использовать `.env` или переменные окружения.
- Проверять входные данные.
- Не использовать eval/exec.

## Copilot Behavior

- Всегда следовать этим правилам при генерации кода.
- Если пользовательский запрос противоречит правилам — предложить корректный вариант.
- При генерации кода объяснять, какие правила были применены.

## Checks

- Проверять код на соответствие PEP8.
- Проверять код на наличие type hints.
- Всегда использовать для проверки `mypy`, `ruff` и `pytest`.

# NATS Queueing

- Use NATS for asynchronous message passing between services if it will be required.
- NATS is a single way to communicate between gateway, backend and cli services, and it is the only way to communicate between gateway, backend and cli services.
- Use NATS JetStream for message persistence and replay capabilities.
- Use NATS subjects to define message channels and topics for communication.
- Use NATS consumers to subscribe to specific subjects and process messages asynchronously.
- Use NATS publishers to send messages to specific subjects for communication between services.
- Use NATS message headers to include metadata and context information in messages.
- Use 3 queues for NATS message processing: high-priority, medium-priority, and low-priority queues.
- Use high-priority queue for internal service-to-service communication and critical messages like communications between cli, backend and gateway.
- Use medium-priority queue for regular service-to-service communication and pass prepared request from client to gateway services.
- Use low-priority queue for non-critical and background tasks.
- CLI cannot directly communicate with backend services; it must go through the chain: queue -> gateway.
- Backend services cannot directly communicate with CLI; they must go through the chain: queue -> gateway.
