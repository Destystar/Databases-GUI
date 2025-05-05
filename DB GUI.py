import psycopg2
from pathlib import Path
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
from dotenv import load_dotenv
import os
import sys
import re

#%% User auth
# Function to load the env
def loadEnv():
    """Load environment variables with clear error messages"""
    dotenvPath = Path(getPath(".env"))
    
    if not dotenvPath.exists():
        raise FileNotFoundError("Error: .env file not found!\nPlease create a database.env file in the application directory")
    print("Found .env file, loading environment variables...")
    load_dotenv(dotenvPath)
    
# Function to get path
def getPath(relativePath):
    # MEIPASS is for pyinstaller
    try:
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.abspath(".")

    return os.path.join(basePath, relativePath)

# User auth run
try:
    loadEnv()
except FileNotFoundError as e:
    messagebox.showerror("Auth Error", str(e))
    sys.exit("Failed to authenticate")
    
#%% Database connection and execution
# Connect to database
def connect():
    host = os.getenv("HOST")
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    connStr = f"host={host} dbname={dbname} user={user} password={password}"
    
    connection = psycopg2.connect(connStr)         
    return connection

# Execute the command input
def executeCommand(command, returnType=False, *params):
    connection = None
    try:
        connection = connect()
        connection.autocommit = True
        cur = connection.cursor()  
        cur.execute('set search_path to cmps_db')
        
        # Execute command with parameters
        if params:
            cur.execute(command, params)
        else:
            cur.execute(command)
            
        if returnType:
            rows = cur.fetchall()
            return rows
        
        return None
            
    except Exception as e:
        print(e)
        raise e
        
    finally:
        if connection:
            connection.close()

#%% Validation Methods
def validateTimeInput(char, timeEntry):
    if char == "":
        return True
    currentText = timeEntry.get()
    newText = currentText[:-1] + char if len(currentText) > 0 else char
    if not re.match(r'^[\d:]$', char):
        return False
    if len(newText.replace(':', '')) > 6:
        return False     
    return True

def formatTimeInput(timeEntry):
    currentText = timeEntry.get()
    digits = currentText.replace(':', '')
    digits = re.sub(r'\D', '', digits)
    
    if len(digits) <= 2:
        formatted = digits.zfill(2)
    elif len(digits) <= 4:
        formatted = f"{digits[:2]}:{digits[2:].zfill(2)}"
    else:
        formatted = f"{digits[:2]}:{digits[2:4].zfill(2)}:{digits[4:].zfill(2)}"
        
    hours = int(formatted.split(':')[0]) if ':' in formatted else int(formatted)
    minutes = formatted.split(':')[1] if len(formatted.split(':')) > 1 else '00'
    seconds = formatted.split(':')[2] if len(formatted.split(':')) > 2 else '00'
    
    if hours > 24:
        formatted = formatted.replace(str(hours), '24', 1)
    
    if int(minutes) > 59:
        formatted = formatted.replace(minutes, '59')
    if int(seconds) > 59:
        formatted = formatted.replace(seconds, '59')
        
    timeEntry.delete(0, tk.END)
    timeEntry.insert(0, formatted)

#%% GUI Management Functions
    
# Command to define the options of the second dropdown
def getCommands(commandType):
    commands = {
        "Student Management": ["Add Student", "Delete Student", "Search Student By Email/ID/Name", "View Students", "View Student Timetable"],
        "Exam Management": ["Add New Exam", "Delete Exam", "View Exam Schedule", "Search Exam By Title/Code", "View Results For Exam"],
        "Entry Management": ["Create Entry", "Cancel Entry", "Update Grade", "View Entries", "View Cancelled Entries"]
    }
    return commands.get(commandType, [""])

# Command to change the values of the second dropdown
def updateCommandOptions(value):
    specificCommand.set("Select Command")
    newOptions = getCommands(value)
    specificCommand.configure(values=[""])
    if newOptions:
        specificCommand.configure(values=newOptions)
        
