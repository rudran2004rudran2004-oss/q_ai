import pdfkit
import os
import pandas as pd
from datetime import datetime
import random


def extract_latest_csv_payroll(upload_dir="uploads"):
    # Step 1: Find latest CSV
    files = [f for f in os.listdir(upload_dir) if f.endswith(".csv")]
    if not files:
        return {"error": "No CSV files found."}

    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(upload_dir, f)))
    filepath = os.path.join(upload_dir, latest_file)

    # Step 2: Load CSV
    df = pd.read_csv(filepath, low_memory=False)

    # Step 3: Clean salary column
    df["gross_salary"] = df["gross_salary"].replace(r"[^\d]", "", regex=True).astype(int)
    EmployeeID = df['EmployeeID'] 

    # Step 4: Summary stats
    total_employees = len(df)
    total_payroll = df["gross_salary"].sum()

    Executive = ["CEO", "CTO", "CFO", "Chief Strategy Officer"]
    Senior = ["VP of Engineering", "VP of Marketing", "Director of Finance", "Head of Product"]
    Mid = ["Project Manager", "Team Lead", "Senior Analyst", "Senior Developer"]
    Junior = ["Analyst", "Developer", "QA Engineer", "Marketing Associate"]
    Entry = ["Intern", "Trainee", "Support Assistant", "Junior Developer"]

    Executive_count = 0
    Senior_count = 0
    Mid_count = 0
    Junior_count = 0
    Entry_count = 0

    salary = df["gross_salary"].tolist()
    employee_role = list(df['role'])
    for role in employee_role:
        if role in Executive:
            Executive_count+= 1
        elif role in Senior:
            Senior_count+= 1
        elif role in Mid:
            Mid_count+= 1
        elif role in Junior:
            Junior_count+= 1
        elif role in Entry:
            Entry_count+= 1
    
    Executive_salary = 0
    Senior_salary = 0
    Mid_salary = 0
    Junior_salary = 0
    Entry_salary = 0
    level = []

    for i,j in zip(salary,employee_role):
        if j in Executive:
            Executive_salary += i
            level.append("Executive")
        elif j in Senior:
            Senior_salary += i
            level.append("Senior")
        elif j in Mid:
            Mid_salary += i
            level.append("Mid")
        elif j in Junior:
            Junior_salary += i
            level.append("Junior")
        elif j in Entry:
            Entry_salary += i
            level.append("Entry")


    table_rows = ""
    emp_id = []
    emp_level = []
    emp_salary = []
    status = ["completed" ,"processing" ,"pending"]
    for _ in range(1000):
        number= random.randint(1,1000000)
        emp_id.append(EmployeeID[number])
        emp_level.append(level[number])
        emp_salary.append(salary[number])
                    
    for id,l,sal in zip(emp_id,emp_level,emp_salary):
        stat = random.choice(status)
        table_rows += f"""
            <tr>
                <td>{id}</td>
                <td>{l}</td>
                <td>₹{sal:,}</td>
                <td class="status-completed">{stat}</td>
            </tr>
        """


    timestamp = datetime.now().replace(microsecond=0)


            
        
    data ={
            "total_employees" : total_employees,
            "EmployeeID" : EmployeeID,
            "total_payroll" : total_payroll,
            "Executive_count" : Executive_count,
            "Senior_count" : Senior_count,
            "Mid_count" : Mid_count,
            "Junior_count" : Junior_count,
            "Entry_count" : Entry_count,
            "Executive_salary" : Executive_salary,
            "Senior_salary" : Senior_salary,
            "Mid_salary" : Mid_salary,
            "Junior_salary" : Junior_salary,
            "Entry_salary" : Entry_salary,
            "timestamp" : timestamp,
            "table_rows" : table_rows
    }
    return data
data = extract_latest_csv_payroll()

config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")



html_content ="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quantum Payroll Report</title>
    <style>
        
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Quantum Payroll Report</h1>
            <div class="timestamp">Generated: {timestamp} </div>
        </div>
        
        <div class="summary-section">
            <h2>Summary Statistics</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{total_employees}</div>
                    <div class="stat-label">Total Employees</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{total_employees}</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">0</div>
                    <div class="stat-label">Processing</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">0</div>
                    <div class="stat-label">Pending</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{total_payroll}</div>
                    <div class="stat-label">Total Payroll</div>
                </div>
            </div>
        </div>
        
        <h2 class="section-title">Employee Details</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Department</th>
                    <th>Salary</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <h2 class="section-title">Department Breakdown</h2>
        <div class="department-breakdown">
            <div class="department-card">
                <div class="department-name">Executive</div>
                <div class="department-stats">{Executive_count} Employees</div>
                <div class="department-stats">Total Salary: {Executive_salary}</div>
            </div>
            <div class="department-card">
                <div class="department-name">Senior</div>
                <div class="department-stats">{Senior_count} Employee</div>
                <div class="department-stats">Total Salary: {Senior_salary}</div>
            </div>
            <div class="department-card">
                <div class="department-name">MID</div>
                <div class="department-stats">{Mid_count} Employees</div>
                <div class="department-stats">Total Salary: {Mid_salary}</div>
            </div>
            <div class="department-card">
                <div class="department-name">Junior</div>
                <div class="department-stats">{Junior_count} Employee</div>
                <div class="department-stats">Total Salary: {Junior_salary}</div>
            </div>
            <div class="department-card">
                <div class="department-name">Entry_salary</div>
                <div class="department-stats">{Entry_count} Employee</div>
                <div class="department-stats">Total Salary: {Entry_salary}</div>
            </div>
        </div>
    </div>
</body>
</html>
""".format(**data)

time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
def report_generator(html_content, time_stamp, config):
    return pdfkit.from_string(html_content, f"output_{time_stamp}.pdf", configuration=config, css="report_genarator.css")
print(f"✅ PDF generated: output_{time_stamp}.pdf")

pdf= report_generator(html_content, time_stamp, config)

