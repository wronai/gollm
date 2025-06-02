
#!/usr/bin/env python3
"""
Podstawowy test funkcjonalności goLLM
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

def run_command(cmd):
    """Uruchamia komendę i zwraca wynik"""
    try:
        result = subprocess.run(
            cmd.split(), 
            capture_output=True, 
            text=True, 
            timeout=30
        )
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
        print(f"❌ Failed to import goLLM: {e}")
        return False
    
    # Test CLI
    returncode, stdout, stderr = run_command("python -m gollm --help")
    if returncode == 0:
        print("✅ goLLM CLI works")
    else:
        print(f"❌ goLLM CLI failed: {stderr}")
        return False
    
    return True

def test_validation():
    """Test walidacji kodu"""
    print("\n🔍 Testing code validation...")
    
    # Utwórz plik testowy z błędami
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
def bad_function(a, b, c, d, e, f):  # Zbyt wiele parametrów
    print("Bad code")  # Print statement
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:  # Wysoka złożoność
                    return a + b + c + d + e + f
    return 0
''')
        test_file = f.name
    
    try:
        # Test walidacji
        returncode, stdout, stderr = run_command(f"python -m gollm validate {test_file}")
        
        if "violations" in stdout.lower() or returncode != 0:
            print("✅ Validation detects code issues correctly")
        else:
            print("❌ Validation should detect issues in bad code")
            return False
            
    finally:
        os.unlink(test_file)
    
    return True

def test_config_loading():
    """Test ładowania konfiguracji"""
    print("\n⚙️  Testing configuration loading...")
    
    # Utwórz tymczasową konfigurację
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('''
{
  "validation_rules": {
    "max_function_lines": 25,
    "forbid_print_statements": true
  }
}
''')
        config_file = f.name
    
    try:
        # Test ładowania konfiguracji
        from gollm.config.config import GollmConfig
        config = GollmConfig.load(config_file)
        
        if config.validation_rules.max_function_lines == 25:
            print("✅ Configuration loads correctly")
        else:
            print("❌ Configuration not loaded properly")
            return False
            
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False
    finally:
        os.unlink(config_file)
    
    return True

def test_todo_management():
    """Test zarządzania TODO"""
    print("\n📋 Testing TODO management...")
    
    try:
        from gollm.project_management.todo_manager import TodoManager
        from gollm.config.config import GollmConfig
        
        # Użyj domyślnej konfiguracji
        config = GollmConfig.default()
        config.project_management.todo_file = "test_todo.md"
        
        todo_manager = TodoManager(config)
        
        # Test dodawania zadania
        task = todo_manager.add_task_from_violation(
            "function_too_long",
            {"file_path": "test.py", "line_number": 10, "message": "Function too long"}
        )
        
        if task and task.title:
            print("✅ TODO task creation works")
        else:
            print("❌ TODO task creation failed")
            return False
            
        # Cleanup
        if os.path.exists("test_todo.md"):
            os.unlink("test_todo.md")
            
    except Exception as e:
        print(f"❌ TODO management failed: {e}")
        return False
    
    return True

def main():
    """Główna funkcja testowa"""
    print("🧪 goLLM Basic Functionality Test")
    print("=================================")
    
    tests = [
        test_installation,
        test_validation,
        test_config_loading,
        test_todo_management
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! goLLM is ready to use.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