# Function to open a popup for futher command functionality
def selectedCommand():
    selectedType = commandTypeSelect.get()
    selectedCommand = specificCommand.get()
    
    if not selectedCommand or selectedCommand == "Select Command":
       messagebox.showerror("Error", "Please select a valid command!")
       return
    
    # Create the popup
    popup = ctk.CTkToplevel(App)
    popup.title(f"{selectedType} - {selectedCommand}")
    
    # Popup visual config
    popup.configure(
        appearance_mode="dark",  
        fg_color="#2a2b2e",      
        bg_color="#2a2b2e"
    )
    
    # Move popup to front of screen (modify z order of the windows)
    popup.lift()
    popup.attributes('-topmost', True)
    
    # Window size config based on window type
    if selectedCommand in ["View Exam Schedule", "View Students", "View Entries", "View Cancelled Entries"]:
        popup.geometry("200x100") 
    elif selectedCommand in ["Delete Student", "Delete Exam", "Cancel Entry", "View Results For Exam", "View Student Timetable"]:
        popup.geometry("500x200")
    elif selectedCommand in ["Add Student", "Add New Exam", "Create Entry", "Update Grade"]:
        popup.geometry("500x400")
    else:
        popup.geometry("500x350")
        
    mainFrame = ctk.CTkFrame(popup)
    mainFrame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
    
    addWidgets(mainFrame, selectedType, selectedCommand)

