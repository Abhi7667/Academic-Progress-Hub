import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
import os

# Import necessary modules but not non-existent functions
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# No longer trying to import functions that don't exist
# from faculty import get_faculty_list
# from subjects import get_subject_list

class LessonDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Lesson")
        self.geometry("600x550") # Adjusted size to better fit elements
        
        # Connect to database
        self.db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "files", "timetable.db")
        self.conn = self.connect_to_db()
        
        # Create tables if they don't exist
        self.create_tables()

        # Main frame
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- Teacher Section ---
        teacher_frame = ttk.LabelFrame(main_frame, text="Teacher", padding="10 10 10 10")
        teacher_frame.pack(fill=tk.X, pady=5)
        
        self.teacher_var = tk.StringVar()
        self.teacher_combo = ttk.Combobox(teacher_frame, textvariable=self.teacher_var, state="readonly")
        # Populate with faculty data from faculty.py
        self.teacher_list = self.get_faculty_data()
        self.teacher_combo['values'] = [f"{t[1]} ({t[0]})" for t in self.teacher_list] if self.teacher_list else ["No teachers found"]
        self.teacher_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        
        more_teachers_btn = ttk.Button(teacher_frame, text="More teachers", command=self.open_faculty_window)
        more_teachers_btn.pack(side=tk.LEFT)

        # --- Subject Section ---
        subject_frame = ttk.LabelFrame(main_frame, text="Subject", padding="10 10 10 10")
        subject_frame.pack(fill=tk.X, pady=5)

        self.subject_var = tk.StringVar()
        self.subject_combo = ttk.Combobox(subject_frame, textvariable=self.subject_var, state="readonly")
        # Populate with subjects data from subjects.py
        self.subject_list = self.get_subject_data()
        self.subject_combo['values'] = [f"{s[1]} ({s[0]})" for s in self.subject_list] if self.subject_list else ["No subjects found"]
        if self.subject_list and len(self.subject_list) > 0:
            self.subject_combo.current(0)  # Set first subject as default
        self.subject_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        
        # Add a button to view subjects
        more_subjects_btn = ttk.Button(subject_frame, text="More subjects", command=self.view_subjects)
        more_subjects_btn.pack(side=tk.LEFT)

        # --- Class Section ---
        class_frame = ttk.LabelFrame(main_frame, text="Class", padding="10 10 10 10")
        class_frame.pack(fill=tk.X, pady=5)

        self.class_var = tk.StringVar()
        class_combo = ttk.Combobox(class_frame, textvariable=self.class_var, state="readonly")
        # Get class data from database
        self.class_list = self.get_class_data()
        class_combo['values'] = [c[0] for c in self.class_list] if self.class_list else ["No classes found"]
        if self.class_list and len(self.class_list) > 0:
            class_combo.current(0)  # Set first class as default
        class_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))

        # Add a button for viewing/managing classes
        more_classes_btn = ttk.Button(class_frame, text="More classes", command=self.view_classes)
        more_classes_btn.pack(side=tk.LEFT, padx=(0, 10))

        joint_classes_btn = ttk.Button(class_frame, text="Joint classes", command=self.select_joint_classes)
        joint_classes_btn.pack(side=tk.LEFT)
        
        # --- Lessons/week Section ---
        lessons_frame = ttk.LabelFrame(main_frame, text="Lessons/week", padding="10 10 10 10")
        lessons_frame.pack(fill=tk.X, pady=5)

        self.lessons_count_var = tk.StringVar(value="1")
        lessons_count_combo = ttk.Combobox(lessons_frame, textvariable=self.lessons_count_var, width=5, state="readonly")
        lessons_count_combo['values'] = tuple(str(i) for i in range(1, 11)) # Example: 1 to 10
        lessons_count_combo.pack(side=tk.LEFT, padx=(0, 10))

        # Create a frame for the lesson type selector
        lesson_type_frame = ttk.Frame(lessons_frame)
        lesson_type_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(lesson_type_frame, text="Lesson Type:").pack(side=tk.TOP, anchor=tk.W)
        
        self.lesson_type_var = tk.StringVar(value="Single")
        lesson_type_combo = ttk.Combobox(lesson_type_frame, textvariable=self.lesson_type_var, width=12, state="readonly")
        lesson_type_combo['values'] = ("Single", "Double", "Triple", "Quad", "Quint", "Hex")
        lesson_type_combo.pack(side=tk.TOP)
        
        # Add a short description label below the combo
        self.lesson_type_desc = ttk.Label(lesson_type_frame, text="1 period", font=("Consolas", 8))
        self.lesson_type_desc.pack(side=tk.TOP, anchor=tk.W)
        
        # Function to update the description when lesson type changes
        def update_lesson_type_desc(event=None):
            lesson_type = self.lesson_type_var.get()
            periods = {
                "Single": 1, 
                "Double": 2, 
                "Triple": 3, 
                "Quad": 4, 
                "Quint": 5, 
                "Hex": 6
            }.get(lesson_type, 1)
            self.lesson_type_desc.config(text=f"{periods} {'period' if periods == 1 else 'periods'}")
        
        # Bind the update function to the combobox selection event
        lesson_type_combo.bind("<<ComboboxSelected>>", update_lesson_type_desc)
        
        # Initialize the description label with the default value
        update_lesson_type_desc()

        more_weeks_btn = ttk.Button(lessons_frame, text="More weeks/terms", command=self.manage_weeks_terms)
        more_weeks_btn.pack(side=tk.LEFT, expand=True, anchor=tk.E) # Aligned to the right

        # --- Classroom Section ---
        classroom_frame = ttk.LabelFrame(main_frame, text="Classroom", padding="10 10 10 10")
        classroom_frame.pack(fill=tk.X, pady=5)

        # Checkbuttons and their arrangement
        classroom_options_frame = ttk.Frame(classroom_frame)
        classroom_options_frame.pack(fill=tk.X)

        col1_frame = ttk.Frame(classroom_options_frame)
        col1_frame.pack(side=tk.LEFT, padx=(0,20), anchor='nw')
        
        self.home_classroom_var = tk.BooleanVar(value=True)
        home_cb = ttk.Checkbutton(col1_frame, text="Home classroom", variable=self.home_classroom_var)
        home_cb.pack(anchor=tk.W)

        self.shared_room_var = tk.BooleanVar()
        shared_cb = ttk.Checkbutton(col1_frame, text="Shared room", variable=self.shared_room_var)
        shared_cb.pack(anchor=tk.W)

        col2_frame = ttk.Frame(classroom_options_frame)
        col2_frame.pack(side=tk.LEFT, padx=(0,20), anchor='nw')

        self.teachers_classrooms_var = tk.BooleanVar()
        teachers_cb = ttk.Checkbutton(col2_frame, text="Teacher's classrooms", variable=self.teachers_classrooms_var)
        teachers_cb.pack(anchor=tk.W)

        self.subjects_classrooms_var = tk.BooleanVar()
        subjects_cb = ttk.Checkbutton(col2_frame, text="Subject's classrooms", variable=self.subjects_classrooms_var)
        subjects_cb.pack(anchor=tk.W)
        
        # Buttons in classroom section
        classroom_buttons_frame = ttk.Frame(classroom_frame)
        classroom_buttons_frame.pack(fill=tk.X, pady=(10,0)) # Add some top padding

        other_classrooms_btn = ttk.Button(classroom_buttons_frame, text="Other available classrooms", 
                                         command=self.select_other_classrooms)
        other_classrooms_btn.pack(side=tk.LEFT, padx=(0, 10))

        more_classrooms_btn = ttk.Button(classroom_buttons_frame, text="More classrooms",
                                        command=self.manage_classrooms)
        more_classrooms_btn.pack(side=tk.LEFT)

        # --- Bottom Buttons ---
        button_frame = ttk.Frame(main_frame, padding="10 0 0 0") # Padding only on top
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10,0))

        ok_btn = ttk.Button(button_frame, text="OK", command=self.ok_action)
        ok_btn.pack(side=tk.RIGHT, padx=(5,0))

        help_btn = ttk.Button(button_frame, text="Help", command=self.help_action)
        help_btn.pack(side=tk.RIGHT, padx=(5,0))
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT)
        
        # Refresh data
        self.refresh_combos()

    def connect_to_db(self):
        """Connect to the SQLite database"""
        try:
            if not os.path.exists(os.path.dirname(self.db_file)):
                os.makedirs(os.path.dirname(self.db_file))
            return sqlite3.connect(self.db_file)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {e}")
            return None

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            if self.conn:
                # Create LESSONS table
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS LESSONS (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    TEACHER_ID TEXT NOT NULL,
                    SUBJECT_CODE TEXT NOT NULL,
                    CLASS_NAME TEXT NOT NULL,
                    LESSONS_PER_WEEK INTEGER,
                    LESSON_TYPE TEXT,
                    HOME_CLASSROOM INTEGER,
                    SHARED_ROOM INTEGER,
                    TEACHERS_CLASSROOMS INTEGER,
                    SUBJECTS_CLASSROOMS INTEGER,
                    JOINT_CLASSES TEXT,
                    FOREIGN KEY (TEACHER_ID) REFERENCES FACULTY(FID),
                    FOREIGN KEY (SUBJECT_CODE) REFERENCES SUBJECTS(SUBCODE)
                )
                ''')
                
                # Create CLASSROOMS table if not exists
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS CLASSROOMS (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    NAME TEXT NOT NULL UNIQUE,
                    CAPACITY INTEGER,
                    TYPE TEXT
                )
                ''')
                
                # Create CLASS table if not exists
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS CLASS (
                    NAME TEXT PRIMARY KEY,
                    CAPACITY INTEGER,
                    HOME_CLASSROOM TEXT
                )
                ''')
                
                self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to create tables: {e}")

    def get_faculty_data(self):
        """Get faculty data from database"""
        try:
            if self.conn:
                cursor = self.conn.execute("SELECT FID, NAME FROM FACULTY ORDER BY NAME")
                return list(cursor)
            return []
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to get faculty data: {e}")
            return []

    def get_subject_data(self):
        """Get subject data from database"""
        try:
            if self.conn:
                cursor = self.conn.execute("SELECT SUBCODE, SUBNAME FROM SUBJECTS ORDER BY SUBNAME")
                return list(cursor)
            return []
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to get subject data: {e}")
            return []

    def get_class_data(self):
        """Get class data from database"""
        try:
            if self.conn:
                # Query the CLASSES table (from class.py) instead of CLASS
                cursor = self.conn.execute("SELECT CLASS_NAME, SHORT_NAME FROM CLASSES ORDER BY CLASS_NAME")
                return list(cursor)
            return []
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to get class data: {e}")
            return []
            
    def refresh_combos(self):
        """Refresh all combo boxes with updated data"""
        # Refresh teacher combo
        self.teacher_list = self.get_faculty_data()
        self.teacher_combo['values'] = [f"{t[1]} ({t[0]})" for t in self.teacher_list] if self.teacher_list else ["No teachers found"]
        
        # Refresh subject combo
        self.subject_list = self.get_subject_data()
        self.subject_combo['values'] = [f"{s[1]} ({s[0]})" for s in self.subject_list] if self.subject_list else ["No subjects found"]
        
        # Refresh class combo
        self.class_list = self.get_class_data()
        # Update the class_combo, assuming it's accessible as an instance variable
        if hasattr(self, 'class_combo'):
            self.class_combo['values'] = [c[0] for c in self.class_list] if self.class_list else ["No classes found"]

    def open_faculty_window(self):
        """Open the faculty management window"""
        self.withdraw()  # Hide current window
        
        # Create a simple dialog to view faculty instead of trying to run faculty.py
        faculty_window = tk.Toplevel(self.master)
        faculty_window.title('View Faculty')
        faculty_window.geometry("800x500")
        
        # Set up a function to handle when the window is closed
        def on_close():
            faculty_window.destroy()
            self.deiconify()  # Show lesson dialog again
            self.refresh_combos()  # Refresh the combos
            
        faculty_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # Create a frame for the faculty view
        main_frame = ttk.Frame(faculty_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a label
        ttk.Label(main_frame, text="Faculty List", font=("Consolas", 16, "bold")).pack(pady=10)
        
        # Create a treeview to display faculty
        tree = ttk.Treeview(main_frame, columns=("id", "name", "subject1", "subject2"), show="headings")
        tree.heading("id", text="ID")
        tree.heading("name", text="Name")
        tree.heading("subject1", text="Subject 1")
        tree.heading("subject2", text="Subject 2")
        
        tree.column("id", width=80)
        tree.column("name", width=200)
        tree.column("subject1", width=150)
        tree.column("subject2", width=150)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load faculty data from database
        if self.conn:
            try:
                cursor = self.conn.execute("SELECT FID, NAME, SUBCODE1, SUBCODE2 FROM FACULTY ORDER BY NAME")
                for row in cursor:
                    tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3]))
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error loading faculty data: {e}")
        
        # Add a note about managing faculty
        ttk.Label(faculty_window, 
                 text="Note: To add or edit faculty, please use the main Faculty Management window",
                 font=("Consolas", 10)).pack(pady=10)
        
        # Add close button
        ttk.Button(faculty_window, text="Close", command=on_close).pack(pady=10)
        
    def select_joint_classes(self):
        """Open dialog to select joint classes"""
        messagebox.showinfo("Joint Classes", "This would open a dialog to select joint classes")
        
    def manage_weeks_terms(self):
        """Open dialog to manage weeks/terms"""
        messagebox.showinfo("Weeks/Terms", "This would open a dialog to manage weeks and terms")
        
    def select_other_classrooms(self):
        """Open dialog to select other classrooms"""
        messagebox.showinfo("Other Classrooms", "This would open a dialog to select other available classrooms")
        
    def manage_classrooms(self):
        """Open dialog to manage classrooms"""
        messagebox.showinfo("Manage Classrooms", "This would open a dialog to manage classrooms")
        
    def extract_id_from_combo(self, value, list_data):
        """Extract ID from combo box formatted string"""
        if not value or not list_data:
            return None
        
        for item in list_data:
            if f"{item[1]} ({item[0]})" == value:
                return item[0]
        return None

    def ok_action(self):
        """Save lesson data to database and close dialog"""
        try:
            # Get data from form
            teacher_id = self.extract_id_from_combo(self.teacher_var.get(), self.teacher_list)
            subject_code = self.extract_id_from_combo(self.subject_var.get(), self.subject_list)
            class_name = self.class_var.get()
            lessons_per_week = int(self.lessons_count_var.get())
            lesson_type = self.lesson_type_var.get()
            
            # Map lesson type to number of periods
            lesson_periods = {
                "Single": 1, 
                "Double": 2, 
                "Triple": 3, 
                "Quad": 4, 
                "Quint": 5, 
                "Hex": 6
            }.get(lesson_type, 1)
            
            home_classroom = 1 if self.home_classroom_var.get() else 0
            shared_room = 1 if self.shared_room_var.get() else 0
            teachers_classrooms = 1 if self.teachers_classrooms_var.get() else 0
            subjects_classrooms = 1 if self.subjects_classrooms_var.get() else 0
            
            # Validate data
            if not teacher_id or not subject_code or not class_name:
                messagebox.showwarning("Missing Data", "Please select teacher, subject, and class.")
                return
                
            # Save to database
            if self.conn:
                self.conn.execute('''
                INSERT INTO LESSONS (
                    TEACHER_ID, SUBJECT_CODE, CLASS_NAME, LESSONS_PER_WEEK, LESSON_TYPE,
                    HOME_CLASSROOM, SHARED_ROOM, TEACHERS_CLASSROOMS, SUBJECTS_CLASSROOMS
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    teacher_id, subject_code, class_name, lessons_per_week, lesson_type,
                    home_classroom, shared_room, teachers_classrooms, subjects_classrooms
                ))
                self.conn.commit()
                
                # Provide feedback about the lesson configuration
                messagebox.showinfo(
                    "Success", 
                    f"Lesson added successfully:\n\n"
                    f"• Subject: {subject_code}\n"
                    f"• Class: {class_name}\n"
                    f"• Lesson type: {lesson_type} ({lesson_periods} periods)\n"
                    f"• Lessons per week: {lessons_per_week}"
                )
                
                self.destroy()
            else:
                messagebox.showerror("Database Error", "No database connection")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save lesson: {e}")
            print(f"Error details: {e}")
            
        print(f"Teacher: {self.teacher_var.get()}")
        print(f"Subject: {self.subject_var.get()}")
        print(f"Class: {self.class_var.get()}")
        print(f"Lessons Count: {self.lessons_count_var.get()}")
        print(f"Lesson Type: {self.lesson_type_var.get()} ({lesson_periods} periods)")
        print(f"Home Classroom: {self.home_classroom_var.get()}")
        print(f"Shared Room: {self.shared_room_var.get()}")
        print(f"Teacher's Classrooms: {self.teachers_classrooms_var.get()}")
        print(f"Subject's Classrooms: {self.subjects_classrooms_var.get()}")

    def help_action(self):
        # Placeholder for Help action
        messagebox.showinfo("Help", "This is the lesson scheduling dialog.\n\n" +
                           "Here you can add a new lesson by selecting a teacher, subject, class, " +
                           "and setting other parameters like lessons per week and classroom options.")

    def __del__(self):
        """Close database connection when dialog is destroyed"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def subject_dropdown_click(self, event=None):
        """Handle clicks on the subject dropdown by showing subject details if needed"""
        # Get the currently selected subject code
        subject_code = self.extract_id_from_combo(self.subject_var.get(), self.subject_list)
        if not subject_code:
            return
            
        # We could show a details window here if needed
        print(f"Subject clicked: {self.subject_var.get()}")
        
    def view_subjects(self):
        """Open a window to view subjects"""
        self.withdraw()  # Hide current window
        
        # Create a simple dialog to view subjects
        subject_window = tk.Toplevel(self.master)
        subject_window.title('View Subjects')
        subject_window.geometry("800x500")
        
        # Set up a function to handle when the window is closed
        def on_close():
            subject_window.destroy()
            self.deiconify()  # Show lesson dialog again
            self.refresh_combos()  # Refresh the combos
            
        subject_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # Create a frame for the subject view
        main_frame = ttk.Frame(subject_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a label
        ttk.Label(main_frame, text="Subject List", font=("Consolas", 16, "bold")).pack(pady=10)
        
        # Create a treeview to display subjects
        tree = ttk.Treeview(main_frame, columns=("code", "name", "type"), show="headings")
        tree.heading("code", text="Code")
        tree.heading("name", text="Name")
        tree.heading("type", text="Type")
        
        tree.column("code", width=100)
        tree.column("name", width=350)
        tree.column("type", width=100)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load subject data from database
        if self.conn:
            try:
                cursor = self.conn.execute("SELECT SUBCODE, SUBNAME, SUBTYPE FROM SUBJECTS ORDER BY SUBNAME")
                for row in cursor:
                    # Convert type code to readable format
                    type_text = "Theory" if row[2] == "T" else "Practical" if row[2] == "P" else row[2]
                    tree.insert("", tk.END, values=(row[0], row[1], type_text))
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error loading subject data: {e}")
        
        # Add a note about managing subjects
        ttk.Label(subject_window, 
                 text="Note: To add or edit subjects, please use the main Subjects Management window",
                 font=("Consolas", 10)).pack(pady=10)
        
        # Add close button
        ttk.Button(subject_window, text="Close", command=on_close).pack(pady=10)
        
    def view_classes(self):
        """Open a window to view classes"""
        self.withdraw()  # Hide current window
        
        # Create a simple dialog to view classes
        class_window = tk.Toplevel(self.master)
        class_window.title('View Classes')
        class_window.geometry("850x500")
        
        # Set up a function to handle when the window is closed
        def on_close():
            class_window.destroy()
            self.deiconify()  # Show lesson dialog again
            self.refresh_combos()  # Refresh the combos
            
        class_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # Create a frame for the class view
        main_frame = ttk.Frame(class_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a label
        ttk.Label(main_frame, text="Class List", font=("Consolas", 16, "bold")).pack(pady=10)
        
        # Create a treeview to display classes
        tree = ttk.Treeview(main_frame, columns=("name", "short", "teacher", "grade", "color"), show="headings")
        tree.heading("name", text="Class Name")
        tree.heading("short", text="Short Name")
        tree.heading("teacher", text="Teacher")
        tree.heading("grade", text="Grade")
        tree.heading("color", text="Color")
        
        tree.column("name", width=150)
        tree.column("short", width=100)
        tree.column("teacher", width=200)
        tree.column("grade", width=100)
        tree.column("color", width=100)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load class data from database
        if self.conn:
            try:
                # Join with FACULTY table to get teacher names
                cursor = self.conn.execute("""
                SELECT c.CLASS_NAME, c.SHORT_NAME, f.NAME, c.GRADE, c.COLOR
                FROM CLASSES c
                LEFT JOIN FACULTY f ON c.CLASS_TEACHER_FID = f.FID
                ORDER BY c.CLASS_NAME
                """)
                for row in cursor:
                    # Create small color indicator
                    tree.insert("", tk.END, values=(row[0], row[1], row[2] or "No teacher", row[3] or "", row[4] or ""))
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error loading class data: {e}")
        
        # Add a note about managing classes
        ttk.Label(class_window, 
                 text="Note: To add or edit classes, please use the main Class Management window",
                 font=("Consolas", 10)).pack(pady=10)
        
        # Add close button
        ttk.Button(class_window, text="Close", command=on_close).pack(pady=10)

# Remove unused functions at the bottom
if __name__ == '__main__':
    # This is for testing purposes
    root = tk.Tk()
    root.withdraw() # Hide the main root window

    def open_lesson_dialog():
        dialog = LessonDialog(root)
        dialog.grab_set() # Makes the dialog modal
        root.wait_window(dialog) # Wait until dialog is closed

    open_lesson_dialog() # Open the dialog immediately for testing
 