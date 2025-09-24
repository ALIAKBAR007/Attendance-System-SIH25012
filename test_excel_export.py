#!/usr/bin/env python3
"""
Test script for Excel export functionality
"""

import os
import sys
import tempfile
from datetime import datetime, date

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import AttendanceDatabase

def test_excel_export():
    """Test the Excel export functionality"""
    print("Testing Excel export functionality...")
    
    # Create a temporary database for testing
    temp_db = tempfile.mktemp(suffix='.db')
    
    try:
        # Initialize database
        db = AttendanceDatabase(temp_db)
        
        # Add some test data
        print("Adding test data...")
        
        # Add test teacher
        db.add_teacher("Test Teacher")
        db.teacher_login("Test Teacher")
        
        # Add test students
        db.add_student("Test Student 1", "Test Teacher")
        db.add_student("Test Student 2", "Test Teacher")
        
        # Add some attendance records
        today = date.today().isoformat()
        db.mark_student_present("Test Student 1", "Test Teacher", today)
        db.mark_student_meal_present("Test Student 1", "Test Teacher", today)
        db.mark_student_present("Test Student 2", "Test Teacher", today)
        db.mark_student_meal_present("Test Student 2", "Test Teacher", today)
        
        print("Test data added successfully!")
        
        # Test if pandas is available
        try:
            import pandas as pd
            import openpyxl
            print("✅ pandas and openpyxl are available!")
            
            # Test creating a simple DataFrame and Excel file
            test_data = [
                {'Name': 'Test Student 1', 'Status': 'Present', 'Date': today},
                {'Name': 'Test Student 2', 'Status': 'Present', 'Date': today}
            ]
            
            df = pd.DataFrame(test_data)
            test_file = os.path.join(tempfile.gettempdir(), "test_export.xlsx")
            df.to_excel(test_file, index=False)
            
            if os.path.exists(test_file):
                print(f"✅ Excel export test successful! File created: {test_file}")
                os.remove(test_file)  # Clean up
            else:
                print("❌ Excel file was not created")
                
        except ImportError as e:
            print(f"❌ Missing dependencies: {e}")
            print("Please install: pip install pandas openpyxl")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up temporary database
        if os.path.exists(temp_db):
            os.remove(temp_db)
        print("Test completed!")

if __name__ == "__main__":
    test_excel_export()