import sqlite3
import os
import tkinter as tk
from tkinter import messagebox

class TimetableConditionChecker:
    """
    Class for checking conditions in timetable assignments
    """
    def __init__(self, db_path=None):
        """Initialize the condition checker with database connection"""
        if db_path is None:
            # Default database path
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(project_root, 'files', 'timetable.db')
        else:
            self.db_path = db_path
        
        self.conn = self.connect_to_db()
    
    def connect_to_db(self):
        """Connect to the SQLite database"""
        try:
            if not os.path.exists(self.db_path):
                print(f"Database not found at: {self.db_path}")
                return None
            
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            print(f"Failed to connect to database: {e}")
            return None
    
    def check_lessons_per_week_limit(self, section, subject_code):
        """
        Check if the number of times a subject is assigned in a timetable section
        exceeds the lessons_per_week value defined in the LESSONS table.
        
        Args:
            section (str): The class/section to check
            subject_code (str): The subject code to check
            
        Returns:
            tuple: (exceeded, current_count, limit, warning_message)
        """
        if not self.conn:
            return False, 0, 0, "Database connection failed"
        
        try:
            # 1. Get the lessons_per_week limit for this subject and section from LESSONS table
            cursor = self.conn.execute("""
                SELECT LESSONS_PER_WEEK FROM LESSONS 
                WHERE SUBJECT_CODE=? AND CLASS_NAME=?
            """, (subject_code, section))
            result = cursor.fetchone()
            
            if not result:
                # No lessons_per_week defined for this subject in this section
                return False, 0, 0, f"No lessons_per_week defined for {subject_code} in {section}"
            
            lessons_per_week_limit = result[0]
            
            # 2. Count how many times this subject is already assigned in the timetable
            cursor = self.conn.execute("""
                SELECT COUNT(*) FROM SCHEDULE 
                WHERE SUBCODE=? AND SECTION=?
            """, (subject_code, section))
            result = cursor.fetchone()
            current_assignments = result[0] if result else 0
            
            # 3. Check if the limit is exceeded
            if current_assignments >= lessons_per_week_limit:
                warning_message = (f"Warning: {subject_code} already has {current_assignments} assignments "
                                 f"in {section}, but lessons_per_week is set to {lessons_per_week_limit}!")
                return True, current_assignments, lessons_per_week_limit, warning_message
            
            return False, current_assignments, lessons_per_week_limit, ""
            
        except sqlite3.Error as e:
            error_message = f"Database error in check_lessons_per_week_limit: {e}"
            print(error_message)
            return False, 0, 0, error_message
    
    def check_lesson_type_for_merging(self, section, subject_code):
        """
        Check the lesson type (Single, Double, Triple, etc.) for a subject in a section
        to determine if periods need to be merged when assigning this subject.
        
        Args:
            section (str): The class/section to check
            subject_code (str): The subject code to check
            
        Returns:
            tuple: (periods_to_merge, lesson_type, message)
                periods_to_merge: int - Number of periods that should be merged (1 for Single, 2 for Double, etc.)
                lesson_type: str - The lesson type from the database 
                message: str - Informational message
        """
        if not self.conn:
            return 1, "Unknown", "Database connection failed"
        
        try:
            # Query the LESSONS table to get the lesson type for this subject in this section
            cursor = self.conn.execute("""
                SELECT LESSON_TYPE FROM LESSONS 
                WHERE SUBJECT_CODE=? AND CLASS_NAME=?
            """, (subject_code, section))
            result = cursor.fetchone()
            
            if not result:
                # No lesson type defined, default to Single
                return 1, "Single", f"No lesson type defined for {subject_code} in {section}, assuming Single"
            
            lesson_type = result[0]
            
            # Determine number of periods to merge based on lesson type
            lesson_periods = {
                "Single": 1,
                "Double": 2,
                "Triple": 3,
                "Quad": 4,
                "Quint": 5,
                "Hex": 6
            }
            
            periods_to_merge = lesson_periods.get(lesson_type, 1)
            
            if periods_to_merge == 1:
                message = f"Subject {subject_code} is configured as Single period"
            else:
                message = f"Subject {subject_code} is configured as {lesson_type} lesson - should span {periods_to_merge} consecutive periods"
            
            return periods_to_merge, lesson_type, message
            
        except sqlite3.Error as e:
            error_message = f"Database error in check_lesson_type_for_merging: {e}"
            print(error_message)
            return 1, "Error", error_message
    
    def validate_merged_periods(self, section, subject_code, day_idx, period_idx):
        """
        Validate if a subject can be assigned to a period, considering its lesson type 
        and the required period merging.
        
        For Double/Triple lessons, checks if consecutive periods are available.
        
        Args:
            section (str): The class/section
            subject_code (str): The subject code
            day_idx (int): Day index in the timetable
            period_idx (int): Period index in the timetable
            
        Returns:
            tuple: (is_valid, periods_needed, error_message)
                is_valid: bool - Whether the assignment is valid
                periods_needed: list - Indices of periods needed for this assignment
                error_message: str - Description of the issue, if any
        """
        if not self.conn:
            return False, [], "Database connection failed"
        
        try:
            # Get lesson type and periods to merge
            periods_to_merge, lesson_type, _ = self.check_lesson_type_for_merging(section, subject_code)
            
            # If it's a Single period, no need for additional validation
            if periods_to_merge == 1:
                return True, [period_idx], ""
            
            # For Double/Triple, we need to check consecutive periods
            periods_needed = list(range(period_idx, period_idx + periods_to_merge))
            
            # Check if we have enough periods in the day
            # Get the total number of periods in the day
            cursor = self.conn.execute("SELECT COUNT(DISTINCT PERIODID) FROM SCHEDULE")
            total_periods = cursor.fetchone()[0] or 8  # Default to 8 if not found
            
            if period_idx + periods_to_merge > total_periods:
                return False, periods_needed, f"Not enough periods in the day for {lesson_type} lesson"
            
            # Check if consecutive periods are already assigned
            for check_period_idx in periods_needed[1:]:  # Skip the first one (current period)
                cursor = self.conn.execute("""
                    SELECT SUBCODE FROM SCHEDULE 
                    WHERE SECTION=? AND DAYID=? AND PERIODID=?
                """, (section, day_idx, check_period_idx))
                result = cursor.fetchone()
                
                if result:
                    return False, periods_needed, f"Period {check_period_idx+1} is already assigned to {result[0]}"
            
            return True, periods_needed, ""
            
        except sqlite3.Error as e:
            error_message = f"Database error in validate_merged_periods: {e}"
            print(error_message)
            return False, [], error_message
    
    def merge_periods(self, section, subject_code, day_idx, period_idx, faculty_ini=None):
        """
        Merge periods for a subject according to its lesson type.
        
        Args:
            section (str): The class/section
            subject_code (str): The subject code
            day_idx (int): Day index in the timetable
            period_idx (int): Period index in the timetable
            faculty_ini (str, optional): Faculty initial to assign
            
        Returns:
            tuple: (success, message, affected_periods)
        """
        if not self.conn:
            return False, "Database connection failed", []
        
        try:
            # Validate if periods can be merged
            is_valid, periods_needed, error_message = self.validate_merged_periods(
                section, subject_code, day_idx, period_idx)
            
            if not is_valid:
                return False, error_message, []
            
            # If only one period is needed, no merging required
            if len(periods_needed) == 1:
                return True, "Single period, no merging needed", periods_needed
            
            # Get faculty if not provided
            if faculty_ini is None:
                # Try to get the faculty from the LESSONS table
                cursor = self.conn.execute("""
                    SELECT TEACHER_ID FROM LESSONS 
                    WHERE SUBJECT_CODE=? AND CLASS_NAME=?
                """, (subject_code, section))
                result = cursor.fetchone()
                if result:
                    faculty_ini = result[0]
                else:
                    return False, "Faculty information not found", []
            
            # Perform the merge by inserting entries for all required periods
            for merge_period_idx in periods_needed:
                # Generate a unique ID for each schedule entry
                entry_id = f"{section}{day_idx * 10 + merge_period_idx}"
                
                # Update or insert new schedule entry
                self.conn.execute("""
                    REPLACE INTO SCHEDULE (ID, DAYID, PERIODID, SUBCODE, SECTION, FINI)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (entry_id, day_idx, merge_period_idx, subject_code, section, faculty_ini))
            
            # Commit changes
            self.conn.commit()
            
            return True, f"Successfully merged {len(periods_needed)} periods for {subject_code}", periods_needed
            
        except sqlite3.Error as e:
            error_message = f"Database error in merge_periods: {e}"
            print(error_message)
            return False, error_message, []
    
    def check_all_sections_limits(self):
        """
        Check all sections in the timetable for subjects exceeding their lessons_per_week limits
        
        Returns:
            list: List of tuples (section, subject_code, current_count, limit) for exceeded limits
        """
        if not self.conn:
            return []
        
        exceeded_limits = []
        
        try:
            # Get all sections from the SCHEDULE table
            cursor = self.conn.execute("SELECT DISTINCT SECTION FROM SCHEDULE")
            sections = [row[0] for row in cursor.fetchall()]
            
            for section in sections:
                # Get all subjects in this section from SCHEDULE
                cursor = self.conn.execute("SELECT DISTINCT SUBCODE FROM SCHEDULE WHERE SECTION=?", (section,))
                subject_codes = [row[0] for row in cursor.fetchall()]
                
                for subject_code in subject_codes:
                    exceeded, current_count, limit, _ = self.check_lessons_per_week_limit(section, subject_code)
                    if exceeded:
                        exceeded_limits.append((section, subject_code, current_count, limit))
        
        except sqlite3.Error as e:
            print(f"Database error in check_all_sections_limits: {e}")
        
        return exceeded_limits
    
    def show_subject_limit_warning(self, section, subject_code, current_window=None):
        """
        Show a warning dialog if a subject exceeds its lessons_per_week limit
        
        Args:
            section (str): The class/section to check
            subject_code (str): The subject code to check
            current_window (tk.Toplevel, optional): Parent window for the messagebox
            
        Returns:
            bool: True if limit is exceeded, False otherwise
        """
        exceeded, current_count, limit, warning_message = self.check_lessons_per_week_limit(section, subject_code)
        
        if exceeded:
            if current_window:
                messagebox.showwarning("Subject Limit Exceeded", warning_message, parent=current_window)
            else:
                messagebox.showwarning("Subject Limit Exceeded", warning_message)
            return True
        
        return False
    
    def __del__(self):
        """Close database connection when object is destroyed"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()


# Standalone testing function
def test_checker():
    checker = TimetableConditionChecker()
    
    # Test 1: Check for subjects exceeding their lessons_per_week limits
    print("\n=== Testing lessons_per_week limits ===")
    exceeded_limits = checker.check_all_sections_limits()
    
    if exceeded_limits:
        print("Found subjects exceeding their lessons_per_week limits:")
        for section, subject_code, current_count, limit in exceeded_limits:
            print(f"Section {section}, Subject {subject_code}: {current_count}/{limit} assignments")
    else:
        print("No subjects exceed their lessons_per_week limits.")
    
    # Test 2: Test lesson type merging functionality
    print("\n=== Testing lesson type merging ===")
    
    # Get all sections and subjects from the database
    try:
        sections = []
        if checker.conn:
            cursor = checker.conn.execute("SELECT DISTINCT SECTION FROM SCHEDULE")
            sections = [row[0] for row in cursor.fetchall()]
            
            if not sections:
                cursor = checker.conn.execute("SELECT DISTINCT CLASS_NAME FROM LESSONS")
                sections = [row[0] for row in cursor.fetchall()]
        
        if sections:
            test_section = sections[0]
            print(f"Using section {test_section} for testing")
            
            # Get subjects for this section
            subjects = []
            if checker.conn:
                cursor = checker.conn.execute("""
                    SELECT DISTINCT SUBJECT_CODE FROM LESSONS 
                    WHERE CLASS_NAME=? AND LESSON_TYPE IN ('Double', 'Triple')
                """, (test_section,))
                subjects = [row[0] for row in cursor.fetchall()]
            
            if subjects:
                # Test with the first subject that has a Double or Triple lesson type
                test_subject = subjects[0]
                print(f"Found subject {test_subject} with Double/Triple lesson type")
                
                # Check lesson type
                periods_to_merge, lesson_type, message = checker.check_lesson_type_for_merging(test_section, test_subject)
                print(f"Lesson type check: {periods_to_merge} periods to merge, type: {lesson_type}")
                print(f"Message: {message}")
                
                # Try to validate merging at period 0 of day 0
                is_valid, periods_needed, error_message = checker.validate_merged_periods(test_section, test_subject, 0, 0)
                print(f"Validation result: {'Valid' if is_valid else 'Invalid'}")
                print(f"Periods needed: {periods_needed}")
                if not is_valid:
                    print(f"Error: {error_message}")
                
                # Note: We don't actually perform the merge in this test to avoid modifying the database
                print("Note: Actual period merging not tested to avoid modifying database")
            else:
                print("No subjects with Double/Triple lesson type found")
                
                # Try with any subject
                cursor = checker.conn.execute("SELECT DISTINCT SUBJECT_CODE FROM LESSONS WHERE CLASS_NAME=?", (test_section,))
                all_subjects = [row[0] for row in cursor.fetchall()]
                
                if all_subjects:
                    test_subject = all_subjects[0]
                    print(f"Testing with subject {test_subject} (likely Single period)")
                    
                    # Check lesson type
                    periods_to_merge, lesson_type, message = checker.check_lesson_type_for_merging(test_section, test_subject)
                    print(f"Lesson type check: {periods_to_merge} periods to merge, type: {lesson_type}")
                    print(f"Message: {message}")
                else:
                    print("No subjects found for testing")
        else:
            print("No sections found for testing")
            
    except Exception as e:
        print(f"Error during testing: {e}")


if __name__ == "__main__":
    test_checker() 