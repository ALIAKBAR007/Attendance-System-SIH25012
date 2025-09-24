#!/usr/bin/env python3
"""
Test script to verify the Excel export functionality with pandas and openpyxl
"""

import os
import sys
import tempfile
from datetime import datetime, date
import pandas as pd

def test_excel_export_with_pandas():
    """Test actual Excel export with pandas"""
    print("🧪 Testing Excel export with pandas and openpyxl...")
    
    # Test data similar to what the application would generate
    test_data = [
        {'Teacher Name': 'John Smith', 'Activity Type': 'login', 'Date': '2025-09-24', 'Time': '08:30:00', 'Timestamp': '2025-09-24 08:30:00'},
        {'Teacher Name': 'Jane Doe', 'Activity Type': 'logout', 'Date': '2025-09-24', 'Time': '17:00:00', 'Timestamp': '2025-09-24 17:00:00'},
        {'Teacher Name': 'Bob Johnson', 'Activity Type': 'login', 'Date': '2025-09-24', 'Time': '09:15:00', 'Timestamp': '2025-09-24 09:15:00'}
    ]
    
    # Create DataFrame
    df = pd.DataFrame(test_data)
    
    # Create downloads folder simulation
    downloads_path = os.path.join(tempfile.gettempdir(), "Attendance_Export_Test")
    os.makedirs(downloads_path, exist_ok=True)
    
    # Create Excel file
    filename = os.path.join(downloads_path, "Test_Teacher_Activity_2025-09-20_to_2025-09-24.xlsx")
    
    try:
        # Save to Excel with proper formatting
        df.to_excel(filename, index=False, sheet_name='Teacher Activity')
        
        print(f"✅ Successfully created Excel file: {filename}")
        print(f"📁 Export location: {downloads_path}")
        
        # Verify file exists and can be read back
        if os.path.exists(filename):
            # Read back the Excel file to verify
            df_read = pd.read_excel(filename, sheet_name='Teacher Activity')
            print(f"📊 Excel file contains {len(df_read)} rows and {len(df_read.columns)} columns")
            print(f"📄 Column names: {list(df_read.columns)}")
            
            # Clean up test file
            os.remove(filename)
            try:
                os.rmdir(downloads_path)
            except:
                pass  # Directory might not be empty
            print("🧹 Test files cleaned up")
            
            return True
        else:
            print("❌ Excel file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error creating Excel file: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_sheet_excel():
    """Test Excel file with multiple sheets (like the app does)"""
    print("\n🧪 Testing multi-sheet Excel export...")
    
    # Test data for different sheets
    teacher_data = [
        {'Teacher Name': 'John Smith', 'Activity Type': 'login', 'Date': '2025-09-24'},
        {'Teacher Name': 'Jane Doe', 'Activity Type': 'logout', 'Date': '2025-09-24'}
    ]
    
    student_data = [
        {'Student Name': 'Alice Brown', 'Class Teacher': 'John Smith', 'Registration Date': '2025-09-20'},
        {'Student Name': 'Charlie Wilson', 'Class Teacher': 'Jane Doe', 'Registration Date': '2025-09-21'}
    ]
    
    downloads_path = os.path.join(tempfile.gettempdir(), "Attendance_Export_Test")
    os.makedirs(downloads_path, exist_ok=True)
    filename = os.path.join(downloads_path, "Test_Multi_Sheet_Export.xlsx")
    
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Create teacher sheet
            df_teachers = pd.DataFrame(teacher_data)
            df_teachers.to_excel(writer, sheet_name='Teacher Activity', index=False)
            
            # Create student sheet  
            df_students = pd.DataFrame(student_data)
            df_students.to_excel(writer, sheet_name='Student Registration', index=False)
        
        print(f"✅ Successfully created multi-sheet Excel file: {filename}")
        
        # Verify both sheets exist
        excel_file = pd.ExcelFile(filename)
        sheet_names = excel_file.sheet_names
        print(f"📋 Sheet names: {sheet_names}")
        
        if 'Teacher Activity' in sheet_names and 'Student Registration' in sheet_names:
            print("✅ Both sheets created successfully")
            
            # Clean up
            os.remove(filename)
            try:
                os.rmdir(downloads_path)
            except:
                pass
            print("🧹 Test files cleaned up")
            
            return True
        else:
            print("❌ Not all sheets were created")
            return False
            
    except Exception as e:
        print(f"❌ Error creating multi-sheet Excel file: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Excel export tests"""
    print("🧪 Starting Advanced Excel Export Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Basic Excel export
    results.append(test_excel_export_with_pandas())
    
    # Test 2: Multi-sheet Excel export
    results.append(test_multi_sheet_excel())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 All Excel export tests passed! The functionality is ready for use.")
        return True
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)