import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3

days = 5
periods = 6
recess_break_aft = 3 # recess after 3rd Period
section = None
butt_grid = []


period_names = list(map(lambda x: 'Period ' + str(x), range(1, 6+1)))
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thrusday', 'Friday']


def check_conflicts(faculty_ini, day_id, period_id, current_section):
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
            cursor = conn.execute(
                "SELECT SECTION FROM SCHEDULE WHERE DAYID=? AND PERIODID=? AND FINI=?",
                (day_id, period_id, faculty_ini)
            )
            
            faculty_conflicts = list(cursor)
            for row in faculty_conflicts:
                if row[0] != current_section:
                    conflicts.append(f"Faculty '{faculty_ini}' is already assigned to section '{row[0]}' during {day_names[day_id]} Period {period_id+1}")
                    
            # Check if faculty has too many periods in a day (optional)
            cursor = conn.execute(
                "SELECT COUNT(*) FROM SCHEDULE WHERE DAYID=? AND FINI=?",
                (day_id, faculty_ini)
            )
            period_count = cursor.fetchone()[0]
            if period_count >= 5:  # If faculty already has 5 or more periods in a day
                conflicts.append(f"Faculty '{faculty_ini}' already has {period_count} periods on {day_names[day_id]}")
            
            # Check for back-to-back recess conflict
            if period_id == recess_break_aft or period_id == recess_break_aft - 1:
                adjacent_period = recess_break_aft - 1 if period_id == recess_break_aft else recess_break_aft
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM SCHEDULE WHERE DAYID=? AND PERIODID=? AND FINI=?",
                    (day_id, adjacent_period, faculty_ini)
                )
                has_adjacent = cursor.fetchone()[0] > 0
                if has_adjacent:
                    conflicts.append(f"Faculty '{faculty_ini}' is assigned to adjacent periods across recess on {day_names[day_id]}")
            
        except sqlite3.Error as e:
            print(f"Database error while checking conflicts: {e}")
            return True, f"Database error: {e}"
            
    if conflicts:
        return True, "\n".join(conflicts)
    else:
        return False, ""


def update_p(d, p, tree, parent):
    # print(section, d, p, str(sub.get()))

    try:
        if len(tree.selection()) > 1:
            messagebox.showerror("Bad Select", "Select one subject at a time!")
            parent.destroy()
            return
        
        row = tree.item(tree.selection()[0])['values']
        
        # Handle the NULL case (removing assignment)
        if row[0] == 'NULL' and row[1] == 'NULL':
            conn.execute(f"DELETE FROM SCHEDULE WHERE ID='{section+str((d*periods)+p)}'")
            conn.commit()
            update_table()
            parent.destroy()
            return

        # Check for conflicts before updating
        faculty_ini = row[0]
        has_conflict, conflict_message = check_conflicts(faculty_ini, d, p, section)
        
        if has_conflict:
            # Ask user if they want to proceed despite conflicts
            proceed = messagebox.askyesno(
                "Scheduling Conflict", 
                f"The following conflicts were detected:\n\n{conflict_message}\n\nDo you want to proceed anyway?"
            )
            if not proceed:
                return  # User chose not to proceed
        
        # Continue with the update
        conn.commit()
        print(row)
        conn.execute(f"REPLACE INTO SCHEDULE (ID, DAYID, PERIODID, SUBCODE, SECTION, FINI)\
            VALUES ('{section+str((d*periods)+p)}', {d}, {p}, '{row[1]}', '{section}', '{row[0]}')")
        conn.commit()
        update_table()

    except IndexError:
        messagebox.showerror("Bad Select", "Please select a subject from the list!")
        parent.destroy()
        return

    parent.destroy()


