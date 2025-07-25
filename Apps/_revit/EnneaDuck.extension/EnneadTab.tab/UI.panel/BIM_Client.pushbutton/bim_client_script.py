#! python3
# r: openai
# r: requests
# -*- coding: utf-8 -*-

__doc__ = "BIM Client tool for managing BIM data and workflows. This tool provides a centralized interface for BIM operations and data management."
__title__ = "BIM\nClient"
__tip__ = True

# Apply Python 3.9+ compatibility fixes FIRST, before any other imports
try:
    import compatibility
    compatibility.apply_compatibility_fixes()
except ImportError:
    print("⚠️ BIM Client compatibility module not available")

import proDUCKtion # pyright: ignore
proDUCKtion.validify()

# Standard library imports
import sys
import traceback
import subprocess
import os
from datetime import datetime

def get_pyrevit_python_executable():
    """Get the correct Python executable for PyRevit CPython mode"""
    # In PyRevit CPython mode, sys.executable points to Revit.exe
    # We need to find the actual Python interpreter in pyrevitlib
    if hasattr(sys, 'implementation') and sys.implementation.name == 'cpython':
        # Get current user's home directory
        user_home = os.path.expanduser("~")
        
        # Try to find pyRevit CPython engine directory using dynamic detection
        possible_paths = []
        
        # Method 1: Dynamic CPY\d+ detection in pyRevit-Master
        pyrevit_master_cengines = os.path.join(user_home, "AppData", "Roaming", "pyRevit-Master", "bin", "cengines")
        if os.path.exists(pyrevit_master_cengines):
            try:
                import re
                # Find all CPY#### directories
                for item in os.listdir(pyrevit_master_cengines):
                    if re.match(r'CPY\d+', item):
                        engine_path = os.path.join(pyrevit_master_cengines, item, "python.exe")
                        if os.path.exists(engine_path):
                            possible_paths.append(engine_path)
                            print(f"Found PyRevit CPython engine: {engine_path}")
            except Exception as e:
                print(f"Error scanning CPY directories: {e}")
        
        # Method 2: Alternative pyRevit location
        alt_engine_path = os.path.join(user_home, "AppData", "Roaming", "pyRevit", "pyrevitlib", "python.exe")
        if os.path.exists(alt_engine_path):
            possible_paths.append(alt_engine_path)
            print(f"Found alternative PyRevit engine: {alt_engine_path}")
        
        # Return the first found path
        if possible_paths:
            return possible_paths[0]
        
        # If not found in pyrevitlib, try to find Python in PATH (but avoid Windows Store alias)
        try:
            result = subprocess.run(["where", "python"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                python_paths = result.stdout.strip().split('\n')
                for path in python_paths:
                    path = path.strip()
                    if path and os.path.exists(path):
                        # Avoid Windows Store Python alias
                        if "WindowsApps" not in path and "Microsoft" not in path:
                            return path
        except:
            pass
        
        # Try to find Python in common installation locations
        common_paths = [
            "C:\\Python312\\python.exe",
            "C:\\Python311\\python.exe",
            "C:\\Python310\\python.exe",
            "C:\\Python39\\python.exe",
            "C:\\Program Files\\Python312\\python.exe",
            "C:\\Program Files\\Python311\\python.exe",
            "C:\\Program Files\\Python310\\python.exe",
            "C:\\Program Files\\Python39\\python.exe",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
    
    # Fallback to sys.executable (works for IronPython)
    return sys.executable

# Attempt to install OpenAI if not needed
def install_openai_if_needed():
    """Ensure OpenAI package is available by importing from the dependency folder if not found."""
    try:
        import openai
        return True
    except ImportError:
        # Try to import from dependency folder directly
        output = script.get_output()
        output.print_md("## Importing OpenAI from dependency folder...")
        import os
        import sys
        script_dir = os.path.dirname(__file__)
        # Find the parent folder until 'Apps' is reached
        def find_apps_root(start_path):
            current = os.path.abspath(start_path)
            while True:
                if os.path.basename(current) == "Apps":
                    return current
                parent = os.path.dirname(current)
                if parent == current:
                    # Reached the root of the filesystem
                    return None
                current = parent
        apps_root = find_apps_root(script_dir)
        if apps_root:
            dependency_path = os.path.join(apps_root, "lib", "dependency", "py3")
        else:
            dependency_path = None
        if dependency_path and os.path.exists(dependency_path):
            if dependency_path not in sys.path:
                sys.path.insert(0, dependency_path)
                output.print_md(f"✅ Added dependency path to sys.path: {dependency_path}")
            try:
                import openai
                output.print_md("✅ OpenAI imported successfully from dependency folder!")
                return True
            except ImportError as e:
                output.print_md(f"❌ Failed to import OpenAI from dependency folder: {e}")
                output.print_md("**Manual installation required or check dependency folder.**")
                return False
        else:
            output.print_md(f"❌ Dependency path not found: {dependency_path}")
            output.print_md("**Manual installation required or check dependency folder.**")
            return False

# CLR imports for Revit API (conditional for CPython compatibility)
try:
    import clr # pyright: ignore
    clr.AddReference('System')
    clr.AddReference('RevitAPI')
    clr.AddReference('RevitAPIUI')

    # Revit API imports
    from Autodesk.Revit import DB # pyright: ignore
    from Autodesk.Revit import UI # pyright: ignore
    REVIT_API_AVAILABLE = True
    print("✅ Revit API modules imported successfully")
except Exception as e:
    REVIT_API_AVAILABLE = False
    print(f"⚠️ Revit API modules not available: {e}")
    print("Using CPython mode without Revit API access")

# PyRevit imports
from pyrevit import script
from pyrevit import HOST_APP

# Note: pyrevit.forms is not supported in CPython - using output window only
FORMS_AVAILABLE = False

# EnneadTab imports (optional for CPython compatibility)
try:
    from EnneadTab.REVIT import REVIT_APPLICATION
    from EnneadTab import USER, ENVIRONMENT, SOUND, TIME, ERROR_HANDLE, FOLDER, IMAGE, LOG
    ENNEADTAB_AVAILABLE = True
    print("✅ EnneadTab modules imported successfully")
except ImportError as e:
    ENNEADTAB_AVAILABLE = False
    print(f"⚠️ EnneadTab modules not available: {e}")
    print("Using fallback functionality for CPython mode")

# Get Revit application objects (with fallback)
try:
    if ENNEADTAB_AVAILABLE and REVIT_API_AVAILABLE:
        uidoc = REVIT_APPLICATION.get_uidoc()
        doc = REVIT_APPLICATION.get_doc()
        print("✅ Revit application objects retrieved successfully")
    else:
        # Fallback for CPython mode
        uidoc = None
        doc = None
        if not ENNEADTAB_AVAILABLE:
            print("⚠️ Revit application objects not available - EnneadTab not available")
        if not REVIT_API_AVAILABLE:
            print("⚠️ Revit application objects not available - Revit API not available")
except Exception as e:
    uidoc = None
    doc = None
    print(f"⚠️ Failed to get Revit application objects: {e}")

__persistentengine__ = True


# Fallback decorator for when EnneadTab is not available
def fallback_decorator(func):
    """Decorator to handle cases where EnneadTab modules are not available"""
    def wrapper(*args, **kwargs):
        if ENNEADTAB_AVAILABLE:
            return func(*args, **kwargs)
        else:
            # Fallback behavior for CPython mode
            output = script.get_output()
            output.print_md(f"## {func.__name__} - CPython Fallback Mode")
            output.print_md("**Note:** EnneadTab modules not available - using basic functionality")
            return True
    return wrapper


@fallback_decorator
def test_f_string_functionality():
    """Test function to demonstrate f-string usage in Python 3"""
    if not ENNEADTAB_AVAILABLE:
        # Fallback for CPython mode without EnneadTab
        output = script.get_output()
        output.print_md("## BIM Client - F-String Test Results (CPython Mode)")
        
        # Basic f-string tests without EnneadTab dependencies
        current_time = datetime.now()
        python_version = sys.version_info
        
        # Using f-strings for string formatting
        message = f"Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}"
        time_info = f"Current Time: {current_time}"
        engine_info = f"Engine: {'CPython' if hasattr(sys, 'implementation') and sys.implementation.name == 'cpython' else 'Other'}"
        
        # F-string with formatting
        formatted_time = f"Time: {current_time:%Y-%m-%d %H:%M:%S}"
        
        # Display the results
        output.print_md(f"**{message}**")
        output.print_md(f"**{time_info}**")
        output.print_md(f"**{engine_info}**")
        output.print_md(f"**{formatted_time}**")
        
        # Show a simple alert with f-string
        alert_message = f"BIM Client initialized in CPython mode"
        output.print_md(f"## 🎉 {alert_message}")
        output.print_md("**Note:** Running in CPython mode - EnneadTab modules not available")
        
        return True
    
    # Original functionality with EnneadTab
    try:
        current_user = USER.get_user_name()
    except AttributeError:
        # Fallback if get_user_name doesn't exist
        try:
            current_user = USER.USER_NAME
        except AttributeError:
            current_user = "Unknown User"
    
    try:
        current_time = TIME.get_current_time()
    except AttributeError:
        # Fallback if get_current_time doesn't exist
        current_time = datetime.now()
    
    doc_title = doc.Title if doc else "No Document"
    
    # Using f-strings for string formatting
    message = f"Current User: {current_user}"
    time_info = f"Current Time: {current_time}"
    doc_info = f"Active Document: {doc_title}"
    
    # More complex f-string with expressions (safe Revit API access)
    if REVIT_API_AVAILABLE and doc:
        try:
            element_count = len(list(DB.FilteredElementCollector(doc).WhereElementIsNotElementType()))
            summary = f"Document '{doc_title}' contains {element_count} elements"
        except Exception as e:
            summary = f"Document '{doc_title}' - element count unavailable ({e})"
    else:
        summary = f"Document '{doc_title}' - Revit API not available for element counting"
    
    # F-string with formatting
    formatted_time = f"Time: {current_time:%Y-%m-%d %H:%M:%S}"
    
    # Display the results
    output = script.get_output()
    output.print_md("## BIM Client - F-String Test Results")
    output.print_md(f"**{message}**")
    output.print_md(f"**{time_info}**")
    output.print_md(f"**{doc_info}**")
    output.print_md(f"**{summary}**")
    output.print_md(f"**{formatted_time}**")
    
    # Show a simple alert with f-string (CPython compatible - output window only)
    alert_message = f"BIM Client initialized for user: {current_user}"
    output.print_md(f"## 🎉 {alert_message}")
    output.print_md("**Note:** Running in CPython mode - using output window for all interactions")
    
    return True


def detect_python_engine():
    """Detect and report the Python engine being used"""
    output = script.get_output()
    
    # Detect Python engine
    if hasattr(sys, 'implementation'):
        engine_name = sys.implementation.name
        engine_version = f"{sys.implementation.version.major}.{sys.implementation.version.minor}.{sys.implementation.version.micro}"
    else:
        engine_name = "Unknown"
        engine_version = "Unknown"
    
    # Check for CPython specific characteristics
    is_cpython = engine_name == 'cpython'
    
    # Get the correct Python executable
    python_exe = get_pyrevit_python_executable()
    
    output.print_md("## Python Engine Detection")
    output.print_md(f"**Engine:** {engine_name.title()}")
    output.print_md(f"**Engine Version:** {engine_version}")
    output.print_md(f"**Python Version:** {sys.version}")
    output.print_md(f"**Python Executable:** {python_exe}")
    output.print_md(f"**Forms Available:** No (CPython compatible mode)")
    
    if is_cpython:
        output.print_md("**✅ CPython Mode:** Optimized for CPython compatibility")
        output.print_md("- Using output window for all user interactions")
        output.print_md("- Full pip installation support")
        output.print_md("- Enhanced debugging capabilities")
    else:
        output.print_md("**⚠️ IronPython Mode:** Some features may be limited")
        output.print_md("- Limited pip installation support")
        output.print_md("- Using output window for consistency")
    
    return {
        'engine': engine_name,
        'version': engine_version,
        'is_cpython': is_cpython,
        'forms_available': FORMS_AVAILABLE,
        'python_executable': python_exe
    }


def test_pip_install_missing_module():
    """Test pip installation of missing modules in PyRevit CPython mode"""
    output = script.get_output()
    
    # List of modules to test installation
    test_modules = [
        {'name': 'requests', 'import_name': 'requests', 'description': 'HTTP library'},
        {'name': 'pandas', 'import_name': 'pandas', 'description': 'Data analysis library'},
        {'name': 'numpy', 'import_name': 'numpy', 'description': 'Numerical computing'},
        {'name': 'matplotlib', 'import_name': 'matplotlib', 'description': 'Plotting library'},
        {'name': 'openai', 'import_name': 'openai', 'description': 'OpenAI API client'}
    ]
    
    # Get the correct Python executable
    python_exe = get_pyrevit_python_executable()
    
    output.print_md("## Testing Pip Installation in PyRevit CPython")
    output.print_md(f"**Python Engine:** {'CPython' if hasattr(sys, 'implementation') and sys.implementation.name == 'cpython' else 'IronPython'}")
    output.print_md(f"**Python Version:** {sys.version}")
    output.print_md(f"**Python Executable:** {python_exe}")
    
    # Check if pip is available first
    try:
        result = subprocess.run([python_exe, "-m", "pip", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            output.print_md("⚠️ **Pip not available in PyRevit Python engine**")
            output.print_md("**This is normal for embedded Python distributions.**")
            output.print_md("**Will try local pip module from dependency folder.**")
            # Continue with local pip module
    except Exception as e:
        output.print_md(f"⚠️ **Pip check failed:** {e}")
        output.print_md("**Will try local pip module from dependency folder.**")
        # Continue with local pip module
    
    results = []
    
    for module in test_modules:
        output.print_md(f"\n### Testing: {module['name']} ({module['description']})")
        
        # Check if module is already available
        try:
            __import__(module['import_name'])
            output.print_md(f"✅ **{module['name']}** already available")
            results.append({'module': module['name'], 'status': 'already_available', 'error': None})
            continue
        except ImportError:
            output.print_md(f"❌ **{module['name']}** not available - attempting installation...")
        
        # Attempt to install the module
        try:
            output.print_md(f"Installing {module['name']} via pip...")
            
            # First try system pip
            result = subprocess.run([
                python_exe, "-m", "pip", "install", module['name']
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                output.print_md(f"✅ **{module['name']}** installed successfully via system pip!")
                
                # Try importing the newly installed module
                try:
                    __import__(module['import_name'])
                    output.print_md(f"✅ **{module['name']}** imported successfully after installation")
                    results.append({'module': module['name'], 'status': 'installed_success', 'error': None})
                except ImportError as import_error:
                    output.print_md(f"⚠️ **{module['name']}** installed but import failed: {import_error}")
                    results.append({'module': module['name'], 'status': 'installed_import_failed', 'error': str(import_error)})
            else:
                # System pip failed, try local pip module
                output.print_md(f"⚠️ **{module['name']}** system pip installation failed, trying local pip module...")
                success, message = install_module_with_local_pip(module['name'], python_exe)
                
                if success:
                    output.print_md(f"✅ **{module['name']}** installed successfully via local pip!")
                    
                    # Try importing the newly installed module
                    try:
                        __import__(module['import_name'])
                        output.print_md(f"✅ **{module['name']}** imported successfully after installation")
                        results.append({'module': module['name'], 'status': 'installed_success_local', 'error': None})
                    except ImportError as import_error:
                        output.print_md(f"⚠️ **{module['name']}** installed but import failed: {import_error}")
                        results.append({'module': module['name'], 'status': 'installed_import_failed', 'error': str(import_error)})
                else:
                    output.print_md(f"❌ **{module['name']}** both system and local pip installation failed:")
                    output.print_md(f"**System pip error:** {result.stderr}")
                    output.print_md(f"**Local pip error:** {message}")
                    results.append({'module': module['name'], 'status': 'install_failed', 'error': f"System: {result.stderr}, Local: {message}"})
                
        except subprocess.TimeoutExpired:
            output.print_md(f"⏰ **{module['name']}** installation timed out")
            results.append({'module': module['name'], 'status': 'timeout', 'error': 'Installation timed out'})
        except Exception as e:
            output.print_md(f"❌ **{module['name']}** installation error: {str(e)}")
            results.append({'module': module['name'], 'status': 'error', 'error': str(e)})
    
    # Summary
    output.print_md("\n## Installation Summary")
    success_count = len([r for r in results if r['status'] in ['already_available', 'installed_success', 'installed_success_local']])
    total_count = len(results)
    
    output.print_md(f"**Total modules tested:** {total_count}")
    output.print_md(f"**Successfully available:** {success_count}")
    if total_count > 0:
        output.print_md(f"**Success rate:** {success_count/total_count*100:.1f}%")
    
    # Detailed results
    output.print_md("\n### Detailed Results:")
    for result in results:
        status_icon = {
            'already_available': '✅',
            'installed_success': '✅',
            'installed_success_local': '🔧',
            'installed_import_failed': '⚠️',
            'install_failed': '❌',
            'timeout': '⏰',
            'error': '❌'
        }.get(result['status'], '❓')
        
        status_text = {
            'already_available': 'Already Available',
            'installed_success': 'Installed (System Pip)',
            'installed_success_local': 'Installed (Local Pip)',
            'installed_import_failed': 'Installed but Import Failed',
            'install_failed': 'Installation Failed',
            'timeout': 'Installation Timeout',
            'error': 'Installation Error'
        }.get(result['status'], result['status'])
        
        output.print_md(f"{status_icon} **{result['module']}**: {status_text}")
        if result['error']:
            output.print_md(f"   Error: {result['error'][:100]}...")
    
    return results


def debug_missing_module(module_name):
    """Debug and install a specific missing module"""
    output = script.get_output()
    
    # Get the correct Python executable
    python_exe = get_pyrevit_python_executable()
    
    output.print_md(f"## Debugging Missing Module: {module_name}")
    output.print_md(f"**Python Engine:** {'CPython' if hasattr(sys, 'implementation') and sys.implementation.name == 'cpython' else 'IronPython'}")
    output.print_md(f"**Python Version:** {sys.version}")
    output.print_md(f"**Python Executable:** {python_exe}")
    
    # Check if module is already available
    try:
        module = __import__(module_name)
        output.print_md(f"✅ **{module_name}** is already available")
        output.print_md(f"**Version:** {getattr(module, '__version__', 'Unknown')}")
        return True
    except ImportError as e:
        output.print_md(f"❌ **{module_name}** not available: {e}")
    
    # Check if pip is available first
    try:
        result = subprocess.run([python_exe, "-m", "pip", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            output.print_md("⚠️ **Pip not available in PyRevit Python engine**")
            output.print_md("**This is normal for embedded Python distributions.**")
            output.print_md("**Will try local pip module from dependency folder.**")
            # Continue with local pip module
    except Exception as e:
        output.print_md(f"⚠️ **Pip check failed:** {e}")
        output.print_md("**Will try local pip module from dependency folder.**")
        # Continue with local pip module
    
    # Attempt installation
    output.print_md(f"\n### Attempting to install {module_name}...")
    
    try:
        # First try system pip
        result = subprocess.run([
            python_exe, "-m", "pip", "install", module_name
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            output.print_md(f"✅ **{module_name}** installed successfully via system pip!")
            
            # Try importing again
            try:
                module = __import__(module_name)
                output.print_md(f"✅ **{module_name}** imported successfully after installation")
                output.print_md(f"**Version:** {getattr(module, '__version__', 'Unknown')}")
                return True
            except ImportError as import_error:
                output.print_md(f"⚠️ **{module_name}** installed but import failed: {import_error}")
                return False
        else:
            # System pip failed, try local pip module
            output.print_md(f"⚠️ **{module_name}** system pip installation failed, trying local pip module...")
            success, message = install_module_with_local_pip(module_name, python_exe)
            
            if success:
                output.print_md(f"✅ **{module_name}** installed successfully via local pip!")
                
                # Try importing again
                try:
                    module = __import__(module_name)
                    output.print_md(f"✅ **{module_name}** imported successfully after installation")
                    output.print_md(f"**Version:** {getattr(module, '__version__', 'Unknown')}")
                    return True
                except ImportError as import_error:
                    output.print_md(f"⚠️ **{module_name}** installed but import failed: {import_error}")
                    return False
            else:
                output.print_md(f"❌ **{module_name}** both system and local pip installation failed:")
                output.print_md(f"**System pip error:** {result.stderr}")
                output.print_md(f"**Local pip error:** {message}")
                return False
            
    except subprocess.TimeoutExpired:
        output.print_md(f"⏰ **{module_name}** installation timed out")
        return False
    except Exception as e:
        output.print_md(f"❌ **{module_name}** installation error: {str(e)}")
        return False


# --- BEGIN: Helper to get OpenAI API key without EnneadTab imports ---
def get_openai_api_key_from_secret(app_name="EnneadTabAPI"):
    """Get OpenAI API key from EA_API_KEY.secret file without EnneadTab imports."""
    import os
    import json
    # Try to find the DB folder from environment variable or fallback to relative path
    db_folder = os.environ.get("ENNEADTAB_DB_FOLDER")
    if not db_folder:
        # Fallback: try to find Apps/lib/EnneadTab/DB or sibling DB folder
        script_dir = os.path.dirname(__file__)
        # Try up to 6 levels up
        current = script_dir
        for _ in range(6):
            candidate = os.path.join(current, "..", "..", "..", "lib", "EnneadTab", "DB")
            candidate = os.path.abspath(candidate)
            if os.path.exists(candidate):
                db_folder = candidate
                break
            current = os.path.dirname(current)
    if not db_folder or not os.path.exists(db_folder):
        # Fallback: try L drive
        db_folder = "L:/EnneadTab/DB"
    secret_file = os.path.join(db_folder, "EA_API_KEY.secret")
    if not os.path.exists(secret_file):
        # Try local secret file in script dir
        secret_file = os.path.join(os.path.dirname(__file__), "EA_API_KEY.secret")
        if not os.path.exists(secret_file):
            return None
    try:
        with open(secret_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Try to get value from specified app_name first, fallback to any key if not found
        if app_name in data:
            return data[app_name]
        return next(iter(data.values()), None)
    except Exception as e:
        return None
# --- END: Helper to get OpenAI API key without EnneadTab imports ---


def test_openai_functionality():
    """Test OpenAI functionality if available, using dependency folder import if needed."""
    output = script.get_output()
    # Attempt to import OpenAI from dependency folder if not found
    if install_openai_if_needed():
        try:
            import openai
            # Set API key from secret file if available
            api_key = get_openai_api_key_from_secret()
            if api_key:
                openai.api_key = api_key
                output.print_md("✅ OpenAI API key loaded from secret file.")
            else:
                output.print_md("⚠️ OpenAI API key not found. Please check EA_API_KEY.secret.")
            output.print_md("## OpenAI Package Test")
            output.print_md(f"✅ **OpenAI version:** {getattr(openai, '__version__', 'Unknown')}")
            output.print_md(f"✅ **OpenAI available:** Yes")
            # Test basic OpenAI functionality
            try:
                client = openai.OpenAI()
                output.print_md("✅ **OpenAI client created successfully**")
            except Exception as e:
                output.print_md(f"⚠️ OpenAI client creation failed: {e}")
            return True
        except Exception as e:
            output.print_md(f"❌ **OpenAI test failed:** {str(e)}")
            return False
    else:
        output.print_md("❌ **OpenAI package not available**")
        return False


def main():
    """
    Main function for BIM Client button - CPython 3 compatible
    """
    output = script.get_output()
    
    # Check if EnneadTab is available
    if ENNEADTAB_AVAILABLE:
        # Full functionality with EnneadTab
        try:
            # Safe user name access
            try:
                current_user = USER.get_user_name()
            except AttributeError:
                try:
                    current_user = USER.USER_NAME
                except AttributeError:
                    current_user = "Unknown"
            
            # Safe time access
            try:
                current_time = TIME.get_current_time()
            except AttributeError:
                current_time = datetime.now()
            
            logger = script.get_logger()
            logger.info(f"BIM Client started by user: {current_user} at {current_time}")
        except Exception as e:
            output.print_md(f"⚠️ Error getting user info: {e}")
            current_user = "Unknown"
            current_time = datetime.now()
    else:
        # CPython mode without EnneadTab
        current_user = "CPython User"
        current_time = datetime.now()
        output.print_md("## BIM Client - CPython Mode")
        output.print_md("**Note:** Running without EnneadTab modules")
    
    # Test f-string functionality
    try:
        test_f_string_functionality()
    except Exception as e:
        output.print_md(f"⚠️ Error in f-string test: {e}")
    
    # Test OpenAI functionality (only check/install openai, not others)
    try:
        test_openai_functionality()
    except Exception as e:
        output.print_md(f"⚠️ Error in OpenAI test: {e}")
    
    # Detect Python engine
    try:
        detect_python_engine()
    except Exception as e:
        output.print_md(f"⚠️ Error in engine detection: {e}")
    
    # Additional f-string test
    output.print_md("## BIM Client Initialization Complete")
    output.print_md(f"**User:** {current_user}")
    output.print_md(f"**Time:** {current_time}")
    output.print_md(f"**Python Version:** {sys.version}")
    
    if ENNEADTAB_AVAILABLE and REVIT_API_AVAILABLE:
        try:
            output.print_md(f"**Revit Version:** {HOST_APP.version}")
        except Exception as e:
            output.print_md(f"**Revit Version:** Unknown ({e})")
    else:
        output.print_md("**Revit Version:** Not available in CPython mode")
    
    # Test more f-string variations
    python_version = sys.version_info
    version_info = f"Python {python_version.major}.{python_version.minor}.{python_version.micro}"
    output.print_md(f"**Version Info:** {version_info}")
    
    # Test f-string with conditional expressions
    is_cpython = hasattr(sys, 'implementation') and sys.implementation.name == 'cpython'
    engine_type = f"Engine: {'CPython' if is_cpython else 'Other'}"
    output.print_md(f"**{engine_type}**")
    
    # EnneadTab availability status
    enneadtab_status = f"EnneadTab: {'Available' if ENNEADTAB_AVAILABLE else 'Not Available (CPython Mode)'}"
    output.print_md(f"**{enneadtab_status}**")
    
    # Revit API availability status
    revit_api_status = f"Revit API: {'Available' if REVIT_API_AVAILABLE else 'Not Available (CPython Mode)'}"
    output.print_md(f"**{revit_api_status}**")
    
    return True


if __name__ == "__main__":
    output = script.get_output()
    output.close_others()
    main() 