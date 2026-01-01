import os
import sys
import subprocess
import tempfile
import time
import logging
import signal
import importlib.util
import asyncio
import threading
from pathlib import Path


def _bootstrap_python_deps() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.join(base_dir, 'requirements.txt')

    required_modules = [
        'dotenv',
        'telegram',
        'PIL',
        'cv2',
        'simpleaudio',
    ]

    missing = [m for m in required_modules if importlib.util.find_spec(m) is None]
    if not missing:
        return

    print(f"Eksik Python paketleri bulundu: {', '.join(missing)}")
    print("Kurulum deneniyor (pip ile)...")

    try:
        if os.path.exists(requirements_path):
            cmd = [sys.executable, '-m', 'pip', 'install', '-r', requirements_path]
        else:
            cmd = [sys.executable, '-m', 'pip', 'install', 'python-telegram-bot==20.7', 'Pillow==10.0.0', 'python-dotenv==1.0.0', 'opencv-python==4.8.1.78', 'simpleaudio==1.0.4']

        subprocess.check_call(cmd)
    except Exception as e:
        print(f"Paket kurulumu başarısız: {e}")
        print("Lütfen şunu çalıştırın: python -m pip install -r requirements.txt")
        return

    os.execv(sys.executable, [sys.executable, os.path.abspath(__file__), *sys.argv[1:]])


from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

# Audio imports
try:
    import simpleaudio as sa
    SIMPLEAUDIO_AVAILABLE = True
except ImportError:
    SIMPLEAUDIO_AVAILABLE = False

try:
    import subprocess
    import threading
    SUBPROCESS_AUDIO_AVAILABLE = True
except ImportError:
    SUBPROCESS_AUDIO_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # More verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('screen_display.log', encoding='utf-8')
    ]
)

# Set higher log level for some noisy libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

VIDEO_AVAILABLE = importlib.util.find_spec('cv2') is not None
AUDIO_AVAILABLE = SIMPLEAUDIO_AVAILABLE or SUBPROCESS_AUDIO_AVAILABLE

# Load environment variables
load_dotenv()

# Configuration
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8006349550:AAFOvRAVED05Q7Ijro9HKYKW_NHhDgjJQ34"
AUTHORIZED_USERS = [7435892118]  # Your Telegram Chat ID
DEFAULT_DISPLAY_TIME = 10  # Default display time in seconds


def _run_viewer_image(image_path: str, display_time: int) -> None:
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.configure(bg='black')
    root.overrideredirect(True)

    def _block_event(_event=None):
        return 'break'

    root.protocol('WM_DELETE_WINDOW', lambda: None)
    root.bind('<Alt-F4>', _block_event)
    root.bind('<Command-q>', _block_event)
    root.bind('<Command-w>', _block_event)
    root.bind('<Control-q>', _block_event)
    root.bind('<Meta-q>', _block_event)
    root.bind('<Control-w>', _block_event)
    root.bind('<Meta-w>', _block_event)

    img = Image.open(image_path)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    img_ratio = img.width / img.height
    screen_ratio = screen_width / screen_height
    if img_ratio > screen_ratio:
        new_width = screen_width
        new_height = int(screen_width / img_ratio)
    else:
        new_height = screen_height
        new_width = int(screen_height * img_ratio)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(img)

    frame = tk.Frame(root, bg='black')
    frame.place(relx=0.5, rely=0.5, anchor='center')
    label = ttk.Label(frame, image=photo, background='black')
    label.pack()

    def _close():
        try:
            root.quit()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass

    # Viewer should be closable remotely via Telegram (/iptal). We use SIGUSR1 for that.
    if hasattr(signal, 'SIGUSR1'):
        def _sigusr1_handler(_signum, _frame):
            _close()

        signal.signal(signal.SIGUSR1, _sigusr1_handler)

    # Best-effort: ignore common termination signals so local close attempts don't stop it.
    try:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    except Exception:
        pass
    try:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    except Exception:
        pass

    # Local emergency exit (safety): Ctrl+Shift+Esc
    root.bind('<Control-Shift-Escape>', lambda e: _close())

    root.after(max(1, int(display_time)) * 1000, _close)
    root.mainloop()


