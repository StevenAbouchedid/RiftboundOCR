# Troubleshooting Guide

Common issues and solutions for RiftboundOCR setup.

---

## 🔴 **Error: "Error loading torch\lib\shm.dll or one of its dependencies"**

### **Problem**

```
OSError: [WinError 127] The specified procedure could not be found. 
Error loading "C:\...\torch\lib\shm.dll" or one of its dependencies.
```

### **Cause**

PyTorch requires **Microsoft Visual C++ Redistributable**, which is missing or outdated on your system.

### **Solution**

#### **Option 1: Install Visual C++ Redistributable (Recommended)**

1. **Download** (5MB, 30 second install):
   - https://aka.ms/vs/17/release/vc_redist.x64.exe
   
2. **Run the installer**

3. **Restart your terminal**

4. **Try again:**
   ```powershell
   cd C:\Users\Steb\Documents\GitHub\RiftboundOCR
   .\venv\Scripts\activate
   $env:PYTHONPATH=(Get-Location).Path
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8002
   ```

#### **Option 2: Automated Install (PowerShell as Admin)**

```powershell
# Run PowerShell as Administrator
$url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
$output = "$env:TEMP\vc_redist.x64.exe"
Invoke-WebRequest -Uri $url -OutFile $output
Start-Process -FilePath $output -ArgumentList "/install", "/quiet", "/norestart" -Wait
Write-Host "✓ Installed! Restart your terminal."
```

#### **Option 3: Verify Installation**

After installing, check if it's present:

```powershell
Get-ItemProperty HKLM:\SOFTWARE\Microsoft\VisualStudio\*\VC\Runtimes\X64 | Select-Object PSChildName,Version
```

Should show: `Microsoft Visual C++ 2015-2022 Redistributable (x64)`

---

## 🔴 **Error: "No module named 'src'"**

### **Problem**

```
ModuleNotFoundError: No module named 'src'
```

### **Solution**

Set `PYTHONPATH` before running:

```powershell
# Windows PowerShell
$env:PYTHONPATH=(Get-Location).Path
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002

# Or use run_local.py (handles this automatically)
python run_local.py
```

---

## 🔴 **Error: Server crashes with --reload flag**

### **Problem**

Server crashes when using `--reload` flag due to Windows multiprocessing issues with PyTorch DLLs.

### **Solution**

**Don't use `--reload` for development on Windows:**

```powershell
# ✗ BAD (crashes on Windows)
python -m uvicorn src.main:app --reload

# ✓ GOOD
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002
```

For development, just restart the server manually when you make changes.

---

## 🔴 **Python 3.13 Compatibility Issues**

### **Problem**

```
ERROR: Cannot install paddleocr 2.9.1 and numpy>=2.0.0
The conflict is caused by: paddleocr 2.9.1 depends on numpy<2.0
```

### **Solution**

**Use Python 3.11 or 3.12** (not 3.13):

```powershell
# Check available versions
py --list

# Create venv with Python 3.12
Remove-Item -Recurse -Force venv
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Why?**
- Python 3.13 requires numpy≥2.1
- paddleocr 2.9.1 requires numpy<2.0
- **Incompatible!**

---

## 🔴 **Port 8002 Already in Use**

### **Problem**

```
OSError: [WinError 10048] Only one usage of each socket address is normally permitted
```

### **Solution**

#### **Find what's using the port:**

```powershell
netstat -ano | findstr :8002
```

#### **Kill the process:**

```powershell
# Get the PID from above command, then:
taskkill /PID <PID> /F
```

#### **Or use a different port:**

```powershell
python -m uvicorn src.main:app --host 0.0.0.0 --port 8003
```

---

## 🔴 **Virtual Environment Not Activating**

### **Problem**

```
venv\Scripts\activate : File cannot be loaded because running scripts is disabled
```

### **Solution**

Allow script execution:

```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again:

```powershell
venv\Scripts\activate
```

