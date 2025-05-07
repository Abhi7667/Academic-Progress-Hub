import tkinter as tk
import sys
import os
import threading
from PIL import Image, ImageTk

def run_sub(): os.system('pythonw windows\\subjects.py')
def run_fac(): os.system('pythonw windows\\faculty.py')
def run_stud(): os.system('pythonw windows\\student.py')
def run_sch(): os.system('pythonw windows\\scheduler.py')
def run_tt_s(): os.system('pythonw windows\\timetable_stud.py')
def run_tt_f(): os.system('pythonw windows\\timetable_fac.py')
def run_step1(): os.system('pythonw windows\\step1.py')

ad = tk.Tk()
ad.state('zoomed')  # This will maximize the window while keeping the title bar
ad.minsize(800, 600)  # Set minimum window size

# Add escape key binding to exit fullscreen
def toggle_fullscreen(event=None):
    if ad.attributes('-fullscreen'):
        ad.attributes('-fullscreen', False)
        ad.state('zoomed')
    else:
        ad.attributes('-fullscreen', True)

def quit_fullscreen(event=None):
    ad.attributes('-fullscreen', False)
    ad.state('zoomed')
    
ad.bind('<Escape>', quit_fullscreen)  # Escape key exits fullscreen
ad.bind('<F11>', toggle_fullscreen)   # F11 toggles fullscreen

ad.title('Administrator')

tk.Label(
    ad,
    text='A D M I N I S T R A T O R',
    font=('Consolas', 20, 'bold'),
    pady=10
).pack()

tk.Label(
    ad,
    text='You are the Administrator',
    font=('Consolas', 12, 'italic'),
).pack(pady=9)

# Quit Button - Pack this BEFORE the expanding content frame
tk.Button(
    ad,
    text='Quit',
    font=('Consolas'),
    command=ad.destroy
).pack(side=tk.BOTTOM, pady=20)

# Create a main frame for the two LabelFrames
content_frame = tk.Frame(ad)
content_frame.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)

modify_frame = tk.LabelFrame(content_frame, text='Modify', font=('Consolas'), padx=20, pady=10)
modify_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=10)

tk.Button(
    modify_frame,
    text='Subjects',
    font=('Consolas'),
    command=run_sub
).pack(pady=10)

tk.Button(
    modify_frame,
    text='Faculties',
    font=('Consolas'),
    command=run_fac
).pack(pady=10)

tk.Button(
    modify_frame,
    text='Students',
    font=('Consolas'),
    command=run_stud
).pack(pady=10)

tt_frame = tk.LabelFrame(content_frame, text='Timetable', font=('Consolas'), padx=20, pady=10)
tt_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=10)

tk.Button(
    tt_frame,
    text='Schedule Periods',
    font=('Consolas'),
    command=run_sch
).pack(pady=10)

tk.Button(
    tt_frame,
    text='View Section-Wise',
    font=('Consolas'),
    command=run_tt_s
).pack(pady=10)

tk.Button(
    tt_frame,
    text='View Faculty-wise',
    font=('Consolas'),
    command=run_tt_f
).pack(pady=10)

# Load the image
try:
    img_path = "Screenshot 2025-05-06 144328.png"
    img = Image.open(img_path)
    img = img.resize((50, 50), Image.Resampling.LANCZOS)
    create_tt_img = ImageTk.PhotoImage(img)

    create_tt_button = tk.Button(
        tt_frame,
        text='Create new timetable',
        image=create_tt_img,
        compound=tk.TOP,
        font=('Consolas', 10),
        command=run_step1,
        borderwidth=0
    )
    create_tt_button.pack(pady=20)

except FileNotFoundError:
    print(f"Error: Image file not found at {img_path}")
    tk.Button(
        tt_frame,
        text='Create New Timetable',
        font=('Consolas'),
        command=run_step1
    ).pack(pady=20)
except Exception as e:
    print(f"Error loading image: {e}")
    tk.Button(
        tt_frame,
        text='Create New Timetable',
        font=('Consolas'),
        command=run_step1
    ).pack(pady=20)

ad.mainloop()