def _run_viewer_video(video_path: str, display_time: int) -> int:
    """Play video with audio using FFmpeg for perfect sync."""
    
    stopped = False
    
    def signal_handler(signum, frame):
        nonlocal stopped
        stopped = True
    
    # Handle remote cancel signal
    if hasattr(signal, 'SIGUSR1'):
        signal.signal(signal.SIGUSR1, signal_handler)

    try:
        # Check for local FFmpeg installation first
        local_ffmpeg = Path("ffmpeg")
        ffplay_path = None
        
        if sys.platform == "win32":
            ffplay_exe = local_ffmpeg / "bin" / "ffplay.exe"
            if ffplay_exe.exists():
                ffplay_path = str(ffplay_exe)
        
        # Use system or local FFmpeg
        ffplay_cmd = ffplay_path if ffplay_path else "ffplay"
        
        # Use FFmpeg for both video and audio playback
        if sys.platform == "win32":  # Windows
            cmd = [
                ffplay_cmd, 
                '-fs',  # Fullscreen
                '-autoexit',  # Exit when video ends
                '-v', 'quiet',  # Suppress verbose output
                '-x', '1920',  # Force width
                '-y', '1080',  # Force height
                video_path
            ]
        elif sys.platform == "darwin":  # macOS
            cmd = [
                ffplay_cmd, 
                '-fs',  # Fullscreen
                '-autoexit',  # Exit when video ends
                '-v', 'quiet',  # Suppress verbose output
                video_path
            ]
        else:  # Linux
            cmd = [
                ffplay_cmd, 
                '-fs',  # Fullscreen
                '-autoexit',
                '-v', 'quiet',
                video_path
            ]
        
        # Start FFmpeg process
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for process to complete or manual stop
        while process.poll() is None and not stopped:
            time.sleep(0.1)
        
        # Clean up if still running (shouldn't happen with -autoexit)
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=2)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        
        return 0
        
    except FileNotFoundError:
        # FFmpeg not found
        return 7
    except Exception as e:
        logger.error(f"Video playback error: {e}")
        return 8


