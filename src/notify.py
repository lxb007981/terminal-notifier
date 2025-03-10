import tkinter as tk
from tkinter import messagebox

def show_and_quit(root):
    messagebox.showinfo("Greetings", "The target process has stopped.")
    root.destroy()

def startGUI():
    root = tk.Tk()
    root.geometry("1x1")  # Hide the window
    root.resizable(False, False)
    root.after(0, show_and_quit, root)  # Show popup immediately after starting
    root.mainloop()