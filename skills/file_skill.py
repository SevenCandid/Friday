import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import file_manager

def handle(command, speak):
    # Folder opening
    if "download" in command:
        file_manager.open_folder("downloads")
        speak("Opening your downloads folder.")
        return True
        
    if "desktop" in command:
        file_manager.open_folder("desktop")
        speak("Opening your desktop.")
        return True
        
    if "document" in command:
        file_manager.open_folder("documents")
        speak("Opening your documents folder.")
        return True

    # File Creation
    if "create" in command and "file" in command:
        filename = "New_File"
        if "named" in command:
            filename = command.split("named")[-1].strip()
        elif "name it" in command:
            filename = command.split("name it")[-1].strip()
        elif "name" in command:
            filename = command.split("name")[-1].strip()
            
        filepath = file_manager.SHORTCUTS["desktop"] / f"{filename}.txt"
        if file_manager.create_file(str(filepath), "File created by Friday.\n"):
            speak(f"I have created the file named {filename} on your desktop.")
        else:
            speak("I encountered an error creating the file.")
        return True
                
    # Note Writing
    if "write" in command and "note" in command:
        note_content = "Empty note."
        if "note" in command:
            note_content = command.split("note")[-1].strip()
            
        filepath = file_manager.SHORTCUTS["desktop"] / "Friday_Notes.txt"
        if file_manager.write_file(str(filepath), f"- {note_content}"):
            speak("I have added that note to your Friday Notes file on the desktop.")
        else:
            speak("I couldn't write the note.")
        return True
                
    # File Reading
    if "read" in command and "file" in command:
        filename = ""
        if "file" in command:
            filename = command.split("file")[-1].strip()
            
        filepath = file_manager.SHORTCUTS["desktop"] / f"{filename}.txt"
        content = file_manager.read_file(str(filepath))
        if content:
            if len(content) > 300:
                content = content[:300] + "... The file is too long to read entirely."
            speak(f"The file says: {content}")
        else:
            speak(f"I couldn't find a file named {filename} on your desktop.")
        return True
        
    return False
