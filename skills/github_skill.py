import webbrowser
import requests
from core import config
from core import state_manager

# GitHub Token and Username should be in config.json
GITHUB_TOKEN = config.get("github", "token")
GITHUB_USER = config.get("github", "username")

def handle(command, speak):
    if "github" not in command:
        return False

    # 1. Open GitHub Profile or Main Site
    if "profile" in command:
        url = f"https://github.com/{GITHUB_USER}"
        webbrowser.open(url)
        speak(f"Opening your GitHub profile, {GITHUB_USER}.")
        return True

    # 2. Check Notifications
    if "notification" in command or "update" in command:
        if not GITHUB_TOKEN:
            speak("I need a GitHub token to check your notifications. Please add it to my configuration.")
            return True
            
        try:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get("https://api.github.com/notifications", headers=headers)
            if response.status_code == 200:
                notes = response.json()
                count = len(notes)
                if count == 0:
                    speak("You have no unread GitHub notifications.")
                else:
                    speak(f"You have {count} unread notifications. I've listed them in your HUD.")
                    msg = "--- GITHUB NOTIFICATIONS ---\n"
                    for n in notes[:5]: # Show top 5
                        msg += f"• {n['subject']['title']} ({n['repository']['full_name']})\n"
                    state_manager.add_to_chat("SEVEN", msg)
            else:
                speak("I'm having trouble connecting to GitHub right now.")
        except Exception as e:
            print(f"[GitHub Error] {e}")
            speak("I encountered an error while checking your notifications.")
        return True

    # 3. Open Specific Repository
    if "open" in command or "repo" in command:
        repo_name = command.split("github")[-1].replace("open", "").replace("repo", "").strip()
        if repo_name:
            url = f"https://github.com/{GITHUB_USER}/{repo_name.replace(' ', '-')}"
            webbrowser.open(url)
            speak(f"Opening your {repo_name} repository.")
            return True

    # Default fallback
    webbrowser.open("https://github.com")
    speak("Opening GitHub.")
    return True
