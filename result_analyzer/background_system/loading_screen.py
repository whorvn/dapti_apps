import tkinter as tk
from tkinter import ttk
import time
import os
import sys
from threading import Thread
import random

class LoadingScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Setup in Progress")
        
        # Make window centered and position it on screen
        window_width = 500
        window_height = 300
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_pos = (screen_width // 2) - (window_width // 2)
        y_pos = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
        
        # Remove window decorations
        self.root.overrideredirect(True)
        
        # Set window always on top
        self.root.attributes('-topmost', True)
        
        # Add a subtle border
        self.root.configure(bg='#f0f0f0')
        self.frame = tk.Frame(root, bg='#f0f0f0', relief=tk.RIDGE, bd=1)
        self.frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)
        
        # App title
        self.title_label = tk.Label(
            self.frame, 
            text="Student Task Analysis", 
            font=("Helvetica", 16, "bold"),
            bg='#f0f0f0'
        )
        self.title_label.pack(pady=20)
        
        # Status message with animation dots
        self.status_var = tk.StringVar()
        self.status_var.set("Setting up environment...")
        self.status_label = tk.Label(
            self.frame,
            textvariable=self.status_var,
            font=("Helvetica", 12),
            bg='#f0f0f0'
        )
        self.status_label.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.frame, 
            orient="horizontal",
            length=400, 
            mode="determinate"
        )
        self.progress.pack(pady=10)
        
        # Installation details
        self.details_var = tk.StringVar()
        self.details_var.set("Installing required packages...")
        self.details_label = tk.Label(
            self.frame,
            textvariable=self.details_var,
            font=("Helvetica", 9),
            fg="#666666",
            bg='#f0f0f0'
        )
        self.details_label.pack(pady=5)
        
        # Animation canvas
        self.canvas = tk.Canvas(self.frame, width=400, height=60, bg='#f0f0f0', highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # Footer text
        footer_text = "© DAPTI Analyzer - v1.0"
        self.footer_label = tk.Label(
            self.frame,
            text=footer_text,
            font=("Helvetica", 8),
            fg="#999999",
            bg='#f0f0f0'
        )
        self.footer_label.pack(side=tk.BOTTOM, pady=10)
        
        # Start animation and progress update
        self.progress_value = 0
        self.dot_count = 0
        self.animation_circles = []
        self.packages = [
            "pandas", "matplotlib", "numpy", 
            "tkinter", "pillow", "openpyxl"
        ]
        self.current_package_index = 0
        
        # Create animation elements
        self.create_animation_objects()
        
        # Start monitoring progress and updating animations
        self.running = True
        Thread(target=self.check_installation_complete).start()
        self.animate_dots()
        self.update_progress()
        self.animate_objects()
    
    def create_animation_objects(self):
        """Create the animation circles on the canvas"""
        for i in range(8):
            x = 50 + i * 40
            y = 30
            circle = self.canvas.create_oval(x-10, y-10, x+10, y+10, fill="#4CAF50", outline="")
            self.animation_circles.append({
                "id": circle,
                "x": x,
                "y": y,
                "dx": 0,
                "dy": 0,
                "phase": i * 0.3
            })
    
    def animate_objects(self):
        """Animate the circles on the canvas"""
        if not self.running:
            return
            
        # Update each circle
        for circle in self.animation_circles:
            # Create a wave-like motion
            time_factor = time.time() * 2 + circle["phase"]
            new_y = circle["y"] + 10 * (2 + (0.8 * self.progress_value / 100)) * (
                abs(round(time_factor % 2) - 0.5) - 0.5
            )
            
            # Move the circle
            self.canvas.moveto(
                circle["id"], 
                circle["x"] - 10, 
                new_y - 10
            )
            
            # Change color based on progress
            progress_color = self.get_color_for_progress(self.progress_value)
            self.canvas.itemconfig(circle["id"], fill=progress_color)
            
        self.root.after(50, self.animate_objects)
    
    def get_color_for_progress(self, progress):
        """Returns a color based on the progress value"""
        if progress < 33:
            return "#4CAF50"  # Green
        elif progress < 66:
            return "#2196F3"  # Blue
        else:
            return "#9C27B0"  # Purple
    
    def animate_dots(self):
        """Animate the dots in the status message"""
        if not self.running:
            return
            
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.status_var.set(f"Setting up environment{dots}")
        self.root.after(500, self.animate_dots)
    
    def update_progress(self):
        """Update the progress bar and installation details"""
        if not self.running:
            return
            
        # Simulate progress
        if self.progress_value < 100:
            # Increment more slowly as we get closer to 100%
            increment = max(1, int((100 - self.progress_value) / 10))
            self.progress_value += random.randint(1, increment)
            if self.progress_value > 100:
                self.progress_value = 100
                
        self.progress["value"] = self.progress_value
        
        # Update package installation details
        if self.progress_value > (self.current_package_index + 1) * (100 / len(self.packages)):
            self.current_package_index = min(self.current_package_index + 1, len(self.packages) - 1)
        
        self.details_var.set(f"Installing {self.packages[self.current_package_index]}...")
        
        self.root.after(300, self.update_progress)
    
    def check_installation_complete(self):
        """Check if the installation is complete by looking for a marker file"""
        marker_file = os.path.join(os.path.dirname(__file__), "installation_complete.tmp")
        print(f"Checking for marker file at: {marker_file}")
        
        max_wait_time = 60  # Maximum seconds to wait before force closing
        start_time = time.time()
        
        while self.running and self.progress_value < 100:
            if os.path.exists(marker_file):
                print(f"Marker file found at: {marker_file}")
                # Set flag to exit the loop
                self.running = False
                break
                
            # Force exit after max wait time
            if time.time() - start_time > max_wait_time:
                print("Maximum wait time exceeded, forcing exit")
                self.running = False
                break
                
            time.sleep(0.5)
        
        # Set progress to 100% and update UI
        self.progress_value = 100
        self.root.after(0, lambda: self.details_var.set("Installation complete!"))
        self.root.after(0, lambda: self.status_var.set("Setup complete!"))
        self.root.after(0, lambda: self.progress.configure(value=100))
        
        # Wait a bit to show 100% before closing
        time.sleep(2)
        
        # Remove the marker file if it exists
        try:
            if os.path.exists(marker_file):
                os.remove(marker_file)
                print(f"Removed marker file: {marker_file}")
        except Exception as e:
            print(f"Error removing marker file: {e}")
        
        # Schedule the window to close
        print("Scheduling window to close")
        self.root.after(500, self.close_window)
    
    def close_window(self):
        """Safely close the window"""
        print("Closing window")
        try:
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Error closing window: {e}")
            sys.exit(0)  # Force exit if necessary

# Only keep the simple initialization for direct execution
if __name__ == "__main__":
    print("Starting loading screen")
    root = tk.Tk()
    app = LoadingScreen(root)
    root.mainloop()
    print("Loading screen closed")
    sys.exit(0)  # Ensure process exits
