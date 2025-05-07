import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import sqlite3
from PIL import Image, ImageTk
import subprocess

# Database paths
DB_FOLDER = 'files'
DB_NAME = 'timetable.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

# Placeholder functions
def import_requests():
    print("Import student's requests clicked")

def import_lessons():
    print("Import lessons clicked")

def test_timetable():
    print("Test clicked")

def generate_timetable():
    print("Generate timetable button clicked - attempting to open timetable_display_component.py")
    try:
        # Determine the correct path to timetable_display_component.py within the windows directory
        script_path = os.path.join(os.path.dirname(__file__), 'timetable_display_component.py')
        
        # Use subprocess.Popen to run the script
        # Using pythonw to avoid console window on Windows if available
        python_executable = 'pythonw' if os.name == 'nt' else 'python'
        
        startupinfo = None
        creation_flags = 0
        if os.name == 'nt':  # Windows specific startupinfo to hide console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creation_flags = subprocess.CREATE_NO_WINDOW

        # For timetable display, we want to see its window.
        # The timetable_display_component.py creates its own Tkinter window.
        subprocess.Popen(
            [python_executable, script_path],
            startupinfo=startupinfo,
            # creationflags=creation_flags # Not needed if timetable_display_component is a GUI app
        )
        # Optionally, you might want to close or hide the current step3 window
        # root.destroy() # or root.withdraw()
        print(f"Launched {script_path}")

    except FileNotFoundError:
        messagebox.showerror("File Not Found", f"Error: timetable_display_component.py not found at {script_path}")
        print(f"Error: timetable_display_component.py not found at {script_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not open timetable display: {e}")
        print(f"Error launching timetable_display_component.py: {e}")

def show_help():
    print("Help button clicked")

