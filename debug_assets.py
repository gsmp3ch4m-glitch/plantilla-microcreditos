import tkinter as tk
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'src'))

from ui.assets_window import AssetsWindow
from database import init_db

def test_assets_window():
    print("Initializing DB...")
    init_db()
    
    print("Creating Root...")
    root = tk.Tk()
    root.withdraw() # Hide root
    
    print("Launching AssetsWindow...")
    try:
        # Dummy user data
        user_data = {'username': 'admin', 'role': 'admin', 'full_name': 'Admin Test'}
        
        window = AssetsWindow(root, user_data)
        window.protocol("WM_DELETE_WINDOW", root.destroy)
        
        print("AssetsWindow created successfully. Loop starting...")
        # Auto close after 2 seconds to prove it launched
        root.after(2000, root.destroy)
        
        root.mainloop()
        print("Test passed.")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_assets_window()
