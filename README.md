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

```bash
pip install -r requirements.txt
```

You may need Python 3.8+ and optionally a GPU-enabled system for better OCR speed (via EasyOCR).

## 💻 Running the Bot

```bash
python -m bot.run.run_bot
```

You can configure your preferences in the `settings.py` file or through command-line arguments (feature in progress).

---

## 🧱 Project Structure

```
shop-titans-bot/
├── bot/
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

## 📄 License

This project is licensed under the **MIT License**.  
You are free to use, modify, distribute, and integrate this project in commercial or private software.

> See [LICENSE](LICENSE) for details.
