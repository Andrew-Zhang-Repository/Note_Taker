import ctypes
import platform

def make_window_invisible(window):
    

    if platform.system() != "Windows":
        print("Stealth mode is only supported on Windows.")
        return

    try:
        
        window.update_idletasks()
        hwnd = int(window.wm_frame(), 16)
        WDA_EXCLUDEFROMCAPTURE = 0x00000011

        result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        
        if not result:
            print("Failed to hide window. Ensure you are on Windows 10 (v2004) or newer.")
        else:
            print("Stealth mode activated successfully!")
            
    except Exception as e:
        print(f"Error applying stealth mode: {e}")