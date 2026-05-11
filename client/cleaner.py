import os

# --- CONFIGURATION ---
# Ensure this matches the TEST_TARGET in your main ransomware script
TEST_TARGET = r"C:\Users\rs685\OneDrive\Desktop\TestFolder"
ID_FILE_NAME = "Machine_id.txt"
RANSOM_NOTE_NAME = "READ_ME_FOR_DECRYPTION.txt"

def cleanup():
    print(f"--- Starting System Cleanup in {TEST_TARGET} ---")
    notes_removed = 0
    
    # 1. Remove the Machine ID file
    # This resets the simulation so the next time you run the ransomware, it starts fresh
    id_path = os.path.join(TEST_TARGET, ID_FILE_NAME)
    if os.path.exists(id_path):
        os.remove(id_path)
        print(f"[CLEANUP] Deleted: {ID_FILE_NAME}")

    # 2. Walk through all folders to find and delete Ransom Notes
    for root, dirs, files in os.walk(TEST_TARGET):
        if RANSOM_NOTE_NAME in files:
            note_path = os.path.join(root, RANSOM_NOTE_NAME)
            try:
                os.remove(note_path)
                notes_removed += 1
            except Exception as e:
                print(f"[ERROR] Could not remove {note_path}: {e}")

    # 3. Optional: Reset the Wallpaper
    # If you want to reset the wallpaper to a default Windows color/image
    # import ctypes
    # ctypes.windll.user32.SystemParametersInfoW(20, 0, None, 3)

    print("---------------------------------------")
    print(f"Cleanup Complete!")
    print(f"Total Ransom Notes deleted: {notes_removed}")
    print("The environment is now ready for a new test.")

if __name__ == "__main__":
    print("WARNING: This will delete the Machine ID and all Ransom Notes.")
    confirm = input("Proceed with cleanup? (y/n): ")
    if confirm.lower() == 'y':
        cleanup()
    else:
        print("Cleanup aborted.")