#!/usr/bin/env python3
"""
Test the updated filtering functionality
"""
import datetime
from database import AttendanceDatabase

def test_attendance_filtering():
    print("=== Testing Updated Attendance Filtering ===\n")
    
    db = AttendanceDatabase()
    
    # Test dates
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    
    print(f"Today: {today}")
    print(f"Yesterday: {yesterday}")
    
    # Test with a sample teacher
    teacher_name = "Ms. Johnson"
    
    print(f"\nTesting attendance data structure for {teacher_name}:")
    
    # Get today's attendance
    today_data = db.get_attendance_for_teacher(teacher_name, today)
    print(f"\nToday's Data:")
    if today_data:
        for record in today_data:
            print(f"  Student: {record['student_name']}")
            print(f"  Status: {record['status']}")
            print(f"  Marked Time: {record.get('marked_time', 'N/A')}")
            print(f"  Date: {record['date']}")
            print("  ---")
    else:
        print("  No data found for today")
    
    # Get yesterday's attendance
    yesterday_data = db.get_attendance_for_teacher(teacher_name, yesterday)
    print(f"\nYesterday's Data:")
    if yesterday_data:
        for record in yesterday_data:
            print(f"  Student: {record['student_name']}")
            print(f"  Status: {record['status']}")
            print(f"  Marked Time: {record.get('marked_time', 'N/A')}")
            print(f"  Date: {record['date']}")
            print("  ---")
    else:
        print("  No data found for yesterday")
    
    # Test data structure
    print(f"\nData Structure Test:")
    if today_data:
        sample = today_data[0]
        print(f"Available fields: {list(sample.keys())}")
    else:
        print("No data to test structure")

if __name__ == "__main__":
    test_attendance_filtering()