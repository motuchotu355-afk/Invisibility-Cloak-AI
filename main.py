import mss
import mss.tools
from PIL import Image
from google import genai
import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import ctypes
from ctypes import wintypes
import os
import keyboard

# ==========================================
# 1. CONSTANTS & FILE PATHS
# ==========================================
MODEL_ID = 'gemini-2.5-flash'
NOTES_FILE = "my_notes.txt"
API_KEY_FILE = "saved_api_key.txt"


# ==========================================
# 2. CORE FUNCTIONS
# ==========================================
def take_screenshot(filename="screen_capture.png"):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
        return filename


def ask_gemini_stream(client, user_question, image_path=None):
    """Sends the prompt using the client passed from the main task."""
    strict_prompt = user_question + "\n\nIMPORTANT: Give a very brief, direct answer. Do NOT use any markdown formatting like ** or *."
    if image_path:
        img = Image.open(image_path)
        contents = [strict_prompt, img]
    else:
        contents = [strict_prompt]

    # Return the stream directly
    return client.models.generate_content_stream(
        model=MODEL_ID,
        contents=contents
    )


# ==========================================
# 3. THE INVISIBILITY CLOAK ENGINE
# ==========================================
def apply_invisibility_cloak(window):
    try:
        user32 = ctypes.windll.user32
        user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
        user32.SetWindowDisplayAffinity.restype = wintypes.BOOL

        hwnd = int(window.wm_frame(), 16)
        success = user32.SetWindowDisplayAffinity(hwnd, 17)

        if success:
            print(f"👻 Invisibility active for: {window.title()}")
        else:
            print(f"❌ Invisibility failed for {window.title()}. Error code: {ctypes.GetLastError()}")
    except Exception as e:
        print(f"❌ Crash during invisibility: {e}")


def bind_cloak(window):
    def trigger(event):
        if event.widget == window:
            window.unbind("<Map>")
            apply_invisibility_cloak(window)

    window.bind("<Map>", trigger)


# ==========================================
# 4. DATA SAVING & LOADING
# ==========================================
notes_window = None
notes_box = None


def load_saved_data():
    """Loads the saved API key and notes when the app opens."""
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r", encoding="utf-8") as file:
            api_key_entry.insert(0, file.read().strip())


def load_notes_data():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as file:
            notes_box.insert(tk.END, file.read())


def save_all_data():
    """Saves both the API key and the Notes before closing."""
    # Save API Key
    with open(API_KEY_FILE, "w", encoding="utf-8") as file:
        file.write(api_key_entry.get().strip())

    # Save Notes (if the window was opened)
    if notes_box is not None and notes_box.winfo_exists():
        with open(NOTES_FILE, "w", encoding="utf-8") as file:
            file.write(notes_box.get(1.0, tk.END).strip())


# ==========================================
# 5. THE POP-OUT NOTES SYSTEM
# ==========================================
def open_notes_window():
    global notes_window, notes_box
    if notes_window is not None and notes_window.winfo_exists():
        force_to_front(notes_window)
        return

    notes_window = tk.Toplevel(root)
    notes_window.title("Secret Notes")
    notes_window.geometry("350x450")
    notes_window.configure(padx=10, pady=10)
    notes_window.attributes('-toolwindow', True)

    bind_cloak(notes_window)
    notes_window.protocol("WM_DELETE_WINDOW", hide_notes)

    tk.Label(notes_window, text="📝 My Notes (Auto-saves):", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 5))
    notes_box = scrolledtext.ScrolledText(notes_window, font=("Arial", 11), wrap=tk.WORD, bg="#fffdeb")
    notes_box.pack(fill="both", expand=True)

    load_notes_data()


def hide_notes():
    save_all_data()
    if notes_window is not None:
        notes_window.withdraw()


# ==========================================
# 6. APP LOGIC & GLOBAL HOTKEY
# ==========================================
def on_app_close():
    save_all_data()
    root.destroy()


def force_to_front(window):
    window.deiconify()
    window.attributes('-topmost', True)
    window.lift()
    window.focus_force()
    window.after(200, lambda: window.attributes('-topmost', False))


is_app_visible = True


def toggle_app_visibility():
    global is_app_visible
    if is_app_visible:
        root.withdraw()
        if notes_window is not None and notes_window.winfo_exists():
            notes_window.withdraw()
        is_app_visible = False
    else:
        force_to_front(root)
        if notes_window is not None and notes_window.winfo_exists():
            force_to_front(notes_window)
        is_app_visible = True


def safe_toggle():
    root.after(0, toggle_app_visibility)


