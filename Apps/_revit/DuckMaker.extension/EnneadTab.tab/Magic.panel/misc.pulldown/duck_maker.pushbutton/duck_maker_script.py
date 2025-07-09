#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = "Create new button in plugin system with a simple GUI interface. Supports both PyRevit and standalone environments."
__title__ = "Duck\nMaker"
__context__ = "zero-doc"

import os
import shutil
import sys

try:
    from pyrevit import forms
    from pyrevit.loader import sessionmgr
    IS_PYREVIT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox
    from tkinter import filedialog
    IS_PYREVIT = False

class ButtonCreatorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Duck Maker - Create New Button")
        self.root.geometry("400x200")
        self.setup_gui()
        
    def setup_gui(self):
        # Button name input
        ttk.Label(self.root, text="Enter button name:").pack(pady=10)
        self.name_entry = ttk.Entry(self.root, width=40)
        self.name_entry.pack(pady=5)
        self.name_entry.insert(0, "New_Button_Name")
        
        # Create button
        ttk.Button(self.root, text="Create Button", command=self.create_button).pack(pady=20)
        
    def create_button(self):
        func_name = self.name_entry.get().strip()
        if not func_name:
            messagebox.showerror("Error", "Please enter a button name")
            return
            
        folder = filedialog.askdirectory(title="Select button location")
        if not folder:
            return
            
        self.root.destroy()
        create_new_button(func_name, folder)
        
    def run(self):
        self.root.mainloop()

def create_new_button(func_name=None, folder=None):
    if func_name is None:
        if IS_PYREVIT:
            func_name = forms.ask_for_string(
                default="New_Button_Name",
                prompt="Type in the name for new script",
                title="You are going to change the world..."
            )
        else:
            func_name = input("Type in the name for new script:")

    func_name = func_name.replace(" ", "_").lower()

    if folder is None:
        if IS_PYREVIT:
            folder = forms.pick_folder(title="New script location of container pushbutton")
        else:
            folder = filedialog.askdirectory(title="Select button location")
    
    if not folder:
        return

    target_folder = os.path.join(folder, "{}.pushbutton".format(func_name))
    new_location = os.path.join(target_folder, "{}_script.py".format(func_name))

    # Create target folder
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    template_folder = os.path.join(os.path.dirname(__file__), "NAME_OF_THE_BUTTON.BUTTONEXTENSION")
    
    try:
        for file in os.listdir(template_folder):
            shutil.copyfile(
                os.path.join(template_folder, file),
                os.path.join(target_folder, file)
            )
            if "_script" in file:
                new_file_name = file.replace("NAME_OF_THE_BUTTON", func_name)
                os.rename(
                    os.path.join(target_folder, file),
                    os.path.join(target_folder, new_file_name)
                )

        # Update script content
        with open(new_location, 'r') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            line = line.replace('PRETTY_NAME', pretty_name(func_name))
            line = line.replace('NAME_OF_THE_BUTTON', func_name)
            new_lines.append(line)

        with open(new_location, "w") as f:
            f.write("".join(new_lines))

        # Open the created file
        os.startfile(new_location)
        
        # Open icons website
        os.startfile("https://icons8.com/")
        
        if IS_PYREVIT:
            sessionmgr.reload_pyrevit()
        else:
            messagebox.showinfo("Success", "Button created successfully at:\n{}".format(new_location))
            
    except Exception as e:
        if IS_PYREVIT:
            forms.alert("Error creating button: {}".format(str(e)))
        else:
            messagebox.showerror("Error", "Error creating button: {}".format(str(e)))

def pretty_name(name):
    words = name.split('_')
    return ' '.join(word.title() for word in words)

if __name__ == "__main__":
    if IS_PYREVIT:
        create_new_button()
    else:
        app = ButtonCreatorGUI()
        app.run()
