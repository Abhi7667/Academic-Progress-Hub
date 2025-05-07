import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser # For color picker
from tkinter import messagebox
import sqlite3 # For database integration
import os      # For path manipulation

class TeacherSelectionDialog(tk.Toplevel):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.title("Select Class Teacher")
        self.geometry("400x350")
        self.parent = parent
        self.conn = conn
        self.selected_teacher_id = None
        self.selected_teacher_name = None

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(main_frame, text="Select a teacher:", font=("Arial", 12)).pack(pady=(0,10))

        # Treeview for teacher list
        self.tree = ttk.Treeview(main_frame, columns=("id", "name"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.column("id", width=80, anchor=tk.W)
        self.tree.column("name", width=250, anchor=tk.W)
        self.tree.pack(expand=True, fill=tk.BOTH, pady=(0,10))

        self.populate_teachers()

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        select_btn = ttk.Button(btn_frame, text="Select", command=self.select_teacher)
        select_btn.pack(side=tk.RIGHT, padx=(5,0))

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT)

        self.tree.bind("<Double-1>", self.select_teacher_on_double_click)
        self.grab_set() # Modal dialog
        self.transient(parent)

    def populate_teachers(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        if self.conn:
            try:
                cursor = self.conn.execute("SELECT FID, NAME FROM FACULTY ORDER BY NAME")
                for row in cursor:
                    self.tree.insert("", tk.END, values=(row[0], row[1]))
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to load teachers: {e}", parent=self)
        else:
            messagebox.showwarning("Database Error", "No database connection available.", parent=self)

    def select_teacher_on_double_click(self, event):
        self.select_teacher()

    def select_teacher(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a teacher from the list.", parent=self)
            return
        
        teacher_data = self.tree.item(selected_item)
        self.selected_teacher_id = teacher_data["values"][0]
        self.selected_teacher_name = teacher_data["values"][1]
        self.destroy()

class ClassDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Class")
        self.geometry("450x500") # Adjusted for content
        self.resizable(False, False)

        # Database connection
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'files', 'timetable.db')
        self.conn = self._connect_db()
        self.selected_teacher_id = None # Initialize selected_teacher_id

        # --- Main Frame ---
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- Class Details Frame ---
        details_frame = ttk.Frame(main_frame)
        details_frame.pack(fill=tk.X, pady=(0, 10))

        # Class Name
        ttk.Label(details_frame, text="Class name :").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.class_name_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.class_name_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        # Short
        ttk.Label(details_frame, text="Short :").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.short_name_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.short_name_var, width=30).grid(row=1, column=1, padx=5, pady=5)

        # Custom Fields Button
        custom_fields_btn = ttk.Button(details_frame, text="Custom fields", command=self.custom_fields_action)
        custom_fields_btn.grid(row=2, column=1, sticky=tk.E, padx=5, pady=10)

        # Print Subject Pictures Checkbox
        self.print_subject_pictures_var = tk.BooleanVar()
        ttk.Checkbutton(
            details_frame,
            text="Print subject pictures",
            variable=self.print_subject_pictures_var
        ).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)


        # --- Color Section ---
        color_frame = ttk.LabelFrame(main_frame, text="Color", padding="10")
        color_frame.pack(fill=tk.X, pady=10)

        self.selected_color = tk.StringVar(value="#0078D7") # Default blue
        self.color_display = tk.Label(color_frame, text="", bg=self.selected_color.get(), width=30, height=2, relief=tk.SUNKEN)
        self.color_display.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,10))

        change_color_btn = ttk.Button(color_frame, text="Change", command=self.change_color_action)
        change_color_btn.pack(side=tk.LEFT)

        # --- Class Teacher Section ---
        teacher_frame = ttk.LabelFrame(main_frame, text="Class teacher", padding="10")
        teacher_frame.pack(fill=tk.X, pady=10)
        
        self.class_teacher_var = tk.StringVar(value="Not selected") # Placeholder
        self.teacher_display_label = ttk.Label(teacher_frame, textvariable=self.class_teacher_var, width=30, relief=tk.GROOVE, padding=5)
        self.teacher_display_label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,10))

        change_teacher_btn = ttk.Button(teacher_frame, text="Change", command=self.change_teacher_action)
        change_teacher_btn.pack(side=tk.LEFT)
        
        # --- Grade Section ---
        grade_frame = ttk.Frame(main_frame) # No LabelFrame needed here based on image
        grade_frame.pack(fill=tk.X, pady=10)

        ttk.Label(grade_frame, text="Grade").pack(side=tk.LEFT, padx=(5,10))
        self.grade_var = tk.StringVar()
        grade_combo = ttk.Combobox(grade_frame, textvariable=self.grade_var, state="readonly", width=25)
        # TODO: Populate with actual grade data
        grade_combo['values'] = ("Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12")
        grade_combo.pack(side=tk.LEFT, expand=True, fill=tk.X)
        if grade_combo['values']:
             grade_combo.current(0)


        # --- Bottom Buttons ---
        button_frame = ttk.Frame(main_frame, padding="10 0 0 0")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20,0))

        ok_btn = ttk.Button(button_frame, text="OK", command=self.ok_action)
        ok_btn.pack(side=tk.RIGHT, padx=(5,0))
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT)

    def custom_fields_action(self):
        messagebox.showinfo("Custom Fields", "Custom fields button clicked. Implement functionality here.")

    def change_color_action(self):
        color_code = colorchooser.askcolor(title="Choose color", initialcolor=self.selected_color.get())
        if color_code and color_code[1]:
            self.selected_color.set(color_code[1])
            self.color_display.config(bg=self.selected_color.get())

    def _connect_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            # Ensure FACULTY table exists (basic schema for selection)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS FACULTY (
                FID TEXT PRIMARY KEY NOT NULL,
                NAME TEXT NOT NULL
            );
            """)
            # Ensure CLASSES table exists
            conn.execute("""
            CREATE TABLE IF NOT EXISTS CLASSES (
                CLASS_NAME TEXT PRIMARY KEY NOT NULL,
                SHORT_NAME TEXT,
                PRINT_SUBJECT_PICTURES INTEGER, -- 0 for False, 1 for True
                COLOR TEXT,
                CLASS_TEACHER_FID TEXT, -- Foreign key to FACULTY table
                GRADE TEXT,
                FOREIGN KEY (CLASS_TEACHER_FID) REFERENCES FACULTY(FID)
            );
            """)
            conn.commit()
            return conn
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to or create tables: {e}")
            return None

    def change_teacher_action(self):
        if not self.conn:
            messagebox.showerror("Database Error", "Database connection is not available.", parent=self)
            return

        selection_dialog = TeacherSelectionDialog(self, self.conn)
        self.wait_window(selection_dialog) # Wait for the dialog to close

        if selection_dialog.selected_teacher_name:
            self.class_teacher_var.set(selection_dialog.selected_teacher_name)
            # You might want to store selection_dialog.selected_teacher_id as well
            self.selected_teacher_id = selection_dialog.selected_teacher_id
            print(f"Selected Teacher ID: {self.selected_teacher_id}") # For debugging
        else:
            # Keep existing or default if no selection was made or dialog cancelled
            # self.class_teacher_var.set("Not selected") # Or keep current
            pass 

    def ok_action(self):
        class_name = self.class_name_var.get().strip()
        short_name = self.short_name_var.get().strip()
        print_pics = 1 if self.print_subject_pictures_var.get() else 0
        color = self.selected_color.get()
        # class_teacher_id is already stored in self.selected_teacher_id from change_teacher_action
        grade = self.grade_var.get()

        if not class_name:
            messagebox.showwarning("Input Error", "Class name cannot be empty.", parent=self)
            return

        if not self.conn:
            messagebox.showerror("Database Error", "No database connection available.", parent=self)
            return

        try:
            cursor = self.conn.cursor()
            # Using REPLACE to handle both insert and update (if class_name is primary key)
            cursor.execute("""
            REPLACE INTO CLASSES (CLASS_NAME, SHORT_NAME, PRINT_SUBJECT_PICTURES, COLOR, CLASS_TEACHER_FID, GRADE)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (class_name, short_name, print_pics, color, self.selected_teacher_id, grade))
            self.conn.commit()
            messagebox.showinfo("Success", f"Class '{class_name}' saved successfully.", parent=self)
            self.destroy() # Close dialog on successful save

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to save class: {e}", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"An unexpected error occurred: {ex}", parent=self)

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    # This is for testing purposes
    root = tk.Tk()
    root.withdraw() # Hide the main root window

    def open_class_dialog():
        dialog = ClassDialog(root)
        dialog.grab_set() # Makes the dialog modal
        root.wait_window(dialog) # Wait until dialog is closed

    # Example button to open the dialog (optional, if you want to test from a main window)
    # test_button = ttk.Button(root.deiconify(), text="Open Class Dialog", command=open_class_dialog)
    # test_button.pack(pady=20)
    # root.mainloop()

    open_class_dialog() # Open the dialog immediately for testing 