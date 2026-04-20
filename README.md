# 🕵️‍♂️ Invisibility Cloak: AI Screen Assistant
A Python-based desktop assistant that uses Google Gemini 1.5 Flash to analyze your screen in real-time. Designed with a custom "Stealth Mode," this application remains completely invisible to screen-sharing software, recorders, and screenshots.

# 🚀 Features
Anti-Screen Capture: Uses the Windows SetWindowDisplayAffinity API to prevent the UI from appearing in Discord, Zoom, Teams, or OBS.

Dual-Mode AI: * 📸 + Ask: Captures your current screen and asks Gemini for analysis.

# 💬 Text Only: Chat with Gemini directly without screen context.

Secret Notes: A pop-out, auto-saving notepad that also inherits the "invisibility cloak" for private drafting.

Global Hotkey: Toggle the entire app's visibility instantly with Ctrl + Shift + Space.

Persistent Settings: Automatically saves your API key and notes locally so you don't have to re-enter them.

# 🛠️ Installation
Clone the repository:

Bash
git clone https://github.com/YOUR_USERNAME/Invisibility-Cloak-AI.git
cd Invisibility-Cloak-AI
Install Dependencies:

Bash
pip install mss Pillow google-genai keyboard
(Note: ctypes and tkinter are built into Python).

Run the App:

Bash
python main.py
# 📖 How to Use
API Key: Get a free API key from Google AI Studio. Paste it into the 🔑 API Key field at the top of the app. It will be saved securely for next time.

Stealth Check: Open a screen share (like Discord) or take a Windows screenshot (Win+Shift+S). You will see that the app window simply doesn't appear in the capture!

Shortcuts:

Ctrl + Shift + Space: Hide or Show the app.

📝 Notes: Opens the invisible secondary window for taking notes.

# 🏗️ Technical Deep Dive
The "Invisibility" is handled by the apply_invisibility_cloak function. It interfaces with user32.dll to set the window's display affinity to WDA_EXCLUDEFROMCAPTURE (hex value 0x11 or 17).

Python
# The magic behind the cloak
hwnd = int(window.wm_frame(), 16)
ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 17)