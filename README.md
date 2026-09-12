# NoteTaker
---
An app built on python, tkinter to provide you with an invisible note app only visible client sided. Has opacity adjustable settings, text colors, and AI integration with recording from speaker source to transcription capabilities. AI integration is using free Gemini API keys that can be inputted in the config user chooses to use this feature if not the rest of the app still can be used.


### Hotkeys and basic info:
- CTRL + Shift + u (Increase opacity of selected overlay)
- CTRL + Shift + d (Increase opacity of selected overlay)
- CTRL + Shift + t (Change text color of current window)
- CTRL + b (Change border of current window)
- CTRL + x (Quit out of all windows)
- Press settings to input AI model name and API key


---

### Sample Run Visualization with privacy off (In action this will not be viewable in anything let alone screenshots)

<div align="center">
  <img src="https://github.com/user-attachments/assets/05b44ba2-1ae9-4c29-8a29-616f188e2d44" alt="Main Overlay" width="800"/>
  <p><i>Main overlay</i></p>
</div>

<br>

<div align="center">
  <img src="https://github.com/user-attachments/assets/128fd829-4dd0-44b3-a855-3dbdd4315730" alt="Pop Out Feature" width="800"/>
  <p><i>Figure 2: Note being popped out </i></p>
</div>

<br>

<div align="center">
  <img src="https://github.com/user-attachments/assets/b90c92fd-d5d2-4c99-9ddf-2a1b16accc4c" alt="LLM Integeration" width="800"/>
  <p><i>Figure 3: LLM integeration.</i></p>
</div>


<div align="center">
  <img src="https://github.com/user-attachments/assets/d8f78247-d3a5-44cc-80c3-ec13cbece4a7" alt="All Overlays" width="800"/>
  <p><i>Figure 4: All overlays in action.</i></p>
</div>


<div align="center">
  <img src="https://github.com/user-attachments/assets/a9e2ed7f-5e6d-4ef5-9300-4084cf7a0bbf" alt="Invisbility On" width="800"/>
  <p><i>Figure 5: What it actually looks like.</i></p>
</div>

---

### How to build from source if you are making any edits



```bash 

# Build

pip install -r requirements.txt
cd ./src
pyinstaller --noconsole --name "NoteTaker" overlay.py


```

---

### Disclaimer and Conditions
- No Cheating on exams or assessments
- Violating academic integrity policies
- Breaking terms of service of any platform
-Any illegal or unethical activities
- You are solely responsible for how you use this software.