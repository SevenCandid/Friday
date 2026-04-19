import json
import os

CONFIG_FILE = "config.json"

_default_config = {
    "ai": {
        "ollama_url": "http://localhost:11434/api/generate",
        "model": "llama3.2:1b",
        "temperature": 0.3
    },
    "voice": {
        "piper_exe": "piper/piper.exe",
        "model": "piper/en_US-amy-low.onnx"
    },
    "user": {
        "city": "Accra"
    },
    "system": {
        "cpu_warning_threshold": 85,
        "battery_warning_threshold": 20
    }
}

_config = {}

def load_config():
    global _config
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'w', encoding="utf-8") as f:
                json.dump(_default_config, f, indent=4)
        except Exception as e:
            print(f"[Config Error] Could not create default config: {e}")
        _config = _default_config
    else:
        try:
            with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
                loaded = json.load(f)
                
                # Merge with defaults to ensure missing keys are populated safely
                _config = {**_default_config}
                for k, v in loaded.items():
                    if isinstance(v, dict) and k in _config:
                        _config[k].update(v)
                    else:
                        _config[k] = v
        except Exception as e:
            print(f"[Config Error] Could not parse config.json. Falling back to defaults: {e}")
            _config = _default_config

# Load immediately on import
load_config()

def get(section: str, key: str):
    """Retrieves a configuration value safely."""
    return _config.get(section, {}).get(key, _default_config[section][key])
