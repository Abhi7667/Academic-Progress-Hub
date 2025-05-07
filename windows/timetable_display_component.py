import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import sqlite3

class TimetableDisplayComponent(ttk.Frame):
    def __init__(self, parent, class_names_list=None, period_labels_list=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Load days from database instead of hardcoding
        self.days = self.load_days_from_db()
        
        # Use provided lists or defaults
        self.class_names = class_names_list if class_names_list else [f"Class {i+1}" for i in range(10)] # Default to 10 classes
        self.periods = period_labels_list if period_labels_list else [str(i) for i in range(8)] # Default to 0-7 periods
        
        self.num_classes_display = len(self.class_names)

        # To store references to widgets for potential updates or data loading
        self.class_label_widgets = []
        self.period_header_widgets = [] # For day and period headers
        self.timetable_cells = {} # To store cell frames: {(class_idx, day_idx, period_idx): frame}
        
        # For cell movement functionality
        self.selected_cell = None
        self.selected_cell_data = None
        self.highlighted_cells = []

        self.configure_grid_weights()
        self.create_header_labels()
        self.create_class_labels()
        self.create_timetable_grid_cells()
        self.create_control_buttons()
        # self.load_data(timetable_data) # Method to be implemented later

    def load_days_from_db(self):
        """Load day names from the database based on settings in step1.py"""
        try:
            # Determine the path to the database
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, 'files', 'timetable.db')
            
            if not os.path.exists(db_path):
                print(f"Database not found at: {db_path}")
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

    def configure_grid_weights(self):
        # Configure column weight for class labels
        self.grid_columnconfigure(0, weight=0) # Fixed width for class labels initially
        
        # Configure column weights for period cells
        total_period_columns = len(self.days) * len(self.periods)
        for i in range(1, total_period_columns + 1):
            self.grid_columnconfigure(i, weight=1)

        # Configure row weights for header and class rows
        self.grid_rowconfigure(0, weight=0) # Day headers
        self.grid_rowconfigure(1, weight=0) # Period headers
        for i in range(self.num_classes_display):
            self.grid_rowconfigure(2 + i, weight=1)

    def create_header_labels(self):
        # Create day labels (spanning across their respective periods)
        for day_idx, day_name in enumerate(self.days):
            start_col = 1 + (day_idx * len(self.periods))
            day_label = ttk.Label(self, text=day_name, font=('Arial', 10, 'bold'), relief=tk.RIDGE, anchor=tk.CENTER)
            day_label.grid(row=0, column=start_col, columnspan=len(self.periods), sticky="nsew")
            self.period_header_widgets.append(day_label) # Store reference

        # Create period labels (under each day)
        for day_idx in range(len(self.days)):
            for period_idx, period_name in enumerate(self.periods):
                col = 1 + (day_idx * len(self.periods)) + period_idx
                period_label = ttk.Label(self, text=period_name, relief=tk.RIDGE, anchor=tk.CENTER)
                period_label.grid(row=1, column=col, sticky="nsew")
                self.period_header_widgets.append(period_label) # Store reference
        
        # Placeholder for the top-left empty cell or "Class" header
        top_left_label = ttk.Label(self, text="Class", relief=tk.RIDGE, anchor=tk.CENTER)
        top_left_label.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.period_header_widgets.append(top_left_label) # Store reference


    def create_class_labels(self):
        self.class_label_widgets = [] # Clear previous widgets if any
        for i, class_name_text in enumerate(self.class_names):
            class_label = ttk.Label(self, text=class_name_text, relief=tk.RIDGE, anchor=tk.W, padding=(5,0))
            class_label.grid(row=2 + i, column=0, sticky="nsew")
            self.class_label_widgets.append(class_label)

    def create_timetable_grid_cells(self):
        # Create empty frames for each timetable cell
        self.timetable_cells = {} # Clear previous cells
        for class_idx in range(self.num_classes_display):
            for day_idx in range(len(self.days)):
                for period_idx in range(len(self.periods)):
                    col = 1 + (day_idx * len(self.periods)) + period_idx
                    row = 2 + class_idx
                    
                    cell_key = (class_idx, day_idx, period_idx)
                    cell_frame = tk.Frame(self, borderwidth=1, relief=tk.SUNKEN) # bg="white"
                    cell_frame.grid(row=row, column=col, sticky="nsew")
                    self.timetable_cells[cell_key] = cell_frame
                    
                    # Add bindings for cell movement
                    cell_frame.bind("<Button-1>", lambda event, c=cell_key: self.on_cell_click(event, c))
                    cell_frame.bind("<B1-Motion>", self.on_drag)
                    cell_frame.bind("<ButtonRelease-1>", self.on_drop)
                    # Add binding for showing details on right-click
                    cell_frame.bind("<Button-3>", lambda event, c=cell_key: self.show_cell_details(event, c))
                    # We'll use these frames to display subject info or merge them for double/triple lessons

    def on_cell_click(self, event, cell_key):
        """Handler for clicking on a cell to start drag operation"""
        # Remove previous highlights if any
        for cell in self.highlighted_cells:
            if cell in self.timetable_cells:
                self.timetable_cells[cell].config(highlightbackground="SystemButtonFace", highlightthickness=0)
        self.highlighted_cells = []
        
        # Save the selected cell and its data
        self.selected_cell = cell_key
        self.selected_cell_data = self.get_cell_data(cell_key)
        
        # Highlight the selected cell - use a thicker border and better color
        if cell_key in self.timetable_cells:
            self.timetable_cells[cell_key].config(highlightbackground="#007BFF", highlightthickness=3)
            self.highlighted_cells.append(cell_key)
            
            # Change cursor to indicate drag is possible
            self.timetable_cells[cell_key].config(cursor="fleur")  # Use move cursor
            
            # You could also change the opacity/color of the cell to indicate selection
            for widget in self.timetable_cells[cell_key].winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(relief="raised")  # Make it appear raised
    
    def on_drag(self, event):
        """Handler for dragging a cell"""
        if not self.selected_cell:
            return
            
        # Change cursor during drag
        self.config(cursor="fleur")
        
        # Optional: Show a "ghost" image of the cell being dragged
        # This requires more complex canvas operations, but we can at least
        # provide feedback by changing the appearance of the original cell
        
        # Get current mouse position
        x, y = event.widget.winfo_pointerxy()
        target_widget = event.widget.winfo_containing(x, y)
        
        # Reset all potential targets
        for cell_key, frame in self.timetable_cells.items():
            if cell_key != self.selected_cell and cell_key not in self.highlighted_cells:
                frame.config(highlightbackground="SystemButtonFace", highlightthickness=0)
        
        # Highlight potential drop target
        for cell_key, frame in self.timetable_cells.items():
            if frame == target_widget or target_widget in frame.winfo_children():
                if cell_key != self.selected_cell:
                    frame.config(highlightbackground="#32CD32", highlightthickness=2)  # Light green for potential target
                break
        
    def on_drop(self, event):
        """Handler for dropping a cell onto another cell position"""
        if not self.selected_cell:
            return
            
        # Find the cell that was dropped on
        try:
            # Get global mouse coordinates
            x, y = event.widget.winfo_pointerxy()
            
            # Find widget under mouse
            target_widget = event.widget.winfo_containing(x, y)
            
            # Find which cell contains this widget
            target_cell = None
            for key, frame in self.timetable_cells.items():
                if frame == target_widget or target_widget in frame.winfo_children():
                    target_cell = key
                    break
            
            if target_cell and target_cell != self.selected_cell:
                # Swap cells
                self.swap_cells(self.selected_cell, target_cell)
                
                # Update the database with the new cell positions
                self.update_db_with_cell_swap(self.selected_cell, target_cell)
                
                print(f"Swapped cell {self.selected_cell} with {target_cell}")
            else:
                print(f"No valid target cell found or same as source cell.")
                
        except Exception as e:
            print(f"Error during drag and drop: {e}")
            
        # Reset selection
        self.selected_cell = None
        self.selected_cell_data = None
        
        # Remove highlights and restore appearance
        for cell_key, frame in self.timetable_cells.items():
            # Reset border highlights
            frame.config(highlightbackground="SystemButtonFace", highlightthickness=0)
            
            # Reset cursor
            frame.config(cursor="")
            
            # Reset any raised effect on labels
            for widget in frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(relief="flat")
        
        # Reset main cursor
        self.config(cursor="")
        
        # Clear highlighted cells list
        self.highlighted_cells = []
    
    def get_cell_data(self, cell_key):
        """Extract data from a cell"""
        cell_frame = self.timetable_cells.get(cell_key)
        if not cell_frame:
            return None
            
        # Get all the widgets in the cell
        widgets = cell_frame.winfo_children()
        data = {"widgets": [], "texts": [], "colors": []}
        
        for widget in widgets:
            if isinstance(widget, tk.Label):
                data["widgets"].append(widget)
                data["texts"].append(widget.cget("text"))
                data["colors"].append(widget.cget("bg"))
                
        return data
    
    def swap_cells(self, cell1, cell2):
        """Swap the content of two cells"""
        # Get data from both cells
        data1 = self.get_cell_data(cell1)
        data2 = self.get_cell_data(cell2)
        
        if not data1 or not data2:
            return
            
        # Clear both cells
        for cell in [cell1, cell2]:
            for widget in self.timetable_cells[cell].winfo_children():
                widget.destroy()
        
        # Recreate widgets in swapped cells
        self.recreate_cell_content(cell2, data1)
        self.recreate_cell_content(cell1, data2)
    
    def recreate_cell_content(self, cell_key, data):
        """Recreate cell content based on data"""
        if not data or "texts" not in data or not data["texts"]:
            return
            
        cell_frame = self.timetable_cells.get(cell_key)
        if not cell_frame:
            return
            
        # Create new labels with the same text and colors
        for i, text in enumerate(data["texts"]):
            color = data["colors"][i] if i < len(data["colors"]) else "#FFFFFF"
            font_size = 9 if i == 0 else 8  # First label is usually subject
            font_style = "bold" if i == 0 else ""
            
            label = tk.Label(
                cell_frame,
                text=text,
                bg=color,
                font=("Arial", font_size, font_style),
                borderwidth=1 if i == 0 else 0,
                relief="solid" if i == 0 else "flat"
            )
            
            # Pack the first label (subject) to fill the frame
            if i == 0:
                label.pack(expand=True, fill=tk.BOTH)
            else:
                label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_db_with_cell_swap(self, cell1, cell2):
        """Update the database with the swapped cell positions"""
        # Extract class, day, and period info from cell keys
        class1_idx, day1_idx, period1_idx = cell1
        class2_idx, day2_idx, period2_idx = cell2
        
        # Get the corresponding class names
        class1_name = self.class_names[class1_idx] if class1_idx < len(self.class_names) else None
        class2_name = self.class_names[class2_idx] if class2_idx < len(self.class_names) else None
        
        if not class1_name or not class2_name:
            return
            
        try:
            # Connect to database
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, 'files', 'timetable.db')
            
            if not os.path.exists(db_path):
                print(f"Database not found at: {db_path}")
                return
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try to update SCHEDULE table first (newer format)
            try:
                # Get subjects for both cells
                cursor.execute("""
                    SELECT SUBCODE, FINI FROM SCHEDULE 
                    WHERE SECTION=? AND DAYID=? AND PERIODID=?
                """, (class1_name, day1_idx, period1_idx))
                subj1 = cursor.fetchone()
                
                cursor.execute("""
                    SELECT SUBCODE, FINI FROM SCHEDULE 
                    WHERE SECTION=? AND DAYID=? AND PERIODID=?
                """, (class2_name, day2_idx, period2_idx))
                subj2 = cursor.fetchone()
                
                # Swap the subjects
                if subj1 and subj2:
                    cursor.execute("""
                        UPDATE SCHEDULE SET SUBCODE=?, FINI=? 
                        WHERE SECTION=? AND DAYID=? AND PERIODID=?
                    """, (subj2[0], subj2[1], class1_name, day1_idx, period1_idx))
                    
                    cursor.execute("""
                        UPDATE SCHEDULE SET SUBCODE=?, FINI=? 
                        WHERE SECTION=? AND DAYID=? AND PERIODID=?
                    """, (subj1[0], subj1[1], class2_name, day2_idx, period2_idx))
            except sqlite3.Error as e:
                print(f"Error updating SCHEDULE: {e}")
                
            # Try updating SCHEDULED_LESSONS table (older format)
            try:
                # Convert day indices to day codes
                day_codes = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
                day1_code = day_codes[day1_idx] if day1_idx < len(day_codes) else None
                day2_code = day_codes[day2_idx] if day2_idx < len(day_codes) else None
                
                if day1_code and day2_code:
                    # Get subjects and teachers for both cells
                    cursor.execute("""
                        SELECT SUBJECT_CODE, TEACHER_ID FROM SCHEDULED_LESSONS 
                        WHERE CLASS_NAME=? AND DAY_OF_WEEK=? AND PERIOD_NUMBER=?
                    """, (class1_name, day1_code, period1_idx + 1))  # +1 because periods are 1-indexed in this table
                    lesson1 = cursor.fetchone()
                    
                    cursor.execute("""
                        SELECT SUBJECT_CODE, TEACHER_ID FROM SCHEDULED_LESSONS 
                        WHERE CLASS_NAME=? AND DAY_OF_WEEK=? AND PERIOD_NUMBER=?
                    """, (class2_name, day2_code, period2_idx + 1))
                    lesson2 = cursor.fetchone()
                    
                    # Swap the lessons
                    if lesson1 and lesson2:
                        cursor.execute("""
                            UPDATE SCHEDULED_LESSONS SET SUBJECT_CODE=?, TEACHER_ID=? 
                            WHERE CLASS_NAME=? AND DAY_OF_WEEK=? AND PERIOD_NUMBER=?
                        """, (lesson2[0], lesson2[1], class1_name, day1_code, period1_idx + 1))
                        
                        cursor.execute("""
                            UPDATE SCHEDULED_LESSONS SET SUBJECT_CODE=?, TEACHER_ID=? 
                            WHERE CLASS_NAME=? AND DAY_OF_WEEK=? AND PERIOD_NUMBER=?
                        """, (lesson1[0], lesson1[1], class2_name, day2_code, period2_idx + 1))
            except sqlite3.Error as e:
                print(f"Error updating SCHEDULED_LESSONS: {e}")
                
            conn.commit()
            
            # Check for conflicts after the swap
            conflicts, _ = check_faculty_conflicts()
            
            # If conflicts were created by this swap, warn the user
            new_conflicts = []
            for conflict in conflicts:
                day_id, period_id, fini, section1, section2 = conflict
                # Check if this conflict involves one of our swapped cells
                if ((day_id == day1_idx and period_id == period1_idx and (section1 == class1_name or section2 == class1_name)) or
                    (day_id == day2_idx and period_id == period2_idx and (section1 == class2_name or section2 == class2_name))):
                    new_conflicts.append((day_id, period_id, fini, section1, section2))
            
            if new_conflicts:
                error_message = "Faculty scheduling conflicts created:\n\n"
                for conflict in new_conflicts[:5]:  # Show up to 5 conflicts
                    day_id, period_id, fini, section1, section2 = conflict
                    day_name = self.days[day_id] if day_id < len(self.days) else f"Day {day_id}"
                    error_message += f"Faculty {fini} assigned to {section1} and {section2} at {day_name} period {period_id+1}\n"
                
                if len(new_conflicts) > 5:
                    error_message += "...(more conflicts)...\n"
                
                error_message += "\nThese conflicts will be highlighted in red in the timetable."
                messagebox.showwarning("Scheduling Conflicts", error_message)
                
                # Reload the timetable to show the conflicts
                days = self.days
                periods_per_day = len(self.periods)
                timetable_data = load_timetable_data(self.class_names, days, periods_per_day)
                self.load_data(timetable_data)
            
            conn.close()
        except Exception as e:
            print(f"Error updating database with swapped cells: {e}")

    def create_control_buttons(self):
        """Create control buttons like the Review button"""
        control_frame = ttk.Frame(self, padding=(5, 10))
        control_frame.grid(row=self.num_classes_display + 2, column=0, columnspan=len(self.days) * len(self.periods) + 1, sticky="ew")
        
        # Review button that opens timetable_generator.py
        review_button = ttk.Button(
            control_frame, 
            text="Review Timetable",
            command=self.open_timetable_generator
        )
        review_button.pack(side=tk.RIGHT, padx=10)
        
        # Add a save button
        save_button = ttk.Button(
            control_frame,
            text="Save Changes",
            command=self.save_timetable_changes
        )
        save_button.pack(side=tk.RIGHT, padx=10)
        
        # Add a reload button
        reload_button = ttk.Button(
            control_frame,
            text="Reload Timetable",
            command=self.reload_timetable
        )
        reload_button.pack(side=tk.RIGHT, padx=10)

    def save_timetable_changes(self):
        """Save any pending changes to the database"""
        messagebox.showinfo("Save Changes", "Changes saved to database successfully.")
        
    def reload_timetable(self):
        """Reload timetable data from the database"""
        days = self.days
        periods_per_day = len(self.periods)
        timetable_data = load_timetable_data(self.class_names, days, periods_per_day)
        self.load_data(timetable_data)
        messagebox.showinfo("Reload", "Timetable reloaded from database.")

    def open_timetable_generator(self):
        """Open the timetable generator window"""
        try:
            # Get the path to the timetable_generator.py file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            generator_path = os.path.join(current_dir, 'timetable_generator.py')
            
            # Launch the generator in a new process
            if sys.platform.startswith('win'):
                subprocess.Popen([sys.executable, generator_path])
            else:
                subprocess.Popen([sys.executable, generator_path])
                
            print(f"Opening timetable generator: {generator_path}")
        except Exception as e:
            print(f"Error opening timetable generator: {e}")

    def load_data(self, timetable_data):
        """
        Populates the grid with timetable data.
        timetable_data is expected to have the structure:
        {
            "class_name": {
                "day": [
                    {"subject": "Ma", "teacher": "Te", "color": "#RRGGBB", "lesson_type": "Single"}, # Period 0
                    {"subject": "En", "teacher": "Te", "color": "#RRGGBB", "lesson_type": "Double"}, # Period 1
                    # ... other periods
                ],
                # ... other days
            },
            # ... other classes
        }
        """
        # Load subject colors from database
        subject_colors_db = load_subject_colors()
        
        # Check for faculty conflicts
        _, conflict_cells = check_faculty_conflicts()
        
        # Default subject code to color mapping (fallback if not in database)
        default_subject_colors = {
            "Ma": "#ADD8E6",  # Light Blue
            "En": "#90EE90",  # Light Green
            "Hi": "#FFB6C1",  # Light Pink
            "Sc": "#FFFFE0",  # Light Yellow
            "Ph": "#E6E6FA",  # Lavender
            "Ch": "#FFA07A",  # Light Salmon
            "Bi": "#98FB98",  # Pale Green
            "Cs": "#D8BFD8",  # Thistle
            "Pe": "#FFDAB9",  # Peach Puff
            "Ar": "#F0FFF0",  # Honeydew
            "Mu": "#F5DEB3",  # Wheat
            "Sp": "#DDA0DD",  # Plum
            "Ge": "#B0E0E6",  # Powder Blue
            "Ec": "#F5F5DC",  # Beige
            "Py": "#FAEBD7",  # Antique White
            "Ja": "#E0FFFF",  # Light Cyan
            "Na": "#FFF8DC",  # Cornsilk
            "Op": "#FFE4E1",  # Misty Rose
            "Et": "#F5FFFA",  # Mint Cream
            "Pa": "#F0F8FF",  # Alice Blue
        }
        
        # Clear existing cell contents and reset grid configuration
        for cell_frame in self.timetable_cells.values():
            for widget in cell_frame.winfo_children():
                widget.destroy()
            cell_frame.grid_forget()  # Remove from grid to reset

        # Recreate the grid with all cells (we'll hide/merge as needed)
        for class_idx in range(self.num_classes_display):
            for day_idx in range(len(self.days)):
                for period_idx in range(len(self.periods)):
                    col = 1 + (day_idx * len(self.periods)) + period_idx
                    row = 2 + class_idx
                    
                    cell_key = (class_idx, day_idx, period_idx)
                    if cell_key in self.timetable_cells:
                        self.timetable_cells[cell_key].grid(row=row, column=col, sticky="nsew")
        
        # Process and display timetable data, handling merged cells for double/triple lessons
        processed_cells = set()  # Track which cells have been processed to avoid duplicates
        
        for class_idx, class_name in enumerate(self.class_names):
            if class_name in timetable_data:
                class_data = timetable_data[class_name]
                
                for day_idx, day in enumerate(self.days):
                    if day in class_data:
                        day_data = class_data[day]
                        
                        for period_idx, period_data in enumerate(day_data):
                            if period_idx < len(self.periods) and period_data and (class_idx, day_idx, period_idx) not in processed_cells:
                                cell_key = (class_idx, day_idx, period_idx)
                                
                                if cell_key in self.timetable_cells:
                                    # Get lesson details
                                    subject = period_data.get("subject", "")
                                    teacher = period_data.get("teacher", "")
                                    subcode = period_data.get("subcode", "")  # Full subject code if available
                                    lesson_type = period_data.get("lesson_type", "Single")
                                    
                                    # Determine background color - priority:
                                    # 1. Use color from data if provided
                                    # 2. Use color from database based on subject code
                                    # 3. Use color from database based on subject abbreviation
                                    # 4. Use default color map
                                    # 5. Default white
                                    
                                    bg_color = period_data.get("color", None)
                                    
                                    if not bg_color and subcode and subcode in subject_colors_db:
                                        bg_color = subject_colors_db[subcode]
                                    elif not bg_color and subject in subject_colors_db:
                                        bg_color = subject_colors_db[subject]
                                    elif not bg_color:
                                        bg_color = default_subject_colors.get(subject, "#FFFFFF")
                                    
                                    # Check if this cell has a conflict
                                    has_conflict = cell_key in conflict_cells
                                    
                                    # Handle merged cells for double/triple lessons
                                    colspan = 1  # Default is single period
                                    if lesson_type == "Double" and period_idx < len(self.periods) - 1:
                                        colspan = 2
                                        # Mark the next cell as processed
                                        processed_cells.add((class_idx, day_idx, period_idx + 1))
                                    elif lesson_type == "Triple" and period_idx < len(self.periods) - 2:
                                        colspan = 3
                                        # Mark the next two cells as processed
                                        processed_cells.add((class_idx, day_idx, period_idx + 1))
                                        processed_cells.add((class_idx, day_idx, period_idx + 2))
                                    
                                    # If this is a multi-period lesson, reconfigure the grid
                                    if colspan > 1:
                                        # Remove the cells that will be merged from the grid
                                        for i in range(1, colspan):
                                            next_cell_key = (class_idx, day_idx, period_idx + i)
                                            if next_cell_key in self.timetable_cells:
                                                self.timetable_cells[next_cell_key].grid_forget()
                                        
                                        # Configure this cell to span multiple columns
                                        cell_frame = self.timetable_cells[cell_key]
                                        col = 1 + (day_idx * len(self.periods)) + period_idx
                                        cell_frame.grid(row=row, column=col, columnspan=colspan, sticky="nsew")
                                    
                                    # Clear the cell frame
                                    cell_frame = self.timetable_cells[cell_key]
                                    for widget in cell_frame.winfo_children():
                                        widget.destroy()
                                    
                                    # Create or update subject label with border for conflicts
                                    subject_label = tk.Label(
                                        cell_frame, 
                                        text=subject,
                                        bg=bg_color,
                                        font=("Arial", 9, "bold"),
                                        borderwidth=2 if has_conflict else 1,
                                        relief="solid",
                                        # Add a red border if there's a conflict
                                        highlightbackground="red" if has_conflict else bg_color,
                                        highlightcolor="red" if has_conflict else bg_color,
                                        highlightthickness=2 if has_conflict else 0
                                    )
                                    subject_label.pack(expand=True, fill=tk.BOTH)
                                    
                                    # Add teacher initials if available
                                    if teacher:
                                        teacher_label = tk.Label(
                                            cell_frame,
                                            text=teacher,
                                            bg=bg_color,
                                            font=("Arial", 8),
                                            fg="red" if has_conflict else "black"  # Red text for conflicts
                                        )
                                        teacher_label.pack(side=tk.BOTTOM, fill=tk.X)
                                    
                                    # Add lesson type indicator for double/triple lessons
                                    if colspan > 1:
                                        type_label = tk.Label(
                                            cell_frame,
                                            text=f"({lesson_type})",
                                            bg=bg_color,
                                            font=("Arial", 7, "italic")
                                        )
                                        type_label.pack(side=tk.BOTTOM, fill=tk.X)
                                    
                                    # Mark this cell as processed
                                    processed_cells.add(cell_key)

    def show_cell_details(self, event, cell_key):
        """Display detailed information about the class when a cell is clicked"""
        if not cell_key or cell_key not in self.timetable_cells:
            return
            
        class_idx, day_idx, period_idx = cell_key
        class_name = self.class_names[class_idx] if class_idx < len(self.class_names) else None
        
        if not class_name:
            return
            
        try:
            # Connect to database
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, 'files', 'timetable.db')
            
            if not os.path.exists(db_path):
                messagebox.showinfo("Database Missing", "Timetable database not found.")
                return
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Day name from index
            day_name = self.days[day_idx] if day_idx < len(self.days) else f"Day {day_idx}"
            
            # Check for conflicts for this cell
            conflicts, conflict_cells = check_faculty_conflicts()
            has_conflict = cell_key in conflict_cells
            conflict_details = []
            
            if has_conflict:
                for conflict in conflicts:
                    day_id, period_id, fini, section1, section2 = conflict
                    if day_id == day_idx and period_id == period_idx and (section1 == class_name or section2 == class_name):
                        conflict_details.append((fini, section1, section2))
            
            # Try to get data from SCHEDULE table first (newer format)
            query = """
                SELECT sch.SUBCODE, sch.FINI, s.SUBNAME, s.SUBTYPE, f.NAME, f.EMAIL, s.COLOR 
                FROM SCHEDULE sch
                LEFT JOIN SUBJECTS s ON sch.SUBCODE = s.SUBCODE
                LEFT JOIN FACULTY f ON sch.FINI = f.INI
                WHERE sch.SECTION = ? AND sch.DAYID = ? AND sch.PERIODID = ?
            """
            cursor.execute(query, (class_name, day_idx, period_idx))
            schedule_data = cursor.fetchone()
            
            if schedule_data:
                # Extract data
                data_fields = ["subcode", "fini", "subname", "subtype", "faculty_name", "faculty_email", "color"]
                data = {field: value for field, value in zip(data_fields, schedule_data)}
                
                # Convert subject type code to description
                if data["subtype"] == 'T':
                    subtype_display = 'Theory'
                elif data["subtype"] == 'P':
                    subtype_display = 'Practical'
                else:
                    subtype_display = data["subtype"] or 'Not specified'
                
                # Get associated classrooms for this subject
                classrooms = []
                try:
                    classroom_cursor = conn.execute("""
                        SELECT CLASSROOM_NAME FROM SUBJECT_CLASSROOMS 
                        WHERE SUBCODE = ? 
                        ORDER BY CLASSROOM_NAME
                    """, (data["subcode"],))
                    classrooms = [c[0] for c in classroom_cursor.fetchall()]
                except sqlite3.Error as e:
                    print(f"Error fetching classrooms: {e}")
                
                # Create detail window
                details = tk.Toplevel(self)
                details.title("Class Details")
                details.geometry("450x450")  # Larger to accommodate conflict info
                
                # Configure a frame with the subject color as background
                color_frame = tk.Frame(details, bg=data["color"] if data["color"] else "#FFFFFF", padx=10, pady=10)
                color_frame.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(color_frame, text='Class Details', font=('Arial', 15, 'bold'), background=data["color"]).pack(pady=15)
                
                # Show conflict warning if needed
                if has_conflict:
                    conflict_frame = tk.Frame(color_frame, bg="#FFD0D0", padx=5, pady=5, borderwidth=2, relief="raised")
                    conflict_frame.pack(fill=tk.X, pady=(0, 15))
                    ttk.Label(conflict_frame, text="FACULTY SCHEDULING CONFLICT!", foreground="red", font=('Arial', 10, 'bold')).pack(anchor="w")
                    
                    for fini, section1, section2 in conflict_details:
                        conflict_text = f"Faculty {fini} is assigned to both {section1} and {section2} at this time"
                        ttk.Label(conflict_frame, text=conflict_text, foreground="red").pack(anchor="w", padx=10)
                
                # Basic details
                ttk.Label(color_frame, text=f'Day: {day_name}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                ttk.Label(color_frame, text=f'Period: {period_idx + 1}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                ttk.Label(color_frame, text=f'Subject Code: {data["subcode"] or "N/A"}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                ttk.Label(color_frame, text=f'Subject Name: {data["subname"] or "N/A"}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                ttk.Label(color_frame, text=f'Subject Type: {subtype_display}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                ttk.Label(color_frame, text=f'Faculty Initials: {data["fini"] or "N/A"}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                ttk.Label(color_frame, text=f'Faculty Name: {data["faculty_name"] or "N/A"}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                ttk.Label(color_frame, text=f'Faculty Email: {data["faculty_email"] or "N/A"}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                ttk.Label(color_frame, text=f'Section: {class_name}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                
                # Show classrooms if available
                if classrooms:
                    ttk.Label(color_frame, text=f'Classrooms: {", ".join(classrooms)}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                
                ttk.Button(
                    color_frame,
                    text="OK",
                    width=10,
                    command=details.destroy
                ).pack(pady=10)
            else:
                # Try SCHEDULED_LESSONS table (older format)
                # Convert day index to day code
                day_codes = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
                day_code = day_codes[day_idx] if day_idx < len(day_codes) else None
                
                if day_code:
                    query = """
                        SELECT sl.SUBJECT_CODE, sl.TEACHER_ID, s.SUBNAME, s.SUBTYPE, f.NAME, f.EMAIL, s.COLOR
                        FROM SCHEDULED_LESSONS sl
                        LEFT JOIN SUBJECTS s ON sl.SUBJECT_CODE = s.SUBCODE
                        LEFT JOIN FACULTY f ON sl.TEACHER_ID = f.FID
                        WHERE sl.CLASS_NAME = ? AND sl.DAY_OF_WEEK = ? AND sl.PERIOD_NUMBER = ?
                    """
                    cursor.execute(query, (class_name, day_code, period_idx + 1))  # +1 because periods are 1-indexed in this table
                    lesson_data = cursor.fetchone()
                    
                    if lesson_data:
                        # Extract data
                        data_fields = ["subcode", "teacher_id", "subname", "subtype", "faculty_name", "faculty_email", "color"]
                        data = {field: value for field, value in zip(data_fields, lesson_data)}
                        
                        # Convert subject type code to description
                        if data["subtype"] == 'T':
                            subtype_display = 'Theory'
                        elif data["subtype"] == 'P':
                            subtype_display = 'Practical'
                        else:
                            subtype_display = data["subtype"] or 'Not specified'
                        
                        # Get associated classrooms for this subject
                        classrooms = []
                        try:
                            classroom_cursor = conn.execute("""
                                SELECT CLASSROOM_NAME FROM SUBJECT_CLASSROOMS 
                                WHERE SUBCODE = ? 
                                ORDER BY CLASSROOM_NAME
                            """, (data["subcode"],))
                            classrooms = [c[0] for c in classroom_cursor.fetchall()]
                        except sqlite3.Error as e:
                            print(f"Error fetching classrooms: {e}")
                        
                        # Create detail window
                        details = tk.Toplevel(self)
                        details.title("Class Details")
                        details.geometry("450x450")  # Larger to accommodate conflict info
                        
                        # Configure a frame with the subject color as background
                        color_frame = tk.Frame(details, bg=data["color"] if data["color"] else "#FFFFFF", padx=10, pady=10)
                        color_frame.pack(fill=tk.BOTH, expand=True)
                        
                        ttk.Label(color_frame, text='Class Details', font=('Arial', 15, 'bold'), background=data["color"]).pack(pady=15)
                        
                        # Show conflict warning if needed
                        if has_conflict:
                            conflict_frame = tk.Frame(color_frame, bg="#FFD0D0", padx=5, pady=5, borderwidth=2, relief="raised")
                            conflict_frame.pack(fill=tk.X, pady=(0, 15))
                            ttk.Label(conflict_frame, text="FACULTY SCHEDULING CONFLICT!", foreground="red", font=('Arial', 10, 'bold')).pack(anchor="w")
                            
                            for fini, section1, section2 in conflict_details:
                                conflict_text = f"Faculty {fini} is assigned to both {section1} and {section2} at this time"
                                ttk.Label(conflict_frame, text=conflict_text, foreground="red").pack(anchor="w", padx=10)
                        
                        # Basic details
                        ttk.Label(color_frame, text=f'Day: {day_name}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                        ttk.Label(color_frame, text=f'Period: {period_idx + 1}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                        ttk.Label(color_frame, text=f'Subject Code: {data["subcode"] or "N/A"}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                        ttk.Label(color_frame, text=f'Subject Name: {data["subname"] or "N/A"}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                        ttk.Label(color_frame, text=f'Subject Type: {subtype_display}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                        ttk.Label(color_frame, text=f'Faculty ID: {data["teacher_id"] or "N/A"}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                        ttk.Label(color_frame, text=f'Faculty Name: {data["faculty_name"] or "N/A"}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                        ttk.Label(color_frame, text=f'Faculty Email: {data["faculty_email"] or "N/A"}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                        ttk.Label(color_frame, text=f'Section: {class_name}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                        
                        # Show classrooms if available
                        if classrooms:
                            ttk.Label(color_frame, text=f'Classrooms: {", ".join(classrooms)}', anchor="w", background=data["color"]).pack(expand=1, fill=tk.X)
                        
                        ttk.Button(
                            color_frame,
                            text="OK",
                            width=10,
                            command=details.destroy
                        ).pack(pady=10)
                    else:
                        messagebox.showinfo("No Class", f"No class scheduled for {day_name} Period {period_idx + 1}")
            
            conn.close()
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error retrieving class details: {e}")
        except Exception as ex:
            messagebox.showerror("Error", f"Unexpected error: {ex}")

def load_classes_from_db():
    """Load class data from the database"""
    classes = []
    try:
        # Determine the path to the database
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'files', 'timetable.db')
        
        if not os.path.exists(db_path):
            print(f"Database not found at: {db_path}")
            return []
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Try to get classes from SCHEDULE table first
        cursor.execute("SELECT DISTINCT SECTION FROM SCHEDULE ORDER BY SECTION")
        classes = [row[0] for row in cursor.fetchall()]
        
        # If no classes found in SCHEDULE, try SCHEDULED_LESSONS
        if not classes:
            cursor.execute("SELECT DISTINCT CLASS_NAME FROM SCHEDULED_LESSONS ORDER BY CLASS_NAME")
            classes = [row[0] for row in cursor.fetchall()]
            
        # If still no classes, try CLASS table
        if not classes:
            cursor.execute("SELECT DISTINCT SECTION FROM CLASS ORDER BY SECTION")
            classes = [row[0] for row in cursor.fetchall()]
            
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error loading classes: {e}")
        
    return classes if classes else [f"Class {i+1}" for i in range(5)]

def load_periods_from_db():
    """Load period data from the database"""
    periods = []
    try:
        # Determine the path to the database
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'files', 'timetable.db')
        
        if not os.path.exists(db_path):
            return [f"P{i+1}" for i in range(8)]  # Default periods if DB not found
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First check if there's a setting in SCHOOL_CONFIG from step1.py
        cursor.execute("SELECT periods_per_day FROM SCHOOL_CONFIG WHERE config_id=1")
        result = cursor.fetchone()
        
        if result and result[0]:
            num_periods = int(result[0])
            periods = [f"P{i+1}" for i in range(num_periods)]
        else:
            # Try to get period information from TIMETABLE_SETTINGS
            cursor.execute("SELECT setting_value FROM TIMETABLE_SETTINGS WHERE setting_name='NUM_PERIODS'")
            result = cursor.fetchone()
            
            if result and result[0]:
                num_periods = int(result[0])
                periods = [f"P{i+1}" for i in range(num_periods)]
            else:
                # If no setting found, check for max period in SCHEDULE
                cursor.execute("SELECT MAX(PERIODID) FROM SCHEDULE")
                result = cursor.fetchone()
                if result and result[0] is not None:
                    max_period = int(result[0])
                    periods = [f"P{i+1}" for i in range(max_period + 1)]
            
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error loading periods: {e}")
    except Exception as e:
        print(f"Error loading periods: {e}")
        
    return periods if periods else [f"P{i+1}" for i in range(8)]

def load_timetable_data(class_names, days, periods_per_day):
    """
    Load timetable data from the database for the given classes.
    Returns a structured dictionary of timetable data.
    """
    timetable_data = {}
    
    try:
        # Determine the path to the database
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'files', 'timetable.db')
        
        if not os.path.exists(db_path):
            print(f"Database not found at: {db_path}")
            return {}
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get subject colors
        subject_colors = load_subject_colors()
        
        # Initialize timetable data structure for each class
        for class_name in class_names:
            timetable_data[class_name] = {}
            for day in days:
                timetable_data[class_name][day] = [{} for _ in range(periods_per_day)]
        
        # Try to load from SCHEDULE table first (newer format)
        try:
            for class_name in class_names:
                # Map days (0-based in DB) to day names
                day_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
                
                # Get lesson type information from LESSONS table
                lesson_types = {}
                try:
                    cursor.execute("""
                        SELECT SUBJECT_CODE, LESSON_TYPE
                        FROM LESSONS
                        WHERE CLASS_NAME = ?
                    """, (class_name,))
                    for subject_code, lesson_type in cursor.fetchall():
                        lesson_types[subject_code] = lesson_type
                except sqlite3.Error as e:
                    print(f"Error fetching lesson types: {e}")
                
                cursor.execute("""
                    SELECT sch.DAYID, sch.PERIODID, s.SUBNAME, sch.FINI, s.SUBCODE, s.COLOR
                    FROM SCHEDULE sch
                    LEFT JOIN SUBJECTS s ON sch.SUBCODE = s.SUBCODE
                    WHERE sch.SECTION = ? 
                    ORDER BY sch.DAYID, sch.PERIODID
                """, (class_name,))
                
                schedule_entries = cursor.fetchall()
                
                for entry in schedule_entries:
                    if len(entry) >= 5:  # Ensure we have at least the basic data
                        day_id, period_id, subject_name, faculty_ini, subject_code = entry[:5]
                        
                        # Get color if available (might be 6th column)
                        color = None
                        if len(entry) >= 6 and entry[5]:
                            color = entry[5]
                        elif subject_code in subject_colors:
                            color = subject_colors[subject_code]
                        
                        # Convert day ID to day name and handle index adjustments
                        day_name = day_map.get(day_id, f"Day{day_id}")
                        
                        # Skip if day not in our display or period outside range
                        if day_name not in days or period_id >= periods_per_day:
                            continue
                        
                        # Use first two letters of subject as code, or use subject code directly
                        subject_code_display = subject_code[:2] if subject_code else (subject_name[:2] if subject_name else "")
                        
                        # Get lesson type for this subject
                        lesson_type = lesson_types.get(subject_code, "Single")
                        
                        # Add to timetable data
                        timetable_data[class_name][day_name][period_id] = {
                            "subject": subject_code_display,
                            "teacher": faculty_ini,
                            "full_name": subject_name,
                            "subcode": subject_code,  # Store full subject code
                            "color": color,          # Store color
                            "lesson_type": lesson_type
                        }
        except Exception as e:
            print(f"Error loading from SCHEDULE: {e}")
            
        # If no data from SCHEDULE, try SCHEDULED_LESSONS table (older format)
        for class_name in class_names:
            day_map = {"Mo": "Monday", "Tu": "Tuesday", "We": "Wednesday", "Th": "Thursday", "Fr": "Friday", "Sa": "Saturday", "Su": "Sunday"}
            
            # Get lesson type information from LESSONS table
            lesson_types = {}
            try:
                cursor.execute("""
                    SELECT SUBJECT_CODE, LESSON_TYPE
                    FROM LESSONS
                    WHERE CLASS_NAME = ?
                """, (class_name,))
                for subject_code, lesson_type in cursor.fetchall():
                    lesson_types[subject_code] = lesson_type
            except sqlite3.Error as e:
                print(f"Error fetching lesson types: {e}")
            
            cursor.execute("""
                SELECT sl.DAY_OF_WEEK, sl.PERIOD_NUMBER, s.SUBNAME, f.INI, s.SUBCODE, s.COLOR
                FROM SCHEDULED_LESSONS sl
                LEFT JOIN SUBJECTS s ON sl.SUBJECT_CODE = s.SUBCODE
                LEFT JOIN FACULTY f ON sl.TEACHER_ID = f.FID
                WHERE sl.CLASS_NAME = ? 
                ORDER BY sl.DAY_OF_WEEK, sl.PERIOD_NUMBER
            """, (class_name,))
            
            schedule_entries = cursor.fetchall()
            
            for entry in schedule_entries:
                if len(entry) >= 5:  # Ensure we have at least the basic data
                    day_code, period_num, subject_name, faculty_ini, subject_code = entry[:5]
                    
                    # Get color if available (might be 6th column)
                    color = None
                    if len(entry) >= 6 and entry[5]:
                        color = entry[5]
                    elif subject_code in subject_colors:
                        color = subject_colors[subject_code]
                    
                    # Convert day code to day name and adjust period (DB is 1-indexed, we want 0-indexed)
                    day_name = day_map.get(day_code, day_code)
                    period_idx = period_num - 1  # Convert from 1-indexed to 0-indexed
                    
                    # Skip if day not in our display or period outside range
                    if day_name not in days or period_idx >= periods_per_day or period_idx < 0:
                        continue
                    
                    # Use first two letters of subject as code, or use subject code directly
                    subject_code_display = subject_code[:2] if subject_code else (subject_name[:2] if subject_name else "")
                    
                    # Get lesson type for this subject
                    lesson_type = lesson_types.get(subject_code, "Single")
                    
                    # Add to timetable data if slot is empty
                    if not timetable_data[class_name][day_name][period_idx].get("subject"):
                        timetable_data[class_name][day_name][period_idx] = {
                            "subject": subject_code_display,
                            "teacher": faculty_ini,
                            "full_name": subject_name,
                            "subcode": subject_code,  # Store full subject code
                            "color": color,          # Store color
                            "lesson_type": lesson_type
                        }
                
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error loading timetable: {e}")
    except Exception as e:
        print(f"Error loading timetable data: {e}")
    
    return timetable_data

def load_subject_colors():
    """Load subject colors from the SUBJECTS table"""
    subject_colors = {}
    try:
        # Connect to database
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'files', 'timetable.db')
        
        if not os.path.exists(db_path):
            print(f"Database not found at: {db_path}")
            return subject_colors
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if COLOR column exists in SUBJECTS table
        cursor.execute("PRAGMA table_info(SUBJECTS)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'COLOR' in columns:
            # Get subject colors
            cursor.execute("SELECT SUBCODE, COLOR FROM SUBJECTS")
            for row in cursor.fetchall():
                if row[0] and row[1]:  # Ensure both values exist
                    subject_colors[row[0]] = row[1]
        
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error loading subject colors: {e}")
    except Exception as e:
        print(f"Error loading subject colors: {e}")
        
    return subject_colors

def check_faculty_conflicts():
    """Check for conflicts where the same faculty is assigned to multiple sections at the same time"""
    conflicts = []
    conflict_cells = set()  # Store cell keys with conflicts
    
    try:
        # Connect to database
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'files', 'timetable.db')
        
        if not os.path.exists(db_path):
            return conflicts, conflict_cells
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check conflicts in SCHEDULE table (scheduler.py format)
        query = """
        SELECT s1.DAYID, s1.PERIODID, s1.FINI, s1.SECTION, s2.SECTION
        FROM SCHEDULE s1
        JOIN SCHEDULE s2 ON s1.DAYID = s2.DAYID 
                         AND s1.PERIODID = s2.PERIODID
                         AND s1.FINI = s2.FINI
                         AND s1.SECTION != s2.SECTION
        ORDER BY s1.DAYID, s1.PERIODID, s1.FINI;
        """
        
        cursor.execute(query)
        conflicts_schedule = cursor.fetchall()
        
        # Process conflicts
        for conflict in conflicts_schedule:
            day_id, period_id, fini, section1, section2 = conflict
            conflicts.append((day_id, period_id, fini, section1, section2))
            
            # Find corresponding class indices
            for class_idx, class_name in enumerate(load_classes_from_db()):
                if class_name == section1 or class_name == section2:
                    conflict_cells.add((class_idx, day_id, period_id))
        
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error checking for conflicts: {e}")
    
    return conflicts, conflict_cells

# Example usage (for testing this component)
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Timetable Display")
    root.geometry("1200x800") # Adjusted size for better viewing

    # Create a main frame to hold the timetable component
    main_container = ttk.Frame(root, padding="10")
    main_container.pack(expand=True, fill=tk.BOTH)

    # Load data from database
    class_names = load_classes_from_db()
    period_labels = load_periods_from_db()
    
    if not class_names:
        messagebox.showwarning("No Classes Found", "No classes were found in the database. Using default values.")
        class_names = [f"{grade}.{chr(ord('A') + section)}" for grade in range(5, 7) for section in range(3)]
    
    # Instantiate the timetable component with data from the database
    timetable_component = TimetableDisplayComponent(main_container, 
                                                  class_names_list=class_names, 
                                                  period_labels_list=period_labels)
    timetable_component.pack(expand=True, fill=tk.BOTH)
    
    # Load timetable data from the database
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    periods_per_day = len(period_labels)
    timetable_data = load_timetable_data(class_names, days, periods_per_day)
    
    # Load the timetable data into the component
    timetable_component.load_data(timetable_data)

    root.mainloop() 