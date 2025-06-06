import tkinter as tk
from tkinter import messagebox
import time
import sys
import threading
import importlib
from PIL import Image, ImageTk

# Preload modules in background
def preload_modules():
    try:
        global VirtualPainter
        import VirtualPainter
        import cv2
        import numpy as np
        import HandTrackingModule
        import KeyboardInput
    except Exception as e:
        print(f"Preloading error: {e}")

class Launcher:
    def __init__(self):
        self.CORRECT_CODE = "hYwfg"
        # Define global font settings
        self.title_font = ("Arial", 48, "bold")
        self.normal_font = ("Arial", 18)
        self.loading_font = ("Arial", 24)
        
        # Create a single root window to be reused
        self.root = tk.Tk()
        self.root.title("Beyond The Brush")
        self.root.geometry("1280x720")  # Exact size matching VirtualPainter
        self.root.resizable(False, False)  # Prevent resizing
        
        # Set the window icon
        try:
            # For Windows, use the .ico file directly with wm_iconbitmap
            if sys.platform == "win32":
                self.root.wm_iconbitmap("icon/app.ico")
            else:
                # For other platforms, use a PNG with PhotoImage
                icon_img = tk.PhotoImage(file="icon/app.ico")
                self.root.iconphoto(True, icon_img)
        except Exception as e:
            print(f"Could not set icon: {e}")
            # Fallback: try to load icon using PIL which has better format support
            try:
                from PIL import Image, ImageTk
                icon = Image.open("icon/app.ico")
                icon_photo = ImageTk.PhotoImage(icon)
                self.root.iconphoto(True, icon_photo)
            except Exception as e2:
                print(f"Fallback icon loading also failed: {e2}")
        
        # Set up protocol to force close when X button is clicked
        self.root.protocol("WM_DELETE_WINDOW", self.force_close)
        
        # Center the window on screen
        self.center_window()
        
        # Start preloading in background during loading screen
        self.preload_thread = threading.Thread(target=preload_modules)
        self.preload_thread.daemon = True
        self.preload_thread.start()
        
        self.show_loading_screen()
        
        # Only call mainloop once, at the end of initialization
        self.root.mainloop()

    def center_window(self):
        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width - 1280) // 2
        y = (screen_height - 720) // 2
        
        # Set the position
        self.root.geometry(f"1280x720+{x}+{y}")

    def show_loading_screen(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        canvas = tk.Canvas(self.root, width=1280, height=720)
        canvas.pack()
        
        # Background - #383232 as requested
        bg_color = "#383232"
        canvas.create_rectangle(0, 0, 1280, 720, fill=bg_color, outline="")
        
        # Try to load logo image
        try:
            logo_img = Image.open("icon/logo.png")
            logo_img = logo_img.resize((200, 200))
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            canvas.create_image(610, 150, image=self.logo_photo)
        except FileNotFoundError:
            print("Logo image not found, using text instead")
            canvas.create_text(610, 150, text="Beyond The Brush",
                               font=self.title_font, fill="white")

        # Loading text with loading font
        canvas.create_text(610, 360, text="Loading...",
                           font=self.loading_font, fill="white")

        # Progress bar
        progress = canvas.create_rectangle(410, 400, 410, 430, fill="#3498db", outline="")

        # Animate progress bar
        for i in range(1, 101):
            # Check if window still exists before updating
            try:
                canvas.coords(progress, 410, 400, 410 + (i * 4), 430)
                self.root.update()
                time.sleep(0.03)
            except tk.TclError:
                # Window was closed during loading
                return

        self.show_entry_page()

    def show_entry_page(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Background - #383232
        bg_color = "#383232"
        canvas = tk.Canvas(self.root, width=1280, height=720, bg=bg_color)
        canvas.pack()

        # Center everything vertically with more spacing
        center_y = 360  # Middle of 720
        logo_spacing = 150   # Increased spacing for logo
        button_spacing = 120  # Spacing for button

        # Try to load logo image
        try:
            logo_img = Image.open("icon/app.ico")
            logo_img = logo_img.resize((200, 200))
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            # Position logo higher up - center horizontally at 610 (half of 1220)
            canvas.create_image(610, center_y - logo_spacing, image=self.logo_photo)
            
            # Show title text lower with more space between logo
            canvas.create_text(610, center_y, text="Beyond The Brush",
                              font=self.title_font, fill="white")
        except FileNotFoundError:
            print("Logo image not found, using text instead")
            # If no logo, just show the title text centered
            canvas.create_text(610, center_y, text="Beyond The Brush",
                              font=self.title_font, fill="white")

        # Default role to student
        self.role_var = tk.StringVar(value="student")

        # Enter button lower - centered horizontally
        enter_btn = tk.Button(self.root, text="ENTER", font=self.normal_font,
                              command=self.launch_application, bg="#ff00ff", fg="white",
                              activebackground="#cc00cc", activeforeground="white")
        enter_btn.place(x=510, y=center_y + button_spacing, width=200, height=60)
        
        # Exit button - green color, positioned below enter button
        exit_btn = tk.Button(self.root, text="EXIT", font=self.normal_font,
                             command=self.force_close, bg="#00cc00", fg="white",
                             activebackground="#009900", activeforeground="white")
        exit_btn.place(x=510, y=center_y + button_spacing + 80, width=200, height=60)

        self.root.bind('<Return>', lambda event: self.launch_application())
        # Don't call mainloop here - it will be called once at the end of __init__

    def launch_application(self):
        # Close entry window and launch the application
        self.root.destroy()
        self.launch_VirtualPainter_program()

    def launch_VirtualPainter_program(self):
        # Get the selected role
        role = self.role_var.get()

        # Determine if we're running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            try:
                # Import the module directly
                import VirtualPainter
                # Execute VirtualPainter directly by running its main code
                print("Launching VirtualPainter as frozen application...")
                # Just run the module's code directly
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch VirtualPainter: {str(e)}")
                print(f"Error launching VirtualPainter: {e}")
        else:
            # Running as normal Python script
            try:
                print("Launching VirtualPainter as Python script...")
                # Use subprocess to run VirtualPainter.py as a separate process
                # This avoids Tkinter threading issues
                import subprocess
                subprocess.Popen([sys.executable, "VirtualPainter.py", role])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch VirtualPainter: {str(e)}")
                print(f"Error launching VirtualPainter: {e}")
                # Fallback: try direct import as last resort
                try:
                    import VirtualPainter
                    print("Fallback: Imported VirtualPainter module directly")
                except Exception as e2:
                    print(f"Fallback import also failed: {e2}")

    def force_close(self):
        """Force close the application when X button is clicked"""
        self.root.destroy()
        sys.exit(0)  # Force exit the program


if __name__ == "__main__":
    try:
        launcher = Launcher()
    except KeyboardInterrupt:
        print("Application terminated by user")
        sys.exit(0)
