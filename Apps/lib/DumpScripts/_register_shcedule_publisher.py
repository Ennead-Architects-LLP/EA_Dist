import os
import subprocess
import getpass
import ctypes
import sys

script_path = "C:\\Users\\szhang\\duck-repo\\EnneadTab-OS\\DarkSide\\_schedule_publish.py"
venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '..', '.venv', 'Scripts', 'python.exe')
venv_python = os.path.abspath(venv_python)
vscode_path = r"C:\\Users\\szhang\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
task_name = "EnneadTab_SchedulePublisher"

def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Re-run the script with administrator privileges"""
    if not is_admin():
        print("This script requires administrator privileges to set up ONSTART task.")
        print("Attempting to re-run with elevated privileges...")
        
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                " ".join(sys.argv), 
                None, 
                1
            )
            return True
        except Exception as e:
            print(f"Failed to elevate privileges: {e}")
            print("Please run this script as Administrator manually.")
            return False
    return True

def create_startup_batch():
    """Create a batch file in the user's startup folder as a fallback method"""
    startup_folder = os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup")
    batch_file = os.path.join(startup_folder, "EnneadTab_SchedulePublisher.bat")
    
    batch_content = '@echo off\nstart "VSCode" "{}" && "{}" "{}"\n'.format(vscode_path, venv_python, script_path)
    
    try:
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        print("Created startup batch file at: {}".format(batch_file))
        
        # Open the startup folder in Windows Explorer
        try:
            os.startfile(startup_folder)
            print("Opened startup folder in Windows Explorer")
        except Exception as e:
            print("Could not open startup folder: {}".format(e))
        
        return True
    except Exception as e:
        print("Failed to create startup batch file: {}".format(e))
        return False

def check_task_exists():
    """Check if the scheduled task already exists"""
    try:
        result = subprocess.run(['schtasks', '/Query', '/TN', task_name], 
                              capture_output=True, text=True, shell=True)
        return result.returncode == 0
    except:
        return False

def delete_existing_task():
    """Delete existing scheduled task if it exists"""
    if check_task_exists():
        print(f"Deleting existing task '{task_name}'...")
        try:
            subprocess.run(['schtasks', '/Delete', '/TN', task_name, '/F'], 
                          check=True, shell=True)
            print("Existing task deleted successfully.")
            return True
        except Exception as e:
            print(f"Failed to delete existing task: {e}")
            return False
    return True

def create_onstart_task():
    """Create ONSTART scheduled task (runs before user login)"""
    print("Creating ONSTART scheduled task...")
    
    # Delete existing task first
    if not delete_existing_task():
        return False
    
    # Create the command with proper escaping
    action_cmd = f'cmd /c "start \\"VSCode\\" \\"{vscode_path}\\" && \\"{venv_python}\\" \\"{script_path}\\""'
    
    schtasks_cmd = [
        'schtasks', '/Create', '/F',
        '/SC', 'ONSTART',
        '/TN', task_name,
        '/TR', action_cmd,
        '/RU', 'SYSTEM',  # Run as SYSTEM account for startup before login
        '/RL', 'HIGHEST'  # Run with highest privileges
    ]
    
    try:
        result = subprocess.run(schtasks_cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("✅ SUCCESS! ONSTART task created successfully.")
            print("   The script will now run immediately after computer restart, BEFORE user login.")
            return True
        else:
            print(f"❌ Failed to create ONSTART task:")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception creating ONSTART task: {e}")
        return False

def create_onlogon_task():
    """Create ONLOGON scheduled task (runs after user login)"""
    print("Creating ONLOGON scheduled task...")
    
    # Delete existing task first
    if not delete_existing_task():
        return False
    
    action_cmd = f'cmd /c "start \\"VSCode\\" \\"{vscode_path}\\" && \\"{venv_python}\\" \\"{script_path}\\""'
    
    schtasks_cmd = [
        'schtasks', '/Create', '/F',
        '/SC', 'ONLOGON',
        '/TN', task_name,
        '/TR', action_cmd,
        '/RU', getpass.getuser(),  # Run as current user
        '/RL', 'HIGHEST'
    ]
    
    try:
        result = subprocess.run(schtasks_cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("✅ ONLOGON task created successfully.")
            print("   The script will run AFTER user login.")
            return True
        else:
            print(f"❌ Failed to create ONLOGON task: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception creating ONLOGON task: {e}")
        return False

def verify_task_creation():
    """Verify that the task was created successfully"""
    if check_task_exists():
        print("✅ Task verification successful - task exists in scheduler.")
        return True
    else:
        print("❌ Task verification failed - task not found in scheduler.")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("EnneadTab Schedule Publisher - Startup Registration")
    print("=" * 60)
    
    # Check computer name and script existence
    if os.environ.get('COMPUTERNAME', '').upper() != 'SZHANG':
        print("❌ Not running on SZHANG computer. Exiting.")
        sys.exit(1)
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found at: {script_path}")
        sys.exit(1)
    
    if not os.path.exists(venv_python):
        print(f"❌ Python executable not found at: {venv_python}")
        sys.exit(1)
    
    print("✅ Environment checks passed.")
    print(f"   Script: {script_path}")
    print(f"   Python: {venv_python}")
    print(f"   VSCode: {vscode_path}")
    print()
    
    # Check for administrator privileges
    if not is_admin():
        print("⚠️  Administrator privileges required for ONSTART (before login).")
        print("   Attempting to elevate privileges...")
        if run_as_admin():
            sys.exit(0)  # Script will restart with admin privileges
        else:
            print("❌ Could not obtain administrator privileges.")
            print("   You must run this script as Administrator manually.")
            print("   Right-click on this script and select 'Run as administrator'")
            sys.exit(1)
    
    print("✅ Running with administrator privileges.")
    print()
    
    # Try ONSTART first (before user login)
    print("🎯 Attempting ONSTART registration (runs BEFORE user login)...")
    if create_onstart_task() and verify_task_creation():
        print()
        print("🎉 SUCCESS! Your script is now configured to run at startup BEFORE user login.")
        print("   The task will execute immediately after computer restart.")
        print()
        print("📋 Task Details:")
        print(f"   Name: {task_name}")
        print("   Trigger: ONSTART (system startup)")
        print("   Account: SYSTEM")
        print("   Privileges: HIGHEST")
        print()
        print("💡 To test: Restart your computer and check if the script runs automatically.")
        print("💡 To manage: Open Task Scheduler and look for 'EnneadTab_SchedulePublisher'")
        
    else:
        print()
        print("⚠️  ONSTART failed. Trying ONLOGON as fallback...")
        if create_onlogon_task() and verify_task_creation():
            print()
            print("✅ ONLOGON task created successfully.")
            print("   The script will run AFTER user login (not at startup).")
            print()
            print("📋 Task Details:")
            print(f"   Name: {task_name}")
            print("   Trigger: ONLOGON (user login)")
            print(f"   Account: {getpass.getuser()}")
            print("   Privileges: HIGHEST")
            print()
            print("💡 To test: Log out and log back in to test the script.")
        else:
            print()
            print("❌ Both ONSTART and ONLOGON failed.")
            print("   Trying startup folder method as last resort...")
            if create_startup_batch():
                print("✅ Startup folder method successful.")
                print("   Script will run after user login via startup folder.")
            else:
                print("❌ All methods failed. Manual setup required.")
    
    print()
    print("=" * 60)