# Function for displaying the results
def displayResults(results, commandName, *params):
    # Create popup window
    resultPopup = ctk.CTkToplevel(App)
    resultPopup.title(f"{commandName}")
    
    # Add title label
    commandLabel = ctk.CTkLabel(resultPopup, text=commandName, font=("Inter", 14, "bold"), text_color="#ffffff")
    commandLabel.place(relx=0.5, rely=0.05, anchor="center")
    
    # Calculate required dimensions
    if not results or len(results) == 0:
        popupWidth = 400
        popupHeight = 150
    elif len(results) == 1 and len(results[0]) == 1:
        content_width = max(400, len(str(results[0][0])) * 8 + 60)
        popupWidth = min(content_width, resultPopup.winfo_screenwidth() - 100)
        popupHeight = 200
    else:
        colWidths = [max(len(str(row[i])) for row in results for i in range(len(results[0]))) for i in range(len(results[0]))]
        colWidths = [min(width * 8 + 20, 200) for width in colWidths]
        numRows = len(results) 
        popupWidth = min(sum(colWidths) + 100, resultPopup.winfo_screenwidth() - 100)
        popupHeight = min((40 * numRows) + 120, resultPopup.winfo_screenheight() - 100)
        
        popupWidth = max(popupWidth, 400)
        popupHeight = max(popupHeight, 300)
   
    # Center Popup
    screenWidth = resultPopup.winfo_screenwidth()
    screenHeight = resultPopup.winfo_screenheight()
    x = (screenWidth // 2) - (popupWidth // 2)
    x = max(0, min(x, screenWidth - popupWidth))
    y = (screenHeight // 2) - (popupHeight // 2)
    y = max(0, min(y, screenHeight - popupHeight))
    
    # Window geometry
    resultPopup.geometry(f"{int(popupWidth)}x{int(popupHeight)}+{int(x)}+{int(y)}")
    
    # Create main frame with scrollbar
    mainFrame = ctk.CTkFrame(resultPopup)
    mainFrame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.85)
    
    # Create canvas and scrollbar
    canvas = ctk.CTkCanvas(mainFrame, bg="#2a2b2e", highlightthickness=0)
    scrollbar = ctk.CTkScrollbar(mainFrame, orientation="vertical", command=canvas.yview)
    scrollableFrame = ctk.CTkFrame(canvas, fg_color="#2a2b2e")
    
    # Configure canvas scrolling
    scrollableFrame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollableFrame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack widgets
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Handle empty results
    if not results or len(results) == 0:
        resultLabel = ctk.CTkLabel(scrollableFrame, text="No results found", font=("Inter", 12))
        resultLabel.pack(pady=20)
        return
    
    
    # Create header row
    headerFrame = ctk.CTkFrame(scrollableFrame, fg_color="#404040")
    headerFrame.pack(fill="x", pady=(0, 10))
    
    # Add column headers
    for i, column in enumerate(params if params else results[0]):
        headerLabel = ctk.CTkLabel(headerFrame, text=str(column), font=("Inter", 11, "bold"), text_color="#ffffff", width=colWidths[i])
        headerLabel.grid(row=0, column=i, padx=2)
    
    # Add data rows
    for row in results:
        rowFrame = ctk.CTkFrame(scrollableFrame, fg_color="#2a2b2e")
        rowFrame.pack(fill="x", pady=2)
       
        for j, value in enumerate(row):
            cellLabel = ctk.CTkLabel(rowFrame, text=str(value), font=("Inter", 11), text_color="#ffffff", width=colWidths[j])
            cellLabel.grid(row=0, column=j, padx=2)
                
#Function to add widgets to the popup based on the command
def addWidgets(frame, commandType, command):
    for widget in frame.winfo_children():
        widget.destroy()
    
    if commandType == "Student Management":
        if command == "Add Student":
            snoLabel = ctk.CTkLabel(frame, text="Student Number")
            snoLabel.place(relx=0.05, rely=0.2, anchor="w")
            snoEntry = ctk.CTkEntry(frame)
            snoEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            snameLabel = ctk.CTkLabel(frame, text="Student Name")
            snameLabel.place(relx=0.1, rely=0.4, anchor="w")
            snameEntry = ctk.CTkEntry(frame)
            snameEntry.place(relx=0.3, rely=0.4, anchor="w", relwidth=0.6)
            
            semailLabel = ctk.CTkLabel(frame, text="Student Email")
            semailLabel.place(relx=0.1, rely=0.6, anchor="w")
            semailEntry = ctk.CTkEntry(frame)
            semailEntry.place(relx=0.3, rely=0.6, anchor="w", relwidth=0.6)
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: saveStudent(snoEntry.get(), snameEntry.get(), semailEntry.get()))
            executeButton.place(relx=0.5, rely=0.85, anchor="center")
            
        elif command == "Delete Student":
            snoLabel = ctk.CTkLabel(frame, text="Student Number")
            snoLabel.place(relx=0.05, rely=0.2, anchor="w")
            snoEntry = ctk.CTkEntry(frame)
            snoEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: deleteStudent(snoEntry.get()))
            executeButton.place(relx=0.5, rely=0.65, anchor="center")
            
        elif command == "Search Student By Email/ID/Name":
            searchLabel = ctk.CTkLabel(frame, text="Search Term")
            searchLabel.place(relx=0.1, rely=0.2, anchor="w")
            searchEntry = ctk.CTkEntry(frame)
            searchEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            searchByLabel = ctk.CTkLabel(frame, text="Search By")
            searchByLabel.place(relx=0.1, rely=0.4, anchor="w")
            searchBy = ctk.CTkComboBox(frame, values=["Email", "ID", "Name"])
            searchBy.set("ID")
            searchBy.place(relx=0.3, rely=0.4, anchor="w", relwidth=0.6)
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: searchStudents(searchEntry.get(), searchBy.get()))
            executeButton.place(relx=0.5, rely=0.75, anchor="center")
        
        elif command == "View Students":
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=getStudents)
            executeButton.place(relx=0.5, rely=0.65, anchor="center")
            
        elif command == "View Student Timetable":
            snoLabel = ctk.CTkLabel(frame, text="Student Number")
            snoLabel.place(relx=0.05, rely=0.2, anchor="w")
            snoEntry = ctk.CTkEntry(frame)
            snoEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: getStudentTimetable(snoEntry.get()))
            executeButton.place(relx=0.5, rely=0.65, anchor="center")
                        
    elif commandType == "Exam Management":
        if command == "Add New Exam":
            excodeLabel = ctk.CTkLabel(frame, text="Exam Code")
            excodeLabel.place(relx=0.1, rely=0.2, anchor="w")
            excodeEntry = ctk.CTkEntry(frame)
            excodeEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            extitleLabel = ctk.CTkLabel(frame, text="Exam Title")
            extitleLabel.place(relx=0.1, rely=0.35, anchor="w")
            extitleEntry = ctk.CTkEntry(frame)
            extitleEntry.place(relx=0.3, rely=0.35, anchor="w", relwidth=0.6)
            
            exlocationLabel = ctk.CTkLabel(frame, text="Exam Location")
            exlocationLabel.place(relx=0.1, rely=0.5, anchor="w")
            exlocationEntry = ctk.CTkEntry(frame)
            exlocationEntry.place(relx=0.3, rely=0.5, anchor="w", relwidth=0.6)
            
            exdateLabel = ctk.CTkLabel(frame, text="Exam Date")
            exdateLabel.place(relx=0.1, rely=0.65, anchor="w")
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("my.DateEntry", foreground="#a0a0a0", background="#2a2b2e", fieldforeground="#a0a0a0", fieldbackground="#2a2b2e", border_width=2, arrowcolor="#404040")
            exdateEntry = DateEntry(frame, style="my.DateEntry", width=33, font=("Inter", 20), selectmode='day', date_pattern='yyyy-mm-dd')
            exdateEntry.pack()
            exdateEntry.place(relx=0.3, rely=0.65, anchor="w")
            
            extimeLabel = ctk.CTkLabel(frame, text="Exam Time")
            extimeLabel.place(relx=0.1, rely=0.8, anchor="w")
            hour = tk.StringVar(value=12)
            minute = tk.StringVar(value=00)
            extimeEntryHour = tk.Spinbox(frame, from_=0, to=24, textvariable=hour, wrap=True, width=15, font=("Inter", 20), bg="#2a2b2e", fg="#a0a0a0", buttonbackground="#404040", highlightbackground="#404040")
            extimeEntryHour.place(relx=0.3, rely=0.8, anchor="w")
            colonLabel = tk.Label(frame, text=":", fg="#a0a0a0", font=("Inter", 20, "bold"), bg="#212121")
            colonLabel.place(relx=0.58, rely=0.8, anchor="w")
            extimeEntryMinute = tk.Spinbox(frame, from_=00, to=59, textvariable=minute, wrap=True, width=15, font=("Inter", 20), bg="#2a2b2e", fg="#a0a0a0", buttonbackground="#404040", highlightbackground="#404040", format="%02.0f")
            extimeEntryMinute.place(relx=0.6, rely=0.8, anchor="w")
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: saveExam(excodeEntry.get(), extitleEntry.get(), exlocationEntry.get(), exdateEntry.get(), extimeEntryHour.get(), extimeEntryMinute.get()))
            executeButton.place(relx=0.5, rely=0.9, anchor="center")
            
        elif command == "Delete Exam":
            excodeLabel = ctk.CTkLabel(frame, text="Exam Code")
            excodeLabel.place(relx=0.1, rely=0.2, anchor="w")
            excodeEntry = ctk.CTkEntry(frame)
            excodeEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: deleteExam(excodeEntry.get()))
            executeButton.place(relx=0.5, rely=0.65, anchor="center")
            
        elif command == "View Exam Schedule":
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=viewExamSchedule)
            executeButton.place(relx=0.5, rely=0.65, anchor="center")
            
        elif command == "Search Exam By Title/Code":
            searchLabel = ctk.CTkLabel(frame, text="Search Term")
            searchLabel.place(relx=0.1, rely=0.2, anchor="w")
            searchEntry = ctk.CTkEntry(frame)
            searchEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            searchByLabel = ctk.CTkLabel(frame, text="Search By")
            searchByLabel.place(relx=0.1, rely=0.4, anchor="w")
            searchBy = ctk.CTkComboBox(frame, values=["Title", "Code"])
            searchBy.set("Code")
            searchBy.place(relx=0.3, rely=0.4, anchor="w", relwidth=0.6)
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: searchExams(searchEntry.get(), searchBy.get()))
            executeButton.place(relx=0.5, rely=0.75, anchor="center")
            
        elif command == "View Results For Exam":
            excodeLabel = ctk.CTkLabel(frame, text="Exam Code")
            excodeLabel.place(relx=0.1, rely=0.2, anchor="w")
            excodeEntry = ctk.CTkEntry(frame)
            excodeEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: getResultsForExam(excodeEntry.get()))
            executeButton.place(relx=0.5, rely=0.65, anchor="center")
            
    elif commandType == "Entry Management":
        if command == "Create Entry":
            enoLabel = ctk.CTkLabel(frame, text="Entry ID")
            enoLabel.place(relx=0.05, rely=0.2, anchor="w")
            enoEntry = ctk.CTkEntry(frame)
            enoEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            snoLabel = ctk.CTkLabel(frame, text="Student Number")
            snoLabel.place(relx=0.05, rely=0.4, anchor="w")
            snoEntry = ctk.CTkEntry(frame)
            snoEntry.place(relx=0.3, rely=0.4, anchor="w", relwidth=0.6)
            
            excodeLabel = ctk.CTkLabel(frame, text="Exam Code")
            excodeLabel.place(relx=0.1, rely=0.6, anchor="w")
            excodeEntry = ctk.CTkEntry(frame)
            excodeEntry.place(relx=0.3, rely=0.6, anchor="w", relwidth=0.6)
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: createEntry(snoEntry.get(), excodeEntry.get()))
            executeButton.place(relx=0.5, rely=0.85, anchor="center")
            
        elif command == "Update Grade":
            enoLabel = ctk.CTkLabel(frame, text="Entry Number")
            enoLabel.place(relx=0.1, rely=0.2, anchor="w")
            enoEntry = ctk.CTkEntry(frame)
            enoEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            gradeLabel = ctk.CTkLabel(frame, text="Grade")
            gradeLabel.place(relx=0.1, rely=0.4, anchor="w")
            gradeEntry = ctk.CTkEntry(frame)
            gradeEntry.place(relx=0.3, rely=0.4, anchor="w", relwidth=0.6)
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: updateGrade(enoEntry.get(), gradeEntry.get()))
            executeButton.place(relx=0.5, rely=0.85, anchor="center")
            
        elif command == "Cancel Entry":
            enoLabel = ctk.CTkLabel(frame, text="Entry Number")
            enoLabel.place(relx=0.1, rely=0.2, anchor="w")
            enoEntry = ctk.CTkEntry(frame)
            enoEntry.place(relx=0.3, rely=0.2, anchor="w", relwidth=0.6)
            
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=lambda: cancelEntry(enoEntry.get()))
            executeButton.place(relx=0.5, rely=0.65, anchor="center")
            
        elif command == "View Entries":
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=viewEntries)
            executeButton.place(relx=0.5, rely=0.65, anchor="center")
            
        elif command == "View Cancelled Entries":
            executeButton = ctk.CTkButton(frame, text="EXECUTE", command=viewCancelledEntries)
            executeButton.place(relx=0.5, rely=0.65, anchor="center")


