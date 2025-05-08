import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
from condition import TimetableConditionChecker

class TimetableEditorComponent(ttk.Frame):
    def __init__(self, parent, class_names_list=None, period_labels_list=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Load days from database
        self.days = self.load_days_from_db()
        
        # Use provided lists or defaults
        self.class_names = class_names_list if class_names_list else self.load_classes_from_db()
        self.periods = period_labels_list if period_labels_list else self.load_periods_from_db()
        
        # Database connection setup
        self.setup_db_connection()
        
        self.num_classes_display = len(self.class_names)
        self.recess_break_after = 3  # Default recess after 3rd period

        # To store references to widgets
        self.class_label_widgets = []
        self.period_header_widgets = [] 
        self.timetable_cells = {}  # To store cell frames: {(class_idx, day_idx, period_idx): frame}
        
        # For cell editing functionality
        self.selected_cell = None
        self.highlighted_cells = []

        self.configure_grid_weights()
        self.create_header_labels()
        self.create_class_labels()
        self.create_timetable_grid_cells()
        self.create_control_buttons()
        self.load_timetable_data()

    def setup_db_connection(self):
        """Set up the connection to the SQLite database"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(project_root, 'files', 'timetable.db')
            
            if not os.path.exists(self.db_path):
                messagebox.showerror("Database Error", f"Database not found at: {self.db_path}")
                return False
                
            self.conn = sqlite3.connect(self.db_path)
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {e}")
            return False

    def load_days_from_db(self):
        """Load day names from the database"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, 'files', 'timetable.db')
            
            if not os.path.exists(db_path):
                return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try to get days enabled from TIMETABLE_SETTINGS
            cursor.execute("SELECT setting_value FROM TIMETABLE_SETTINGS WHERE setting_name='DAYS_ENABLED'")
            result = cursor.fetchone()
            
            if result and result[0]:
                # Days are stored as comma-separated codes
                day_codes = result[0].split(',')
                # Map day codes to full names
                day_map = {
                    "Mo": "Monday", 
                    "Tu": "Tuesday", 
                    "We": "Wednesday", 
                    "Th": "Thursday", 
                    "Fr": "Friday",
                    "Sa": "Saturday",
                    "Su": "Sunday"
                }
                days = [day_map.get(code, code) for code in day_codes]
                return days
            
            # If no setting found, get number of days from config
            cursor.execute("SELECT num_days FROM SCHOOL_CONFIG WHERE config_id=1")
            result = cursor.fetchone()
            
            if result and result[0]:
                num_days = int(result[0])
                default_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                return default_days[:num_days]
                
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error loading days: {e}")
        except Exception as e:
            print(f"Error loading days: {e}")
            
        # Default days if nothing found in database
        return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    def load_classes_from_db(self):
        """Load class names from the database"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, 'files', 'timetable.db')
            
            if not os.path.exists(db_path):
                return [f"Class {i+1}" for i in range(10)]
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get distinct sections from SCHEDULE table
            cursor.execute("SELECT DISTINCT SECTION FROM SCHEDULE ORDER BY SECTION")
            sections = cursor.fetchall()
            
            if sections:
                return [section[0] for section in sections]
            
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error loading classes: {e}")
            
        # Default classes if nothing found in database
        return [f"Class {i+1}" for i in range(10)]

    def load_periods_from_db(self):
        """Load period labels from the database"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, 'files', 'timetable.db')
            
            if not os.path.exists(db_path):
                return [f"P{i+1}" for i in range(8)]  # Using shorter P1, P2 format
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try to get number of periods from config
            cursor.execute("SELECT num_periods FROM SCHOOL_CONFIG WHERE config_id=1")
            result = cursor.fetchone()
            
            if result and result[0]:
                num_periods = int(result[0])
                return [f"P{i+1}" for i in range(num_periods)]  # Using shorter P1, P2 format
            
            # Alternate approach: get distinct periods from SCHEDULE
            cursor.execute("SELECT DISTINCT PERIODID FROM SCHEDULE ORDER BY PERIODID")
            period_ids = cursor.fetchall()
            
            if period_ids:
                return [f"P{period_id[0]+1}" for period_id in period_ids]  # Using shorter P1, P2 format
                
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error loading periods: {e}")
            
        # Default periods if nothing found in database
        return [f"P{i+1}" for i in range(8)]  # Using shorter P1, P2 format

    def configure_grid_weights(self):
        """Configure grid weights for the timetable layout"""
        # Configure column weight for class labels
        self.grid_columnconfigure(0, weight=0)
        
        # Configure column weights for period cells
        total_period_columns = len(self.days) * len(self.periods)
        for i in range(1, total_period_columns + 1):
            self.grid_columnconfigure(i, weight=1)

        # Configure row weights for header and class rows
        self.grid_rowconfigure(0, weight=0)  # Day headers
        self.grid_rowconfigure(1, weight=0)  # Period headers
        for i in range(self.num_classes_display):
            self.grid_rowconfigure(2 + i, weight=1)

    def create_header_labels(self):
        """Create day and period header labels"""
        cell_size = 60  # Match the size used for grid cells
        
        # Create day labels
        for day_idx, day_name in enumerate(self.days):
            start_col = 1 + (day_idx * len(self.periods))
            day_label = ttk.Label(self, text=day_name, font=('Arial', 8, 'bold'), relief=tk.RIDGE, anchor=tk.CENTER)
            day_label.grid(row=0, column=start_col, columnspan=len(self.periods), sticky="nsew")
            self.period_header_widgets.append(day_label)

        # Create period labels
        for day_idx in range(len(self.days)):
            for period_idx, period_name in enumerate(self.periods):
                col = 1 + (day_idx * len(self.periods)) + period_idx
                period_label = ttk.Label(self, text=period_name, font=('Arial', 8), relief=tk.RIDGE, anchor=tk.CENTER)
                period_label.grid(row=1, column=col, sticky="nsew")
                self.period_header_widgets.append(period_label)
        
        # Placeholder for the top-left cell
        top_left_label = ttk.Label(self, text="Class", font=('Arial', 8, 'bold'), relief=tk.RIDGE, anchor=tk.CENTER)
        top_left_label.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.period_header_widgets.append(top_left_label)

    def create_class_labels(self):
        """Create labels for classes/sections"""
        self.class_label_widgets = []
        for i, class_name_text in enumerate(self.class_names):
            class_label = ttk.Label(self, text=class_name_text, font=('Arial', 8, 'bold'), 
                                   relief=tk.RIDGE, anchor=tk.W, padding=(5,0))
            class_label.grid(row=2 + i, column=0, sticky="nsew")
            self.class_label_widgets.append(class_label)

    def create_timetable_grid_cells(self):
        """Create cells for the timetable grid"""
        self.timetable_cells = {}
        cell_size = 60  # Fixed cell size for more square-like appearance
        
        for class_idx in range(self.num_classes_display):
            for day_idx in range(len(self.days)):
                for period_idx in range(len(self.periods)):
                    col = 1 + (day_idx * len(self.periods)) + period_idx
                    row = 2 + class_idx
                    
                    cell_key = (class_idx, day_idx, period_idx)
                    cell_frame = tk.Frame(self, borderwidth=1, relief=tk.SUNKEN, bg="white", 
                                         width=cell_size, height=cell_size)
                    cell_frame.grid(row=row, column=col, sticky="nsew")
                    cell_frame.grid_propagate(False)  # Prevent resizing based on content
                    
                    # Add label inside the frame to display subject info
                    cell_label = tk.Label(cell_frame, text="", bg="white", justify=tk.CENTER, 
                                        font=('Arial', 8))  # Smaller font size
                    cell_label.pack(expand=True, fill=tk.BOTH)
                    
                    self.timetable_cells[cell_key] = cell_frame
                    
                    # Bind click event to edit cell
                    cell_frame.bind("<Button-1>", lambda event, c=cell_key: self.on_cell_click(event, c))
                    # Bind right-click for context menu or details
                    cell_frame.bind("<Button-3>", lambda event, c=cell_key: self.show_cell_details(event, c))

    def on_cell_click(self, event, cell_key):
        """Handle click on a timetable cell to edit it"""
        # Highlight the selected cell
        if self.selected_cell:
            self.timetable_cells[self.selected_cell].config(bg="white")
            for widget in self.timetable_cells[self.selected_cell].winfo_children():
                widget.config(bg="white")
        
        self.selected_cell = cell_key
        self.timetable_cells[cell_key].config(bg="#e0e0ff")  # Light blue highlight
        for widget in self.timetable_cells[cell_key].winfo_children():
            widget.config(bg="#e0e0ff")
            
        # Get cell information
        class_idx, day_idx, period_idx = cell_key
        section = self.class_names[class_idx]
        
        # Open editor dialog
        self.open_subject_editor(section, day_idx, period_idx)

    def check_subject_usage(self, section, subject_code):
        """
        Check the current usage of a subject in a section compared to its lessons_per_week limit
        
        Args:
            section (str): The class/section to check
            subject_code (str): The subject code to check
            
        Returns:
            tuple: (current_count, limit, message)
        """
        try:
            # Create a condition checker
            condition_checker = TimetableConditionChecker(self.db_path)
            
            # Get the current count and limit
            exceeded, current_count, limit, _ = condition_checker.check_lessons_per_week_limit(section, subject_code)
            
            if limit <= 0:
                # No limit defined
                message = f"No lessons_per_week limit defined for {subject_code} in {section}"
                return current_count, limit, message
                
            if exceeded:
                message = f"WARNING: {subject_code} is assigned {current_count}/{limit} times (LIMIT EXCEEDED)"
            else:
                message = f"Current usage: {current_count}/{limit} lessons per week"
                
            return current_count, limit, message
            
        except Exception as e:
            print(f"Error checking subject usage: {e}")
            return 0, 0, "Error checking subject usage"

    def open_subject_editor(self, section, day_idx, period_idx):
        """Open dialog to edit subject for the selected cell"""
        editor = tk.Toplevel(self)
        editor.title("Edit Timetable Cell")
        editor.grab_set()  # Make dialog modal
        
        # Show cell information
        tk.Label(
            editor,
            text=f'Section: {section}',
            font=('Consolas', 12, 'bold')
        ).pack(pady=5)
        
        tk.Label(
            editor,
            text=f'Day: {self.days[day_idx]}',
            font=('Consolas', 12)
        ).pack(pady=5)
        
        tk.Label(
            editor,
            text=f'Period: {period_idx + 1}',
            font=('Consolas', 12)
        ).pack(pady=5)
        
        # Create a frame for subject usage info
        subject_usage_frame = tk.Frame(editor, relief=tk.GROOVE, bd=1)
        subject_usage_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        subject_usage_label = tk.Label(
            subject_usage_frame,
            text="Select a subject to see usage information",
            font=('Consolas', 10, 'italic'),
            fg='gray'
        )
        subject_usage_label.pack(pady=5)
        
        # Create treeview to display subject and faculty options
        tree = ttk.Treeview(editor)
        tree['columns'] = ('faculty', 'subject')
        tree.column("#0", width=0, stretch=tk.NO)
        tree.column("faculty", width=100, stretch=tk.NO)
        tree.column("subject", width=120, stretch=tk.NO)
        tree.heading('#0', text="")
        tree.heading('faculty', text="Faculty")
        tree.heading('subject', text="Subject Code")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(editor, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Get faculty and subject data from database
        try:
            cursor = self.conn.execute("""
                SELECT FACULTY.INI, FACULTY.SUBCODE1, FACULTY.SUBCODE2, SUBJECTS.SUBCODE
                FROM FACULTY, SUBJECTS
                WHERE FACULTY.SUBCODE1=SUBJECTS.SUBCODE OR FACULTY.SUBCODE2=SUBJECTS.SUBCODE
            """)
            
            for row in cursor:
                tree.insert("", "end", values=(row[0], row[3]))
            
            # Add option to clear the cell
            tree.insert("", 0, values=('NULL', 'NULL'))
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load faculty and subjects: {e}")
        
        # Function to update subject usage info when a subject is selected
        def on_tree_select(event):
            selection = tree.selection()
            if selection:
                row = tree.item(selection[0])['values']
                if len(row) >= 2 and row[1] != 'NULL':
                    subject_code = row[1]
                    count, limit, message = self.check_subject_usage(section, subject_code)
                    
                    # Set color based on status
                    if limit > 0 and count >= limit:
                        subject_usage_label.config(text=message, fg='red', font=('Consolas', 10, 'bold'))
                    elif limit > 0 and count >= limit - 1:  # Close to limit
                        subject_usage_label.config(text=message, fg='orange', font=('Consolas', 10, 'bold'))
                    else:
                        subject_usage_label.config(text=message, fg='green', font=('Consolas', 10))
                else:
                    subject_usage_label.config(text="No subject selected", fg='gray', font=('Consolas', 10, 'italic'))
        
        # Bind selection event
        tree.bind('<<TreeviewSelect>>', on_tree_select)
        
        # Button frame
        button_frame = tk.Frame(editor)
        button_frame.pack(fill="x", pady=10)
        
        # OK button
        tk.Button(
            button_frame,
            text="OK",
            padx=20,
            command=lambda: self.update_cell(tree, section, day_idx, period_idx, editor)
        ).pack(side="left", padx=10)
        
        # Cancel button
        tk.Button(
            button_frame,
            text="Cancel",
            padx=20,
            command=editor.destroy
        ).pack(side="right", padx=10)

    def update_cell(self, tree, section, day_idx, period_idx, dialog):
        """Update the cell data in the database"""
        try:
            selection = tree.selection()
            if not selection:
                messagebox.showerror("Selection Error", "Please select a subject")
                return
                
            if len(selection) > 1:
                messagebox.showerror("Selection Error", "Select only one subject")
                return
            
            # Get selected values
            row = tree.item(selection[0])['values']
            faculty_ini = row[0]
            subject_code = row[1]
            
            # Check for conflicts
            has_conflict, conflict_message = self.check_conflicts(faculty_ini, day_idx, period_idx, section)
            
            if has_conflict:
                proceed = messagebox.askyesno(
                    "Scheduling Conflict", 
                    f"The following conflicts were detected:\n\n{conflict_message}\n\nDo you want to proceed anyway?"
                )
                if not proceed:
                    return
            
            # Check if this would exceed the lessons_per_week limit for this subject
            # Only check if we're adding a new subject (not NULL)
            if subject_code != 'NULL':
                condition_checker = TimetableConditionChecker(self.db_path)
                
                # Count existing assignments for this subject in this section
                cursor = self.conn.execute("""
                    SELECT COUNT(*) FROM SCHEDULE 
                    WHERE SUBCODE=? AND SECTION=?
                """, (subject_code, section))
                current_count = cursor.fetchone()[0]
                
                # Check if adding one more would exceed the limit
                exceeded, count, limit, warning_message = condition_checker.check_lessons_per_week_limit(section, subject_code)
                
                # If adding one more would exceed the limit (or it's already exceeded)
                if exceeded or (count + 1 > limit and limit > 0):
                    proceed = messagebox.askyesno(
                        "Subject Limit Warning", 
                        f"Subject {subject_code} has a lessons_per_week limit of {limit}.\n\n"
                        f"This subject is already assigned {count} times in section {section}.\n\n"
                        f"Do you want to proceed with this assignment anyway?",
                        parent=dialog
                    )
                    if not proceed:
                        return
                
                # Check for lesson type and handle period merging if needed
                periods_to_merge, lesson_type, merge_message = condition_checker.check_lesson_type_for_merging(section, subject_code)
                
                # If subject requires multiple periods (Double/Triple)
                if periods_to_merge > 1:
                    # Validate if merging is possible
                    is_valid, periods_needed, error_message = condition_checker.validate_merged_periods(
                        section, subject_code, day_idx, period_idx)
                    
                    if not is_valid:
                        # Show error message and ask if user wants to continue with just this period
                        proceed = messagebox.askyesno(
                            "Period Merging Issue", 
                            f"This subject requires {periods_to_merge} consecutive periods ({lesson_type} lesson).\n\n"
                            f"However, there is an issue: {error_message}\n\n"
                            f"Do you want to assign it to just this period instead?",
                            parent=dialog
                        )
                        if not proceed:
                            return
                    else:
                        # Merging is valid, ask user if they want to merge periods
                        proceed = messagebox.askyesno(
                            "Merge Periods", 
                            f"This subject requires {periods_to_merge} consecutive periods ({lesson_type} lesson).\n\n"
                            f"Do you want to automatically assign this subject to the next "
                            f"{periods_to_merge-1} period(s) as well?",
                            parent=dialog
                        )
                        if proceed:
                            # Proceed with merging periods
                            success, result_message, affected_periods = condition_checker.merge_periods(
                                section, subject_code, day_idx, period_idx, faculty_ini)
                            
                            if success:
                                # Commit changes
                                self.conn.commit()
                                
                                # Update the cell display
                                self.load_timetable_data()
                                
                                # Close the dialog
                                dialog.destroy()
                                
                                # Show success message
                                messagebox.showinfo("Success", result_message, parent=self)
                                return
                            else:
                                # Show error message
                                messagebox.showerror("Merging Error", result_message, parent=dialog)
                                return
            
            # If we're here, either we're removing an assignment (NULL) or we're not merging periods
            
            # Generate a unique ID for the schedule entry
            entry_id = f"{section}{day_idx * len(self.periods) + period_idx}"
            
            # Handle NULL case (removing assignment)
            if faculty_ini == 'NULL' and subject_code == 'NULL':
                self.conn.execute(
                    "DELETE FROM SCHEDULE WHERE ID=? AND SECTION=? AND DAYID=? AND PERIODID=?",
                    (entry_id, section, day_idx, period_idx)
                )
            else:
                # Update or insert new schedule entry
                self.conn.execute("""
                    REPLACE INTO SCHEDULE (ID, DAYID, PERIODID, SUBCODE, SECTION, FINI)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (entry_id, day_idx, period_idx, subject_code, section, faculty_ini))
                
            # Commit changes
            self.conn.commit()
            
            # Update the cell display
            self.load_timetable_data()
            
            # Close the dialog
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to update cell: {e}")

    def check_conflicts(self, faculty_ini, day_id, period_id, current_section):
        """
        Check for scheduling conflicts:
        1. Same faculty teaching in different sections during the same period/day
        2. Same section having multiple classes during the same period/day
        
        Returns a tuple (has_conflict, conflict_message)
        """
        conflicts = []
        
        # Only check for conflicts if we're adding a faculty (not removing)
        if faculty_ini != 'NULL':
            try:
                # Check if faculty is already assigned to this period on this day
                cursor = self.conn.execute(
                    "SELECT SECTION FROM SCHEDULE WHERE DAYID=? AND PERIODID=? AND FINI=?",
                    (day_id, period_id, faculty_ini)
                )
                
                faculty_conflicts = list(cursor)
                for row in faculty_conflicts:
                    if row[0] != current_section:
                        conflicts.append(f"Faculty '{faculty_ini}' is already assigned to section '{row[0]}' during {self.days[day_id]} Period {period_id+1}")
                        
                # Check if faculty has too many periods in a day
                cursor = self.conn.execute(
                    "SELECT COUNT(*) FROM SCHEDULE WHERE DAYID=? AND FINI=?",
                    (day_id, faculty_ini)
                )
                period_count = cursor.fetchone()[0]
                if period_count >= 5:  # If faculty already has 5 or more periods in a day
                    conflicts.append(f"Faculty '{faculty_ini}' already has {period_count} periods on {self.days[day_id]}")
                
                # Check for back-to-back recess conflict
                if period_id == self.recess_break_after or period_id == self.recess_break_after - 1:
                    adjacent_period = self.recess_break_after - 1 if period_id == self.recess_break_after else self.recess_break_after
                    cursor = self.conn.execute(
                        "SELECT COUNT(*) FROM SCHEDULE WHERE DAYID=? AND PERIODID=? AND FINI=?",
                        (day_id, adjacent_period, faculty_ini)
                    )
                    has_adjacent = cursor.fetchone()[0] > 0
                    if has_adjacent:
                        conflicts.append(f"Faculty '{faculty_ini}' is assigned to adjacent periods across recess on {self.days[day_id]}")
                
            except sqlite3.Error as e:
                print(f"Database error while checking conflicts: {e}")
                return True, f"Database error: {e}"
                
        if conflicts:
            return True, "\n".join(conflicts)
        else:
            return False, ""

    def load_timetable_data(self):
        """Load timetable data from the database"""
        try:
            # Clear existing cell content
            for cell_key, cell_frame in self.timetable_cells.items():
                for widget in cell_frame.winfo_children():
                    if isinstance(widget, tk.Label):
                        widget.config(text="")  # Empty text for empty cells
            
            # Load and display data for each section
            for class_idx, section in enumerate(self.class_names):
                for day_idx in range(len(self.days)):
                    for period_idx in range(len(self.periods)):
                        cursor = self.conn.execute("""
                            SELECT SUBCODE, FINI FROM SCHEDULE
                            WHERE DAYID=? AND PERIODID=? AND SECTION=?
                        """, (day_idx, period_idx, section))
                        
                        result = cursor.fetchone()
                        cell_key = (class_idx, day_idx, period_idx)
                        
                        if result:
                            subject_code, faculty_ini = result
                            # Only display the subject code (short name)
                            cell_text = f"{subject_code}"
                            
                            # Update the cell label
                            for widget in self.timetable_cells[cell_key].winfo_children():
                                if isinstance(widget, tk.Label):
                                    widget.config(text=cell_text)
                                    
                                    # Set background color based on subject (optional)
                                    subject_color = self.get_subject_color(subject_code)
                                    if subject_color:
                                        widget.config(bg=subject_color)
                                        self.timetable_cells[cell_key].config(bg=subject_color)
                        
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load timetable data: {e}")

    def get_subject_color(self, subject_code):
        """Get color for a subject from the database"""
        try:
            cursor = self.conn.execute(
                "SELECT color FROM SUBJECTS WHERE SUBCODE=?", (subject_code,)
            )
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
        except:
            pass
        return None

    def show_cell_details(self, event, cell_key):
        """Show detailed information about a cell on right-click"""
        class_idx, day_idx, period_idx = cell_key
        section = self.class_names[class_idx]
        
        try:
            # Get cell data
            cursor = self.conn.execute("""
                SELECT SCHEDULE.SUBCODE, SCHEDULE.FINI, SUBJECTS.SUBNAME, FACULTY.NAME
                FROM SCHEDULE 
                LEFT JOIN SUBJECTS ON SCHEDULE.SUBCODE = SUBJECTS.SUBCODE
                LEFT JOIN FACULTY ON SCHEDULE.FINI = FACULTY.INI
                WHERE SCHEDULE.DAYID=? AND SCHEDULE.PERIODID=? AND SCHEDULE.SECTION=?
            """, (day_idx, period_idx, section))
            
            result = cursor.fetchone()
            
            if result:
                subject_code, faculty_ini, subject_name, faculty_name = result
                
                # Check if this is part of a merged (Double/Triple) lesson
                condition_checker = TimetableConditionChecker(self.db_path)
                periods_to_merge, lesson_type, _ = condition_checker.check_lesson_type_for_merging(section, subject_code)
                
                # Build the basic details string
                details = f"Section: {section}\n"
                details += f"Day: {self.days[day_idx]}\n"
                details += f"Period: {period_idx + 1}\n\n"
                details += f"Subject: {subject_name} ({subject_code})\n"
                details += f"Faculty: {faculty_name} ({faculty_ini})\n"
                
                # Add lesson type information if it's a multi-period lesson
                if periods_to_merge > 1:
                    # Check if this subject is actually assigned to consecutive periods
                    consecutive_periods = []
                    for p in range(max(0, period_idx - periods_to_merge + 1), 
                                  min(len(self.periods), period_idx + periods_to_merge)):
                        if p == period_idx:
                            continue  # Skip current period
                        
                        cursor = self.conn.execute("""
                            SELECT SUBCODE FROM SCHEDULE 
                            WHERE DAYID=? AND PERIODID=? AND SECTION=?
                        """, (day_idx, p, section))
                        result = cursor.fetchone()
                        
                        if result and result[0] == subject_code:
                            consecutive_periods.append(p + 1)  # 1-based period numbering
                    
                    details += f"\nLesson Type: {lesson_type} ({periods_to_merge} periods)\n"
                    
                    if consecutive_periods:
                        consecutive_periods.sort()
                        details += f"Spans periods: {period_idx+1} + {', '.join(map(str, consecutive_periods))}\n"
                    else:
                        details += f"Warning: This is a {lesson_type} lesson but does not span consecutive periods as expected.\n"
                
                # Show the details in a popup
                messagebox.showinfo("Cell Details", details)
            else:
                messagebox.showinfo("Cell Details", f"No class scheduled for {section} on {self.days[day_idx]} Period {period_idx + 1}")
                
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load cell details: {e}")

    def create_control_buttons(self):
        """Create control buttons for the timetable"""
        control_frame = ttk.Frame(self)
        control_frame.grid(row=self.num_classes_display + 2, column=0, columnspan=len(self.days) * len(self.periods) + 1, sticky="ew", padx=10, pady=10)
        
        # Save button
        save_button = ttk.Button(
            control_frame, 
            text="Save Changes",
            command=self.save_timetable_changes
        )
        save_button.pack(side=tk.LEFT, padx=5)
        
        # Reload button
        reload_button = ttk.Button(
            control_frame, 
            text="Reload Timetable",
            command=self.reload_timetable
        )
        reload_button.pack(side=tk.LEFT, padx=5)
        
        # Check conflicts button
        check_conflicts_button = ttk.Button(
            control_frame, 
            text="Check All Conflicts",
            command=self.check_all_conflicts
        )
        check_conflicts_button.pack(side=tk.LEFT, padx=5)
        
        # Print Timetable button
        print_timetable_button = ttk.Button(
            control_frame,
            text="Print Timetable",
            command=self.open_timetable_generator
        )
        print_timetable_button.pack(side=tk.LEFT, padx=5)
        
        # Class selector combobox
        if len(self.class_names) > 1:
            ttk.Label(control_frame, text="Select Section:").pack(side=tk.LEFT, padx=(20, 5))
            self.section_var = tk.StringVar(value=self.class_names[0])
            section_combo = ttk.Combobox(
                control_frame,
                textvariable=self.section_var,
                values=self.class_names,
                state="readonly"
            )
            section_combo.pack(side=tk.LEFT, padx=5)
            section_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_by_section())

    def save_timetable_changes(self):
        """Save all changes to the database"""
        try:
            self.conn.commit()
            messagebox.showinfo("Success", "Timetable changes saved successfully!")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to save changes: {e}")

    def reload_timetable(self):
        """Reload timetable data from the database"""
        self.load_timetable_data()
        messagebox.showinfo("Success", "Timetable reloaded successfully!")

    def filter_by_section(self):
        """Filter timetable display to show only the selected section"""
        selected_section = self.section_var.get()
        if selected_section in self.class_names:
            for i, class_name in enumerate(self.class_names):
                # Make all rows invisible first
                for cell_key in [(i, day_idx, period_idx) for day_idx in range(len(self.days)) for period_idx in range(len(self.periods))]:
                    if cell_key in self.timetable_cells:
                        self.timetable_cells[cell_key].grid_remove()
                self.class_label_widgets[i].grid_remove()
                
            # Make the selected section visible
            idx = self.class_names.index(selected_section)
            self.class_label_widgets[idx].grid()
            for cell_key in [(idx, day_idx, period_idx) for day_idx in range(len(self.days)) for period_idx in range(len(self.periods))]:
                if cell_key in self.timetable_cells:
                    self.timetable_cells[cell_key].grid()

    def check_all_conflicts(self):
        """Check and display all conflicts in the current timetable"""
        conflict_report = []
        
        try:
            # Query all schedule entries
            cursor = self.conn.execute(
                "SELECT DISTINCT DAYID, PERIODID, FINI FROM SCHEDULE WHERE FINI != 'NULL'"
            )
            schedule_items = list(cursor)
            
            # Check for faculty conflicts (same faculty assigned to multiple sections in same period)
            for day_id, period_id, faculty_ini in schedule_items:
                cursor = self.conn.execute(
                    "SELECT SECTION FROM SCHEDULE WHERE DAYID=? AND PERIODID=? AND FINI=?", 
                    (day_id, period_id, faculty_ini)
                )
                sections = [row[0] for row in cursor]
                
                if len(sections) > 1:
                    conflict_report.append(
                        f"CONFLICT: Faculty '{faculty_ini}' is assigned to multiple sections ({', '.join(sections)}) "
                        f"during {self.days[day_id]} Period {period_id+1}"
                    )
            
            # Check for faculty workload (too many periods in a day)
            cursor = self.conn.execute("SELECT DISTINCT FINI FROM SCHEDULE WHERE FINI != 'NULL'")
            faculty_list = [row[0] for row in cursor]
            
            for faculty in faculty_list:
                for day in range(len(self.days)):
                    cursor = self.conn.execute(
                        "SELECT COUNT(*) FROM SCHEDULE WHERE DAYID=? AND FINI=?",
                        (day, faculty)
                    )
                    period_count = cursor.fetchone()[0]
                    if period_count > 5:  # If faculty has more than 5 periods in a day
                        conflict_report.append(
                            f"WORKLOAD: Faculty '{faculty}' has {period_count} periods on {self.days[day]} (recommended max: 5)"
                        )
            
            # Check for subject assignments exceeding lessons_per_week limits
            condition_checker = TimetableConditionChecker(self.db_path)
            exceeded_limits = condition_checker.check_all_sections_limits()
            
            for section, subject_code, current_count, limit in exceeded_limits:
                conflict_report.append(
                    f"WARNING: Subject '{subject_code}' in section '{section}' has {current_count} assignments "
                    f"but lessons_per_week is set to {limit}"
                )
                
            # Check for incorrectly merged periods (Double/Triple lessons not spanning consecutive periods)
            # Get all distinct sections and subjects
            cursor = self.conn.execute("SELECT DISTINCT SECTION, SUBCODE FROM SCHEDULE WHERE SUBCODE != 'NULL'")
            section_subjects = [(row[0], row[1]) for row in cursor.fetchall()]
            
            for section, subject_code in section_subjects:
                # Check the lesson type for this subject
                periods_to_merge, lesson_type, _ = condition_checker.check_lesson_type_for_merging(section, subject_code)
                
                # Only check subjects with Double/Triple lesson type
                if periods_to_merge > 1:
                    # Get all periods where this subject is assigned
                    cursor = self.conn.execute("""
                        SELECT DAYID, PERIODID FROM SCHEDULE 
                        WHERE SECTION=? AND SUBCODE=?
                        ORDER BY DAYID, PERIODID
                    """, (section, subject_code))
                    assignments = [row for row in cursor.fetchall()]
                    
                    # For each assignment, check if it has the correct number of consecutive periods
                    for day_id, period_id in assignments:
                        # Find if there are consecutive periods with the same subject
                        consecutive_count = 1  # Start with 1 (the current period)
                        consecutive_periods = [period_id]
                        
                        # Check periods after this one
                        for i in range(1, periods_to_merge):
                            next_period = period_id + i
                            if (day_id, next_period) in assignments:
                                consecutive_count += 1
                                consecutive_periods.append(next_period)
                                
                        # Check periods before this one
                        for i in range(1, periods_to_merge):
                            prev_period = period_id - i
                            if prev_period >= 0 and (day_id, prev_period) in assignments:
                                consecutive_count += 1
                                consecutive_periods.append(prev_period)
                        
                        # Check if this period is part of a proper consecutive sequence
                        is_properly_merged = False
                        consecutive_periods.sort()
                        
                        # Check for each possible start position if there's a full span of consecutive periods
                        for start_idx in range(max(0, period_id - periods_to_merge + 1), period_id + 1):
                            expected_span = list(range(start_idx, start_idx + periods_to_merge))
                            if all(p in consecutive_periods for p in expected_span):
                                is_properly_merged = True
                                break
                        
                        # Only report if this specific period is not part of a proper merged sequence
                        # and we haven't reported it before
                        if not is_properly_merged:
                            # Check if we've already reported this specific period
                            conflict_key = f"{section}_{subject_code}_{day_id}_{period_id}"
                            if conflict_key not in [getattr(c, '_reported_key', '') for c in conflict_report]:
                                conflict_msg = (
                                    f"MERGE ISSUE: Subject '{subject_code}' in section '{section}' on {self.days[day_id]} "
                                    f"Period {period_id+1} is configured as {lesson_type} lesson but does not span {periods_to_merge} "
                                    f"consecutive periods as required"
                                )
                                # Add a custom attribute to track reported conflicts
                                conflict_msg = type('', (), {'__str__': lambda self: conflict_msg, '_reported_key': conflict_key})()
                                conflict_report.append(conflict_msg)
            
            # Display conflict report
            if conflict_report:
                conflict_text = "\n\n".join(str(c) for c in conflict_report)
                messagebox.showwarning("Timetable Conflicts", 
                                     f"The following conflicts were detected in the timetable:\n\n{conflict_text}")
            else:
                messagebox.showinfo("Conflict Check", "No conflicts found in the timetable!")
                
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to check conflicts: {e}")

    def open_timetable_generator(self):
        """Open the timetable generator to print the current timetable"""
        try:
            # Get the current section
            if hasattr(self, 'section_var'):
                current_section = self.section_var.get()
            else:
                current_section = self.class_names[0] if self.class_names else ""
            
            # Get the path to the timetable_generator.py file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            timetable_generator_path = os.path.join(current_dir, "timetable_generator.py")
            
            if not os.path.exists(timetable_generator_path):
                messagebox.showerror("File Not Found", "The timetable generator file was not found.")
                return
            
            # Launch the timetable generator with the current section as parameter
            import subprocess
            python_executable = sys.executable
            
            # Create a command that will run the timetable generator with the current section
            cmd = [python_executable, timetable_generator_path, current_section]
            
            # Launch the process
            subprocess.Popen(cmd)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open timetable generator: {str(e)}")


# Example usage:
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Timetable Editor")
    root.geometry("1200x800")
    
    editor = TimetableEditorComponent(root)
    editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    root.mainloop()