def process_button(d, p):
    print(d, p)
    add_p = tk.Tk()
    # add_p.geometry('200x500')

    # get subject code list from the database
    cursor = conn.execute("SELECT SUBCODE FROM SUBJECTS")
    subcode_li = [row[0] for row in cursor]
    subcode_li.insert(0, 'NULL')

    # Label10
    tk.Label(
        add_p,
        text='Select Subject',
        font=('Consolas', 12, 'bold')
    ).pack()

    tk.Label(
        add_p,
        text=f'Day: {day_names[d]}',
        font=('Consolas', 12)
    ).pack()

    tk.Label(
        add_p,
        text=f'Period: {p+1}',
        font=('Consolas', 12)
    ).pack()

    tree = ttk.Treeview(add_p)
    tree['columns'] = ('one', 'two')
    tree.column("#0", width=0, stretch=tk.NO)
    tree.column("one", width=70, stretch=tk.NO)
    tree.column("two", width=80, stretch=tk.NO)
    tree.heading('#0', text="")
    tree.heading('one', text="Faculty")
    tree.heading('two', text="Subject Code")
    
    cursor = conn.execute("SELECT FACULTY.INI, FACULTY.SUBCODE1, FACULTY.SUBCODE2, SUBJECTS.SUBCODE\
    FROM FACULTY, SUBJECTS\
    WHERE FACULTY.SUBCODE1=SUBJECTS.SUBCODE OR FACULTY.SUBCODE2=SUBJECTS.SUBCODE")
    for row in cursor:
        print(row)
        tree.insert(
            "",
            0,
            values=(row[0],row[-1])
        )
    tree.insert("", 0, value=('NULL', 'NULL'))
    tree.pack(pady=10, padx=30)

    tk.Button(
        add_p,
        text="OK",
        padx=15,
        command=lambda x=d, y=p, z=tree, d=add_p: update_p(x, y, z, d)
    ).pack(pady=20)

    add_p.mainloop()


def select_sec():
    global section
    section = str(combo1.get())
    print(section)
    update_table()


def update_table():
    for i in range(days):
        for j in range(periods):
            cursor = conn.execute(f"SELECT SUBCODE, FINI FROM SCHEDULE\
                WHERE DAYID={i} AND PERIODID={j} AND SECTION='{section}'")
            cursor = list(cursor)
            print(cursor)
            if len(cursor) != 0:
                butt_grid[i][j]['text'] = str(cursor[0][0]) + '\n' + str(cursor[0][1])
                butt_grid[i][j].update()
                print(i, j, cursor[0][0])
            else:
                butt_grid[i][j]['text'] = "No Class"
                butt_grid[i][j].update()
            

def check_all_conflicts():
    """Check and display all conflicts in the current schedule"""
    conflict_report = []
    
    # Query all schedule entries
    cursor = conn.execute("SELECT DISTINCT DAYID, PERIODID, FINI FROM SCHEDULE WHERE FINI != 'NULL'")
    schedule_items = list(cursor)
    
    # Check for faculty conflicts (same faculty assigned to multiple sections in same period)
    for day_id, period_id, faculty_ini in schedule_items:
        cursor = conn.execute(
            "SELECT SECTION FROM SCHEDULE WHERE DAYID=? AND PERIODID=? AND FINI=?", 
            (day_id, period_id, faculty_ini)
        )
        sections = [row[0] for row in cursor]
        
        if len(sections) > 1:
            conflict_report.append(
                f"CONFLICT: Faculty '{faculty_ini}' is assigned to multiple sections ({', '.join(sections)}) "
                f"during {day_names[day_id]} Period {period_id+1}"
            )
    
    # Check for faculty workload (too many periods in a day)
    cursor = conn.execute("SELECT DISTINCT FINI FROM SCHEDULE WHERE FINI != 'NULL'")
    faculty_list = [row[0] for row in cursor]
    
    for faculty in faculty_list:
        for day in range(days):
            cursor = conn.execute(
                "SELECT COUNT(*) FROM SCHEDULE WHERE DAYID=? AND FINI=?",
                (day, faculty)
            )
            period_count = cursor.fetchone()[0]
            if period_count > 5:  # If faculty has more than 5 periods in a day
                conflict_report.append(
                    f"WORKLOAD: Faculty '{faculty}' has {period_count} periods on {day_names[day]} (recommended max: 5)"
                )
    
    # Display conflicts or success message
    if conflict_report:
        result = messagebox.askokcancel(
            "Timetable Conflicts", 
            "The following conflicts were found in the timetable:\n\n" + "\n".join(conflict_report)
        )
    else:
        messagebox.showinfo("No Conflicts", "No conflicts found in the current timetable.")
            

