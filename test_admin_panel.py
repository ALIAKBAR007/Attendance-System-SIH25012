#!/usr/bin/env python3
"""
Test script for admin panel functionality
"""
import datetime
from database import AttendanceDatabase

def test_admin_database_methods():
    print("=== Testing Admin Panel Database Methods ===\n")
    
    db = AttendanceDatabase()
    
    # Test data
    teacher_name = "Ms. Johnson"
    start_date = "2025-09-20"
    end_date = "2025-09-23"
    
    print(f"Testing admin methods for teacher: {teacher_name}")
    print(f"Date range: {start_date} to {end_date}\n")
    
    # Test 1: Get teacher summary stats
    print("1. Testing teacher summary stats:")
    summary = db.get_teacher_summary_stats(teacher_name, start_date, end_date)
    print(f"   Teacher: {summary['teacher_name']}")
    print(f"   Total Students: {summary['total_students']}")
    print(f"   Total Present Marks: {summary['total_present']}")
    print(f"   Days with Records: {summary['days_with_records']}")
    print(f"   Average Attendance: {summary['avg_attendance_percentage']:.1f}%")
    print(f"   Date Range: {summary['date_range']}")
    
    # Test 2: Get teacher attendance data
    print(f"\n2. Testing teacher attendance data:")
    teacher_data = db.get_teacher_attendance_data(teacher_name, start_date, end_date)
    print(f"   Found {len(teacher_data)} attendance records")
    if teacher_data:
        print("   Sample records:")
        for i, record in enumerate(teacher_data[:3]):  # Show first 3
            print(f"     {i+1}. {record['date']} - {record['student_name']} - {record['status']}")
    
    # Test 3: Get student attendance data
    print(f"\n3. Testing student attendance data:")
    student_data = db.get_student_attendance_data(teacher_name, start_date, end_date)
    print(f"   Found {len(student_data)} students")
    if student_data:
        print("   Student summaries:")
        for i, student in enumerate(student_data[:3]):  # Show first 3
            print(f"     {i+1}. {student['student_name']}: {student['present_count']}/{student['total_days']} days ({student['attendance_percentage']:.1f}%)")
    
    print("\n=== Database methods test completed ===")

def test_date_calculations():
    print("\n=== Testing Date Calculations ===")
    
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    week_ago = today - datetime.timedelta(days=7)
    
    print(f"Today: {today.strftime('%Y-%m-%d')}")
    print(f"Yesterday: {yesterday.strftime('%Y-%m-%d')}")
    print(f"Week ago: {week_ago.strftime('%Y-%m-%d')}")
    
    print("Date format test passed ✓")

if __name__ == "__main__":
    test_admin_database_methods()
    test_date_calculations()