# Shop Titans Bot (OCR + Template Matching)

An automation bot for **Shop Titans**, built with Python, EasyOCR, and OpenCV.  
This tool helps automate routine tasks like selling and crafting while you sleep.

---

## 🚀 Features

- 🛒 Automatically sells items to regular customers (based on customizable logic).
- 🏭 Automatically crafts and collects finished products you preconfigure.

## Автоматический найм героя

Отдельная точка входа находит окно процесса `ShopTitan.exe`, снимает только его клиентскую
область и выполняет проверяемый цикл найма. Положение окна и монитор могут меняться; координаты
кликов вычисляются относительно найденного окна. Игра должна оставаться видимой, потому что для
Unity используется снимок рабочего стола, обрезанный по границам процесса.

Сценарий умеет выбирать любую из трёх категорий и любой из 21 классов. Бесплатный найм и платный
найм за золото обрабатываются отдельно; кнопка найма за кристаллы никогда не нажимается. Перед
платежом стоимость дважды читается с экрана и проверяется против общего лимита конфигурации.

### Конфигурация найма

Основной пример находится в `configs/hiring.template.yaml`:

```yaml
hiring:
  category: spellcaster
  class: druid
  allowed_skills:
    - adept
    - death_dealer
    - double_cast
    - all_natural
  limits:
    max_gold_spent: 1000000000
    max_attempts: 100
```

Оба случайных навыка героя должны входить в `allowed_skills`. Первый, фиксированный навык класса,
не участвует в решении. Идентификаторы навыков перечислены в `bot/hiring/catalog.py`, а их эталоны
хранятся в `bot/data/templates/hiring/skills/`. Неизвестный идентификатор в YAML приводит к ошибке
до любых действий в игре.

### Полный каталог категорий и классов

В YAML используются английские стабильные идентификаторы:

| Категория | Классы по порядку в интерфейсе |
| --- | --- |
| `warrior` — Воин | `soldier` — Солдат; `barbarian` — Варвар; `knight` — Рыцарь; `ranger` — Охотник; `samurai` — Самурай; `berserker` — Берсерк; `dark_knight` — Тёмный рыцарь |
| `rogue` — Странник | `thief` — Вор; `monk` — Монах; `musketeer` — Мушкетёр; `wanderer` — Бродяга; `ninja` — Ниндзя; `dancer` — Танцор; `velite` — Велит |
| `spellcaster` — Заклинатель | `mage` — Маг; `cleric` — Священник; `druid` — Друид; `sorcerer` — Волшебник; `spellblade` — Чудотворец; `geomancer` — Геомант; `chronomancer` — Хрономант |

### Полный распознаваемый пул навыков

Это все навыки, для которых сейчас присутствуют PNG-эталоны. Контур и HSV-расцветка плитки
сравниваются раздельно, поэтому навыки с одинаковым рисунком, но разной редкостью не считаются
одинаковыми.

Обычные:

| ID в конфиге | Название в игре | ID в конфиге | Название в игре |
| --- | --- | --- | --- |
| `acrobatics` | Акробатика | `arcane_blast` | Магический взрыв |
| `axe_master` | Повелитель топоров | `bow_master` | Мастер лучник |
| `catalyst_master` | Мастер катализаторов | `cleave` | Рассекание |
| `dagger_master` | Эксперт по кинжалам | `shield_master` | Король щитов |
| `eagle_eyes` | Орлиный глаз | `fast_learner` | Быстрое обучение |
| `instrument_master` | Мастер инструментов | `mace_master` | Мастер булав |
| `mage_armor` | Доспехи мага | `magic_darts` | Магические дротики |
| `maintenance` | Обслуживание | `on_guard` | На страже |
| `perforate` | Протыкание | `smite` | Удар небес |
| `spear_master` | Мастер копья | `staff_master` | Мастер посоха |
| `sturdy` | Прочность | `sword_master` | Мечник |
| `wand_master` | Мастер палочки | | |

Редкие (синие):

| ID в конфиге | Название в игре | ID в конфиге | Название в игре |
| --- | --- | --- | --- |
| `all_natural` | Природный дар | `antimagic_net` | Сеть против магии |
| `caltrops` | Шипы | `curse` | Проклятье |
| `deadly_criticals` | Смертельные критические удары | `deception` | Обман |
| `extra_conditioning` | Дополнительная отработка | `fast_healer` | Быстрое исцеление |
| `fireball` | Огненный шар | `flame_brand` | Огненный клинок |
| `juggernaut` | Джагернаут | `power_attack` | Мощная атака |
| `shining_blade` | Сияющий клинок | `sunder` | Раскол |
| `telling_blows` | Говорящие удары | `thick_skin` | Толстая кожа |
| `throw_daggers` | Метание кинжалов | `toughness` | Стойкость |
| `wall_of_force` | Стена силы | | |

Эпические (золотые):

