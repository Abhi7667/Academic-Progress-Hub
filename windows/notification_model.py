import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import threading
import time

class NotificationModel:
    def __init__(self, db_path='files/timetable.db'):
        self.db_path = db_path
        self._stop_flag = False
        self._notification_thread = None
        self._last_notification_time = {}  # Track last notification time for each class

    def connect_db(self):
        """Connect to the database"""
        return sqlite3.connect(self.db_path)

    def show_notification(self, title, message):
        """Show a notification using Tkinter messagebox"""
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            messagebox.showinfo(title, message)
            root.destroy()
        except Exception as e:
            print(f"Notification error: {e}")

    def notify_upcoming_class(self, user_id, user_type='student'):
        """Notify about upcoming classes"""
        try:
            conn = self.connect_db()
            current_time = datetime.now()
            day_of_week = current_time.weekday()  # Monday is 0
            
            if day_of_week >= 5:  # Weekend
                return
            
            current_hour = current_time.hour
            current_minute = current_time.minute
            
            # Map periods to time slots
            period_times = {
                0: (9, 0),   # 9:00 AM
                1: (10, 0),  # 10:00 AM
                2: (11, 10),  # 11:00 AM
                3: (12, 0),  # 12:00 PM
                4: (14, 0),  # 2:00 PM
                5: (15, 0),  # 3:00 PM
            }
            
            try:
                if user_type.lower() == 'student':
                    cursor = conn.execute(f"SELECT SECTION FROM STUDENT WHERE SID='{user_id}'")
                    student_data = cursor.fetchone()
                    if not student_data:
                        return
                    
                    section = student_data[0]
                    
                    # Check each period
                    for period, (hour, minute) in period_times.items():
                        class_time = datetime.now().replace(hour=hour, minute=minute, second=0)
                        time_diff = (class_time - current_time).total_seconds() / 60
                        
                        # Notify 15 minutes before class
                        if 0 <= time_diff <= 15:
                            # Check if we already notified for this class
                            notification_key = f"{day_of_week}_{period}"
                            if notification_key not in self._last_notification_time or \
                               (current_time - self._last_notification_time[notification_key]).seconds > 900:  # 15 minutes
                                
                                cursor = conn.execute(f"""
                                    SELECT SCHEDULE.SUBCODE, SUBJECTS.SUBNAME, FACULTY.NAME 
                                    FROM SCHEDULE 
                                    JOIN SUBJECTS ON SCHEDULE.SUBCODE = SUBJECTS.SUBCODE 
                                    JOIN FACULTY ON SCHEDULE.FINI = FACULTY.INI 
                                    WHERE SECTION='{section}' AND DAYID={day_of_week} AND PERIODID={period}
                                """)
                                class_data = cursor.fetchone()
                                
                                if class_data:
                                    title = "Upcoming Class"
                                    message = f"You have {class_data[1]} ({class_data[0]}) in {int(time_diff)} minutes!\nFaculty: {class_data[2]}\nPeriod: {period + 1}"
                                    self.show_notification(title, message)
                                    self._last_notification_time[notification_key] = current_time
                
                elif user_type.lower() == 'faculty':
                    for period, (hour, minute) in period_times.items():
                        class_time = datetime.now().replace(hour=hour, minute=minute, second=0)
                        time_diff = (class_time - current_time).total_seconds() / 60
                        
                        if 0 <= time_diff <= 15:
                            notification_key = f"{day_of_week}_{period}"
                            if notification_key not in self._last_notification_time or \
                               (current_time - self._last_notification_time[notification_key]).seconds > 900:
                                
                                cursor = conn.execute(f"""
                                    SELECT SCHEDULE.SUBCODE, SUBJECTS.SUBNAME, SCHEDULE.SECTION 
                                    FROM SCHEDULE 
                                    JOIN SUBJECTS ON SCHEDULE.SUBCODE = SUBJECTS.SUBCODE 
                                    WHERE FINI=(SELECT INI FROM FACULTY WHERE FID='{user_id}')
                                    AND DAYID={day_of_week} AND PERIODID={period}
                                """)
                                class_data = cursor.fetchone()
                                
                                if class_data:
                                    title = "Upcoming Class"
                                    message = f"You have {class_data[1]} ({class_data[0]}) in {int(time_diff)} minutes!\nSection: {class_data[2]}\nPeriod: {period + 1}"
                                    self.show_notification(title, message)
                                    self._last_notification_time[notification_key] = current_time
                                    
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in notify_upcoming_class: {e}")

    def start_notification_service(self, user_id, user_type='student'):
        """Start the notification service in a background thread"""
        def notification_loop():
            while not self._stop_flag:
                try:
                    self.notify_upcoming_class(user_id, user_type)
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    print(f"Error in notification loop: {e}")
                    time.sleep(60)  # Wait before retrying

        # Stop existing thread if running
        self.stop_notification_service()
        
        # Start new thread
        self._stop_flag = False
        self._notification_thread = threading.Thread(target=notification_loop)
        self._notification_thread.daemon = True
        self._notification_thread.start()

    def stop_notification_service(self):
        """Stop the notification service"""
        self._stop_flag = True
        if self._notification_thread and self._notification_thread.is_alive():
            self._notification_thread.join(timeout=1)
            self._notification_thread = None

# Example usage:
if __name__ == "__main__":
    notifier = NotificationModel()
    notifier.show_notification("Test", "Test notification!") 