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
python -m run_bot.py
```

You can configure your preferences in the `settings.py` file or through command-line arguments (feature in progress).

---

## 🧱 Project Structure

```
shop-titans-bot/
├── logic/                      # Core logic modules
│   ├── production.py           # Handles crafting logic and queueing of items
│   ├── status.py               # Detects current UI state (main screen, dialogs, etc.)
│   └── trading.py              # Automates selling to regular customers
├── screenshots/                # Saved screenshots for debugging or testing
├── pictures/                   # Template images used for matching
├── tests/                      # Optional test scripts
├── interaction.py              # Coordinates UI interaction logic and flow control
├── matcher.py                  # Template matching functions
├── mouse_control.py            # Mouse interaction: clicking, movement, confirmations
├── run_bot.py                  # Main entry point to start the bot
├── run_check.py                # Debug mode: run specific checks or visual outputs
├── run_optimization.py         # Parameter tuning for OCR or image preprocessing
├── screen.py                   # Screen capture utilities and region extraction
├── settings.py                 # Configuration file: thresholds, colors, regions, paths
├── utility.py                  # Helper utilities: logging, image saving, file IO
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
└── LICENSE                     # Project license (MIT)
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
