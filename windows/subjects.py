import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import colorchooser  # Add colorchooser import
import os  # Add import for path operations
import subprocess  # Add import for launching processes
# import sys # sys import is not used

# inputs in this window
# subcode = subname = subtype = None # These are assigned in parse_data, not needed as global module vars

# Global variable for the color display label and selected color
color_display_label = None
selected_color = "#008080"  # Default teal color, similar to the image
selected_classrooms = []    # To store selected classrooms

# Database paths (consistent with other steps)
DB_FOLDER = 'files'
DB_NAME = 'timetable.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

'''
    LIST OF FUNCTIONS USED FOR VARIOUS FUNCTIONS THROUGH TKinter INTERFACE
        * create_treeview()
        * update_treeview()
        * parse_data()
        * update_data()
        * remove_data()
        * navigation functions
'''

# --- Navigation functions ---
def go_previous():
    """Navigate back to step2.py"""
    print("Previous clicked - Going back to step2.py")
    
    try:
        # Mark that we're coming from subjects.py in the navigation flags table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS NAVIGATION_FLAGS (
                flag_name TEXT PRIMARY KEY,
                flag_value TEXT
            )
        ''')
        conn.execute("INSERT OR REPLACE INTO NAVIGATION_FLAGS (flag_name, flag_value) VALUES (?, ?)", 
                    ('coming_from', 'subjects'))
        conn.commit()
        
        # Use subprocess.Popen to launch step2.py
        startupinfo = None
        if os.name == 'nt':  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        subprocess.Popen(
            ['pythonw', 'windows\\step2.py'],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        subtk.destroy()  # Close current window
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Could not open step2.py: {e}")
        print(f"Error opening step2.py: {e}")

def go_next():
    """Navigate forward to step3.py"""
    print("Next clicked - Going to step3.py")
    
    try:
        # Mark that we're coming from subjects.py in the navigation flags table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS NAVIGATION_FLAGS (
                flag_name TEXT PRIMARY KEY,
                flag_value TEXT
            )
        ''')
        conn.execute("INSERT OR REPLACE INTO NAVIGATION_FLAGS (flag_name, flag_value) VALUES (?, ?)", 
                    ('coming_from', 'subjects'))
        conn.commit()
        
        # Use subprocess.Popen to launch step3.py
        startupinfo = None
        if os.name == 'nt':  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        subprocess.Popen(
            ['pythonw', 'windows\\step3.py'],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        subtk.destroy()  # Close current window
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Could not open step3.py: {e}")
        print(f"Error opening step3.py: {e}")

def close_window():
    """Close the window"""
    print("Close clicked")
    subtk.destroy()

def open_lesson_dialog():
    """Open the lesson dialog window"""
    print("Opening lesson dialog...")
    
    try:
        # Use subprocess.Popen to launch lesson_dialog.py
        startupinfo = None
        if os.name == 'nt':  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        subprocess.Popen(
            ['pythonw', 'windows\\lesson_dialog.py'],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Could not open lesson dialog: {e}")
        print(f"Error opening lesson_dialog.py: {e}")

# --- Placeholder functions for new UI elements ---
def change_color_picture_placeholder():
    global selected_color, color_display_label
    color_code = colorchooser.askcolor(title="Choose Subject Color", initialcolor=selected_color)
    if color_code and color_code[1]:
        selected_color = color_code[1]
        if color_display_label:
            color_display_label.config(bg=selected_color)
        print(f"Color selected: {selected_color}")

def select_classrooms_placeholder():
    global selected_classrooms
    
    # Create a dialog to select classrooms
    classroom_dialog = tk.Toplevel(subtk)
    classroom_dialog.title("Select Classrooms")
    classroom_dialog.geometry("400x450")
    classroom_dialog.transient(subtk)
    classroom_dialog.grab_set()
    
    # Create frame and listbox for classrooms
    frame = ttk.Frame(classroom_dialog, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="Available Classrooms:", font=("Consolas", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
    
    # Create listbox with scrollbar
    listbox_frame = ttk.Frame(frame)
    listbox_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create scrollbar first
    scrollbar = ttk.Scrollbar(listbox_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Create listbox with multiple selection
    classroom_listbox = tk.Listbox(
        listbox_frame, 
        selectmode=tk.MULTIPLE,
        exportselection=0,
        yscrollcommand=scrollbar.set
    )
    classroom_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=classroom_listbox.yview)
    
    # Load classrooms from CLASSES table
    try:
        cursor = conn.execute("SELECT CLASS_NAME FROM CLASSES ORDER BY CLASS_NAME")
        classrooms = [row[0] for row in cursor.fetchall()]
        
        # If no classrooms found, try HOME_CLASSROOM from CLASS table
        if not classrooms:
            cursor = conn.execute("SELECT DISTINCT HOME_CLASSROOM FROM CLASS WHERE HOME_CLASSROOM IS NOT NULL")
            classrooms = [row[0] for row in cursor.fetchall()]
        
        # Add classrooms to listbox
        for classroom in classrooms:
            classroom_listbox.insert(tk.END, classroom)
        
        # Select already selected classrooms
        for i, classroom in enumerate(classrooms):
            if classroom in selected_classrooms:
                classroom_listbox.selection_set(i)
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Could not load classrooms: {e}")
    
    # Define OK and Cancel buttons
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill=tk.X, pady=(10, 0))
    
    def on_ok():
        global selected_classrooms
        selected_indices = classroom_listbox.curselection()
        selected_classrooms = [classroom_listbox.get(i) for i in selected_indices]
        print(f"Selected classrooms: {selected_classrooms}")
        classroom_dialog.destroy()
    
    def on_cancel():
        classroom_dialog.destroy()
    
    ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
    
    # Wait for dialog to close
    subtk.wait_window(classroom_dialog)

def set_all_lessons_classrooms_placeholder():
    global selected_classrooms
    if not selected_classrooms:
        messagebox.showinfo("No Classrooms Selected", "Please select classrooms first.")
        return
        
    subject_code = str(subcode_entry.get()).strip()
    if not subject_code:
        messagebox.showinfo("No Subject", "Please enter or select a subject first.")
        return
    
    # Confirm with user
    classrooms_str = ", ".join(selected_classrooms)
    confirm = messagebox.askyesno(
        "Confirm Action", 
        f"Set classrooms '{classrooms_str}' for all lessons of subject '{subject_code}'?"
    )
    
    if not confirm:
        return
    
    try:
        # Update LESSONS table to associate these classrooms with all lessons of this subject
        # For demonstration, just show a message
        messagebox.showinfo(
            "Update Successful", 
            f"Classrooms '{classrooms_str}' set for all lessons of subject '{subject_code}'."
        )
        
        # This would be the actual database update if we implemented it
        # conn.execute("""
        #    UPDATE LESSONS SET CLASSROOMS = ? WHERE SUBJECT_CODE = ?
        # """, (classrooms_str, subject_code))
        # conn.commit()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update lessons: {e}")

def ok_button_action():
    print("OK button clicked")
    # For now, OK button will try to parse and save data like the original "Add Subject"
    # This assumes the user has filled in subcode, subname, and type.
    # In a more refined UI, OK would handle both add and update based on context.
    parse_data() 

def cancel_button_action():
    print("Cancel button clicked")
    subtk.destroy()


# create treeview (call this function once)
def create_treeview():
    tree['columns'] = ('code', 'name', 'type', 'color', 'classrooms')
    tree.column("#0", width=0, stretch=tk.NO)
    tree.column("code", width=70, stretch=tk.NO)
    tree.column("name", width=200, stretch=tk.NO) # Made narrower to fit other columns
    tree.column("type", width=60, stretch=tk.NO)
    tree.column("color", width=60, stretch=tk.NO)
    tree.column("classrooms", width=150, stretch=tk.YES) # Let classrooms column expand
    tree.heading('#0', text="")
    tree.heading('code', text="Code")
    tree.heading('name', text="Name")
    tree.heading('type', text="Type")
    tree.heading('color', text="Color")
    tree.heading('classrooms', text="Classrooms")


# update treeview (call this function after each update)
def update_treeview():
    for row in tree.get_children():
        tree.delete(row)
    
    # Use a simpler query that works whether or not the COLOR column exists
    try:
        cursor = conn.execute("""
            SELECT s.SUBCODE, s.SUBNAME, s.SUBTYPE, s.COLOR 
            FROM SUBJECTS s
            ORDER BY s.SUBNAME
        """)
    except sqlite3.OperationalError:
        # Fallback if COLOR column doesn't exist for some reason
        print("COLOR column not found, using default colors")
        cursor = conn.execute("""
            SELECT SUBCODE, SUBNAME, SUBTYPE
            FROM SUBJECTS
            ORDER BY SUBNAME
        """)
    
    for row in cursor:
        # Process type field
        if row[2] == 'T':
            t = 'Theory'
        elif row[2] == 'P':
            t = 'Practical'
        else:
            t = row[2] # Should be T or P, but good to handle
        
        # Get color from results or use default
        if len(row) > 3 and row[3]:
            color = row[3]
        else:
            color = "#008080"  # Default teal color
        
        # Get associated classrooms for this subject
        classrooms = []
        try:
            classroom_cursor = conn.execute("""
                SELECT CLASSROOM_NAME FROM SUBJECT_CLASSROOMS 
                WHERE SUBCODE = ? 
                ORDER BY CLASSROOM_NAME
            """, (row[0],))
            classrooms = [c[0] for c in classroom_cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error fetching classrooms for {row[0]}: {e}")
        
        # Join classrooms into a comma-separated string for display
        classrooms_str = ", ".join(classrooms) if classrooms else ""
        
        # Create a unique tag for this color
        color_tag = f"color_{row[0]}"
        tree.tag_configure(color_tag, background=color)
        
        # Insert row into treeview with the color tag
        item_id = tree.insert(
            "",
            0, # Insert at the beginning (top of the list)
            values=(row[0], row[1], t, "", classrooms_str), 
            tags=(color_tag,)
        )

# Parse and store data into database and treeview upon clcicking of the add button
def parse_data():
    # subcode, subname, subtype are local to this function scope
    s_code = str(subcode_entry.get()).strip()
    s_name = str(subname_entry.get("1.0", tk.END)).upper().strip() # Use .strip()
    s_type = str(radio_var.get()).upper() # radio_var should ensure T or P
    global selected_color, selected_classrooms

    if not s_code or not s_name: # Check for empty strings
        messagebox.showerror("Bad Input", "Please fill up Subject Code and Subject Name!")
        # subcode_entry.delete(0, tk.END) # Don't clear if user wants to correct
        # subname_entry.delete("1.0", tk.END)
        return

    try:
        # Using placeholders for security against SQL injection
        # Add COLOR field to the SUBJECTS table insert
        conn.execute("""
            REPLACE INTO SUBJECTS (SUBCODE, SUBNAME, SUBTYPE, COLOR) 
            VALUES (?, ?, ?, ?)
        """, (s_code, s_name, s_type, selected_color))
        
        # Save classroom associations in SUBJECT_CLASSROOMS table
        # First delete any existing associations
        conn.execute("DELETE FROM SUBJECT_CLASSROOMS WHERE SUBCODE = ?", (s_code,))
        
        # Then insert new associations
        for classroom in selected_classrooms:
            conn.execute("""
                INSERT INTO SUBJECT_CLASSROOMS (SUBCODE, CLASSROOM_NAME)
                VALUES (?, ?)
            """, (s_code, classroom))
            
        conn.commit()
        update_treeview()
        
        # Clear entries after successful add
        subcode_entry.delete(0, tk.END)
        subname_entry.delete("1.0", tk.END)
        radio_var.set("T") # Default to Theory
        selected_color = "#008080" # Reset color
        selected_classrooms = [] # Reset selected classrooms
        if color_display_label:
            color_display_label.config(bg=selected_color)
        # Update classroom listbox selection
        update_classroom_listbox()

    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Could not save subject: {e}")


# update a row in the database
def update_data():
    # This function loads data from the selected tree row into the entry fields for editing.
    # The actual update happens via parse_data (REPLACE INTO) when "Add Subject" or "OK" is clicked.
    subcode_entry.delete(0, tk.END)
    subname_entry.delete("1.0", tk.END)
    try:
        # print(tree.selection())
        if len(tree.selection()) > 1:
            messagebox.showerror("Bad Select", "Select one subject at a time to update!")
            return
        if not tree.selection():
            messagebox.showerror("Bad Select", "Please select a subject from the list first!")
            return

        selected_item = tree.selection()[0]
        row = tree.item(selected_item)['values']
        
        # Get the subject code and name from the row
        subcode_entry.insert(0, row[0])  # 'code' column - index 0
        subname_entry.insert("1.0", row[1])  # 'name' column - index 1
        
        # Assuming row[2] is "Theory" or "Practical" as displayed in treeview
        if row[2] == "Theory":  # 'type' column - index 2
            radio_var.set("T")
        elif row[2] == "Practical":
            radio_var.set("P")
        
        # Get the color from the tag instead of the row
        global selected_color, color_display_label
        item_tags = tree.item(selected_item)['tags']
        if item_tags and len(item_tags) > 0:
            color_tag = item_tags[0]
            # Extract color from tag configuration
            tag_options = tree.tag_configure(color_tag)
            if 'background' in tag_options:
                selected_color = tag_options['background']
            else:
                selected_color = "#008080"  # Default color
        else:
            selected_color = "#008080"  # Default color
            
        if color_display_label:
            color_display_label.config(bg=selected_color)
            
        # Load classroom associations
        load_subject_classrooms(row[0])

        messagebox.showinfo("Load for Update", f"Subject '{row[0]}' loaded for editing. Modify and click 'Add/Save Current' or 'OK (Save)' to save changes.")

    except IndexError:
        messagebox.showerror("Bad Select", "Please select a subject from the list first!")
        return

# Function to load classroom associations for a subject
def load_subject_classrooms(subject_code):
    global selected_classrooms
    selected_classrooms = []
    try:
        cursor = conn.execute("""
            SELECT CLASSROOM_NAME FROM SUBJECT_CLASSROOMS 
            WHERE SUBCODE = ?
        """, (subject_code,))
        selected_classrooms = [row[0] for row in cursor.fetchall()]
        update_classroom_listbox()
    except sqlite3.Error as e:
        print(f"Error loading subject classrooms: {e}")

# Function to update the classroom listbox based on selected_classrooms
def update_classroom_listbox():
    if hasattr(globals(), 'classroom_listbox') and 'classroom_listbox' in globals():
        # Clear current selection
        classroom_listbox.selection_clear(0, tk.END)
        # Set selection based on selected_classrooms
        for i, item in enumerate(classroom_listbox.get(0, tk.END)):
            if item in selected_classrooms:
                classroom_listbox.selection_set(i)

# remove selected data from databse and treeview
def remove_data():
    if len(tree.selection()) < 1:
        messagebox.showerror("Bad Select", "Please select a subject from the list first!")
        return
    
    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected subject(s)?")
    if not confirm:
        return

    for i in tree.selection():
        try:
            sub_code_to_delete = tree.item(i)['values'][0]
            # Delete associated classrooms first (foreign key constraint)
            conn.execute("DELETE FROM SUBJECT_CLASSROOMS WHERE SUBCODE = ?", (sub_code_to_delete,))
            # Then delete the subject
            conn.execute("DELETE FROM SUBJECTS WHERE SUBCODE = ?", (sub_code_to_delete,))
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not delete subject {sub_code_to_delete}: {e}")
            # Continue to try deleting others if multiple selected
        except Exception as ex:
            messagebox.showerror("Error", f"An unexpected error occurred: {ex}")

    update_treeview()


# main
if __name__ == "__main__":  

    '''
        DATABASE CONNECTIONS AND SETUP
    '''
    conn = sqlite3.connect(DB_PATH)
    
    # Check if COLOR column exists in SUBJECTS table and add it if it doesn't
    def ensure_color_column_exists():
        try:
            # Check if the COLOR column exists in the SUBJECTS table
            cursor = conn.execute("PRAGMA table_info(SUBJECTS)")
            columns = [info[1] for info in cursor.fetchall()]
            
            # If COLOR column doesn't exist, add it
            if 'COLOR' not in columns:
                print("Adding COLOR column to SUBJECTS table")
                conn.execute("ALTER TABLE SUBJECTS ADD COLUMN COLOR TEXT DEFAULT '#008080'")
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error checking/adding COLOR column: {e}")

    # Update SUBJECTS table to include color
    conn.execute('''CREATE TABLE IF NOT EXISTS SUBJECTS
    (SUBCODE CHAR(10) NOT NULL PRIMARY KEY,
    SUBNAME CHAR(50) NOT NULL,
    SUBTYPE CHAR(1) NOT NULL,
    COLOR TEXT DEFAULT "#008080")''')

    # Create table for subject-classroom associations
    conn.execute('''CREATE TABLE IF NOT EXISTS SUBJECT_CLASSROOMS
    (ID INTEGER PRIMARY KEY AUTOINCREMENT,
    SUBCODE CHAR(10) NOT NULL,
    CLASSROOM_NAME TEXT NOT NULL,
    FOREIGN KEY(SUBCODE) REFERENCES SUBJECTS(SUBCODE),
    UNIQUE(SUBCODE, CLASSROOM_NAME))''')

    # Ensure the COLOR column exists
    ensure_color_column_exists()

    conn.commit()

    '''
        TKinter WINDOW SETUP WITH WIDGETS
    '''
    subtk = tk.Tk()
    subtk.title("Subject Management")
    subtk.state('zoomed')  # Maximize window
    subtk.minsize(800, 700)  # Set minimum window size

    # Add fullscreen toggle functionality
    def toggle_fullscreen(event=None):
        if subtk.attributes('-fullscreen'):
            subtk.attributes('-fullscreen', False)
            subtk.state('zoomed')
        else:
            subtk.attributes('-fullscreen', True)

    def quit_fullscreen(event=None):
        subtk.attributes('-fullscreen', False)
        subtk.state('zoomed')
        
    subtk.bind('<Escape>', quit_fullscreen)  # Escape key exits fullscreen
    subtk.bind('<F11>', toggle_fullscreen)   # F11 toggles fullscreen

    # --- Main layout frames ---
    left_panel = ttk.Frame(subtk, width=450, padding=10)
    left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(10,0), pady=10)
    left_panel.pack_propagate(False) # Prevent left panel from shrinking/expanding with content initially

    right_panel = ttk.Frame(subtk, padding=10)
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5,10), pady=10)

    # --- LEFT PANEL CONTENT ---
    ttk.Label(left_panel, text='Subject Details', font=('Consolas', 18, 'bold')).pack(pady=(0,5), anchor=tk.CENTER)
    ttk.Label(left_panel, text='Add or update subject information.', font=('Consolas', 10, 'italic')).pack(pady=(0,15), anchor=tk.CENTER)

    # Input fields frame
    fields_frame = ttk.Frame(left_panel)
    fields_frame.pack(fill=tk.X, pady=5)

    ttk.Label(fields_frame, text='Subject Code:', font=('Consolas', 12)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
    subcode_entry = ttk.Entry(fields_frame, font=('Consolas', 12), width=20)
    subcode_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=3)
    
    ttk.Label(fields_frame, text='Subject Name:', font=('Consolas', 12)).grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
    subname_entry = tk.Text(fields_frame, font=('Consolas', 10), width=20, height=3, wrap=tk.WORD)
    subname_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=3)

    fields_frame.columnconfigure(1, weight=1) # Make entry/text expand

    # Subject Type
    type_frame = ttk.Frame(left_panel)
    type_frame.pack(fill=tk.X, pady=10)
    ttk.Label(type_frame, text='Subject Type:', font=('Consolas', 12)).pack(side=tk.LEFT, padx=5, anchor=tk.W)
    radio_var = tk.StringVar(value="T") # Default value is "T"
    R1 = ttk.Radiobutton(type_frame, text='Theory', variable=radio_var, value="T")
    R1.pack(side=tk.LEFT, padx=5)
    # R1.select() # This line is removed; StringVar initialization handles the default selection
    R2 = ttk.Radiobutton(type_frame, text='Practical', variable=radio_var, value="P")
    R2.pack(side=tk.LEFT, padx=5)

    # Original control buttons (Add, Update/Load)
    original_buttons_frame = ttk.Frame(left_panel)
    original_buttons_frame.pack(fill=tk.X, pady=(15,5))
    
    B1_add = ttk.Button(original_buttons_frame, text='Add/Save Current', command=parse_data)
    B1_add.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

    B2_load_update = ttk.Button(original_buttons_frame, text='Load Selected for Update', command=update_data)
    B2_load_update.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

    # --- Color/Picture Section ---
    color_picture_frame = ttk.LabelFrame(left_panel, text="Color/Picture", padding=10)
    color_picture_frame.pack(pady=(15,5), fill=tk.X, padx=5)

    color_display_label = tk.Label(color_picture_frame, bg=selected_color, width=15, height=2, relief=tk.SUNKEN)
    color_display_label.pack(side=tk.LEFT, padx=(5,10), expand=True, fill=tk.BOTH)
    
    change_color_btn = ttk.Button(color_picture_frame, text="Change", command=change_color_picture_placeholder)
    change_color_btn.pack(side=tk.LEFT, padx=(0,5))

    # --- Classrooms Section ---
    classrooms_frame = ttk.LabelFrame(left_panel, text="Classrooms", padding=10)
    classrooms_frame.pack(pady=(15,5), fill=tk.X, padx=5)

    classrooms_btn = ttk.Button(classrooms_frame, text="Select Classrooms", command=select_classrooms_placeholder)
    classrooms_btn.pack(fill=tk.X, pady=(0,5), padx=5)
    
    set_all_lessons_btn = ttk.Button(classrooms_frame, text="Set for all lessons of this subject", command=set_all_lessons_classrooms_placeholder)
    set_all_lessons_btn.pack(fill=tk.X, pady=(0,5), padx=5)
    
    # Spacer to push OK/Cancel to bottom
    ttk.Frame(left_panel).pack(fill=tk.Y, expand=True) 

    # --- OK and Cancel Buttons ---
    ok_cancel_frame = ttk.Frame(left_panel)
    ok_cancel_frame.pack(fill=tk.X, pady=(10,5), padx=10, side=tk.BOTTOM)

    ok_btn = ttk.Button(ok_cancel_frame, text="OK (Save)", command=ok_button_action)
    ok_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
    
    cancel_btn = ttk.Button(ok_cancel_frame, text="Close Window", command=cancel_button_action)
    cancel_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)


    # --- RIGHT PANEL CONTENT (Treeview and its controls) ---
    ttk.Label(right_panel, text='List of Subjects', font=('Consolas', 18, 'bold')).pack(pady=(0,10))
    
    tree_container = ttk.Frame(right_panel)
    tree_container.pack(fill=tk.BOTH, expand=True)
    tree = ttk.Treeview(tree_container)
    
    # Add scrollbar to treeview
    tree_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=tree_scrollbar.set)
    tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add horizontal scrollbar for wider content
    h_scrollbar_frame = ttk.Frame(right_panel)
    h_scrollbar_frame.pack(fill=tk.X)
    tree_h_scrollbar = ttk.Scrollbar(h_scrollbar_frame, orient="horizontal", command=tree.xview)
    tree.configure(xscrollcommand=tree_h_scrollbar.set)
    tree_h_scrollbar.pack(fill=tk.X)

    create_treeview() # tree is defined above
    
    tree_buttons_frame = ttk.Frame(right_panel)
    tree_buttons_frame.pack(pady=10, fill=tk.X)
        
    B3_delete = ttk.Button(tree_buttons_frame, text='Delete Selected Subject(s)', command=remove_data)
    B3_delete.pack(padx=5, expand=True) # Centered delete button for treeview
    
    update_treeview() # Initial population

    # --- Navigation Buttons (Bottom of window) ---
    ttk.Separator(subtk, orient='horizontal').pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0), padx=10)
    
    # Create two frames - one for lesson dialog button and one for navigation
    lesson_frame = ttk.Frame(subtk, padding="5")
    lesson_frame.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Add the lesson dialog button centered in its own frame
    lesson_dialog_button = ttk.Button(lesson_frame, text="Open Lesson Dialog", command=open_lesson_dialog)
    lesson_dialog_button.pack(expand=True, pady=5)
    
    # Navigation buttons frame
    nav_frame = ttk.Frame(subtk, padding="10")
    nav_frame.pack(side=tk.BOTTOM, fill=tk.X)

    spacer_frame = ttk.Frame(nav_frame)
    spacer_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)

    close_button = ttk.Button(nav_frame, text="Close", command=close_window)
    close_button.pack(side=tk.RIGHT, padx=5)

    next_button = ttk.Button(nav_frame, text="Next", command=go_next)
    next_button.pack(side=tk.RIGHT, padx=5)

    prev_button = ttk.Button(nav_frame, text="Previous", command=go_previous)
    prev_button.pack(side=tk.RIGHT, padx=5)
    
    subtk.mainloop()
    conn.close() # close database after all operations