# Windows Setup Guide for Media Monitoring Agent

This guide provides Windows-specific instructions for setting up the Media Monitoring Agent.

## Prerequisites

### 1. Python Installation
- Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
- **Important**: During installation, check "Add Python to PATH"
- Verify installation:
  ```cmd
  python --version
  pip --version
  ```

### 2. Microsoft Visual C++ Build Tools (if needed)
If you encounter compilation errors, install Visual C++ Build Tools:
- Download from [Microsoft Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Install "C++ build tools" workload

## Installation Steps

### 1. Clone or Download the Project
```cmd
git clone https://github.com/mistry247/media-monitoring-agent.git
cd media-monitoring-agent
```

### 2. Create Virtual Environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Upgrade pip and setuptools
```cmd
python -m pip install --upgrade pip setuptools wheel
```

### 4. Install Dependencies
```cmd
pip install -r requirements.txt
```

If you still encounter Rust-related errors, try installing with pre-compiled wheels only:
```cmd
pip install --only-binary=all -r requirements.txt
```

### 5. Configure the Application
```cmd
copy .env.example .env
notepad .env
```
Edit the `.env` file with your configuration (see main README for details).

### 6. Initialize Database
```cmd
python migrate.py migrate
```

### 7. Run the Application
```cmd
python main.py
```

## Troubleshooting Windows Issues

### Issue 1: "Microsoft Visual C++ 14.0 is required"
**Solution:**
1. Install Microsoft Visual C++ Build Tools
2. Or use pre-compiled wheels: `pip install --only-binary=all -r requirements.txt`

### Issue 2: "error: Microsoft Visual C++ 14.0 or greater is required"
**Solution:**
```cmd
pip install --upgrade pip setuptools wheel
pip install --only-binary=all pydantic fastapi
pip install -r requirements.txt
```

### Issue 3: "Rust compiler not found"
**Solution:**
The updated requirements.txt uses pydantic versions with pre-compiled wheels. If you still see this error:
```cmd
pip install --only-binary=pydantic,pydantic-core -r requirements.txt
```

### Issue 4: PowerShell Execution Policy Error
If you can't activate the virtual environment:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

### Issue 5: Path Issues
If Python or pip commands aren't found:
1. Add Python to PATH during installation
2. Or use full paths:
   ```cmd
   C:\Users\YourName\AppData\Local\Programs\Python\Python39\python.exe -m pip install -r requirements.txt
   ```

## Alternative Installation Methods

### Method 1: Using Conda (Recommended for Windows)
```cmd
# Install Miniconda from https://docs.conda.io/en/latest/miniconda.html
conda create -n media-monitoring python=3.9
conda activate media-monitoring
pip install -r requirements.txt
```

### Method 2: Using Docker (Easiest)
```cmd
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
docker-compose up -d
```

## Running on Windows

### Development Mode
```cmd
venv\Scripts\activate
python main.py
```

### As Windows Service (Advanced)
1. Install NSSM (Non-Sucking Service Manager)
2. Create service:
   ```cmd
   nssm install MediaMonitoring
   nssm set MediaMonitoring Application "C:\path\to\venv\Scripts\python.exe"
   nssm set MediaMonitoring AppParameters "C:\path\to\main.py"
   nssm set MediaMonitoring AppDirectory "C:\path\to\media-monitoring-agent"
   nssm start MediaMonitoring
   ```

## Windows-Specific Configuration

### File Paths in .env
Use forward slashes or double backslashes:
```env
# Good
DATABASE_URL=sqlite:///C:/data/media_monitoring.db
LOG_FILE=C:/logs/media_monitoring.log

# Also good
DATABASE_URL=sqlite:///C:\\data\\media_monitoring.db
LOG_FILE=C:\\logs\\media_monitoring.log
```

### Windows Firewall
If accessing from other machines, allow Python through Windows Firewall:
1. Windows Security → Firewall & network protection
2. Allow an app through firewall
3. Add Python.exe

## Performance Tips for Windows

1. **Use SSD storage** for better SQLite performance
2. **Exclude project folder** from Windows Defender real-time scanning
3. **Use Windows Terminal** for better command-line experience
4. **Consider WSL2** for Linux-like environment on Windows

## Getting Help

If you continue to have issues:
1. Check the main README.md troubleshooting section
2. Ensure you're using the latest Python version
3. Try the Docker installation method as an alternative
4. Check Windows Event Viewer for system-level errors