import tkinter as tk
from tkinter import ttk
from tkinter import messagebox # Import messagebox
import sqlite3               # Import sqlite3
import os                    # Import os to construct path
import subprocess            # Import subprocess for launching processes

# --- Database Setup ---
DB_FOLDER = 'files'
DB_NAME = 'timetable.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

def init_db():
    """Initialize the database and create the config table if it doesn't exist."""
    # Ensure the directory exists
    os.makedirs(DB_FOLDER, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SCHOOL_CONFIG (
            config_id INTEGER PRIMARY KEY, -- Use a fixed ID for single config
            school_name TEXT NOT NULL,
            academic_year TEXT,
            registration_name TEXT,
            periods_per_day INTEGER,
            num_days INTEGER,
            weekend_type TEXT,
            use_multiweek BOOLEAN
        )
    ''')
    conn.commit()
    return conn

def save_config(show_message=True):
    """Retrieve data from UI and save to the database."""
    # Retrieve values
    school_name = school_name_entry.get()
    academic_year = academic_year_entry.get()
    # reg_name = registration_name_entry.get() # Currently readonly, decide if needed
    periods = periods_spinbox.get()
    days = days_spinbox.get()
    weekend = weekend_combobox.get()
    multiweek = multiweek_var.get()

    # Basic Validation
    if not school_name:
        messagebox.showwarning("Input Error", "School Name cannot be empty.")
        return False

    try:
        periods_int = int(periods)
        days_int = int(days)
    except ValueError:
        messagebox.showerror("Input Error", "Periods per day and Number of days must be integers.")
        return False

    conn = None
    try:
        conn = init_db() # Get connection
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO SCHOOL_CONFIG (
                config_id, school_name, academic_year, registration_name, 
                periods_per_day, num_days, weekend_type, use_multiweek
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (1, school_name, academic_year, "", periods_int, days_int, weekend, multiweek))
        
        # Create a flag table to track completion of steps
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SETUP_PROGRESS (
                step TEXT PRIMARY KEY,
                completed INTEGER DEFAULT 0,
                completion_date TEXT
            )
        ''')
        
        # Mark step 1 as complete
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT OR REPLACE INTO SETUP_PROGRESS (step, completed, completion_date)
            VALUES (?, ?, ?)
        ''', ('step1', 1, current_time))
        
        # Save timetable structure info for timetable_generator.py
        # Create table for timetable settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TIMETABLE_SETTINGS (
                setting_name TEXT PRIMARY KEY,
                setting_value TEXT,
                last_updated TEXT
            )
        ''')
        
        # Store days and periods settings
        cursor.execute('''
            INSERT OR REPLACE INTO TIMETABLE_SETTINGS (setting_name, setting_value, last_updated)
            VALUES (?, ?, ?)
        ''', ('NUM_PERIODS', str(periods_int), current_time))
        
        cursor.execute('''
            INSERT OR REPLACE INTO TIMETABLE_SETTINGS (setting_name, setting_value, last_updated)
            VALUES (?, ?, ?)
        ''', ('NUM_DAYS', str(days_int), current_time))
        
        # Store which days are enabled based on the number of days
        days_enabled = []
        all_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for i in range(min(days_int, 7)):
            days_enabled.append(all_days[i])
        
        cursor.execute('''
            INSERT OR REPLACE INTO TIMETABLE_SETTINGS (setting_name, setting_value, last_updated)
            VALUES (?, ?, ?)
        ''', ('DAYS_ENABLED', ','.join(days_enabled), current_time))
        
        conn.commit()
        if show_message:
            messagebox.showinfo("Success", "Configuration saved successfully!")
        return True
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to save configuration: {e}")
        return False
    finally:
        if conn:
            conn.close()

def change_registration():
    print("Change Registration Name clicked")

def rename_periods():
    print("Rename Periods clicked")

def rename_days():
    print("Rename Days clicked")

def go_previous():
    print("Previous clicked")

def go_next():
    print("Next clicked - Checking navigation path...")
    
    # Save configuration silently before proceeding
    if not save_config(show_message=False):
        # If saving failed, don't proceed
        return
    
    # Check if we're coming from step2 (user pressed "Previous" in step2)
    conn = None
    coming_from_step2 = False
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='NAVIGATION_FLAGS'")
        if cursor.fetchone():
            # Check for the coming_from flag
            cursor.execute("SELECT flag_value FROM NAVIGATION_FLAGS WHERE flag_name = 'coming_from'")
            result = cursor.fetchone()
            if result and result[0] == 'step2':
                coming_from_step2 = True
                # Reset the flag
                cursor.execute("DELETE FROM NAVIGATION_FLAGS WHERE flag_name = 'coming_from'")
                conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    # Determine which step to go to
    next_step = 'step3.py' if coming_from_step2 else 'step2.py'
    print(f"Proceeding to {next_step}...")
    
    try:
        # Use subprocess.Popen instead of os.system to hide console window
        # startupinfo hides the console on Windows
        startupinfo = None
        if os.name == 'nt':  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        # Launch the next step
        subprocess.Popen(
            ['pythonw', f'windows\\{next_step}'],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        root.destroy()  # Close current window
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Could not open {next_step}: {e}")
        print(f"Error opening {next_step}: {e}")

# --- Main Window ---
root = tk.Tk()
root.title("Wizard: Step 1 of 7")
# Set initial size (adjust as needed)
root.geometry("700x600")

# --- Main Content Frame ---
main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill=tk.BOTH, expand=True)

