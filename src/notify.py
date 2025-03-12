from threading import Thread
import tkinter as tk
from tkinter import messagebox

def show_and_quit(root, server):
    messagebox.showinfo("Greetings", f"On {server}, the target process has stopped.")
    root.destroy()

def gui_main_loop(server):
    root = tk.Tk()
    root.geometry("1x1")  # Hide the window
    root.resizable(False, False)
    root.after(0, show_and_quit, root, server)  # Show popup immediately after starting
    root.mainloop()
    
def startGUI(server):
    Thread(target=gui_main_loop, args=(server,)).start()
