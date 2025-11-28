import tkinter as tk
from tkinter import messagebox
from database import init_db
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

def main():
    # Initialize Database
    init_db()
    
    # Start Application
    root = tk.Tk()
    root.title("Sistema de Casa de Empeño y Microcréditos")
    root.geometry("400x300")
    
    # Hide main window initially (root is just a controller here)
    root.withdraw()
    
    def show_login():
        # Keep reference to prevent GC
        root.login_window = LoginWindow(root, on_login_success)
        
    def on_login_success(user):
        # When login succeeds, open Main Window
        # We pass show_login as a callback for when Main Window closes/logs out
        root.main_window = MainWindow(root, user, on_logout=show_login)

    # Initial launch
    show_login()
    
    root.mainloop()

if __name__ == "__main__":
    main()