#%% Database Execution Functions
def saveStudent(sno, name, email):
    try:
        sqlCommand = "Insert into student (sno, sname, semail) values (%s, %s, %s)"
        executeCommand(sqlCommand, False, sno, name, email)
        messagebox.showinfo("Success", "Student added successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add student: {str(e)}")
        raise
    
def getStudents():
    try:
        sqlCommand = "Select sno, sname, semail from student order by sno"
        results = executeCommand(sqlCommand, True)
        displayResults(results, "View Students", "Student ID", "Name", "Email")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to show students: {str(e)}")
        raise
        
def deleteStudent(sno):
    try:
        sqlCommand = "Delete from student where sno = %s"
        executeCommand(sqlCommand, False, sno)
        messagebox.showinfo("Success", "Student deleted successfully!")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to delete student: {str(e)}")
       raise
    
def searchStudents(searchTerm, searchBy):
    try:
        searchType = "sno"
        if searchBy.lower() == "name":
            searchType = "sname"
        elif searchBy.lower() == "email":
            searchType = "semail"           
        if searchType == "sname":
            sqlCommand = f"Select sno, sname, semail from student where {searchType} ilike %s"
            searchTerm = f"%{searchTerm}%"
        elif searchType == "sno":
            sqlCommand = f"Select sno, sname, semail from student where {searchType} = %s"
        else:
            sqlCommand = f"Select sno, sname, semail from student where {searchType} ilike %s"        
        results = executeCommand(sqlCommand, True, searchTerm)        
        if not results:
           messagebox.showerror("Error", "No students found matching the criteria")
           return        
        displayResults(results, f"Search Results ({searchBy})", "Student ID", "Name", "Email")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to search students: {str(e)}")
       raise

