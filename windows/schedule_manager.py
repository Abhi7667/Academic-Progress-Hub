import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from condition import TimetableConditionChecker

class ScheduleManager(tk.Tk):
    """
    Application for managing entries in the SCHEDULE table of the timetable database.
    Provides functionality to view, delete, and update schedule entries.
    """
    def __init__(self):
        super().__init__()
        self.title("Schedule Manager")
        self.geometry("1200x700")
        
        # Database connection
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(project_root, 'files', 'timetable.db')
        self.conn = self._connect_db()
        
        if not self.conn:
            messagebox.showerror("Database Error", "Failed to connect to database.")
            self.destroy()
            return
            
        # Create UI elements
        self._create_ui()
        
        # Load data
        self.load_schedule_data()
        
        # Set up protocol for closing
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _connect_db(self):
        """Connect to the SQLite database"""
        try:
            if not os.path.exists(self.db_path):
                messagebox.showerror("Database Error", f"Database not found at: {self.db_path}")
                return None
                
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {e}")
            return None
    
    def _create_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for filters and buttons
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Filter options
        filter_frame = ttk.LabelFrame(top_frame, text="Filters", padding=10)
        filter_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Section filter
        ttk.Label(filter_frame, text="Section:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.section_var = tk.StringVar()
        self.section_combo = ttk.Combobox(filter_frame, textvariable=self.section_var, width=10, state="readonly")
        self.section_combo.grid(row=0, column=1, padx=5)
        
        # Day filter
        ttk.Label(filter_frame, text="Day:").grid(row=0, column=2, padx=(20, 5), sticky=tk.W)
        self.day_var = tk.StringVar()
        self.day_combo = ttk.Combobox(filter_frame, textvariable=self.day_var, width=10, state="readonly")
        self.day_combo.grid(row=0, column=3, padx=5)
        
        # Period filter
        ttk.Label(filter_frame, text="Period:").grid(row=0, column=4, padx=(20, 5), sticky=tk.W)
        self.period_var = tk.StringVar()
        self.period_combo = ttk.Combobox(filter_frame, textvariable=self.period_var, width=10, state="readonly")
        self.period_combo.grid(row=0, column=5, padx=5)
        
        # Subject filter
        ttk.Label(filter_frame, text="Subject:").grid(row=0, column=6, padx=(20, 5), sticky=tk.W)
        self.subject_var = tk.StringVar()
        self.subject_combo = ttk.Combobox(filter_frame, textvariable=self.subject_var, width=15, state="readonly")
        self.subject_combo.grid(row=0, column=7, padx=5)
        
        # Apply filter button
        ttk.Button(filter_frame, text="Apply Filters", command=self.apply_filters).grid(row=0, column=8, padx=(20, 5))
        
        # Clear filter button
        ttk.Button(filter_frame, text="Clear Filters", command=self.clear_filters).grid(row=0, column=9, padx=5)
        
        # Action buttons frame
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Delete button
        self.delete_btn = ttk.Button(
            action_frame,
            text="Delete Selected",
            command=self.delete_selected
        )
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Update button
        self.update_btn = ttk.Button(
            action_frame,
            text="Update Selected",
            command=self.update_selected
        )
        self.update_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Check all conflicts button
        self.check_conflicts_btn = ttk.Button(
            action_frame,
            text="Check for Conflicts",
            command=self.check_for_conflicts
        )
        self.check_conflicts_btn.pack(side=tk.LEFT)
        
        # Reload button
        self.reload_btn = ttk.Button(
            action_frame,
            text="Reload Data",
            command=self.load_schedule_data
        )
        self.reload_btn.pack(side=tk.RIGHT)
        
        # Treeview for schedule data
        self.tree_frame = ttk.Frame(main_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the treeview with columns
        self.tree = ttk.Treeview(self.tree_frame, columns=(
            "id", "section", "day", "day_name", "period", "subject_code", "subject_name", "faculty", "faculty_name"
        ))
        
        # Set column headings
        self.tree.heading("#0", text="")
        self.tree.heading("id", text="ID")
        self.tree.heading("section", text="Section")
        self.tree.heading("day", text="Day ID")
        self.tree.heading("day_name", text="Day")
        self.tree.heading("period", text="Period")
        self.tree.heading("subject_code", text="Subject Code")
        self.tree.heading("subject_name", text="Subject")
        self.tree.heading("faculty", text="Faculty Code")
        self.tree.heading("faculty_name", text="Faculty")
        
        # Set column widths
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("id", width=100, stretch=tk.NO)
        self.tree.column("section", width=80, stretch=tk.NO)
        self.tree.column("day", width=60, stretch=tk.NO)
        self.tree.column("day_name", width=80, stretch=tk.NO)
        self.tree.column("period", width=60, stretch=tk.NO)
        self.tree.column("subject_code", width=100, stretch=tk.NO)
        self.tree.column("subject_name", width=200)
        self.tree.column("faculty", width=100, stretch=tk.NO)
        self.tree.column("faculty_name", width=200)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=x_scrollbar.set)
        
        # Layout scrollbars and treeview
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # Set up treeview bindings
        self.tree.bind("<Double-1>", self.on_row_double_click)
    
    def load_schedule_data(self):
        """Load data from the SCHEDULE table into the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            # Get day names mapping (dayid to day name)
            day_names = {
                0: "Monday",
                1: "Tuesday",
                2: "Wednesday",
                3: "Thursday",
                4: "Friday",
                5: "Saturday",
                6: "Sunday"
            }
            
            # Build query with joins to get subject and faculty names
            query = """
            SELECT 
                SCHEDULE.ID, 
                SCHEDULE.SECTION, 
                SCHEDULE.DAYID, 
                SCHEDULE.PERIODID, 
                SCHEDULE.SUBCODE, 
                SUBJECTS.SUBNAME,
                SCHEDULE.FINI,
                FACULTY.NAME
            FROM SCHEDULE
            LEFT JOIN SUBJECTS ON SCHEDULE.SUBCODE = SUBJECTS.SUBCODE
            LEFT JOIN FACULTY ON SCHEDULE.FINI = FACULTY.INI
            """
            
            # Apply filters if any are set
            where_clauses = []
            params = []
            
            if hasattr(self, 'section_var') and self.section_var.get():
                where_clauses.append("SCHEDULE.SECTION = ?")
                params.append(self.section_var.get())
            
            if hasattr(self, 'day_var') and self.day_var.get() != "":
                where_clauses.append("SCHEDULE.DAYID = ?")
                params.append(int(self.day_var.get()))
            
            if hasattr(self, 'period_var') and self.period_var.get() != "":
                where_clauses.append("SCHEDULE.PERIODID = ?")
                params.append(int(self.period_var.get()))
            
            if hasattr(self, 'subject_var') and self.subject_var.get():
                where_clauses.append("SCHEDULE.SUBCODE = ?")
                params.append(self.subject_var.get())
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += " ORDER BY SCHEDULE.SECTION, SCHEDULE.DAYID, SCHEDULE.PERIODID"
            
            cursor = self.conn.execute(query, params)
            
            # Populate the treeview
            rows = cursor.fetchall()
            for row in rows:
                id_val, section, day_id, period_id, subject_code, subject_name, faculty_code, faculty_name = row
                
                # Get day name from the mapping
                day_name = day_names.get(day_id, f"Day {day_id}")
                
                # Insert into treeview
                self.tree.insert("", tk.END, values=(
                    id_val, 
                    section, 
                    day_id, 
                    day_name, 
                    period_id, 
                    subject_code, 
                    subject_name or "", 
                    faculty_code, 
                    faculty_name or ""
                ))
            
            # Update status bar
            self.status_var.set(f"Loaded {len(rows)} schedule entries")
            
            # Update the filter comboboxes with available values
            self.update_filter_options()
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load schedule data: {e}")
    
    def update_filter_options(self):
        """Update the filter combobox options with values from the database"""
        try:
            # Get sections
            cursor = self.conn.execute("SELECT DISTINCT SECTION FROM SCHEDULE ORDER BY SECTION")
            sections = [row[0] for row in cursor.fetchall()]
            self.section_combo['values'] = [""] + sections
            
            # Get day IDs
            cursor = self.conn.execute("SELECT DISTINCT DAYID FROM SCHEDULE ORDER BY DAYID")
            day_ids = [str(row[0]) for row in cursor.fetchall()]
            self.day_combo['values'] = [""] + day_ids
            
            # Get period IDs
            cursor = self.conn.execute("SELECT DISTINCT PERIODID FROM SCHEDULE ORDER BY PERIODID")
            period_ids = [str(row[0]) for row in cursor.fetchall()]
            self.period_combo['values'] = [""] + period_ids
            
            # Get subject codes
            cursor = self.conn.execute("SELECT DISTINCT SUBCODE FROM SCHEDULE ORDER BY SUBCODE")
            subject_codes = [row[0] for row in cursor.fetchall()]
            self.subject_combo['values'] = [""] + subject_codes
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update filter options: {e}")
    
    def apply_filters(self):
        """Apply the selected filters and reload data"""
        self.load_schedule_data()
    
    def clear_filters(self):
        """Clear all filters and reload data"""
        self.section_var.set("")
        self.day_var.set("")
        self.period_var.set("")
        self.subject_var.set("")
        self.load_schedule_data()
    
    def delete_selected(self):
        """Delete the selected schedule entries"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Selection", "Please select at least one entry to delete.")
            return
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_items)} selected entries?"
        )
        
        if not confirm:
            return
        
        try:
            # Begin transaction
            self.conn.execute("BEGIN")
            
            # Delete each selected item
            for item in selected_items:
                values = self.tree.item(item, "values")
                id_val = values[0]  # ID is the first column
                
                # Delete from the database
                self.conn.execute("DELETE FROM SCHEDULE WHERE ID = ?", (id_val,))
            
            # Commit the transaction
            self.conn.commit()
            
            # Reload data
            self.load_schedule_data()
            
            # Update status
            self.status_var.set(f"Deleted {len(selected_items)} entries")
            
        except sqlite3.Error as e:
            # Rollback on error
            self.conn.rollback()
            messagebox.showerror("Database Error", f"Failed to delete entries: {e}")
    
    def update_selected(self):
        """Open a dialog to update the selected schedule entry"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Selection", "Please select one entry to update.")
            return
        
        if len(selected_items) > 1:
            messagebox.showinfo("Selection", "Please select only one entry to update.")
            return
        
        item = selected_items[0]
        values = self.tree.item(item, "values")
        
        # Extract values
        id_val = values[0]
        section = values[1]
        day_id = int(values[2])
        period_id = int(values[4])
        subject_code = values[5]
        faculty_code = values[7]
        
        # Create update dialog
        self.create_update_dialog(id_val, section, day_id, period_id, subject_code, faculty_code)
    
    def create_update_dialog(self, id_val, section, day_id, period_id, subject_code, faculty_code):
        """Create a dialog for updating a schedule entry"""
        dialog = tk.Toplevel(self)
        dialog.title(f"Update Schedule Entry: {id_val}")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Create a frame for the form
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # ID display (read-only)
        ttk.Label(form_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        id_var = tk.StringVar(value=id_val)
        ttk.Entry(form_frame, textvariable=id_var, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Section
        ttk.Label(form_frame, text="Section:").grid(row=1, column=0, sticky=tk.W, pady=5)
        section_var = tk.StringVar(value=section)
        sections = self.get_sections()
        section_combo = ttk.Combobox(form_frame, textvariable=section_var, values=sections, state="readonly")
        section_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Day
        ttk.Label(form_frame, text="Day:").grid(row=2, column=0, sticky=tk.W, pady=5)
        day_var = tk.IntVar(value=day_id)
        day_names = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday"
        }
        day_options = [f"{idx}: {name}" for idx, name in day_names.items()]
        day_combo = ttk.Combobox(form_frame, values=day_options, state="readonly")
        day_combo.current(day_id)  # Set the current value
        day_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Function to update day_var when the combobox selection changes
        def on_day_selected(event):
            selected_day = day_combo.get()
            day_idx = int(selected_day.split(":")[0])
            day_var.set(day_idx)
        
        day_combo.bind("<<ComboboxSelected>>", on_day_selected)
        
        # Period
        ttk.Label(form_frame, text="Period:").grid(row=3, column=0, sticky=tk.W, pady=5)
        period_var = tk.IntVar(value=period_id)
        period_options = [str(i) for i in range(8)]  # Assuming periods are 0-7
        period_combo = ttk.Combobox(form_frame, values=period_options, state="readonly")
        period_combo.current(period_id)  # Set the current value
        period_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Function to update period_var when the combobox selection changes
        def on_period_selected(event):
            period_var.set(int(period_combo.get()))
        
        period_combo.bind("<<ComboboxSelected>>", on_period_selected)
        
        # Subject
        ttk.Label(form_frame, text="Subject:").grid(row=4, column=0, sticky=tk.W, pady=5)
        subject_var = tk.StringVar(value=subject_code)
        subjects = self.get_subjects()
        subject_combo = ttk.Combobox(form_frame, textvariable=subject_var, values=subjects, state="readonly")
        subject_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Faculty
        ttk.Label(form_frame, text="Faculty:").grid(row=5, column=0, sticky=tk.W, pady=5)
        faculty_var = tk.StringVar(value=faculty_code)
        faculty = self.get_faculty()
        faculty_combo = ttk.Combobox(form_frame, textvariable=faculty_var, values=faculty, state="readonly")
        faculty_combo.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        # Update button
        update_btn = ttk.Button(
            button_frame,
            text="Update",
            command=lambda: self.perform_update(
                dialog,
                id_val,
                section_var.get(),
                day_var.get(),
                period_var.get(),
                subject_var.get(),
                faculty_var.get()
            )
        )
        update_btn.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Configure grid
        form_frame.columnconfigure(1, weight=1)
    
    def get_sections(self):
        """Get all available sections from the database"""
        try:
            cursor = self.conn.execute("SELECT DISTINCT SECTION FROM SCHEDULE ORDER BY SECTION")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def get_subjects(self):
        """Get all available subjects from the database"""
        try:
            cursor = self.conn.execute("""
                SELECT SUBCODE, SUBNAME FROM SUBJECTS ORDER BY SUBNAME
            """)
            subjects = [f"{row[0]}: {row[1]}" for row in cursor.fetchall()]
            # Add NULL option
            subjects.insert(0, "NULL")
            return subjects
        except sqlite3.Error:
            return ["NULL"]
    
    def get_faculty(self):
        """Get all available faculty from the database"""
        try:
            cursor = self.conn.execute("""
                SELECT INI, NAME FROM FACULTY ORDER BY NAME
            """)
            faculty = [f"{row[0]}: {row[1]}" for row in cursor.fetchall()]
            # Add NULL option
            faculty.insert(0, "NULL")
            return faculty
        except sqlite3.Error:
            return ["NULL"]
    
    def perform_update(self, dialog, id_val, section, day_id, period_id, subject, faculty):
        """Update the database with the new values"""
        try:
            # Extract subject_code and faculty_code if they contain descriptions
            if subject != "NULL" and ":" in subject:
                subject_code = subject.split(":")[0].strip()
            else:
                subject_code = subject
                
            if faculty != "NULL" and ":" in faculty:
                faculty_code = faculty.split(":")[0].strip()
            else:
                faculty_code = faculty
            
            # Begin transaction
            self.conn.execute("BEGIN")
            
            # Update the database
            self.conn.execute("""
                UPDATE SCHEDULE 
                SET SECTION = ?, DAYID = ?, PERIODID = ?, SUBCODE = ?, FINI = ?
                WHERE ID = ?
            """, (section, day_id, period_id, subject_code, faculty_code, id_val))
            
            # Commit the transaction
            self.conn.commit()
            
            # Close the dialog
            dialog.destroy()
            
            # Reload data
            self.load_schedule_data()
            
            # Update status
            self.status_var.set(f"Updated entry: {id_val}")
            
        except sqlite3.Error as e:
            # Rollback on error
            self.conn.rollback()
            messagebox.showerror("Database Error", f"Failed to update entry: {e}")
    
    def on_row_double_click(self, event):
        """Handle double-click on a row"""
        # Get the selected item
        item = self.tree.identify_row(event.y)
        if item:
            # Open the update dialog
            self.tree.selection_set(item)
            self.update_selected()
    
    def check_for_conflicts(self):
        """Check for conflicts in the timetable using the TimetableConditionChecker"""
        try:
            # Create a condition checker
            condition_checker = TimetableConditionChecker(self.db_path)
            
            # Get conflicts
            conflicts = []
            
            # 1. Check for subject assignments exceeding lessons_per_week limits
            exceeded_limits = condition_checker.check_all_sections_limits()
            for section, subject_code, current_count, limit in exceeded_limits:
                conflicts.append(
                    f"WARNING: Subject '{subject_code}' in section '{section}' has {current_count} assignments "
                    f"but lessons_per_week is set to {limit}"
                )
            
            # 2. Check for faculty conflicts (same faculty in multiple sections at same time)
            query = """
            SELECT s1.DAYID, s1.PERIODID, s1.FINI, s1.SECTION, s2.SECTION
            FROM SCHEDULE s1
            JOIN SCHEDULE s2 ON 
                s1.DAYID = s2.DAYID AND 
                s1.PERIODID = s2.PERIODID AND 
                s1.FINI = s2.FINI AND 
                s1.SECTION != s2.SECTION AND
                s1.FINI != 'NULL'
            """
            
            cursor = self.conn.execute(query)
            faculty_conflicts = cursor.fetchall()
            
            day_names = {
                0: "Monday",
                1: "Tuesday",
                2: "Wednesday",
                3: "Thursday",
                4: "Friday",
                5: "Saturday",
                6: "Sunday"
            }
            
            for day_id, period_id, faculty, section1, section2 in faculty_conflicts:
                day_name = day_names.get(day_id, f"Day {day_id}")
                conflicts.append(
                    f"CONFLICT: Faculty '{faculty}' is assigned to sections '{section1}' and '{section2}' "
                    f"on {day_name} Period {period_id+1}"
                )
            
            # 3. Check for lesson type conflicts (merged periods)
            # This is typically handled by the condition checker, but would require more complex code
            
            # Display conflicts or success message
            if conflicts:
                conflict_text = "\n\n".join(conflicts)
                messagebox.showwarning(
                    "Timetable Conflicts", 
                    f"The following conflicts were detected in the timetable:\n\n{conflict_text}"
                )
            else:
                messagebox.showinfo("No Conflicts", "No conflicts found in the current timetable.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check for conflicts: {e}")
    
    def _on_closing(self):
        """Close the database connection and destroy the window"""
        if self.conn:
            self.conn.close()
        self.destroy()

if __name__ == "__main__":
    app = ScheduleManager()
    app.mainloop() 