---

## 🔴 **Dependencies Won't Install**

### **Problem**

```
ERROR: Could not find a version that satisfies the requirement...
```

### **Solution**

1. **Upgrade pip:**
   ```powershell
   python -m pip install --upgrade pip
   ```

2. **Use Python 3.12** (not 3.13)

3. **Clear pip cache:**
   ```powershell
   pip cache purge
   pip install -r requirements.txt
   ```

---

## 🔴 **Out of Memory During Installation**

### **Problem**

Installation crashes or system freezes when installing PyTorch/PaddleOCR.

### **Solution**

Install packages one at a time:

```powershell
# Install large packages first
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install paddlepaddle==3.0.0
pip install paddleocr==2.9.1
pip install easyocr==1.7.2

# Then install the rest
pip install -r requirements.txt
```

---

## ✅ **Verify Everything Works**

### **Test 1: Check Python & Venv**

```powershell
python --version  # Should show 3.12.x
pip list | findstr torch  # Should show torch 2.9.1
```

### **Test 2: Test Imports**

```powershell
python -c "import torch; print('Torch OK')"
python -c "import easyocr; print('EasyOCR OK')"
python -c "from src.ocr.parser import DecklistParser; print('Parser OK')"
```

### **Test 3: Run Minimal Server**

```powershell
python test_server_minimal.py
```

Visit: http://localhost:8002/health

### **Test 4: Run Full Server**

```powershell
$env:PYTHONPATH=(Get-Location).Path
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002
```

Visit: http://localhost:8002/docs

### **Test 5: Run Quick Test**

```powershell
python test_local.py --quick
```

---

## 📊 **Common Setup Checklist**

Before asking for help, verify:

- [ ] Python 3.11 or 3.12 installed (not 3.13)
- [ ] Virtual environment created with correct Python version
- [ ] Virtual environment activated (`(venv)` in prompt)
- [ ] Visual C++ Redistributable installed
- [ ] All dependencies installed (`pip list` shows torch, paddleocr, easyocr)
- [ ] `.env` file exists
- [ ] `resources/card_mappings_final.csv` exists
- [ ] Port 8002 is available
- [ ] `PYTHONPATH` environment variable set when running

---

## 🆘 **Still Having Issues?**

### **Collect Diagnostic Info:**

```powershell
# System info
python --version
pip --version
py --list

# Dependency info
pip list

# Test imports
python -c "import torch; print(torch.__version__)"
python -c "import paddleocr; print('PaddleOCR OK')"
python -c "import easyocr; print('EasyOCR OK')"

# Check Visual C++ Redistributable
Get-ItemProperty HKLM:\SOFTWARE\Microsoft\VisualStudio\*\VC\Runtimes\X64
```

### **Test Minimal Server:**

```powershell
python test_server_minimal.py
```

If the minimal server works but full server doesn't, it's definitely the VC++ Redistributable issue.

---

## 🔗 **Quick Links**

| Resource | Link |
|----------|------|
| **Visual C++ Redistributable** | https://aka.ms/vs/17/release/vc_redist.x64.exe |
| **Python 3.12 Download** | https://www.python.org/downloads/ |
| **PyTorch Installation Guide** | https://pytorch.org/get-started/locally/ |
| **Project README** | README.md |
| **Quick Start Guide** | QUICK_START.md |
| **Local Development Guide** | LOCAL_DEVELOPMENT.md |

---

## 📝 **Success Indicators**

You'll know everything is working when:

1. ✅ Server starts without errors
2. ✅ You see: `INFO: Uvicorn running on http://0.0.0.0:8002`
3. ✅ Health endpoint responds: http://localhost:8002/api/v1/health
4. ✅ API docs load: http://localhost:8002/docs
5. ✅ No DLL errors in console
6. ✅ OCR models load successfully

---

**Last Updated:** November 12, 2025  
**Tested On:** Windows 10/11, Python 3.12




