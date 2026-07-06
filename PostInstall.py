import tkinter as tk

print("Hello World")

class PostInstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # 1. Hauptfenster konfigurieren
        self.title("Post Installer")
        self.geometry("1200x800")
        
        # 2. Widgets initialisieren
        self.create_widgets()

    def create_widgets(self):
        # Alle UI-Elemente werden hier definiert und an 'self' gebunden
        self.label1 = tk.Label(self, text="Welcome to the Post Installer!")
        self.label1.pack()

# Script-Einstiegspunkt
if __name__ == "__main__":
    app = PostInstallerApp()
    app.mainloop()

print("Programm finished")