# --- Section 1: School Information ---
school_frame = ttk.LabelFrame(main_frame, text="School Information", padding="10")
school_frame.pack(fill=tk.X, pady=10)
school_frame.columnconfigure(1, weight=1) # Make entry expand

# Widgets for School Information
ttk.Label(school_frame, text="Name of the school:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
school_name_entry = ttk.Entry(school_frame)
school_name_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)

ttk.Label(school_frame, text="Academic year:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
academic_year_entry = ttk.Entry(school_frame)
academic_year_entry.insert(0, "2025/2026") # Pre-fill
academic_year_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

ttk.Label(school_frame, text="Registration name:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
registration_name_entry = ttk.Entry(school_frame, state="readonly") # Placeholder, make readonly
registration_name_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
change_button = ttk.Button(school_frame, text="Change", command=change_registration)
change_button.grid(row=2, column=2, padx=5, pady=5, sticky=tk.E)


# --- Section 2: Timetable Structure ---
structure_frame = ttk.LabelFrame(main_frame, text="Timetable Structure", padding="10")
structure_frame.pack(fill=tk.X, pady=10)
structure_frame.columnconfigure(1, weight=1) # Allow dropdowns/buttons to align
structure_frame.columnconfigure(3, weight=1) # Allow Weekend dropdown to align right

# Widgets for Timetable Structure
ttk.Label(structure_frame, text="Periods per day:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
periods_spinbox = ttk.Spinbox(structure_frame, from_=1, to=20, width=5)
periods_spinbox.set(7)
periods_spinbox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
rename_periods_button = ttk.Button(structure_frame, text="Bell times / Rename periods", command=rename_periods)
rename_periods_button.grid(row=0, column=2, columnspan=2, padx=5, pady=5, sticky=tk.W)

ttk.Label(structure_frame, text="Number of days:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
days_spinbox = ttk.Spinbox(structure_frame, from_=1, to=7, width=5)
days_spinbox.set(5)
days_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
rename_days_button = ttk.Button(structure_frame, text="Rename days", command=rename_days)
rename_days_button.grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky=tk.W)

ttk.Label(structure_frame, text="Weekend:").grid(row=2, column=2, padx=5, pady=5, sticky=tk.E) # Align label right
weekend_options = ["Saturday - Sunday", "Friday - Saturday", "Sunday", "None"]
weekend_combobox = ttk.Combobox(structure_frame, values=weekend_options, state="readonly", width=18)
weekend_combobox.set("Saturday - Sunday")
weekend_combobox.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W) # Align combo box left relative to its cell


# --- Section 3: Multi-week Timetable ---
multiweek_frame = ttk.LabelFrame(main_frame, text="Multi-week Option", padding="10")
multiweek_frame.pack(fill=tk.X, pady=10)

# Widgets for Multi-week
multiweek_var = tk.BooleanVar()
multiweek_check = ttk.Checkbutton(
    multiweek_frame,
    text="I want to create multi term or multi-week timetable that will be different in each week or term",
    variable=multiweek_var
)
multiweek_check.pack(anchor=tk.W, padx=5, pady=5)

# --- Section 4: Navigation ---
ttk.Separator(root, orient='horizontal').pack(fill=tk.X, pady=5, padx=10)
nav_frame = ttk.Frame(root, padding="10")
nav_frame.pack(fill=tk.X)

# Use spacer frames to push buttons to the right
spacer_frame = ttk.Frame(nav_frame)
spacer_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)

close_button = ttk.Button(nav_frame, text="Close", command=root.destroy)
close_button.pack(side=tk.RIGHT, padx=5)

next_button = ttk.Button(nav_frame, text="Next", command=go_next)
next_button.pack(side=tk.RIGHT, padx=5)

prev_button = ttk.Button(nav_frame, text="Previous", command=go_previous, state="disabled") # Initially disabled
prev_button.pack(side=tk.RIGHT, padx=5)


# --- Run ---
conn = init_db() # Initialize DB and table on startup
conn.close()
root.mainloop() 