def saveExam(excode, title, location, date, hour, minute):
    try:
        time = f"{hour}:{minute}:00"
        sqlCommand = "Insert into exam (excode, extitle, exlocation, exdate, extime) values (%s, %s, %s, %s, %s)"
        executeCommand(sqlCommand, False, excode, title, location, date, time)
        messagebox.showinfo("Success", "Exam added successfully!")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to add exam: {str(e)}")
       raise

def deleteExam(excode):
    try:
        sqlCommand = "Delete from exam where excode = %s"
        executeCommand(sqlCommand, False, excode)
        messagebox.showinfo("Success", "Exam deleted successfully!")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to delete exam: {str(e)}")
       raise

def searchExams(searchTerm, searchBy):
    try:
        if searchBy == "Code":
            searchBy = "excode"
        elif searchBy == "Title":
            searchBy = "extitle"
        sqlCommand = f"Select excode, extitle, exlocation, exdate, extime from exam where {searchBy.lower()} ilike %s"
        searchTerm = f"%{searchTerm}%"    
        results = executeCommand(sqlCommand, True, searchTerm)    
        if not results:
           messagebox.showerror("Error", "No exams found matching the criteria")
           return  
        displayResults(results, f"Search Results ({searchBy})", "Code", "Title", "Location", "Date", "Time")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to search exams: {str(e)}")
       raise

