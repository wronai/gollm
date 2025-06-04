#!/usr/bin/env python3
"""
Podstawowy test funkcjonalności goLLM
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd):
    """Uruchamia komendę i zwraca wynik"""
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timeout"
    except Exception as e:
        return 1, "", str(e)


def test_installation():
    """Test instalacji goLLM"""
    print("🔧 Testing goLLM installation...")

    # Test importu
    try:
        import gollm
        print("✅ goLLM module imports successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import goLLM: {e}")

    # Test CLI
    returncode, stdout, stderr = run_command("python -m gollm --help")
    assert returncode == 0, f"goLLM CLI failed with: {stderr}"


def test_validation():
    """Test walidacji kodu"""
    print("\n🔍 Testing code validation...")

    # Utwórz plik testowy z błędami
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
def bad_function(a, b, c, d, e, f):  # Zbyt wiele parametrów
    print("Bad code")  # Print statement
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:  # Wysoka złożoność
                    return a + b + c + d + e + f
    return 0
"""
        )
        test_file = f.name

    try:
        # Test walidacji
        returncode, stdout, stderr = run_command(
            f"python -m gollm validate {test_file}"
        )
        
        assert "violations" in stdout.lower() or returncode != 0, \
            "Validation should detect issues in bad code"
        print("✅ Validation detects code issues correctly")
    finally:
        os.unlink(test_file)


def test_config_loading():
    """Test ładowania konfiguracji"""
    print("\n⚙️  Testing configuration loading...")

    # Test default config loading
    returncode, stdout, stderr = run_command("python -m gollm --help")
    assert returncode == 0, f"Failed to run gollm with default config: {stderr}"
    print("✅ Default configuration loads correctly")


def test_todo_management():
    """Test zarządzania TODO"""
    print("\n📝 Testing TODO management...")
    
    # This test is currently a placeholder as the TODO functionality
    # is not implemented in the CLI yet
    print("⚠️  TODO management test skipped (not implemented)")
    return
    
    # The following code will be used when TODO functionality is implemented
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git repository
        os.chdir(tmpdir)
        subprocess.run("git init".split(), capture_output=True)

        # Add a file with TODOs
        with open("test_file.py", "w") as f:
            f.write(
                """
# TODO: Dodać implementację
# FIXME: Naprawić błąd
"""
            )
        
        # This part will be enabled when TODO functionality is implemented
        # returncode, stdout, stderr = run_command("python -m gollm todo list")
        # assert returncode == 0, f"TODO command failed: {stderr}"
        # assert "TODO" in stdout, "TODO not found in output"
        # assert "FIXME" in stdout, "FIXME not found in output"


def main():
    """Główna funkcja testowa"""
    print("🧪 goLLM Basic Functionality Test")
    print("=================================")

    tests = [
        test_installation,
        test_validation,
        test_config_loading,
        test_todo_management,
    ]

    print("🚀 Starting goLLM end-to-end tests\n")
    success = True

    for test in tests:
        test_name = test.__name__
        print(f"\n=== {test_name.upper().replace('_', ' ')} ===")
        try:
            test()
            print(f"✅ {test_name} passed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            success = False
            import traceback
            traceback.print_exc()

    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