def go_previous():
    print("Previous clicked")
    # Logic to go back to step 2 or subjects.py based on where we came from
    conn = None
    coming_from_subjects = False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if NAVIGATION_FLAGS table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='NAVIGATION_FLAGS'")
        if cursor.fetchone():
            # Check for the coming_from flag
            cursor.execute("SELECT flag_value FROM NAVIGATION_FLAGS WHERE flag_name = 'coming_from'")
            result = cursor.fetchone()
            if result and result[0] == 'subjects':
                coming_from_subjects = True
                # Reset the flag
                cursor.execute("DELETE FROM NAVIGATION_FLAGS WHERE flag_name = 'coming_from'")
                conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    # Determine which step to go back to
    previous_step = 'subjects.py' if coming_from_subjects else 'step2.py'
    print(f"Going back to {previous_step}...")
    
    try:
        # Use subprocess.Popen instead of os.system to hide console window
        startupinfo = None
        if os.name == 'nt':  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        # Launch previous step
        subprocess.Popen(
            ['pythonw', f'windows\\{previous_step}'],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        root.destroy() # Close current window
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Could not open {previous_step}: {e}")
        print(f"Error opening {previous_step}: {e}")

def check_steps_complete():
    """
    Check if steps 1, 2 and 3 are complete by checking the SETUP_PROGRESS table
    Returns tuple (all_complete, status_dict) where status_dict shows completion status of each step
    """
    conn = None
    status = {
        'step1': False,
        'step2': False,
        'step3': False
    }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if SETUP_PROGRESS table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SETUP_PROGRESS'")
        if cursor.fetchone():
            # Query for each step
            for step in status.keys():
                cursor.execute("SELECT completed FROM SETUP_PROGRESS WHERE step = ?", (step,))
                result = cursor.fetchone()
                if result and result[0] == 1:
                    status[step] = True
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    all_complete = all(status.values())
    return (all_complete, status)

def save_all_data():
    """Save all data collected in steps 1-3 to the database"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Mark step 3 as complete
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SETUP_PROGRESS (
                step TEXT PRIMARY KEY,
                completed INTEGER DEFAULT 0,
                completion_date TEXT
            )
        ''')
        
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT OR REPLACE INTO SETUP_PROGRESS (step, completed, completion_date)
            VALUES (?, ?, ?)
        ''', ('step3', 1, current_time))
        
        # Additional data saving for step 3 goes here
        # ...
        
        conn.commit()
        messagebox.showinfo("Success", "All data has been successfully saved to the database.")
        return True
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to save data: {e}")
        return False
    finally:
        if conn:
            conn.close()

def finish_wizard():
    """Handle finishing the wizard and saving data"""
    all_complete, status = check_steps_complete()
    
    if all_complete:
        # All steps are complete, save all data
        save_all_data()
        root.destroy()
    else:
        # Not all steps are complete, ask user what to do
        incomplete_steps = [step for step, complete in status.items() if not complete]
        incomplete_msg = ", ".join(incomplete_steps)
        
        response = messagebox.askyesno(
            "Incomplete Setup",
            f"The following steps are incomplete: {incomplete_msg}\n\nDo you want to save data anyway and exit?",
            icon=messagebox.WARNING
        )
        
        if response:
            # User wants to save anyway
            if save_all_data():
                root.destroy()
        else:
            # User doesn't want to save, stay on current page
            pass

# --- Main Window ---
root = tk.Tk()
root.title("School Timetable Setup Step 3")
root.state('zoomed')  # Maximize window
root.minsize(800, 700)  # Set minimum window size

# Add fullscreen toggle functionality
def toggle_fullscreen(event=None):
    if root.attributes('-fullscreen'):
        root.attributes('-fullscreen', False)
        root.state('zoomed')
    else:
        root.attributes('-fullscreen', True)

def quit_fullscreen(event=None):
    root.attributes('-fullscreen', False)
    root.state('zoomed')
    
root.bind('<Escape>', quit_fullscreen)  # Escape key exits fullscreen
root.bind('<F11>', toggle_fullscreen)   # F11 toggles fullscreen

# --- Main Layout Frames ---
left_frame = ttk.Frame(root, width=250)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
left_frame.pack_propagate(False) # Prevent frame from shrinking to fit content

right_frame = ttk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# --- Left Frame Content (Image) ---
try:
    img_path = "BoyImage.png" # Assuming image is in the root or adjust path
    img = Image.open(img_path)
    # Resize if needed
    img_width, img_height = img.size
    aspect_ratio = img_height / img_width
    new_width = 230 # Fit within the left_frame width
    new_height = int(new_width * aspect_ratio)
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    boy_image = ImageTk.PhotoImage(img)
    image_label = ttk.Label(left_frame, image=boy_image)
    image_label.pack(pady=20, anchor=tk.CENTER)
except FileNotFoundError:
    error_label = ttk.Label(left_frame, text="Image 'BoyImage.png'\nnot found.", justify=tk.CENTER)
    error_label.pack(pady=20, anchor=tk.CENTER)
except Exception as e:
    error_label = ttk.Label(left_frame, text=f"Error loading image:\n{e}", justify=tk.CENTER)
    error_label.pack(pady=20, anchor=tk.CENTER)

# --- Right Frame Content (Sections) ---

# Section 1: Import other data
import_frame = ttk.LabelFrame(right_frame, text="Import other data", padding="10")
import_frame.pack(fill=tk.X, pady=5)

import_buttons_frame = ttk.Frame(import_frame) # Inner frame for side-by-side buttons
import_buttons_frame.pack(pady=5)

requests_button = ttk.Button(import_buttons_frame, text="Import student's requests", command=import_requests)
requests_button.pack(side=tk.LEFT, padx=10)

lessons_button = ttk.Button(import_buttons_frame, text="Import lessons", command=import_lessons)
lessons_button.pack(side=tk.LEFT, padx=10)

# Section 2: Verify and generate
verify_frame = ttk.LabelFrame(right_frame, text="Verify and generate", padding="10")
verify_frame.pack(fill=tk.X, pady=5)

ttk.Label(verify_frame, text="To generate timetable press the 'Generate timetable' button.").pack(anchor=tk.W, pady=(0, 10))

verify_buttons_frame = ttk.Frame(verify_frame) # Inner frame for buttons
verify_buttons_frame.pack(pady=5)

test_button = ttk.Button(verify_buttons_frame, text="Test", command=test_timetable)
test_button.pack(side=tk.LEFT, padx=10)

gen_button = ttk.Button(verify_buttons_frame, text="Generate timetable", command=generate_timetable)
gen_button.pack(side=tk.LEFT, padx=10)

ttk.Label(verify_frame, 
          text="You can find functions for the generating and the verification of the timetable in the Timetable menu.",
          wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, pady=5)
ttk.Label(verify_frame, 
          text="You use Wizard command in the Specification menu to start the Wizard. You can also find options to change subjects, classes teachers there. You can change all these data at any time.",
          wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, pady=5)

# Section 3: Help
help_frame = ttk.LabelFrame(right_frame, text="Help", padding="10")
help_frame.pack(fill=tk.X, pady=5)

ttk.Label(help_frame, 
          text="Don't forget to read the manual. You can find there detail information about the program, the verification of entries and solutions and many other suggestions.",
          wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, pady=5)

help_button = ttk.Button(help_frame, text="Help", command=show_help)
help_button.pack(pady=10)

# --- Navigation Buttons (Bottom of root) ---
ttk.Separator(root, orient='horizontal').pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0), padx=10)
nav_frame = ttk.Frame(root, padding="10")
nav_frame.pack(side=tk.BOTTOM, fill=tk.X)

spacer_frame = ttk.Frame(nav_frame)
spacer_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)

close_button = ttk.Button(nav_frame, text="Close", command=root.destroy)
close_button.pack(side=tk.RIGHT, padx=5)

finish_button = ttk.Button(nav_frame, text="Finish", command=finish_wizard)
finish_button.pack(side=tk.RIGHT, padx=5)

prev_button = ttk.Button(nav_frame, text="Previous", command=go_previous)
prev_button.pack(side=tk.RIGHT, padx=5)

# --- Run ---
root.mainloop()