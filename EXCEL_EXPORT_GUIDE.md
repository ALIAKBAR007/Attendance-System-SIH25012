# 📊 Excel Export Feature - User Guide

## How to Access the Excel Export Feature

### Step 1: Login as Teacher
1. Start the application by running `python main_gui_ctk.py`
2. Go to the **Teacher Login** tab
3. Login with your registered teacher account

### Step 2: Access Admin Panel
1. After successful login, click the **"📊 Admin Panel"** button
2. A new admin window will open with multiple tabs

### Step 3: Navigate to Data Export Tab
1. In the admin panel window, click on the **"📊 Data Export"** tab
2. You will see the Excel export interface with:
   - 📅 Date range selection (From/To dates)
   - 📋 Data type checkboxes
   - 📤 Export button

### Step 4: Configure Export Settings
1. **Select Date Range:**
   - Use the date pickers to choose start and end dates
   - Default is set to today's date

2. **Choose Data Types to Export:**
   - ✅ **👨‍🏫 Teacher Login/Logout Data** - Teacher activity logs
   - ✅ **👨‍🎓 Student Registration Data** - Student enrollment records
   - ✅ **📚 Class Attendance Data** - Regular class attendance records
   - ✅ **🍽️ Midday Meal Attendance Data** - Meal attendance records

### Step 5: Export Data
1. Select at least one data type checkbox
2. Click the **"📤 Export to Excel Files"** button
3. Wait for the export process to complete
4. Files will be saved to your **Downloads/Attendance_Export/** folder

## 📁 Export File Structure

The system creates separate Excel files for each selected data type:

- `Teacher_Activity_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`
- `Student_Registration_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`
- `Class_Attendance_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`
- `Meal_Attendance_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`

## 📊 Excel File Features

### Multi-Sheet Organization
- Each Excel file contains multiple sheets:
  - **Individual teacher sheets** - Data organized by class teacher
  - **Summary sheet** - Combined overview of all data

### Professional Formatting
- Clean column headers
- Proper date/time formatting
- Organized by teacher and date
- Easy to read and analyze

## 🔧 Troubleshooting

### Export Button Not Visible
1. Ensure you are logged in as a teacher
2. Make sure you opened the Admin Panel (separate window)
3. Click on the "📊 Data Export" tab in the admin panel

### Export Fails
1. Check that pandas and openpyxl are installed:
   ```bash
   pip install pandas openpyxl
   ```
2. Ensure at least one checkbox is selected
3. Verify date range is valid (start date ≤ end date)
4. Check that Downloads folder is accessible

### No Data in Export
- Verify the selected date range contains data
- Check that the selected data types have records in the database
- Ensure the date format is correct

## ✨ Features

- **Date Range Filtering** - Export only data within specified dates
- **Selective Export** - Choose which data types to include
- **Organized Output** - Separate files and sheets for easy analysis
- **Professional Format** - Ready for reporting and analysis
- **Automatic Naming** - Files include date ranges in names
- **Safe Location** - Files saved to Downloads folder

## 🎯 Use Cases

- **Monthly Reports** - Export attendance data for monthly analysis
- **Government Compliance** - Generate reports for meal program compliance
- **Data Backup** - Create Excel backups of important data
- **Analysis** - Export data for further analysis in Excel
- **Sharing** - Share attendance reports with stakeholders

---

**Note:** The Excel export feature requires an active internet connection for the initial pandas installation. Once installed, it works offline.