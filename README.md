# Remote Screen Display System

A Telegram bot that displays images, videos, and plays audio files in fullscreen. Works on Windows 7/10/11, macOS, and Linux.

## 🚀 Quick Start (One-Click Setup)

### For All Platforms:
1. Download and extract the project files
2. Run the setup script:
   - **Windows**: Double-click `setup.py` or run `python setup.py`
   - **Mac/Linux**: Run `python setup.py` in terminal
3. Edit `.env` file with your bot token and user ID
4. Start the bot:
   - **Windows**: Double-click `start_bot.bat`
   - **Mac/Linux**: Run `./start_bot.sh`

## 📋 Features

- 🖼️ **Image Display**: Fullscreen image display with automatic centering
- 🎬 **Video Playback**: Fullscreen video with audio support
- 🎵 **Audio Playback**: Background audio playback (MP3, WAV, etc.)
- 📱 **Remote Control**: Control via Telegram commands
- 🔄 **Cross-Platform**: Works on Windows 7/10/11, macOS, Linux
- 🎯 **Perfect Sync**: Video and audio perfectly synchronized
- 📐 **Auto-Scaling**: Maintains aspect ratio, centers content

## 🛠️ Requirements

- **Python 3.8+** (automatically checked by setup)
- **FFmpeg** (automatically installed by setup)
- **Internet Connection** (for Telegram API)

## 📦 Installation

### Automatic Installation (Recommended)
```bash
python setup.py
```

This will:
- ✅ Check Python version compatibility
- ✅ Create virtual environment
- ✅ Install all Python dependencies
- ✅ Install FFmpeg automatically
- ✅ Create configuration files
- ✅ Generate startup scripts

### Manual Installation

#### 1. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Install FFmpeg

**Windows:**
- Download from: https://ffmpeg.org/download.html#build-windows
- Extract to `C:\ffmpeg`
- Add `C:\ffmpeg\bin` to PATH
- Restart command prompt

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

## ⚙️ Configuration

Create a `.env` file:
```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
AUTHORIZED_USERS=YOUR_USER_ID_HERE
DEFAULT_DISPLAY_TIME=10
LOG_FILE=screen_display.log
```

### Getting Your Bot Token:
1. Talk to [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the token

### Getting Your User ID:
1. Talk to [@userinfobot](https://t.me/userinfobot) on Telegram
2. Send any message
3. Copy your user ID

## 🎮 Usage

### Basic Commands:
- Send any **image** → Display fullscreen
- Send any **video** → Play with sound fullscreen
- Send any **audio file** → Play in background
- `/sure <seconds>` → Set display duration
- `/iptal` → Cancel current display
- `/durum` → Check bot status
- `/yardim` → Show all commands

### Advanced Commands:
- `/durdur` → Stop bot
- `/devam` → Resume bot
- `/kapat` → Shutdown bot

## 🔧 Platform-Specific Notes

### Windows 7/10/11:
- ✅ Full compatibility
- ✅ Automatic FFmpeg installation
- ✅ Batch file startup (`start_bot.bat`)
- ✅ Works without admin rights

### macOS:
- ✅ Full compatibility
- ✅ Homebrew integration
- ✅ Shell script startup (`start_bot.sh`)
- ✅ Retina display support

### Linux:
- ✅ Full compatibility
- ✅ Multiple package manager support
- ✅ Shell script startup (`start_bot.sh`)
- ✅ X11/Wayland support

## 🐛 Troubleshooting

### Common Issues:

**"FFmpeg not found"**
- Run `python setup.py` again
- Install FFmpeg manually if needed

**"Python version too old"**
- Install Python 3.8+ from python.org
- Update system Python on Linux/macOS

**"Bot token invalid"**
- Check token in `.env` file
- Create new bot with @BotFather

**"Permission denied"**
- Run as administrator on Windows
- Use `sudo` on Linux if needed

### Debug Mode:
Check `screen_display.log` for detailed error messages.

## 📁 Project Structure

```
telegram-bot/
├── screen_display_bot.py    # Main bot file
├── setup.py                 # Automatic setup script
├── requirements.txt         # Python dependencies
├── .env.example             # Configuration template
├── start_bot.bat           # Windows startup script
├── start_bot.sh            # Mac/Linux startup script
├── README.md               # This file
└── venv/                   # Virtual environment (auto-created)
```

## 🔄 Updates

To update the bot:
1. Download new files
2. Run `python setup.py` again
3. Keep your `.env` file

## 📄 License

MIT License - feel free to use and modify.

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section
2. Look at `screen_display.log`
3. Make sure all requirements are met

---

**Enjoy your cross-platform Telegram media bot! 🎉**
