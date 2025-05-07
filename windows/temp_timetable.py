import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

# Default days and period information (fallback if DB settings not available)
DEFAULT_DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa"]
DEFAULT_PERIODS_INFO = {
    1: "8:00 - 8:45",
    2: "9:00 - 9:45",
    3: "10:00 - 10:45",
    4: "11:00 - 11:45",
    5: "12:00 - 12:45",
    6: "13:00 - 13:45",
}

# Map days from scheduler (0-4) to day codes
DAY_MAP = {
    0: "Mo", 1: "Tu", 2: "We", 3: "Th", 4: "Fr", 5: "Sa"
}

class TimetableApp(tk.Tk):
    def __init__(self, class_name_filter="CSE"):
        super().__init__()
        self.class_name_filter = class_name_filter.upper()
        
        # Database connection
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(project_root, 'files', 'timetable.db')
        self.conn = self._connect_db()
        
        # Initialize days and periods based on DB settings
        self.days, self.periods_info = self._load_timetable_structure()
        
        self.title(f"Timetable - {self.class_name_filter}")
        self.geometry("850x550") # Adjusted for better layout

        self._create_ui()
        if self.conn:
            self._load_and_display_timetable()
        else:
            # Ensure this label is also created within the main UI structure if conn fails early
            ttk.Label(self, text="Database connection failed. Timetable cannot be displayed.",
                      foreground="red", font=("Arial", 12)).pack(pady=20, padx=20)
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_timetable_structure(self):
        """Load days and periods configuration from the database"""
        days = DEFAULT_DAYS.copy()
        periods_info = DEFAULT_PERIODS_INFO.copy()
        
        if not self.conn:
            print("Warning: No database connection. Using default timetable structure.")
            return days, periods_info
            
        try:
            # First check if TIMETABLE_SETTINGS table exists
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TIMETABLE_SETTINGS'")
            if not cursor.fetchone():
                print("Warning: TIMETABLE_SETTINGS table not found. Using default timetable structure.")
                return days, periods_info
                
            # Try to load days configuration
            cursor.execute("SELECT setting_value FROM TIMETABLE_SETTINGS WHERE setting_name = 'DAYS_ENABLED'")
            days_row = cursor.fetchone()
            if days_row and days_row[0]:
                # Format should be comma-separated day codes like "Mo,Tu,We,Th,Fr"
                days_enabled = days_row[0].split(',')
                # Filter the default days list to only include enabled days
                days = [day for day in DEFAULT_DAYS if day in days_enabled]
                
            # Try to load periods configuration
            cursor.execute("SELECT setting_value FROM TIMETABLE_SETTINGS WHERE setting_name = 'PERIODS_CONFIG'")
            periods_row = cursor.fetchone()
            if periods_row and periods_row[0]:
                # Format should be JSON-like: "1:8:00-8:45,2:9:00-9:45,..."
                try:
                    periods_data = {}
                    for period_conf in periods_row[0].split(','):
                        if ':' in period_conf:
                            period_num, time_range = period_conf.split(':', 1)
                            periods_data[int(period_num)] = time_range
                    if periods_data:  # Only replace if we parsed some valid data
                        periods_info = periods_data
                except Exception as e:
                    print(f"Error parsing periods config: {e}. Using default periods.")
            
            # Alternatively, try to load from NUM_PERIODS setting (simpler approach)
            cursor.execute("SELECT setting_value FROM TIMETABLE_SETTINGS WHERE setting_name = 'NUM_PERIODS'")
            num_periods_row = cursor.fetchone()
            if num_periods_row and num_periods_row[0]:
                try:
                    num_periods = int(num_periods_row[0])
                    # Only keep the first num_periods from the default
                    periods_info = {k: v for k, v in DEFAULT_PERIODS_INFO.items() if k <= num_periods}
                except ValueError:
                    print(f"Invalid NUM_PERIODS value: {num_periods_row[0]}. Using default periods.")
            
            print(f"Loaded timetable structure from database: {len(days)} days, {len(periods_info)} periods")
            return days, periods_info
            
        except sqlite3.Error as e:
            print(f"Database error loading timetable structure: {e}")
            return days, periods_info
        except Exception as e:
            print(f"Unexpected error loading timetable structure: {e}")
            return days, periods_info

    def _connect_db(self):
        try:
            # Ensure the 'files' directory exists
            files_dir = os.path.dirname(self.db_path)
            if not os.path.exists(files_dir):
                os.makedirs(files_dir) # Create if it doesn't exist

            conn = sqlite3.connect(self.db_path)
            
            # Create tables if they don't exist (supporting both schemas)
            
            # Minimal FACULTY schema for INI (actual schema in faculty.py)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS FACULTY (
                FID TEXT PRIMARY KEY NOT NULL,
                NAME TEXT NOT NULL,
                INI TEXT 
                /* other columns */
            );""")
            # Minimal SUBJECTS schema for SUBNAME (actual schema in subjects.py)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS SUBJECTS (
                SUBCODE TEXT PRIMARY KEY NOT NULL,
                SUBNAME TEXT NOT NULL 
                /* other columns */
            );""")
            # Schedule table used by scheduler.py
            conn.execute("""
            CREATE TABLE IF NOT EXISTS SCHEDULE (
                ID CHAR(10) NOT NULL PRIMARY KEY,
                DAYID INT NOT NULL,
                PERIODID INT NOT NULL,
                SUBCODE CHAR(10) NOT NULL,
                SECTION CHAR(5) NOT NULL,
                FINI CHAR(10) NOT NULL
            );""")
            # SCHEDULED_LESSONS table (for backward compatibility)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS SCHEDULED_LESSONS (
                SCHEDULE_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                CLASS_NAME TEXT NOT NULL,
                DAY_OF_WEEK TEXT NOT NULL CHECK(DAY_OF_WEEK IN ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa')),
                PERIOD_NUMBER INTEGER NOT NULL CHECK(PERIOD_NUMBER BETWEEN 1 AND 6),
                SUBJECT_CODE TEXT,
                TEACHER_ID TEXT, 
                FOREIGN KEY (SUBJECT_CODE) REFERENCES SUBJECTS(SUBCODE),
                FOREIGN KEY (TEACHER_ID) REFERENCES FACULTY(FID)
            );""")
            conn.commit()
            return conn
        except sqlite3.Error as e:
            messagebox.showerror("Database Connection Error",
                                 f"Failed to connect to database or setup tables: {e}\nDB Path: {self.db_path}")
            return None
        except Exception as ex:
            messagebox.showerror("File System Error",
                                 f"Failed to create directory for database: {ex}\nDB Path: {self.db_path}")
            return None


    def _create_ui(self):
        content_frame = ttk.Frame(self, padding="10")
        content_frame.pack(expand=True, fill=tk.BOTH)

        # Section selection frame
        select_frame = ttk.Frame(content_frame)
        select_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(select_frame, text="Section: ", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Get available sections from the database (from SCHEDULE table)
        self.available_sections = []
        try:
            cursor = self.conn.execute("SELECT DISTINCT SECTION FROM SCHEDULE ORDER BY SECTION")
            self.available_sections = [row[0] for row in cursor.fetchall()]
            
            # If no sections found in SCHEDULE, try SCHEDULED_LESSONS
            if not self.available_sections:
                cursor = self.conn.execute("SELECT DISTINCT CLASS_NAME FROM SCHEDULED_LESSONS ORDER BY CLASS_NAME")
                self.available_sections = [row[0] for row in cursor.fetchall()]
        except:
            self.available_sections = [self.class_name_filter]
            
        # If still empty, use default
        if not self.available_sections:
            self.available_sections = [self.class_name_filter]
            
        self.section_var = tk.StringVar(value=self.class_name_filter)
        self.section_combobox = ttk.Combobox(
            select_frame, 
            textvariable=self.section_var,
            values=self.available_sections,
            width=10
        )
        self.section_combobox.pack(side=tk.LEFT)
        
        # Update button
        ttk.Button(select_frame, text="View", command=self._change_section).pack(side=tk.LEFT, padx=10)

        ttk.Label(content_frame, text=self.class_name_filter, font=("Arial", 20, "bold"), anchor="center").pack(pady=(0, 15))
        
        # Status frame for displaying conflicts
        self.status_frame = ttk.Frame(content_frame)
        self.status_frame.pack(fill=tk.X, pady=(0, 10))
        self.status_label = ttk.Label(self.status_frame, text="", foreground="red")
        self.status_label.pack(anchor="center")

        grid_frame = ttk.Frame(content_frame)
        grid_frame.pack(expand=True, fill=tk.BOTH)
        
        # Empty top-left cell
        ttk.Label(grid_frame, text="", borderwidth=1, relief="solid", anchor="center").grid(row=0, column=0, sticky="nsew")

        # Period headers
        for i, (period_num, time_str) in enumerate(self.periods_info.items()):
            header_text = f"{period_num}\n{time_str}"
            ttk.Label(grid_frame, text=header_text, borderwidth=1, relief="solid", anchor="center",
                      justify="center", font=("Arial", 8, "bold"), padding=3).grid(row=0, column=i+1, sticky="nsew")

        # Day headers and lesson cells
        self.cells = {} 
        for r, day in enumerate(self.days):
            ttk.Label(grid_frame, text=day, borderwidth=1, relief="solid", anchor="center",
                      font=("Arial", 12, "bold"), padding=5).grid(row=r+1, column=0, sticky="nsew")
            for c, period_num in enumerate(self.periods_info.keys()):
                cell_key = (day, period_num) 
                cell_frame = ttk.Frame(grid_frame, borderwidth=1, relief="solid")
                cell_frame.grid(row=r+1, column=c+1, sticky="nsew")
                cell_frame.grid_rowconfigure(0, weight=1)
                cell_frame.grid_columnconfigure(0, weight=1)

                cell_label = ttk.Label(cell_frame, text="", anchor="center", justify="center", 
                                       font=("Arial", 9), wraplength=100, padding=2)
                cell_label.grid(row=0, column=0, sticky="nsew")
                cell_label.bind("<Button-1>", lambda e, d=day, p=period_num: self._show_cell_details(d, p))
                self.cells[cell_key] = cell_label
        
        for i in range(len(self.days) + 1): 
            grid_frame.grid_rowconfigure(i, weight=1, minsize=70 if i > 0 else 45) 
        for i in range(len(self.periods_info) + 1): 
            grid_frame.grid_columnconfigure(i, weight=1, minsize=120 if i > 0 else 70)

    def _change_section(self):
        """Update timetable when section is changed"""
        self.class_name_filter = self.section_var.get()
        # Update the title label
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.Label) and grandchild['font'] == ('Arial', 20, 'bold'):
                        grandchild.config(text=self.class_name_filter)
                        break
        self.title(f"Timetable - {self.class_name_filter}")
        self._load_and_display_timetable()

    def _check_faculty_conflicts(self, section):
        """Check for conflicts where the same faculty is assigned to multiple sections at the same time"""
        conflicts = []
        
        try:
            # Try to check conflicts in SCHEDULE table first (from scheduler.py)
            query = """
            SELECT s1.DAYID, s1.PERIODID, s1.FINI, s1.SECTION, s2.SECTION
            FROM SCHEDULE s1
            JOIN SCHEDULE s2 ON s1.DAYID = s2.DAYID 
                             AND s1.PERIODID = s2.PERIODID
                             AND s1.FINI = s2.FINI
                             AND s1.SECTION != s2.SECTION
            WHERE s1.SECTION = ?
            ORDER BY s1.DAYID, s1.PERIODID;
            """
            cursor = self.conn.execute(query, (section,))
            conflicts_schedule = cursor.fetchall()
            
            # Convert from numeric day ID to day code
            for conflict in conflicts_schedule:
                day_id, period_id, fini, section1, section2 = conflict
                day_code = DAY_MAP.get(day_id, f"Day{day_id}")
                # Add 1 to period_id since we store 0-indexed but display 1-indexed
                conflicts.append((day_code, period_id + 1, fini, section1, section2))
            
            # Also check SCHEDULED_LESSONS table for conflicts (original format)
            query2 = """
            SELECT sl1.DAY_OF_WEEK, sl1.PERIOD_NUMBER, f.INI, sl1.CLASS_NAME, sl2.CLASS_NAME
            FROM SCHEDULED_LESSONS sl1
            JOIN SCHEDULED_LESSONS sl2 ON sl1.DAY_OF_WEEK = sl2.DAY_OF_WEEK 
                                      AND sl1.PERIOD_NUMBER = sl2.PERIOD_NUMBER
                                      AND sl1.TEACHER_ID = sl2.TEACHER_ID
                                      AND sl1.CLASS_NAME != sl2.CLASS_NAME
            JOIN FACULTY f ON sl1.TEACHER_ID = f.FID
            WHERE sl1.CLASS_NAME = ?
            ORDER BY sl1.DAY_OF_WEEK, sl1.PERIOD_NUMBER;
            """
            cursor = self.conn.execute(query2, (section,))
            conflicts.extend(cursor.fetchall())
            
            return conflicts
            
        except sqlite3.Error as e:
            print(f"Database error checking for conflicts: {e}")
            return []

    def _load_and_display_timetable(self):
        for cell_label in self.cells.values():
            cell_label.config(text="") # Clear previous data

        try:
            # Clear previous conflict status
            self.status_label.config(text="")
            
            # Check for faculty conflicts
            conflicts = self._check_faculty_conflicts(self.class_name_filter)
            
            # Display conflicts if found
            if conflicts:
                conflict_msgs = []
                for day, period, faculty, class1, class2 in conflicts:
                    conflict_msgs.append(f"Conflict: {faculty} assigned to {class1} and {class2} at {day} period {period}")
                
                conflict_text = "Faculty scheduling conflicts detected! Check console for details."
                self.status_label.config(text=conflict_text)
                
                # Print detailed conflict information to console
                print("\n=== FACULTY SCHEDULING CONFLICTS ===")
                for msg in conflict_msgs:
                    print(msg)
                print("===================================\n")
                
                # Also show a message box with the conflicts
                messagebox.showwarning("Scheduling Conflicts", 
                                     "Faculty scheduling conflicts detected!\n\n" + 
                                     "\n".join(conflict_msgs[:5]) +
                                     ("\n..." if len(conflict_msgs) > 5 else ""))

            # First try to load data from SCHEDULE table (scheduler.py format)
            has_schedule_data = False
            try:
                # Query to get timetable data from SCHEDULE table
                query = """
                SELECT sch.DAYID, sch.PERIODID, s.SUBNAME, sch.FINI, s.SUBCODE
                FROM SCHEDULE sch
                LEFT JOIN SUBJECTS s ON sch.SUBCODE = s.SUBCODE
                WHERE sch.SECTION = ? 
                ORDER BY sch.DAYID, sch.PERIODID;
                """
                cursor = self.conn.execute(query, (self.class_name_filter,))
                lessons = cursor.fetchall()
                
                if lessons:
                    has_schedule_data = True
                    for lesson_data in lessons:
                        day_id, period_id, sub_name, fini, subcode = lesson_data
                        # Convert from numeric day ID to day code
                        day_code = DAY_MAP.get(day_id, f"Day{day_id}")
                        # Period is 0-indexed in SCHEDULE table, but 1-indexed in UI
                        period_num = period_id + 1
                        
                        # Skip if day or period not in our timetable grid
                        if day_code not in self.days or period_num not in self.periods_info:
                            continue
                            
                        cell_key = (day_code, period_num)
                        if cell_key in self.cells:
                            # Use subject name from SUBJECTS table if available, otherwise use SUBCODE
                            subject_display = sub_name if sub_name else subcode if subcode != "NULL" else "Free"
                            faculty_display = fini if fini != "NULL" else "-"
                            lesson_text = f"{subject_display}\n{faculty_display}"
                            self.cells[cell_key].config(text=lesson_text)
            except sqlite3.Error as e:
                print(f"Error loading SCHEDULE data: {e}")
                has_schedule_data = False

            # If no data from SCHEDULE table, try SCHEDULED_LESSONS
            if not has_schedule_data:
                query = """
                SELECT sl.DAY_OF_WEEK, sl.PERIOD_NUMBER, s.SUBNAME, f.INI 
                FROM SCHEDULED_LESSONS sl
                LEFT JOIN SUBJECTS s ON sl.SUBJECT_CODE = s.SUBCODE
                LEFT JOIN FACULTY f ON sl.TEACHER_ID = f.FID
                WHERE UPPER(sl.CLASS_NAME) = ? 
                ORDER BY sl.DAY_OF_WEEK, sl.PERIOD_NUMBER; 
                """
                cursor = self.conn.execute(query, (self.class_name_filter,))
                lessons = cursor.fetchall()

                if not lessons:
                    print(f"No scheduled lessons found for class: {self.class_name_filter}")
                    # You could show this message in the UI status bar if you add one

                for lesson_data in lessons:
                    day_db, period_num, sub_name, teacher_ini = lesson_data
                    
                    cell_key = (day_db, period_num) # Assumes DAY_OF_WEEK in DB matches DAYS list
                    if cell_key in self.cells:
                        lesson_text = f"{sub_name or 'N/A'}\n{teacher_ini or 'N/A'}"
                        self.cells[cell_key].config(text=lesson_text)
                    else:
                        print(f"Warning: Cell key {cell_key} for day '{day_db}' period {period_num} not found in UI grid.")

        except sqlite3.Error as e:
            messagebox.showerror("Database Query Error", f"Failed to load timetable data: {e}", parent=self)
        except Exception as ex:
            messagebox.showerror("Unexpected Error", f"An error occurred while loading timetable: {ex}", parent=self)

    def _on_closing(self):
        if self.conn:
            self.conn.close()
            print("Database connection closed.")
        self.destroy()

    def _show_cell_details(self, day, period):
        # Implement the logic to show cell details
        print(f"Showing details for {day} period {period}")

if __name__ == '__main__':
    # This makes the script runnable to display the timetable.
    # Ensure that:
    # 1. 'timetable.db' exists in a 'files' directory, one level above 'windows'.
    #    ProjectRoot/
    #    ├── files/
    #    │   └── timetable.db
    #    └── windows/
    #        └── timetable_generator.py
    # 2. The database should have either:
    #    - SCHEDULED_LESSONS table populated (original format)
    #    - SCHEDULE table populated (scheduler.py format)
    
    app = TimetableApp(class_name_filter="CSE") # You can change "CSE" to any class/section name
    app.mainloop() 