| ID в конфиге | Название в игре | ID в конфиге | Название в игре |
| --- | --- | --- | --- |
| `adept` | Архимаг | `battering_blows` | Избиение |
| `blurred_movement` | Размытость | `dance_of_blades` | Танец клинков |
| `death_dealer` | Торговец смертью | `double_cast` | Двойное заклинание |
| `extended_warranty` | Расширенная гарантия | `extra_plating` | Дополнительные латы |
| `impervious` | Непробиваемость | `mana_shield` | Щит маны |
| `marksman` | Снайпер | `perfect_form` | Идеальная стойка |
| `super_genius` | Сверхгениальность | `survivor` | Выживший |
| `warlord` | Военачальник | `whirlwind_attack` | Вихрь |

В предоставленном наборе было два изображения `Сияющего клинка` разного размера; это один навык,
поэтому каталог содержит 58 уникальных ID. Добавление только текстового ID без PNG-эталона
намеренно запрещено.

### Запуск

1. Запустите Shop Titans и оставьте игру на главном экране магазина или на экране
   `Персонажи`. Окно разрешается держать на любом мониторе и не обязательно разворачивать на весь
   экран.
2. Не сворачивайте игру, не переключайте фокус и не двигайте мышь во время работы.
3. Из корня репозитория, в активированном виртуальном окружении, выполните:

```powershell
python -u -m bot.run.hire --config configs\hiring.template.yaml --run
```

Для текущего окружения репозитория команду можно запустить без активации:

```powershell
& ..\env-stb\Scripts\python.exe -u -m bot.run.hire `
  --config configs\hiring.template.yaml --run
```

Поддерживаются оба чистых стартовых состояния:

- главный экран — бот проверит его и нажмёт `Персонажи`;
- экран персонажей — бот сразу найдёт `Новый герой` или продолжит сохранённую попытку.

После найма имя и счётчики записываются в
`bot/data/hiring/checkpoint.json`. Этот файл не попадает в Git. При безопасной остановке повторите
ту же команду: сценарий продолжится с сохранённого героя, а не наймёт дубликат. После успешного
поиска чекпоинт удаляется, подходящий герой остаётся открытым, а консоль выводит его имя, навыки,
число попыток и расход золота.

### Защита от ошибочного увольнения

Перед каждым изменяющим действием экран и кнопка проверяются на двух снимках. Для увольнения
дополнительно проверяются сохранённое имя, уровень 10, карточка героя, оба навыка, окно действий и
подтверждение увольнения.

Каждый случайный навык обязан уверенно совпасть с одним известным шаблоном: оценка не ниже `0.80`
и отрыв от второго кандидата не меньше `0.015`. Если каталог неполный или две иконки нельзя
надёжно различить, результат будет `unknown`: герой не увольняется, скрипт завершается с ошибкой и
показывает слот и оценки кандидатов. Добавьте или улучшите соответствующий PNG-шаблон, затем
повторите запуск.

Остановка также происходит без опасного клика при неизвестном экране, потере фокуса, смещении
курсора Windows, несовпадении имени, превышении числа попыток или бюджета. Стоимость платного
найма прибавляется к чекпоинту сразу после подтверждения, поэтому лимит сохраняется и после
перезапуска скрипта.

### Диагностика найма

Команды ниже не выполняют полный цикл:

```powershell
# Определить текущий экран и сохранить размеченный снимок без кликов
python -m bot.run.hire --config configs\hiring.template.yaml `
  --state-only --output bot\data\hiring\diagnostics\state.png

# Сохранить необработанную клиентскую область процесса без кликов
python -m bot.run.hire --config configs\hiring.template.yaml `
  --capture-only --output bot\data\hiring\diagnostics\window.png

# На открытом экране сведений дважды распознать навыки без кликов
python -m bot.run.hire --config configs\hiring.template.yaml `
  --analyze-skills --output bot\data\hiring\diagnostics\skills.png
```

Диагностические снимки и чекпоинт находятся в игнорируемом каталоге
`bot/data/hiring/`. Исходная папка `context/` со скриншотами также исключена из Git.

### Usage Example

1. Launch the game in fullscreen 4K mode.
2. Run the bot script.
3. Go to sleep — the bot will:
   - interact with clients based on your rules;
   - craft items from your list;
   - collect completed items.

---

## ⚠️ Limitations

- ❗ Works only on **Windows PC**.
- 🖥️ Старые сценарии торговли/производства всё ещё рассчитаны на **4K fullscreen**;
  сценарий найма работает с найденной клиентской областью окна и не требует 4K.
- 🧝‍♂️ **Does not support hero-traders** (e.g., those requiring specific items to initiate a deal).
- 🧪 May contain bugs or incomplete features — this is a hobby open-source project.

---

## 📦 Installation

- Create and activate a virtual environment:

```bash
python -m venv env
source env/bin/activate  # or env\Scripts\activate on Windows
```

- Install dependencies:

```bash
pip install -r requirements.txt
```