def createEntry(eno, sno, excode):
    try:
        sqlCommand = "Insert into entry (eno, sno, excode) values (%s, %s, %s)"
        executeCommand(sqlCommand, False, eno, sno, excode)
        messagebox.showinfo("Success", "Entry created successfully!")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to create entry: {str(e)}")
       raise

def updateGrade(eno, grade):
    try:
        grade = "{:02.2f}".format(float(grade))
        sqlCommand = "Select updateEntryGrade(%s, %s)"
        executeCommand(sqlCommand, False, eno, grade)
        messagebox.showinfo("Success", "Grade updated successfully!")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to update grade: {str(e)}")
       raise

def cancelEntry(eno):
    try:
        sqlCommand = "Select cancelEntry(%s)"
        executeCommand(sqlCommand, False, eno)
        messagebox.showinfo("Success", "Entry cancelled successfully!")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to cancel entry: {str(e)}")
       raise

def viewExamSchedule():
    try:
        sqlCommand = "Select excode, extitle, exlocation, exdate, extime from exam order by exdate, extime"
        results = executeCommand(sqlCommand, True)
        displayResults(results, "View Exam Schedule", "Code", "Title", "Location", "Date", "Time")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to get exam schedule: {str(e)}")
       raise

def getResultsForExam(examCode):
    try:
        sqlCommand = "Select getResultsForExam(%s)"
        results = executeCommand(sqlCommand, True, examCode)
        displayResults(results, "Exam Results", "Code", "Title", "Student ID", "Name", "Grade", "Result")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to get exam results: {str(e)}")
       raise

def getStudentTimetable(studentID):
    try:
        sqlCommand = "Select * from getStudentTimetable(%s)"
        results = executeCommand(sqlCommand, True, studentID)
        displayResults(results, "Student Timetable", "Name", "Code", "Title", "Location", "Date", "Time")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to get student timetable: {str(e)}")
       raise

def viewEntries():
    try:
        sqlCommand = "Select eno, excode, sno, egrade from entry order by eno"
        results = executeCommand(sqlCommand, True)
        displayResults(results, "View Entries", "ID", "Exam Code", "Student ID", "Grade")
    except Exception as e:
       messagebox.showerror("Error", f"Failed to get Entries: {str(e)}")
       raise
       
def viewCancelledEntries():
    try:
        sqlCommand = "Select eno, excode, sno, cdate, cuser from cancel order by eno"
        results = executeCommand(sqlCommand, True)
        displayResults(results, "View Cancelled Entries", "ID", "Exam Code", "Student ID", "Grade", "Cancelled By")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to get Cancelled Entries: {str(e)}")
        raise

