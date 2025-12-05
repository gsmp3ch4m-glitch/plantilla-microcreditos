import tkinter as tk
from database import init_db
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from utils.backup_manager import BackupManager
import atexit
import os

def on_exit(backup_manager):
    print("Realizando copia de seguridad automática...")
    backup_manager.create_backup(trigger='close')

def main():

    
    root = tk.Tk()
    root.title("Sistema de Casa de Empeño y Microcréditos")
    root.geometry("400x300")
    root.withdraw() # Hide root initially
    
    def start_app():
        # Initialize DB after config is ready
        init_db()
        
        # Initialize Backup Manager
        backup_manager = BackupManager()
        backup_manager.check_and_run_auto_backup()
        
        # Register backup on exit
        atexit.register(on_exit, backup_manager)
        
        # Show Login
        show_login()

    def show_login():
        root.login_window = LoginWindow(root, on_login_success)
        
    def on_login_success(user):
        root.main_window = MainWindow(root, user, on_logout=show_login)

    start_app()
    
    root.mainloop()

if __name__ == "__main__":
    main()