# --- AI Tasks ---
def start_process_image():
    ask_img_button.config(state=tk.DISABLED)
    ask_text_button.config(state=tk.DISABLED)
    result_box.delete(1.0, tk.END)
    threading.Thread(target=background_task, args=(True,), daemon=True).start()


def start_process_text():
    ask_img_button.config(state=tk.DISABLED)
    ask_text_button.config(state=tk.DISABLED)
    result_box.delete(1.0, tk.END)
    threading.Thread(target=background_task, args=(False,), daemon=True).start()


def background_task(use_screenshot):
    try:
        # 1. Verify the key and create the client HERE so it stays alive!
        current_api_key = api_key_entry.get().strip()
        if not current_api_key:
            update_ui("❌ ERROR: Please paste your Gemini API Key in the top box first!\n")
            return

        # Create the client that stays awake for the whole process
        live_client = genai.Client(api_key=current_api_key)

        question = question_entry.get()

        # 2. Run the process and pass the live_client into the function
        if use_screenshot:
            if not question.strip():
                question = "Describe what is on this screen."
            saved_image = take_screenshot()
            update_ui("📸 Screenshot taken! Asking Gemini...\n\n🤖 Gemini:\n")
            response_stream = ask_gemini_stream(live_client, question, saved_image)
        else:
            if not question.strip():
                update_ui("❌ Please type a question in the box first!\n")
                return
            update_ui("💬 Asking Gemini...\n\n🤖 Gemini:\n")
            response_stream = ask_gemini_stream(live_client, question, None)

        # 3. Stream the text (The client is still alive to download this!)
        for chunk in response_stream:
            if chunk.text:
                clean_text = chunk.text.replace("**", "").replace("*", "")
                update_ui(clean_text)

        update_ui("\n\n✅ Done!\n" + "=" * 40 + "\n")
    except Exception as e:
        if "API key not valid" in str(e) or "400" in str(e):
            update_ui("❌ ERROR: Your API key is invalid. Please check it and try again.\n")
        else:
            update_ui(f"❌ An error occurred:\n{str(e)}\n")
    finally:
        ask_img_button.config(state=tk.NORMAL)
        ask_text_button.config(state=tk.NORMAL)


def update_ui(text):
    result_box.insert(tk.END, text)
    result_box.see(tk.END)


# ==========================================
# 7. BUILD THE MAIN UI
# ==========================================
root = tk.Tk()
root.attributes('-toolwindow', True)
root.title("Screen AI Assistant")
# Made the app slightly taller to fit the new API key bar comfortably
root.geometry("500x520")
root.configure(padx=15, pady=15)

root.protocol("WM_DELETE_WINDOW", on_app_close)
keyboard.add_hotkey('ctrl+shift+space', safe_toggle)

bind_cloak(root)

# --- UI ELEMENTS ---

# NEW: API Key Input Frame
api_frame = tk.Frame(root)
api_frame.pack(fill="x", pady=(0, 15))
tk.Label(api_frame, text="🔑 API Key:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
# show="*" hides the text like a password field!
api_key_entry = tk.Entry(api_frame, font=("Arial", 10), show="*")
api_key_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=(5, 0))

tk.Label(root, text="Ask a question (or leave blank for general screenshot):", font=("Arial", 11)).pack(anchor="w")

question_entry = tk.Entry(root, font=("Arial", 12), width=50)
question_entry.pack(pady=10, fill="x")

btn_frame = tk.Frame(root)
btn_frame.pack(fill="x", pady=(0, 10))

ask_img_button = tk.Button(btn_frame, text="📸 + Ask", font=("Arial", 11, "bold"),
                           bg="#4CAF50", fg="white", command=start_process_image, pady=8)
ask_img_button.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))

ask_text_button = tk.Button(btn_frame, text="💬 Text Only", font=("Arial", 11, "bold"),
                            bg="#2196F3", fg="white", command=start_process_text, pady=8)
ask_text_button.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))

notes_btn = tk.Button(btn_frame, text="📝 Notes", font=("Arial", 11, "bold"),
                      bg="#FF9800", fg="white", command=open_notes_window, pady=8)
notes_btn.pack(side=tk.RIGHT, fill="x", expand=True, padx=(0, 0))

tk.Label(root, text="AI Response:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(5, 5))
result_box = scrolledtext.ScrolledText(root, font=("Arial", 10), height=10, wrap=tk.WORD, bg="#f4f4f9")
result_box.pack(fill="both", expand=True)

# Load the saved API key (if one exists) as soon as the app opens!
load_saved_data()

if __name__ == "__main__":
    root.mainloop()