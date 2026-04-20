import os
import importlib.util
import sys

# List of loaded skill modules
_skills = []

def load_skills():
    """
    Dynamically discovers and loads all .py files in the /skills directory.
    """
    global _skills
    _skills = []
    
    # Path to the root skills directory
    _ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skills_dir = os.path.join(_ROOT_DIR, "skills")
    
    if not os.path.exists(skills_dir):
        print(f"[Skill Manager] Creating skills directory at {skills_dir}")
        os.makedirs(skills_dir)
        return

    print("[Skill Manager] Loading skills...")
    
    for filename in os.listdir(skills_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            file_path = os.path.join(skills_dir, filename)
            
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'handle'):
                    _skills.append(module)
                    print(f"  - Loaded skill: {module_name}")
                else:
                    print(f"  [Warning] {filename} has no handle() function. Skipping.")
            except Exception as e:
                print(f"  [Error] Failed to load {filename}: {e}")

def execute_command(command, response_callback):
    """
    Passes the command to each loaded skill using a priority system.
    """
    if not command:
        return False
        
    cmd = command.lower().strip()
    
    # HARD-CORE CLEANING: Remove the wake word if it leaked into the command
    for wake in ["hey seven", "hello seven", "okay seven", "seven"]:
        if cmd.startswith(wake):
            cmd = cmd.replace(wake, "", 1).strip(",.?! ")
            break
    
    # PRIORITY ORDER: Tactical skills must be checked before general AI chat
    PRIORITY_LIST = ["explorer", "app_launcher", "app_closer", "system_control", "files", "location_skill", "weather_skill", "github_skill"]
    
    print(f"[Brain] Routing Command: '{cmd}'")
    
    # 1. Check priority skills first
    for skill_name in PRIORITY_LIST:
        for skill in _skills:
            # Check both module name and filename-based name
            if skill.__name__ == skill_name or getattr(skill, "__file__", "").endswith(skill_name + ".py"):
                try:
                    if skill.handle(cmd, response_callback):
                        print(f"[Skill Manager] Handled by Priority Skill: {skill_name}")
                        return True
                except Exception as e:
                    print(f"[Skill Manager Error] In Priority {skill_name}: {e}")
    
    # 2. Check everything else (including chat_skill fallback)
    for skill in _skills:
        # Skip what we already checked
        if skill.__name__ in PRIORITY_LIST: continue
        
        try:
            if skill.handle(cmd, response_callback):
                print(f"[Skill Manager] Handled by Fallback: {skill.__name__}")
                return True
        except Exception as e:
            print(f"[Skill Manager Error] In {skill.__name__}: {e}")
            
    return False
