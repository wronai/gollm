
# run_demo.bat
@echo off
echo 🚀 SPYQ - Smart Python Quality Guardian Demo
echo ==============================================

REM Sprawdź czy Python jest zainstalowany
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed
    pause
    exit /b 1
)

REM Utwórz wirtualne środowisko jeśli nie istnieje
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Aktywuj wirtualne środowisko
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Zainstaluj SPYQ
echo ⬇️  Installing SPYQ...
pip install -e .

echo.
echo 🎯 SPYQ Demo - Code Quality in Action
echo ======================================

echo.
echo 1️⃣  Validating BAD code example...
echo -----------------------------------
python -m spyq validate examples\bad_code.py

echo.
echo 2️⃣  Validating GOOD code example...
echo ------------------------------------
python -m spyq validate examples\good_code.py

echo.
echo 3️⃣  Project status overview...
echo ------------------------------
python -m spyq status

echo.
echo 4️⃣  Next TODO task...
echo --------------------
python -m spyq next-task

echo.
echo 🎉 Demo completed!
echo.
echo 💡 Try these commands:
echo    spyq validate-project    # Validate entire project
echo    spyq generate "create user class"  # Generate code with LLM
echo    spyq fix --auto         # Auto-fix violations
echo    spyq --help             # Show all commands

pause