# connecting database
conn = sqlite3.connect(r'files/timetable.db')

# creating Tabe in the database
conn.execute('CREATE TABLE IF NOT EXISTS SCHEDULE\
(ID CHAR(10) NOT NULL PRIMARY KEY,\
DAYID INT NOT NULL,\
PERIODID INT NOT NULL,\
SUBCODE CHAR(10) NOT NULL,\
SECTION CHAR(5) NOT NULL,\
FINI CHAR(10) NOT NULL)')
# DAYID AND PERIODID ARE ZERO INDEXED


tt = tk.Tk()

tt.title('Scheduler')

title_lab = tk.Label(
    tt,
    text='T  I  M  E  T  A  B  L  E',
    font=('Consolas', 20, 'bold'),
    pady=5
)
title_lab.pack()


table = tk.Frame(tt)
table.pack()

first_half = tk.Frame(table)
first_half.pack(side='left')

recess_frame = tk.Frame(table)
recess_frame.pack(side='left')

second_half = tk.Frame(table)
second_half.pack(side='left')

recess = tk.Label(
    recess_frame,
    text='R\n\nE\n\nC\n\nE\n\nS\n\nS',
    font=('Consolas', 18, 'italic'),
    width=3,
    relief='sunken'
)
recess.pack()

for i in range(days):
    b = tk.Label(
        first_half,
        text=day_names[i],
        font=('Consolas', 12, 'bold'),
        width=9,
        height=2,
        bd=5,
        relief='raised'
    )
    b.grid(row=i+1, column=0)

for i in range(periods):
    if i < recess_break_aft:
        b = tk.Label(first_half)
        b.grid(row=0, column=i+1)
    else:
        b = tk.Label(second_half)
        b.grid(row=0, column=i)

    b.config(
        text=period_names[i],
        font=('Consolas', 12, 'bold'),
        width=9,
        height=1,
        bd=5,
        relief='raised'
    )

for i in range(days):
    b = []
    for j in range(periods):
        if j < recess_break_aft:
            bb = tk.Button(first_half)
            bb.grid(row=i+1, column=j+1)
        else:
            bb = tk.Button(second_half)
            bb.grid(row=i+1, column=j)

        bb.config(
            text='Hello World!',
            font=('Consolas', 10),
            width=13,
            height=3,
            bd=5,
            relief='raised',
            wraplength=80,
            justify='center',
            command=lambda x=i, y=j: process_button(x, y)
        )
        b.append(bb)

    butt_grid.append(b)
    # print(b)
    b = []
sec_select_f = tk.Frame(tt, pady=15)
sec_select_f.pack()

tk.Label(
    sec_select_f,
    text='Select section:  ',
    font=('Consolas', 12, 'bold')
).pack(side=tk.LEFT)

cursor = conn.execute("SELECT DISTINCT SECTION FROM STUDENT")
sec_li = [row[0] for row in cursor]
# sec_li.insert(0, 'NULL')
print(sec_li)
combo1 = ttk.Combobox(
    sec_select_f,
    values=sec_li,
)
combo1.pack(side=tk.LEFT)
combo1.current(0)

b = tk.Button(
    sec_select_f,
    text="OK",
    font=('Consolas', 12, 'bold'),
    padx=10,
    command=select_sec
)
b.pack(side=tk.LEFT, padx=10)
b.invoke()

# Add check conflicts button
check_conflicts_button = tk.Button(
    sec_select_f,
    text="Check All Conflicts",
    font=('Consolas', 12, 'bold'),
    padx=10,
    command=check_all_conflicts
)
check_conflicts_button.pack(side=tk.LEFT, padx=10)


print(butt_grid[0][1], butt_grid[1][1])
update_table()


tt.mainloop()