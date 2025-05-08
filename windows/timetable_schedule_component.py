import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

class TimetableScheduleComponent(ttk.Frame):
    def __init__(self, parent, class_name_filter="CSE", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.class_name_filter = class_name_filter.upper()
        
        # Database connection
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'files', 'timetable.db')
        self.conn = self._connect_db()
        
        # Default timetable settings
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.periods = 6
        self.recess_after = 3  # recess after 3rd Period
        
        # Store cell widgets
        self.cells = {}  # format: {(day_idx, period_idx): cell_frame}
        
        self._create_ui()
        self._load_timetable_data()

    def _connect_db(self):
        """Connect to the database and create tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Create tables if they don't exist
            conn.execute('''CREATE TABLE IF NOT EXISTS SCHEDULE
                (ID CHAR(10) NOT NULL PRIMARY KEY,
                DAYID INT NOT NULL,
                PERIODID INT NOT NULL,
                SUBCODE CHAR(10) NOT NULL,
                SECTION CHAR(5) NOT NULL,
                FINI CHAR(10) NOT NULL)''')
            
            return conn
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {e}")
            return None

    def _create_ui(self):
        """Create the timetable UI structure"""
        # Main container
        content_frame = ttk.Frame(self, padding="10")
        content_frame.pack(expand=True, fill=tk.BOTH)

        # Section selection frame
        select_frame = ttk.Frame(content_frame)
        select_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(select_frame, text="Section: ", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Get available sections
        sections = self._get_available_sections()
        self.section_var = tk.StringVar(value=self.class_name_filter)
        self.section_combobox = ttk.Combobox(
            select_frame, 
            textvariable=self.section_var,
            values=sections,
            width=10
        )
        self.section_combobox.pack(side=tk.LEFT)
        
        # Update button
        ttk.Button(select_frame, text="View", command=self._update_section).pack(side=tk.LEFT, padx=10)

        # Title
        ttk.Label(content_frame, text=self.class_name_filter, font=("Arial", 20, "bold")).pack(pady=(0, 15))
        
        # Create timetable grid
        self._create_timetable_grid(content_frame)

    def _create_timetable_grid(self, parent):
        """Create the timetable grid structure"""
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(expand=True, fill=tk.BOTH)

        # Empty top-left cell
        ttk.Label(grid_frame, text="", borderwidth=1, relief="solid").grid(row=0, column=0, sticky="nsew")

        # Create period headers
        for i in range(self.periods):
            if i == self.recess_after:
                # Add recess column
                recess_label = ttk.Label(grid_frame, text="RECESS", borderwidth=1, relief="solid",
                                       font=("Arial", 10, "bold"))
                recess_label.grid(row=0, rowspan=len(self.days)+1, column=i+1, sticky="nsew")
            else:
                period_num = i if i < self.recess_after else i-1
                ttk.Label(grid_frame, text=f"Period {period_num+1}", borderwidth=1, relief="solid",
                         font=("Arial", 10, "bold")).grid(row=0, column=i+1, sticky="nsew")

        # Create day headers and cells
        for day_idx, day in enumerate(self.days):
            ttk.Label(grid_frame, text=day, borderwidth=1, relief="solid",
                     font=("Arial", 10, "bold")).grid(row=day_idx+1, column=0, sticky="nsew")
            
            for period_idx in range(self.periods):
                if period_idx != self.recess_after:
                    cell_frame = self._create_cell(grid_frame, day_idx, period_idx)
                    cell_frame.grid(row=day_idx+1, column=period_idx+1, sticky="nsew", padx=1, pady=1)
                    self.cells[(day_idx, period_idx)] = cell_frame

        # Configure grid weights
        for i in range(len(self.days) + 1):
            grid_frame.grid_rowconfigure(i, weight=1)
        for i in range(self.periods + 1):
            grid_frame.grid_columnconfigure(i, weight=1)

    def _create_cell(self, parent, day_idx, period_idx):
        """Create an individual timetable cell"""
        cell_frame = ttk.Frame(parent, borderwidth=1, relief="solid")
        
        # Add labels for subject and faculty
        subject_label = ttk.Label(cell_frame, text="No Class", anchor="center", font=("Arial", 9))
        subject_label.pack(expand=True, fill=tk.BOTH)
        
        faculty_label = ttk.Label(cell_frame, text="", anchor="center", font=("Arial", 8))
        faculty_label.pack(expand=True, fill=tk.BOTH)
        
        # Bind click event
        cell_frame.bind("<Button-1>", lambda e, d=day_idx, p=period_idx: self._show_assignment_dialog(d, p))
        
        return cell_frame

    def _show_assignment_dialog(self, day_idx, period_idx):
        """Show dialog to assign subject and faculty"""
        dialog = tk.Toplevel(self)
        dialog.title("Assign Subject and Faculty")
        dialog.transient(self)
        
        # Add dialog content
        ttk.Label(dialog, text=f"Day: {self.days[day_idx]}", font=("Arial", 12)).pack(pady=5)
        ttk.Label(dialog, text=f"Period: {period_idx + 1}", font=("Arial", 12)).pack(pady=5)
        
        # Create Treeview for subject-faculty selection
        tree = ttk.Treeview(dialog, columns=("faculty", "subject"), show="headings", height=10)
        tree.heading("faculty", text="Faculty")
        tree.heading("subject", text="Subject")
        tree.column("faculty", width=100)
        tree.column("subject", width=100)
        
        # Load faculty-subject combinations
        self._load_faculty_subjects(tree)
        
        tree.pack(pady=10, padx=10)
        
        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Assign",
                  command=lambda: self._update_assignment(day_idx, period_idx, tree, dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear",
                  command=lambda: self._clear_assignment(day_idx, period_idx, dialog)).pack(side=tk.LEFT, padx=5)

    def _load_faculty_subjects(self, tree):
        """Load faculty and their subjects into the treeview"""
        try:
            cursor = self.conn.execute("""
                SELECT FACULTY.INI, FACULTY.SUBCODE1, FACULTY.SUBCODE2, SUBJECTS.SUBCODE, SUBJECTS.SUBNAME
                FROM FACULTY, SUBJECTS
                WHERE FACULTY.SUBCODE1=SUBJECTS.SUBCODE OR FACULTY.SUBCODE2=SUBJECTS.SUBCODE
                ORDER BY FACULTY.INI
            """)
            
            for row in cursor:
                faculty_ini, _, _, subcode, subname = row
                tree.insert("", "end", values=(faculty_ini, f"{subcode} - {subname}"))
                
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error loading faculty data: {e}")

    def _update_assignment(self, day_idx, period_idx, tree, dialog):
        """Update the schedule with new assignment"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a faculty-subject combination.")
            return
            
        item = tree.item(selection[0])
        faculty_ini, subject_full = item['values']
        subject_code = subject_full.split(' - ')[0]
        
        # Check for conflicts
        if self._check_conflicts(faculty_ini, day_idx, period_idx):
            return
            
        try:
            # Create unique ID for the schedule entry
            schedule_id = f"{self.class_name_filter}{day_idx}{period_idx}"
            
            # Update database
            self.conn.execute("""
                REPLACE INTO SCHEDULE (ID, DAYID, PERIODID, SUBCODE, SECTION, FINI)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (schedule_id, day_idx, period_idx, subject_code, self.class_name_filter, faculty_ini))
            
            self.conn.commit()
            
            # Update UI
            self._load_timetable_data()
            dialog.destroy()
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error updating schedule: {e}")

    def _clear_assignment(self, day_idx, period_idx, dialog):
        """Clear the assignment for a cell"""
        try:
            schedule_id = f"{self.class_name_filter}{day_idx}{period_idx}"
            self.conn.execute("DELETE FROM SCHEDULE WHERE ID=?", (schedule_id,))
            self.conn.commit()
            
            # Update UI
            self._load_timetable_data()
            dialog.destroy()
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error clearing assignment: {e}")

    def _check_conflicts(self, faculty_ini, day_idx, period_idx):
        """Check for scheduling conflicts"""
        try:
            # Check if faculty is already assigned to this period
            cursor = self.conn.execute("""
                SELECT SECTION FROM SCHEDULE 
                WHERE DAYID=? AND PERIODID=? AND FINI=? AND SECTION!=?
            """, (day_idx, period_idx, faculty_ini, self.class_name_filter))
            
            conflicts = list(cursor)
            if conflicts:
                conflict_sections = [row[0] for row in conflicts]
                message = f"Faculty '{faculty_ini}' is already assigned to section(s) {', '.join(conflict_sections)} during this period."
                result = messagebox.askyesno("Scheduling Conflict", f"{message}\n\nDo you want to proceed anyway?")
                return not result  # Return True if user doesn't want to proceed
                
            return False
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error checking conflicts: {e}")
            return True

    def _get_available_sections(self):
        """Get list of available sections from the database"""
        try:
            cursor = self.conn.execute("SELECT DISTINCT SECTION FROM SCHEDULE ORDER BY SECTION")
            sections = [row[0] for row in cursor]
            
            if not sections:
                # Try getting from STUDENT table as fallback
                cursor = self.conn.execute("SELECT DISTINCT SECTION FROM STUDENT ORDER BY SECTION")
                sections = [row[0] for row in cursor]
            
            return sections if sections else [self.class_name_filter]
            
        except sqlite3.Error:
            return [self.class_name_filter]

    def _update_section(self):
        """Update display when section is changed"""
        self.class_name_filter = self.section_var.get()
        self._load_timetable_data()

    def _load_timetable_data(self):
        """Load and display timetable data from database"""
        try:
            # Clear all cells first
            for cell_frame in self.cells.values():
                for widget in cell_frame.winfo_children():
                    widget.config(text="")
                cell_frame.winfo_children()[0].config(text="No Class")
            
            # Load data from database
            cursor = self.conn.execute("""
                SELECT s.DAYID, s.PERIODID, s.SUBCODE, s.FINI, sub.SUBNAME
                FROM SCHEDULE s
                LEFT JOIN SUBJECTS sub ON s.SUBCODE = sub.SUBCODE
                WHERE s.SECTION = ?
            """, (self.class_name_filter,))
            
            for row in cursor:
                day_idx, period_idx, subcode, faculty_ini, subname = row
                if (day_idx, period_idx) in self.cells:
                    cell_frame = self.cells[(day_idx, period_idx)]
                    cell_frame.winfo_children()[0].config(text=subname or subcode)  # Subject
                    cell_frame.winfo_children()[1].config(text=faculty_ini)  # Faculty
                    
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error loading timetable data: {e}")

    def destroy(self):
        """Clean up resources"""
        if self.conn:
            self.conn.close()
        super().destroy()

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Timetable Scheduler")
    root.geometry("1200x800")
    
    app = TimetableScheduleComponent(root)
    app.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
    root.mainloop()