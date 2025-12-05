import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class SetupWizard(tk.Toplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.title("Asistente de Configuración")
        self.geometry("500x400")
        self.resizable(False, False)
        self.on_complete = on_complete
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="Bienvenido al Sistema", font=("Helvetica", 18, "bold"), fg="white", bg="#2c3e50").pack(pady=20)
        
        # Content
        content_frame = tk.Frame(self, padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        tk.Label(content_frame, text="Por favor, seleccione el modo de uso:", font=("Helvetica", 12)).pack(pady=10)
        
        # Mode Selection
        self.mode_var = tk.StringVar(value="CLOUD")
        
        frame_cloud = tk.LabelFrame(content_frame, text="Modo Nube (Recomendado)", padx=10, pady=10)
        frame_cloud.pack(fill="x", pady=5)
        
        tk.Radiobutton(frame_cloud, text="Sincronizar con Base de Datos en la Nube", variable=self.mode_var, value="CLOUD", command=self.toggle_inputs).pack(anchor="w")
        tk.Label(frame_cloud, text="Requiere internet. Ideal para múltiples usuarios.", fg="gray").pack(anchor="w", padx=20)
        
        # Cloud Inputs
        self.input_frame = tk.Frame(frame_cloud)
        self.input_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(self.input_frame, text="Supabase URL:").grid(row=0, column=0, sticky="w")
        self.entry_url = tk.Entry(self.input_frame, width=30)
        self.entry_url.grid(row=0, column=1, sticky="e")
        
        tk.Label(self.input_frame, text="Supabase Key:").grid(row=1, column=0, sticky="w")
        self.entry_key = tk.Entry(self.input_frame, width=30, show="*")
        self.entry_key.grid(row=1, column=1, sticky="e")
        
        tk.Label(self.input_frame, text="DB URI:").grid(row=2, column=0, sticky="w")
        self.entry_uri = tk.Entry(self.input_frame, width=30, show="*")
        self.entry_uri.grid(row=2, column=1, sticky="e")
        
        # Local Mode
        frame_local = tk.LabelFrame(content_frame, text="Modo Local", padx=10, pady=10)
        frame_local.pack(fill="x", pady=5)
        
        tk.Radiobutton(frame_local, text="Usar solo en esta computadora", variable=self.mode_var, value="LOCAL", command=self.toggle_inputs).pack(anchor="w")
        tk.Label(frame_local, text="No requiere internet. Los datos se guardan aquí.", fg="gray").pack(anchor="w", padx=20)
        
        # Save Button
        tk.Button(content_frame, text="Guardar y Continuar", command=self.save_config, bg="#27ae60", fg="white", font=("Helvetica", 10, "bold"), height=2).pack(fill="x", pady=20)
        
    def toggle_inputs(self):
        if self.mode_var.get() == "CLOUD":
            for child in self.input_frame.winfo_children():
                child.configure(state='normal')
        else:
            for child in self.input_frame.winfo_children():
                child.configure(state='disabled')

    def save_config(self):
        mode = self.mode_var.get()
        secrets = {"MODE": mode}
        
        if mode == "CLOUD":
            url = self.entry_url.get().strip()
            key = self.entry_key.get().strip()
            uri = self.entry_uri.get().strip()
            
            if not url or not key or not uri:
                messagebox.showerror("Error", "Por favor complete todos los campos para el modo Nube.")
                return
            
            secrets["SUPABASE_URL"] = url
            secrets["SUPABASE_KEY"] = key
            secrets["DB_URI"] = uri
            
        # Save to secrets.json
        try:
            secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'secrets.json')
            with open(secrets_path, 'w') as f:
                json.dump(secrets, f, indent=4)
            
            messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
            self.on_complete()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")

    def on_close(self):
        if messagebox.askokcancel("Salir", "¿Desea salir de la configuración? La aplicación se cerrará."):
            self.destroy()
            exit()