You may need Python 3.8+ and optionally a GPU-enabled system for better OCR speed (via EasyOCR).

## ⚙️ Configuration

Before running the bot, create a `config.yaml` file in the `configs` folder.

```yaml
monitor_index: 1

regions:
  energy_borders: [x1, x2, y1, y2]
  cost_borders: [x1, x2, y1, y2]
  raise_borders: [x1, x2, y1, y2]
  lower_borders: [x1, x2, y1, y2]
  ready_borders: [x1, x2, y1, y2]

colors:
  rgb_ready_upper: [R, G, B]
  rgb_ready_lower: [R, G, B]
  rgb_raise_unav: [R, G, B]
  rgb_raise_av: [R, G, B]
  rgb_lower: [R, G, B]
  rgb_cost: [R, G, B]
  rgb_energy: [R, G, B]

wait_time_cycle_min: 2
wait_time_click_sec: 1.5
wait_time_reconnection_sec: 15
wait_time_status_sec: 1.5
wait_time_production_sec: 1

cost_lower: 400000
cost_same: 500000

telegram_token: "<YOUR_BOT_TOKEN>"
allowed_user_id: <YOUR_TELEGRAM_USER_ID>
```

You can start by copying the provided template:

```bash
cp configs/template.yaml configs/my_config.yaml
```

Then adjust the settings to fit your screen setup and resolution:

- monitor_index: Which screen to capture (1 or 2).
- regions: Screen coordinates for energy, cost, production readiness, etc.
- colors: RGB values used to detect UI elements (you don't have to change it).
- costs: for trading logic.

The bot will automatically load these settings at startup.

---

## 💻 Running the Bot

Run only telegram bot (for testing)

```bash
python -m bot.run.tg --config configs/my_config.yaml

```

Run game and telegram bot

```bash
python -m bot.run.main --config configs/my_config.yaml

```

You can configure your preferences in the `settings.py` file or through command-line arguments (feature in progress).

---

## 📲 Telegram Bot Integration

You can control the game bot via Telegram: start/stop it, request a screenshot, or trigger reconnection cycles.

### 🔐 Configuration

Add these fields to your config file:

```yaml
telegram_token: "<YOUR_BOT_TOKEN>"
allowed_user_id: <YOUR_TELEGRAM_NUMERIC_ID>
```

### 🪪 How to get the values

- Get your `telegram_token` from [@BotFather](https://t.me/BotFather)
- Get your `allowed_user_id` using [@userinfobot](https://t.me/userinfobot)

---

## 🧱 Project Structure

```
shop-titans-bot/
├── bot/
│   ├── telegram/          # Telegram bot interface
│   ├── control/               # Input/output handling (e.g., mouse control, click simulation)
│   │   ├── mouse.py           # Functions to move/click/drag the mouse
│   │   └── interaction.py     # High-level interaction logic (click sequences, UI triggers)
│   ├── core/                  # Core gameplay logic: trading, production, state management
│   │   ├── production.py      # Automated crafting setup and product collection
│   │   ├── trading.py         # Customer interaction and selling logic
│   │   └── status.py          # Game state detection (main screen, dialogs, etc.)
│   ├── data/
│   │   ├── templates/         # Template images for in-game UI and item detection
│   │   └── test_images/       # Static test images for OCR and image matching tuning
│   ├── matching/              # Image processing and screen recognition utilities
│   │   ├── matcher.py         # Template matching, pixel color filtering
│   │   └── ocr.py             # Text extraction from screen using OCR (EasyOCR)
│   ├── run/                   # Entrypoints for running the bot and tools
│   │   ├── run_bot.py         # Main loop that runs the bot continuously
│   │   ├── run_check.py       # Diagnostics or debug mode to verify image detection
│   │   └── run_optimization.py# Tool to optimize OCR parameters (e.g., grayscale thresholds)
│   ├── screen.py              # Screenshot capture and region slicing
│   ├── settings.py            # Configuration and runtime constants
│   └── utility.py             # Generic helper functions used across modules
├── .gitignore                 # Git exclusions
├── LICENSE                    # Project license (MIT)
├── README.md                  # Documentation and usage instructions
└── requirements.txt           # Python dependencies
```

---

## 🤖 Technologies Used

- [`opencv-python`](https://pypi.org/project/opencv-python/) — image processing and template matching
- [`easyocr`](https://github.com/JaidedAI/EasyOCR) — OCR for recognizing game text and numbers
- [`pynput`](https://pypi.org/project/pynput/) — simulating mouse actions
- [`mss`](https://pypi.org/project/mss/) — fast multi-monitor screen capture

---

## ✅ Pre-commit formatting (optional)

This repo supports `black`, `isort`, and `flake8`. You can install hooks via:

```bash
pre-commit install
```

---

## 📄 License

This project is licensed under the **MIT License**.  
You are free to use, modify, distribute, and integrate this project in commercial or private software.

> See [LICENSE](LICENSE) for details.