#%% The GUI
# CustomTkinter config
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Main window config
App = ctk.CTk()
App.geometry("800x500")
App.title("CMPS Database")
App.grid_columnconfigure(0, weight=1)
App.grid_rowconfigure(1, weight=1)

# Header
headerFrame = ctk.CTkFrame(App, fg_color="#1a1b1e", corner_radius=0)
headerFrame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
headerFrame.grid_columnconfigure(0, weight=1)

# Title
titleLabel = ctk.CTkLabel(headerFrame, text="CMPS Database Application", text_color="#ffffff", font=("Inter", 28, "bold"), corner_radius=0)
titleLabel.grid(row=0, column=0, pady=20, padx=40, sticky="nsew")

# Input section
# Input section card
inputCard = ctk.CTkFrame(App, fg_color="#2a2b2e", corner_radius=10, border_width=1, border_color="#404040")
inputCard.grid(row=1, column=0, padx=35, pady=10, sticky="nsew")
               
# Input card grid config
inputCard.grid_columnconfigure(0, weight=1)
inputCard.grid_columnconfigure(1, weight=1)
inputCard.grid_columnconfigure(0, minsize=280)
inputCard.grid_columnconfigure(1, minsize=280)

# Dropdown for command type
commandTypeSelect = ctk.CTkOptionMenu(inputCard, values=["Select Type", "Student Management", "Exam Management", "Entry Management"], font=("Inter", 16), command=updateCommandOptions, fg_color="#404040", button_color="#666666", button_hover_color="#808080", width=280, corner_radius=10)
commandTypeSelect.grid(row=0, column=0, pady=(30, 10), padx=(35, 15), sticky="ew")

# Dropdown for specific command
specificCommand = ctk.CTkOptionMenu(inputCard, values=["Select Command"], font=("Inter", 16), fg_color="#404040", button_color="#666666", button_hover_color="#808080", width=280, corner_radius=10)
specificCommand.grid(row=0, column=1, pady=(30, 10), padx=(15, 35), sticky="ew")

# Instructions for use
instructionsFrame = ctk.CTkFrame(inputCard, fg_color="#2a2b2e", bg_color="#2a2b2e", corner_radius=10, border_width=1, border_color="#404040")
instructionsFrame.grid(row=1, column=0, columnspan=2, pady=(15, 20), padx=35, sticky="ew")
instructionsFrame.grid_columnconfigure(0, weight=1)

# Step 1
step1Label = ctk.CTkLabel(instructionsFrame, text="1. Select the type of command you want to execute", text_color="#a0a0a0", font=("Inter", 12), corner_radius=0)
step1Label.grid(row=0, column=0, pady=(20, 10), padx=10, sticky="w")

# Step 2
step2Label = ctk.CTkLabel(instructionsFrame, text="2. Choose a specific command from the selected category", text_color="#a0a0a0", font=("Inter", 12), corner_radius=0)
step2Label.grid(row=1, column=0, pady=(10, 10), padx=10, sticky="w")

# Step 3
step3Label = ctk.CTkLabel(instructionsFrame, text="3. Click the Select Command button and wait for window to popup", text_color="#a0a0a0", font=("Inter", 12), corner_radius=0)
step3Label.grid(row=2, column=0, pady=(10, 10), padx=10, sticky="w")

# Step 4
step4Label = ctk.CTkLabel(instructionsFrame, text="4. Select the desired options and input the data on the popup window and click the Execute button", text_color="#a0a0a0", font=("Inter", 12), corner_radius=0)
step4Label.grid(row=3, column=0, pady=(10, 20), padx=10, sticky="w")

# Button to select command
actionButton = ctk.CTkButton(App, text="Select Command", command=selectedCommand, font=("Inter", 16), fg_color="#666666", hover_color="#808080", text_color="#ffffff", border_width=2, border_color="#808080", corner_radius=10, width=250, height=50)
actionButton.grid(row=2, column=0, pady=10, padx=35)

App.resizable(True, True)

App.mainloop()
