# Shop Titans Bot (OCR + Template Matching)

An automation bot for **Shop Titans**, built with Python, EasyOCR, and OpenCV.  
This tool helps automate routine tasks like selling and crafting while you sleep.

---

## 🚀 Features

- 🛒 Automatically sells items to regular customers (based on customizable logic).
- 🏭 Automatically crafts and collects finished products you preconfigure.

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
- 🖥️ **4K fullscreen** mode is currently required.
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