def _run_viewer_audio(audio_path: str, display_time: int) -> int:
    """Play audio file in background without any visual display."""
    audio_process = None
    
    try:
        # Check for local FFmpeg installation first
        local_ffmpeg = Path("ffmpeg")
        ffplay_path = None
        
        if sys.platform == "win32":
            ffplay_exe = local_ffmpeg / "bin" / "ffplay.exe"
            if ffplay_exe.exists():
                ffplay_path = str(ffplay_exe)
        
        # Use system or local FFmpeg
        ffplay_cmd = ffplay_path if ffplay_path else "ffplay"
        
        if SUBPROCESS_AUDIO_AVAILABLE:
            # Use FFmpeg for audio playback to ensure proper duration
            if sys.platform == "win32":  # Windows
                audio_process = subprocess.Popen([
                    ffplay_cmd, '-nodisp', '-autoexit', '-v', 'quiet', audio_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif sys.platform == "darwin":  # macOS
                audio_process = subprocess.Popen([
                    ffplay_cmd, '-nodisp', '-autoexit', '-v', 'quiet', audio_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:  # Linux
                audio_process = subprocess.Popen([
                    ffplay_cmd, '-nodisp', '-autoexit', '-v', 'quiet', audio_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            return 5  # No audio available

        logger.info(f"Playing audio: {audio_path}")

        # Wait for audio to finish naturally (let -autoexit handle it)
        while audio_process.poll() is None:
            time.sleep(0.1)

        return 0

    except Exception as e:
        logger.error(f"Error playing audio: {e}")
        return 6


def _viewer_main(argv: list[str]) -> int:
    # argv: [--viewer, kind, path, seconds]
    try:
        kind = argv[2]
        media_path = argv[3]
        seconds = int(argv[4])
    except Exception:
        return 2

    try:
        if kind == 'image':
            _run_viewer_image(media_path, seconds)
        elif kind == 'video':
            return _run_viewer_video(media_path, seconds)
        elif kind == 'audio':
            return _run_viewer_audio(media_path, seconds)
        else:
            # Unsupported viewer kind
            return 3
    finally:
        try:
            if os.path.exists(media_path):
                os.remove(media_path)
        except Exception:
            pass

    return 0

class MediaDisplay:
    """Class to handle media display on screen."""
    
    def __init__(self):
        self.root = None
        self.current_media = None
        self.player = None
        self.media_duration = DEFAULT_DISPLAY_TIME
        self.cleanup_timer = None
    
    def display_image(self, image_path: str, display_time: int = None):
        """Display an image in fullscreen mode."""
        try:
            # Clean up any existing display
            self._cleanup()
            
            # Create a new root window
            self.root = tk.Tk()
            self.root.attributes('-fullscreen', True)
            self.root.configure(bg='black')
            
            # Disable window decorations and make it truly fullscreen
            self.root.overrideredirect(True)
            self.root.focus_force()
            
            # Load the image
            img = Image.open(image_path)
            
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Calculate the maximum size while maintaining aspect ratio
            img_ratio = img.width / img.height
            screen_ratio = screen_width / screen_height
            
            if img_ratio > screen_ratio:
                # Image is wider than screen
                new_width = screen_width
                new_height = int(screen_width / img_ratio)
            else:
                # Image is taller than screen
                new_height = screen_height
                new_width = int(screen_height * img_ratio)
                
            # Resize image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(img)
            
            # Create a frame to center the image
            frame = tk.Frame(self.root, bg='black')
            frame.place(relx=0.5, rely=0.5, anchor='center')
            
            # Create and pack label with the image
            self.label = ttk.Label(frame, image=self.photo, background='black')
            self.label.pack()
            
            # Set the display time
            self.media_duration = display_time or DEFAULT_DISPLAY_TIME
            
            # Make window stay on top
            self.root.attributes('-topmost', True)
            self.root.update()
            self.root.attributes('-topmost', False)
            
            # Bind escape key to close
            self.root.bind('<Escape>', lambda e: self._close_window())
            
            # Schedule cleanup using a simple after call
            self.cleanup_timer = self.root.after(self.media_duration * 1000, self._close_window)
            
            # Start the main loop
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            self._cleanup()
            
    def _close_window(self):
        """Close the display window."""
        try:
            if hasattr(self, 'root') and self.root:
                # Cancel any pending timers
                if hasattr(self, 'cleanup_timer') and self.cleanup_timer:
                    self.root.after_cancel(self.cleanup_timer)
                
                # Restore normal cursor
                self.root.config(cursor="")
                self.root.update()
                
                # Quit the mainloop and destroy the window
                self.root.quit()
                self.root.destroy()
                self.root = None
                logger.info("Display window closed automatically")
        except Exception as e:
            logger.error(f"Error closing window: {e}")
        finally:
            self._cleanup()
            
    def _check_should_exit(self):
        """Check if we should exit and clean up if needed."""
        global should_exit
        if should_exit:
            self._cleanup()
            return
        if hasattr(self, 'root') and self.root:
            self.root.after(100, self._check_should_exit)
    
    def play_video(self, video_path: str):
        """Deprecated: Video playback is handled by the separate viewer subprocess."""
        logger.warning("play_video is deprecated; viewer subprocess handles video playback.")
    def _cleanup(self):
        """Clean up resources."""
        try:
            logger.info("Starting cleanup...")
            
            # Clean up photo
            if hasattr(self, 'photo'):
                self.photo = None
            
            # Clean up label
            if hasattr(self, 'label') and self.label:
                try:
                    logger.debug("Destroying label")
                    self.label.pack_forget()
                    self.label.destroy()
                except Exception as e:
                    logger.error(f"Error destroying label: {e}")
                finally:
                    self.label = None
            
            # Clean up root window
            if hasattr(self, 'root') and self.root:
                try:
                    # Cancel any pending cleanup timers
                    if hasattr(self, 'cleanup_timer') and self.cleanup_timer:
                        try:
                            self.root.after_cancel(self.cleanup_timer)
                        except Exception as e:
                            logger.error(f"Error cancelling cleanup timer: {e}")
                    
                    # Restore normal cursor
                    self.root.config(cursor="")
                    self.root.update()
                    
                    # Destroy the window
                    logger.debug("Destroying root window")
                    self.root.destroy()
                except Exception as e:
                    logger.error(f"Error destroying root window: {e}")
                finally:
                    self.root = None
            
            # Force garbage collection
            try:
                import gc
                gc.collect()
                logger.debug("Garbage collection completed")
            except Exception as e:
                logger.error(f"Error during garbage collection: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {e}", exc_info=True)
        finally:
            # Ensure we release any tkinter resources
            try:
                if hasattr(self, 'root') and self.root:
                    self.root.update()
            except Exception as e:
                logger.error(f"Error in final update: {e}")
            logger.info("Cleanup completed")

# Global variables
media_display = MediaDisplay()
should_exit = False  # bot paused flag
_viewer_process: subprocess.Popen | None = None


def _start_viewer_subprocess(kind: str, media_path: str, seconds: int) -> None:
    global _viewer_process

    _stop_viewer_subprocess()

    cmd = [sys.executable, os.path.abspath(__file__), '--viewer', kind, media_path, str(int(seconds))]
    _viewer_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def _ensure_viewer_started_or_report(update: Update, kind: str) -> None:
    # Give the viewer a moment to initialize; if it exits immediately, report.
    await asyncio.sleep(0.35)
    if _viewer_process is None:
        return
    code = _viewer_process.poll()
    if code is None:
        return

    elif kind == 'video':
        if code == 3:
            await update.effective_message.reply_text(
                "❌ Video açılamadı: `opencv-python` kurulu değil.\n"
                "Terminalde şunu çalıştır: `python -m pip install -r requirements.txt`"
            )
        elif code == 4:
            await update.effective_message.reply_text("❌ Video dosyası açılamadı / bozuk olabilir.")
        elif code == 7:
            await update.effective_message.reply_text(
                "❌ Video açılamadı: FFmpeg kurulu değil.\n"
                "macOS için: `brew install ffmpeg`\n"
                "Windows/Linux için: FFmpeg indirip kurun"
            )
        elif code == 8:
            await update.effective_message.reply_text("❌ Video oynatma hatası.")
        else:
            await update.effective_message.reply_text("❌ Video viewer başlatılamadı.")
    elif kind == 'audio':
            if code == 5:
                await update.effective_message.reply_text(
                    "❌ Ses açılamadı: Ses kütüphanesi kurulu değil.\n"
                    "macOS için: afplay zaten kurulu olmalı\n"
                    "Windows/Linux için: FFmpeg kurun"
                )
            elif code == 6:
                await update.effective_message.reply_text("❌ Ses dosyası açılamadı / bozuk olabilir.")
            else:
                await update.effective_message.reply_text("❌ Ses oynatıcı başlatılamadı.")
    else:
        await update.effective_message.reply_text("❌ Görsel viewer başlatılamadı.")


def _stop_viewer_subprocess() -> None:
    global _viewer_process
    if _viewer_process is None:
        return
    try:
        if _viewer_process.poll() is None:
            # Preferred: viewer listens SIGUSR1 for remote cancel.
            if hasattr(signal, 'SIGUSR1'):
                try:
                    _viewer_process.send_signal(signal.SIGUSR1)
                except Exception:
                    pass

            try:
                _viewer_process.wait(timeout=2)
            except Exception:
                # Fallback
                try:
                    _viewer_process.terminate()
                except Exception:
                    pass
                try:
                    _viewer_process.wait(timeout=2)
                except Exception:
                    try:
                        _viewer_process.kill()
                    except Exception:
                        pass
    finally:
        _viewer_process = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı /start komutunu gönderdiğinde bir karşılama mesajı gönderir."""
    if not _is_authorized(update):
        return
        
    user = update.effective_user
    welcome_message = (
        f"👋 Merhaba {user.first_name}!\n\n"
        "📸 Bana bir resim veya video gönderin, tam ekran olarak göstereyim.\n"
        "🎵 MP3 ses dosyalarını arka planda çalabilirim.\n"
        "⏱️ Görüntüleme süresini ayarla: /sure 10\n"
        "🧹 Aktif görüntüyü/sesi kapat: /iptal\n"
        "🔒 Görüntü açıkken yerelden kapatma engellenir (süre bitene kadar).\n"
        "⏹️  Acil durdur: /durdur\n"
        "▶️ Devam ettir: /devam\n"
        "🧨 Programı kapat: /kapat\n"
        "ℹ️  Durum kontrolü: /durum\n"
        "❓ Tüm komutlar: /yardim"
    )
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı /yardim komutunu gönderdiğinde yardım mesajı gönderir."""
    if not _is_authorized(update):
        return
        
    help_text = """
<b>Kullanılabilir Komutlar:</b>
/basla - Botu başlat ve hoşgeldin mesajını göster
/yardim - Bu yardım mesajını göster
/sure [saniye] - Görüntüleme süresini saniye cinsinden ayarla (varsayılan: 10)
/durum - Bot durumunu göster
/iptal - Açık olan görüntüyü/sesi kapat (sadece viewer kapanır)
/durdur - Botu duraklat (yeni medya kabul etmez)
/devam - Botu tekrar aktif et
/kapat - Ana programı kapat

<b>Kullanım:</b>
- Tam ekranda göstermek için bir resim gönderin
- Sesli video göstermek için bir video gönderin
- Arka planda ses çalmak için MP3 dosyası gönderin
- Görsel/video/ses belirtilen süre boyunca gösterilecek, sonra sadece görüntü penceresi kapanacak
- Görüntü açıkken yerelden kapatma (Cmd+Q / Alt+F4 vb.) best-effort engellenir
- Acil durumda Telegram'dan /iptal her zaman çalışır
- Yerel acil çıkış: Ctrl+Shift+Esc
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def set_display_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Medya için görüntüleme süresini ayarlar."""
    global DEFAULT_DISPLAY_TIME
    
    if not _is_authorized(update):
        return
        
    try:
        if not context.args:
            await update.message.reply_text(f"Mevcut görüntüleme süresi: {DEFAULT_DISPLAY_TIME} saniye")
            return
            
        seconds = int(context.args[0])
        if seconds < 1 or seconds > 3600:  # 1 saniye ile 1 saat arasında sınırla
            await update.message.reply_text("Lütfen 1 ile 3600 saniye arasında bir süre belirtin.")
            return
            
        DEFAULT_DISPLAY_TIME = seconds
        await update.message.reply_text(f"Görüntüleme süresi {seconds} saniye olarak ayarlandı.")
        
    except (IndexError, ValueError):
        await update.message.reply_text("Kullanım: /sure [saniye]")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mevcut durumu gösterir."""
    if not _is_authorized(update):
        return
        
    viewer_running = _viewer_process is not None and _viewer_process.poll() is None
    video_status = "Evet (OpenCV)" if VIDEO_AVAILABLE else "Hayır (opencv-python kurulu değil)"
    audio_status = "Evet (Sistem ses)" if AUDIO_AVAILABLE else "Hayır (ses kütüphanesi yok)"
    paused_status = "Evet" if should_exit else "Hayır"
    status_message = (
        "📊 Bot Durumu\n"
        f"🔄 Bot aktif: {'Hayır' if should_exit else 'Evet'}\n"
        f"⏸️ Duraklatıldı: {paused_status}\n"
        f"🖼️ Viewer açık: {'Evet' if viewer_running else 'Hayır'}\n"
        f"⏱️ Görüntüleme süresi: {DEFAULT_DISPLAY_TIME} saniye\n"
        f"🎥 Video oynatma: {video_status}\n"
        f"🎵 Ses oynatma: {audio_status}"
    )
    
    await update.message.reply_text(status_message)

async def emergency_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Botu duraklatır (ana program çalışmaya devam eder)."""
    if not _is_authorized(update):
        return
        
    global should_exit
    should_exit = True
    _stop_viewer_subprocess()
    await update.message.reply_text("⏸️ Bot duraklatıldı. /devam ile tekrar açabilirsiniz.")
    logger.info("Bot kullanıcı tarafından duraklatıldı.")

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Botu tekrar aktif eder."""
    if not _is_authorized(update):
        return
        
    global should_exit
    should_exit = False
    
    await update.message.reply_text("✅ Bot tekrar aktif!")
    logger.info("Bot kullanıcı tarafından tekrar aktif edildi.")
    
    # Kullanıcıya başlangıç mesajını gönder
    await start(update, context)


async def cancel_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sadece görüntü penceresini veya ses çalmayı kapatır."""
    if not _is_authorized(update):
        return
    _stop_viewer_subprocess()
    await update.message.reply_text("🧹 Görüntü/ses kapatıldı.")


async def shutdown_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ana programı kapatır."""
    if not _is_authorized(update):
        return
    _stop_viewer_subprocess()
    await update.message.reply_text("🧨 Program kapatılıyor...")
    logger.info("Bot kullanıcı tarafından kapatıldı.")
    os._exit(0)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gelen fotoğraf, videoları ve ses dosyalarını işler."""
    if not _is_authorized(update):
        return
    
    # Check if bot is stopped
    global should_exit
    if should_exit:
        await update.message.reply_text("⛔ Bot şu anda duraklatılmış durumda. /devam komutu ile tekrar aktif edebilirsiniz.")
        return
        
    file_path = None
    try:
        logger.info(f"Processing media from {update.effective_user.id}")

        if update.message.photo:
            file = await update.message.photo[-1].get_file()
            file_extension = os.path.splitext(file.file_path or '')[-1] or '.jpg'
            file_path = os.path.join(tempfile.gettempdir(), f"hack_photo_{int(time.time())}{file_extension}")
            await file.download_to_drive(file_path)

            _start_viewer_subprocess('image', file_path, DEFAULT_DISPLAY_TIME)
            await update.message.reply_text("✅ Görsel gösteriliyor (viewer açıldı).")
            await _ensure_viewer_started_or_report(update, 'image')
            return

        if update.message.document:
            mime_type = update.message.document.mime_type or ''
            file_name = update.message.document.file_name or ''
            file_extension = os.path.splitext(file_name)[-1].lower()
            
            if 'image' in mime_type:
                file = await update.message.document.get_file()
                file_extension = os.path.splitext(file_name)[-1] or '.jpg'
                file_path = os.path.join(tempfile.gettempdir(), f"hack_doc_{int(time.time())}{file_extension}")
                await file.download_to_drive(file_path)
                _start_viewer_subprocess('image', file_path, DEFAULT_DISPLAY_TIME)
                await update.message.reply_text("✅ Görsel gösteriliyor (viewer açıldı).")
                await _ensure_viewer_started_or_report(update, 'image')
                return
            
            # Handle audio files (MP3, WAV, etc.)
            elif 'audio' in mime_type or file_extension in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
                file = await update.message.document.get_file()
                file_path = os.path.join(tempfile.gettempdir(), f"hack_audio_{int(time.time())}{file_extension}")
                await file.download_to_drive(file_path)
                _start_viewer_subprocess('audio', file_path, DEFAULT_DISPLAY_TIME)
                await update.message.reply_text("🎵 Ses dosyası çalınıyor (arka planda).")
                await _ensure_viewer_started_or_report(update, 'audio')
                return

        if update.message.video:
            file = await update.message.video.get_file()
            file_extension = os.path.splitext(file.file_path or '')[-1] or '.mp4'
            file_path = os.path.join(tempfile.gettempdir(), f"hack_video_{int(time.time())}{file_extension}")
            await file.download_to_drive(file_path)
            _start_viewer_subprocess('video', file_path, DEFAULT_DISPLAY_TIME)
            await update.message.reply_text("✅ Video gösteriliyor (sesli, viewer açıldı).")
            await _ensure_viewer_started_or_report(update, 'video')
            return

        # Handle audio messages (voice notes)
        if update.message.audio:
            file = await update.message.audio.get_file()
            file_extension = os.path.splitext(update.message.audio.file_name or '')[-1] or '.mp3'
            file_path = os.path.join(tempfile.gettempdir(), f"hack_voice_{int(time.time())}{file_extension}")
            await file.download_to_drive(file_path)
            _start_viewer_subprocess('audio', file_path, DEFAULT_DISPLAY_TIME)
            await update.message.reply_text("🎵 Ses mesajı çalınıyor (arka planda).")
            await _ensure_viewer_started_or_report(update, 'audio')
            return

        # Handle voice notes
        if update.message.voice:
            file = await update.message.voice.get_file()
            file_path = os.path.join(tempfile.gettempdir(), f"hack_voice_{int(time.time())}.ogg")
            await file.download_to_drive(file_path)
            _start_viewer_subprocess('audio', file_path, DEFAULT_DISPLAY_TIME)
            await update.message.reply_text("🎵 Sesli mesaj çalınıyor (arka planda).")
            await _ensure_viewer_started_or_report(update, 'audio')
            return

        await update.message.reply_text("❌ Lütfen bir resim, video, ses dosyası veya sesli mesaj gönderin.")

    except Exception as e:
        logger.error(f"Error processing media: {e}", exc_info=True)
        await update.message.reply_text("❌ Medya işlenirken hata oluştu.")
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

def _is_authorized(update: Update) -> bool:
    """Kullanıcının botu kullanmaya yetkili olup olmadığını kontrol eder."""
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        logger.warning(f"Yetkisiz erişim denemesi: Kullanıcı ID {user_id}")
        return False
    return True

def main() -> None:
    """Botu başlat."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Telegram bot token'ı bulunamadı. Lütfen TELEGRAM_BOT_TOKEN ortam değişkenini ayarlayın.")
        return
    
    if not AUTHORIZED_USERS:
        logger.warning("Yetkili kullanıcı belirtilmemiş. Bot hiçbir kullanıcıya yanıt vermeyecek.")
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler(["start", "basla"], start))
    application.add_handler(CommandHandler(["help", "yardim"], help_command))
    application.add_handler(CommandHandler(["time", "sure"], set_display_time))
    application.add_handler(CommandHandler(["status", "durum"], status))
    application.add_handler(CommandHandler(["cancel", "iptal"], cancel_view))
    application.add_handler(CommandHandler(["stop", "durdur"], emergency_stop))
    application.add_handler(CommandHandler(["resume", "devam", "restart", "yenidenbaslat"], start_bot))
    application.add_handler(CommandHandler(["shutdown", "kapat"], shutdown_bot))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VIDEO_NOTE | filters.AUDIO | filters.VOICE | filters.Document.ALL, handle_media))
    
    # Log any errors
    application.add_error_handler(error_handler)
    
    # Bot menüsü için komutları ayarla
    commands = [
        BotCommand("start", "Botu başlat"),
        BotCommand("help", "Yardım mesajını göster"),
        BotCommand("time", "Görüntüleme süresini ayarla"),
        BotCommand("status", "Bot durumunu göster"),
        BotCommand("cancel", "Görüntüyü kapat"),
        BotCommand("stop", "Botu duraklat"),
        BotCommand("resume", "Botu devam ettir"),
        BotCommand("shutdown", "Programı kapat")
    ]
    
    # Set up the bot commands
    async def post_init(application):
        await application.bot.set_my_commands(commands)
    
    application.post_init = post_init
    
    # Botu başlat
    logger.info("Bot başlatılıyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Güncellemelerden kaynaklanan hataları kaydeder."""
    logger.error(f"Hata: {context.error}", exc_info=context.error)
    
    # Sadece yetkili kullanıcılardan gelen hatalar için mesaj gönder
    if isinstance(update, Update) and update.effective_message and _is_authorized(update):
        await update.effective_message.reply_text(
            "❌ İsteğiniz işlenirken bir hata oluştu. Hata kaydedildi."
        )

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == '--viewer':
        raise SystemExit(_viewer_main(sys.argv))
    main()
