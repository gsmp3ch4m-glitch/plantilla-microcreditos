import sys
import traceback
import tkinter as tk

print("DEBUG: Starting script")

try:
    print("DEBUG: Importing database")
    from database import init_db
    print("DEBUG: init_db imported")
    
    print("DEBUG: Importing LoginWindow")
    from ui.login_window import LoginWindow
    print("DEBUG: LoginWindow imported")
    
    print("DEBUG: Importing MainWindow")
    from ui.main_window import MainWindow
    print("DEBUG: MainWindow imported")

    def main():
        print("DEBUG: Running init_db")
        init_db()
        print("DEBUG: init_db done")
        
        print("DEBUG: Creating root")
        root = tk.Tk()
        root.title("Debug App")
        # root.withdraw()
        print("DEBUG: Root created")
        
        def show_login():
            print("DEBUG: Creating LoginWindow")
            LoginWindow(root, on_login_success)
            print("DEBUG: LoginWindow created")
            
        def on_login_success(user):
            print(f"DEBUG: Login success for {user}")
            MainWindow(root, user, on_logout=show_login)

        show_login()
        
        print("DEBUG: Entering mainloop")
        root.mainloop()
        print("DEBUG: Exited mainloop")

    if __name__ == "__main__":
        main()

except Exception:
    print("DEBUG: Exception caught!")
    traceback.print_exc()
    sys.exit(1)
