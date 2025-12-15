import tkinter as tk
from tkinter import ttk
import calendar
from datetime import date, datetime

class CalendarDialog(tk.Toplevel):
    def __init__(self, parent, current_date=None, callback=None):
        super().__init__(parent)
        self.withdraw() # Hide until ready
        self.title("Seleccionar Fecha")
        self.callback = callback
        self.grab_set()
        
        # Style
        self.configure(bg="#ffffff")
        self.geometry("250x250")
        self.resizable(False, False)
        
        # Position near parent
        x = parent.winfo_rootx() + 50
        y = parent.winfo_rooty() + 50
        self.geometry(f"+{x}+{y}")
        
        if current_date:
            self.year = current_date.year
            self.month = current_date.month
            self.sel_day = current_date.day
        else:
            today = date.today()
            self.year = today.year
            self.month = today.month
            self.sel_day = today.day
            
        self.setup_ui()
        self.deiconify()
        
    def setup_ui(self):
        # Header (Month/Year + Nav)
        header = tk.Frame(self, bg="#2196F3")
        header.pack(fill=tk.X)
        
        btn_prev = tk.Button(header, text="<", command=self.prev_month, bg="#2196F3", fg="white", relief="flat")
        btn_prev.pack(side=tk.LEFT)
        
        self.lbl_header = tk.Label(header, text=f"{calendar.month_name[self.month]} {self.year}", bg="#2196F3", fg="white", font=("Segoe UI", 10, "bold"))
        self.lbl_header.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        btn_next = tk.Button(header, text=">", command=self.next_month, bg="#2196F3", fg="white", relief="flat")
        btn_next.pack(side=tk.RIGHT)
        
        # Days Grid
        self.frame_days = tk.Frame(self, bg="white")
        self.frame_days.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.render_calendar()
        
    def render_calendar(self):
        # Clear existing
        for widget in self.frame_days.winfo_children():
            widget.destroy()
            
        # Update Header
        # Map english to spanish simply if needed, or rely on locale. 
        # Using simple list for robustness independent of locale setting
        months = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.lbl_header.config(text=f"{months[self.month]} {self.year}")
        
        # Weekday headers
        days = ["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"]
        for i, day in enumerate(days):
            tk.Label(self.frame_days, text=day, bg="white", fg="#757575", font=("Segoe UI", 8)).grid(row=0, column=i, sticky="nsew")
            
        # Month Days
        cal = calendar.Calendar(firstweekday=6) # Sunday first
        month_days = cal.monthdayscalendar(self.year, self.month)
        
        for r, week in enumerate(month_days):
            for c, day in enumerate(week):
                if day != 0:
                    btn = tk.Button(self.frame_days, text=str(day), relief="flat", bg="white", font=("Segoe UI", 9),
                                    command=lambda d=day: self.select_date(d))
                    
                    if day == self.sel_day and self.year == date.today().year and self.month == date.today().month:
                         btn.config(bg="#E3F2FD", fg="#2196F3", font=("Segoe UI", 9, "bold")) # Weak highlight for "today" or selection
                         
                    btn.grid(row=r+1, column=c, sticky="nsew", padx=1, pady=1)

        # Configure grid weight
        for i in range(7):
            self.frame_days.grid_columnconfigure(i, weight=1)
            
    def prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.render_calendar()
        
    def next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.render_calendar()
        
    def select_date(self, day):
        selected_date = date(self.year, self.month, day)
        if self.callback:
            self.callback(selected_date)
        self.destroy()

class DateEntry(tk.Frame):
    def __init__(self, parent, initial_date=None, date_format="%Y-%m-%d"):
        super().__init__(parent)
        self.date_format = date_format # Internal storage format
        self.display_format = "%d/%m/%Y" # User friendly format
        
        self.entry = tk.Entry(self, width=12)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.btn_cal = tk.Button(self, text="📅", command=self.open_calendar, width=3)
        self.btn_cal.pack(side=tk.LEFT, padx=(2, 0))
        
        if initial_date:
            self.set_date(initial_date)
        else:
            self.set_date(date.today())
            
    def open_calendar(self):
        curr = self.get_date_obj()
        CalendarDialog(self.winfo_toplevel(), curr, self.set_date)
        
    def set_date(self, date_obj):
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, self.date_format).date()
            except:
                pass # Keep as is if fail
                
        if isinstance(date_obj, (date, datetime)):
            self.entry.delete(0, tk.END)
            self.entry.insert(0, date_obj.strftime(self.display_format))
            self.selected_date = date_obj
            
    def get_date(self):
        # Returns string in Internal Format (YYYY-MM-DD by default)
        return self.selected_date.strftime(self.date_format)
        
    def get_date_obj(self):
        return self.selected_date
