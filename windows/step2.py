import tkinter as tk
from tkinter import ttk
import os
import sqlite3
from tkinter import messagebox
import subprocess

# Database paths
DB_FOLDER = 'files'
DB_NAME = 'timetable.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

# Placeholder functions for navigation
def go_previous():
    print("Previous clicked - Going back to step 1")
    # Set a flag in the database indicating we're coming from step2
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create or update navigation flags table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS NAVIGATION_FLAGS (
                flag_name TEXT PRIMARY KEY,
                flag_value TEXT
            )
        ''')
        
        # Set flag that we're coming from step2
        cursor.execute('''
            INSERT OR REPLACE INTO NAVIGATION_FLAGS (flag_name, flag_value)
            VALUES (?, ?)
        ''', ('coming_from', 'step2'))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    # Go back to step1
    try:
        # Use subprocess.Popen instead of os.system to hide console window
        startupinfo = None
        if os.name == 'nt':  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        # Launch step1
        subprocess.Popen(
            ['pythonw', 'windows\\step1.py'],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        root.destroy() # Close current window
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Could not open Step 1: {e}")
        print(f"Error opening step1.py: {e}")

def save_step2_data():
    """Save Step 2 selections to the database"""
    conn = None
    try:
        # Create database folder if it doesn't exist
        os.makedirs(DB_FOLDER, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SCHOOL_CHARACTERISTICS (
                id INTEGER PRIMARY KEY,
                course_word TEXT,
                organized_classes TEXT,
                individual_schedule TEXT,
                options TEXT,
                multiple_buildings TEXT,
                different_weeks TEXT
            )
        ''')
        
        # Get values from the UI
        course_word = course_word_var.get()
        organized_classes = organized_classes_var.get()
        individual_schedule = individual_schedule_var.get()
        options = options_var.get()
        multiple_buildings = multiple_buildings_var.get()
        different_weeks = different_weeks_var.get()
        
        # Insert or update data
        cursor.execute('''
            INSERT OR REPLACE INTO SCHOOL_CHARACTERISTICS (
                id, course_word, organized_classes, individual_schedule, 
                options, multiple_buildings, different_weeks
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (1, course_word, organized_classes, individual_schedule, options, multiple_buildings, different_weeks))
        
        # Create progress tracking table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SETUP_PROGRESS (
                step TEXT PRIMARY KEY,
                completed INTEGER DEFAULT 0,
                completion_date TEXT
            )
        ''')
        
        # Mark step 2 as complete
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT OR REPLACE INTO SETUP_PROGRESS (step, completed, completion_date)
            VALUES (?, ?, ?)
        ''', ('step2', 1, current_time))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to save Step 2 data: {e}")
        return False
    finally:
        if conn:
            conn.close()

def go_next():
    print("Next clicked")
    # Save data to database
    if save_step2_data():
        print("Step 2 data saved successfully")
        # Proceed to subjects.py instead of step3.py
        print("Proceeding to Subjects Management...")
        try:
            # Use subprocess.Popen instead of os.system to hide console window
            startupinfo = None
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
            # Launch subjects.py
            subprocess.Popen(
                ['pythonw', 'windows\\subjects.py'],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            root.destroy() # Close current window
        except Exception as e:
            messagebox.showerror("Navigation Error", f"Could not open Subjects Management: {e}")
            print(f"Error opening subjects.py: {e}")
    else:
        print("Failed to save Step 2 data")

# --- Main Window ---
root = tk.Tk()
root.title("School Timetable Setup Step 2")
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

# Style for radiobuttons to look like links (basic attempt)
style = ttk.Style(root)
style.configure("Link.TRadiobutton", padding=0, relief="flat", background=root.cget('bg')) # Match background
style.map("Link.TRadiobutton", background=[('active', root.cget('bg'))]) # Keep background on hover

# --- Top Labels ---
ttk.Label(root, text="Wizard: Step 2 of 7", font=('Segoe UI', 14, 'bold')).pack(pady=(10, 0))
ttk.Label(root, text="Please tell us a bit more about your school. Do not worry if you are not sure, you can change this anytime later:",
          font=('Segoe UI', 10), wraplength=750, justify=tk.LEFT).pack(pady=(5, 10), padx=20, anchor=tk.W)

# --- Scrollable Frame Setup ---
main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

canvas = tk.Canvas(main_frame)
scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# --- Question Sections --- (Inside scrollable_frame)
def create_question_frame(parent, question_text):
    frame = ttk.Frame(parent, padding=10, borderwidth=1, relief="solid")
    frame.pack(fill=tk.X, pady=5, padx=5)
    frame.columnconfigure(1, weight=1) # Allow radio buttons to space out if needed

    # Icon placeholder (column 0)
    # ttk.Label(frame, text="ICON").grid(row=0, column=0, rowspan=3, padx=10, sticky=tk.N)

    question_label = ttk.Label(frame, text=question_text, wraplength=500, justify=tk.LEFT)
    question_label.grid(row=0, column=1, columnspan=3, padx=10, pady=5, sticky=tk.W)

    return frame

# Question 1: Course vs Subject
q1_frame = create_question_frame(scrollable_frame, "Which word do you use in your school \'Course\' or \'Subject\'?")
course_word_var = tk.StringVar(value="Not sure")
options1 = [("Subject", "Subject"), ("Course", "Course"), ("Not sure", "Not sure")]
row_num = 1
col_num = 1
for text, val in options1:
    rb = ttk.Radiobutton(q1_frame, text=text, variable=course_word_var, value=val, style="Link.TRadiobutton", takefocus=False)
    rb.grid(row=row_num, column=col_num, sticky=tk.W, padx=10)
    row_num += 1

# Question 2: Organized Classes
q2_frame = create_question_frame(scrollable_frame, "Students are organized into classes(groups) that have the same(nearly the same) schedule. Like 6A, 603, 6.3, 6HT etc. Sometimes they are divided into groups.")
organized_classes_var = tk.StringVar(value="Not sure")
options2 = [("Yes", "Yes"), ("No", "No"), ("Not sure", "Not sure")]
row_num = 1
col_num = 1
for text, val in options2:
    rb = ttk.Radiobutton(q2_frame, text=text, variable=organized_classes_var, value=val, style="Link.TRadiobutton", takefocus=False)
    rb.grid(row=row_num, column=col_num, sticky=tk.W, padx=10)
    row_num += 1
q2_frame.configure(style='Selected.TFrame') # Example of highlighting one section (adjust style def if needed)
style.configure("Selected.TFrame", background="#e0ffe0") # Light green background

# Question 3: Individual Schedules
q3_frame = create_question_frame(scrollable_frame, "Some or all students have individual schedule based on their course requests.")
individual_schedule_var = tk.StringVar(value="Not sure")
options3 = [("Yes", "Yes"), ("No", "No"), ("Not sure", "Not sure")]
row_num = 1
col_num = 1
for text, val in options3:
    rb = ttk.Radiobutton(q3_frame, text=text, variable=individual_schedule_var, value=val, style="Link.TRadiobutton", takefocus=False)
    rb.grid(row=row_num, column=col_num, sticky=tk.W, padx=10)
    row_num += 1

# Question 4: Options/Electives
q4_frame = create_question_frame(scrollable_frame, "We use Options: student can select one subject from 5 possible as Option A. But these 5 subjects are placed on the same period in the timetable.")
options_var = tk.StringVar(value="Not sure")
options4 = [("Yes", "Yes"), ("No", "No"), ("Not sure", "Not sure")]
row_num = 1
col_num = 1
for text, val in options4:
    rb = ttk.Radiobutton(q4_frame, text=text, variable=options_var, value=val, style="Link.TRadiobutton", takefocus=False)
    rb.grid(row=row_num, column=col_num, sticky=tk.W, padx=10)
    row_num += 1

# Question 5: Multiple Buildings
q5_frame = create_question_frame(scrollable_frame, "We have multiple buildings and teachers need to travel between them. Some breaks might not be long enough for the teacher to go to different building.")
multiple_buildings_var = tk.StringVar(value="Not sure")
options5 = [("Yes", "Yes"), ("No", "No"), ("Not sure", "Not sure")]
row_num = 1
col_num = 1
for text, val in options5:
    rb = ttk.Radiobutton(q5_frame, text=text, variable=multiple_buildings_var, value=val, style="Link.TRadiobutton", takefocus=False)
    rb.grid(row=row_num, column=col_num, sticky=tk.W, padx=10)
    row_num += 1

# Question 6: Different Weekly Schedules
q6_frame = create_question_frame(scrollable_frame, "We have different schedules in different weeks")
different_weeks_var = tk.StringVar(value="No") # Default seems to be No based on options
options6 = [("Yes", "Yes"), ("No", "No")]
row_num = 1
col_num = 1
for text, val in options6:
    rb = ttk.Radiobutton(q6_frame, text=text, variable=different_weeks_var, value=val, style="Link.TRadiobutton", takefocus=False)
    rb.grid(row=row_num, column=col_num, sticky=tk.W, padx=10)
    row_num += 1

# --- Navigation Buttons ---
ttk.Separator(root, orient='horizontal').pack(fill=tk.X, pady=5, padx=10)
nav_frame = ttk.Frame(root, padding="10")
nav_frame.pack(fill=tk.X)

spacer_frame = ttk.Frame(nav_frame)
spacer_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)

close_button = ttk.Button(nav_frame, text="Close", command=root.destroy)
close_button.pack(side=tk.RIGHT, padx=5)

next_button = ttk.Button(nav_frame, text="Next", command=go_next)
next_button.pack(side=tk.RIGHT, padx=5)

prev_button = ttk.Button(nav_frame, text="Previous", command=go_previous)
prev_button.pack(side=tk.RIGHT, padx=5)


# --- Run ---
root.mainloop()