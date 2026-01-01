#!/usr/bin/env python3
"""
Cross-platform setup script for Telegram Bot
Automatically installs dependencies and sets up virtual environment
"""

import os
import sys
import subprocess
import platform
import urllib.request
import json
from pathlib import Path

def run_command(cmd, check=True, capture_output=False):
    """Run command with proper error handling"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {e}")
        return None

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required. Please upgrade Python.")
        return False
    
    return True

def setup_virtual_environment():
    """Create and activate virtual environment"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        result = run_command(f"{sys.executable} -m venv venv")
        if not result:
            return False
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    return True

def get_pip_command():
    """Get appropriate pip command for the platform"""
    system = platform.system().lower()
    
    if system == "windows":
        return "venv\\Scripts\\pip"
    else:
        return "venv/bin/pip"

def get_python_command():
    """Get appropriate python command for the platform"""
    system = platform.system().lower()
    
    if system == "windows":
        return "venv\\Scripts\\python"
    else:
        return "venv/bin/python"

def install_dependencies():
    """Install required Python packages"""
    print("📚 Installing Python dependencies...")
    
    pip_cmd = get_pip_command()
    
    # Upgrade pip first
    print("🔄 Upgrading pip...")
    run_command(f"{pip_cmd} install --upgrade pip", check=False)
    
    # Install requirements
    print("📦 Installing requirements...")
    result = run_command(f"{pip_cmd} install -r requirements.txt")
    if not result:
        return False
    
    print("✅ Dependencies installed")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    system = platform.system().lower()
    
    if system == "windows":
        ffmpeg_cmd = "ffmpeg.exe"
        ffplay_cmd = "ffplay.exe"
    else:
        ffmpeg_cmd = "ffmpeg"
        ffplay_cmd = "ffplay"
    
    ffmpeg_exists = run_command(f"which {ffmpeg_cmd}" if system != "windows" else f"where {ffmpeg_cmd}", check=False)
    ffplay_exists = run_command(f"which {ffplay_cmd}" if system != "windows" else f"where {ffplay_cmd}", check=False)
    
    return ffmpeg_exists is not None and ffplay_exists is not None

def install_ffmpeg():
    """Install FFmpeg based on platform"""
    system = platform.system().lower()
    
    print("🎬 Installing FFmpeg...")
    
    if system == "darwin":  # macOS
        # Check if Homebrew is installed
        brew_exists = run_command("which brew", check=False)
        if not brew_exists:
            print("🍺 Installing Homebrew...")
            install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            result = run_command(install_cmd)
            if not result:
                print("❌ Failed to install Homebrew. Please install manually.")
                return False
        
        # Install FFmpeg
        result = run_command("brew install ffmpeg")
        return result is not None
        
    elif system == "windows":
        print("🪟 Windows FFmpeg installation:")
        print("1. Download FFmpeg from: https://ffmpeg.org/download.html#build-windows")
        print("2. Extract to C:\\ffmpeg")
        print("3. Add C:\\ffmpeg\\bin to PATH environment variable")
        print("4. Restart command prompt")
        
        # Try to download and extract FFmpeg automatically
        try:
            print("🔄 Attempting automatic FFmpeg installation...")
            ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            
            import zipfile
            import tempfile
            
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "ffmpeg.zip")
                print("📥 Downloading FFmpeg...")
                urllib.request.urlretrieve(ffmpeg_url, zip_path)
                
                print("📂 Extracting FFmpeg...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find ffmpeg directory
                ffmpeg_dir = None
                for item in os.listdir(temp_dir):
                    if item.startswith("ffmpeg"):
                        ffmpeg_dir = os.path.join(temp_dir, item)
                        break
                
                if ffmpeg_dir:
                    # Copy to local directory
                    local_ffmpeg = Path("ffmpeg")
                    local_ffmpeg.mkdir(exist_ok=True)
                    
                    import shutil
                    for item in os.listdir(ffmpeg_dir):
                        s = os.path.join(ffmpeg_dir, item)
                        d = os.path.join(local_ffmpeg, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                    
                    print("✅ FFmpeg installed locally")
                    return True
            
        except Exception as e:
            print(f"❌ Automatic installation failed: {e}")
            print("Please install FFmpeg manually")
            return False
        
    else:  # Linux
        # Try different package managers
        package_managers = [
            ("apt-get", "sudo apt-get update && sudo apt-get install -y ffmpeg"),
            ("yum", "sudo yum install -y ffmpeg"),
            ("dnf", "sudo dnf install -y ffmpeg"),
            ("pacman", "sudo pacman -S ffmpeg"),
        ]
        
        for pm, cmd in package_managers:
            pm_exists = run_command(f"which {pm}", check=False)
            if pm_exists:
                print(f"📦 Using {pm} to install FFmpeg...")
                result = run_command(cmd)
                return result is not None
        
        print("❌ No supported package manager found. Please install FFmpeg manually.")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("📝 Creating .env file template...")
        
        with open(env_file, "w") as f:
            f.write("""# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
AUTHORIZED_USERS=YOUR_USER_ID_HERE

# Display Settings
DEFAULT_DISPLAY_TIME=10
LOG_FILE=screen_display.log
""")
        
        print("✅ .env file created")
        print("⚠️  Please edit .env file and add your bot token and user ID")
        return True
    else:
        print("✅ .env file already exists")
        return True

def create_startup_scripts():
    """Create platform-specific startup scripts"""
    system = platform.system().lower()
    
    if system == "windows":
        # Create batch file
        with open("start_bot.bat", "w") as f:
            f.write("""@echo off
echo Starting Telegram Bot...
call venv\\Scripts\\activate.bat
python screen_display_bot.py
pause
""")
        print("✅ Created start_bot.bat")
        
    else:
        # Create shell script
        with open("start_bot.sh", "w") as f:
            f.write("""#!/bin/bash
echo "Starting Telegram Bot..."
source venv/bin/activate
python screen_display_bot.py
""")
        os.chmod("start_bot.sh", 0o755)
        print("✅ Created start_bot.sh")

def main():
    """Main setup function"""
    print("🚀 Telegram Bot Setup - Cross Platform")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Setup virtual environment
    if not setup_virtual_environment():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check and install FFmpeg
    if not check_ffmpeg():
        print("⚠️  FFmpeg not found. Installing...")
        if not install_ffmpeg():
            print("❌ FFmpeg installation failed. Please install manually.")
            return False
    
    # Create .env file
    create_env_file()
    
    # Create startup scripts
    create_startup_scripts()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your bot token and user ID")
    print("2. Run start_bot.bat (Windows) or start_bot.sh (Mac/Linux)")
    print("\n🔧 To run manually:")
    system = platform.system().lower()
    if system == "windows":
        print("   venv\\Scripts\\activate")
        print("   python screen_display_bot.py")
    else:
        print("   source venv/bin/activate")
        print("   python screen_display_bot.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
