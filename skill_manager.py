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
    
    skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
    
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
    Passes the command to each loaded skill.
    Stops at the first skill that returns True (Handled).
    """
    if not command:
        return False
        
    cmd = command.lower().strip()
    
    for skill in _skills:
        try:
            if skill.handle(cmd, response_callback):
                return True
        except Exception as e:
            print(f"[Skill Manager Error] In {skill.__name__}: {e}")
            
    return False
