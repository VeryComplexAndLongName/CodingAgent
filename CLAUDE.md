# Инструкции для Claude Code в этом репозитории

Этот файл — только указатели на существующую документацию. Не дублируйте
её содержимое сюда — при расхождении дублей побеждает путаница, не
корректность. Правьте исходный документ, не эту страницу.

## Обзор проекта и инфраструктуры

- [`README.md`](README.md) — что это за проект
- [`docs/architecture.md`](docs/architecture.md) — диаграммы топологии VM/
  контейнеров и потоков данных.
- [`docs/adr/`](docs/adr.) - Папка, где живут все ADR. Любые архитектурные изменения идут через ADR.
- [`docs/adr/README.md`](docs/adr/README.md) — архитектурные решения (ADR),
  включая почему компоненты живут там, где живут.

## Конвенции кода

- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) —
  общие правила для Python-кода в этом репозитории (стиль, тестирование,
  логирование через `loguru`, `uv`/`pyproject.toml`, конфигурация через
  `pydantic-settings`). Написаны для GitHub Copilot, но применимы к любому
  ИИ-агенту, работающему с кодом здесь — следуйте им и вы.

## OpenSpec

[`openspec/README.md`](openspec/README.md) — runbook: когда заводить
OpenSpec-запись (и когда достаточно просто коммита), какую команду/skill
использовать (`propose`/`apply`/`explore`/`sync`/`update`/`archive`) и в
каком формате просить агента.

Этот репозиторий использует [OpenSpec](openspec/) (`openspec new change` /
`openspec validate --strict` / `openspec archive --yes`) для капабилities
`docsai-api` (precheck-сервисы: `actuality-check`, `drawing-compliance-
check`, `language-check`, `normokontrol-review`), инфраструктуры реранкера
(`reranker-infrastructure`) и верификации ответа модели
(`response-verification`, `hppii-ui/filters/`) — см. `openspec/specs/` за
текущими требованиями и `openspec/changes/archive/` за историей решений.
Архитектурные развилки (не текущее поведение конкретной капабилити)
документируются отдельно как ADR в `docs/adr/`, не в OpenSpec — см. решение
в этих ADR, если что-то не сходится с код.

Для живых инцидентов/точечного тюнинга конфига (не архитектурное решение)
OpenSpec-запись не обязательна — достаточно подробного commit message (см.
`git log` за примерами). Новое поведение/капабилити — через OpenSpec.
