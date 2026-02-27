import requests

import os ,io,pdfkit,base64
import pandas as pd
from flask import Flask, request, redirect, url_for, render_template, session ,flash,jsonify,send_file,abort, stream_with_context

import glob
from PQC import pqc
from pdf_digital_signature import qds_sign,verify_file
from num2words import num2words
from sqlalchemy import and_,or_, select
import pandas as pd
from datetime import datetime,timedelta
from werkzeug.utils import secure_filename
#from gemini_handler import chat
from payroll_report import build_payroll_pdf
from assistant_route import assistant_bp


from models import (
    db,
    employee_detail,
    jan_2025,
    feb_2025,
    mar_2025,
    apr_2025,
    may_2025,
    jun_2025,
    jul_2025,
    aug_2025,
    sep_2025,
    oct_2025,
    nov_2025,
    dec_2025
)

LM_STUDIO_SERVER = 'http://127.0.0.1:5001'# congiguration to wkhtmltopdf
config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Configure the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# CRITICAL: A SECRET_KEY is required for Flask sessions to work.
app.config['SECRET_KEY'] = 'a_secure_and_random_string_for_session' 
app.permanent_session_lifetime = timedelta(minutes=35)  # session expires after 2 minutes
app.register_blueprint(assistant_bp)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



#connectingt to database

db_path = os.path.abspath("emp_pay.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

monthly_models = {
    "January_2025": jan_2025,
    "February_2025": feb_2025,
    "March_2025": mar_2025,
    "April_2025": apr_2025,
    "May_2025": may_2025,
    "June_2025": jun_2025,
    "July_2025": jul_2025,
    "August_2025": aug_2025,
    "September_2025": sep_2025,
    "October_2025": oct_2025,
    "November_2025": nov_2025,
    "December_2025": dec_2025
}

# helper function
def fig_to_html(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return f'<img src="data:image/png;base64,{img_base64}" />'

def fetching_data():
    user_id = session.get('username')
    if not user_id:
        return None

    user = employee_detail.query.filter_by(EmployeeID=user_id).first()
    if user:
        return {
            "hello": f"Welcome {user.first_name} {user.last_name}",
            "role": user.role,
            "level": user.Level,
            "Department": user.Department,
            "firstname": user.first_name,
            "lastname": user.last_name,
            "email": user.email,
            "Phone": user.Phone_Number,
            "account": user.Account_Number,
            "doj": user.JoiningDate
        }
    return None

def get_user_salary_data(employee_id, month, year):
    table_key = f"{month}_{year}"  # e.g., "March_2025"
    ModelClass = monthly_models.get(table_key)
    if not ModelClass:
        return {"error": f"No model found for {table_key}"}

    with app.app_context():
        personal = employee_detail.query.filter_by(EmployeeID=employee_id).first()
        salary = ModelClass.query.filter_by(EmployeeID=employee_id).first()

        if not personal or not salary:
            return {"error": "User data not found"}

        return {
            "employeeID": employee_id,
            "name":f"Wellcome {personal.first_name} {personal.last_name}",
            "department": personal.Department,
            "role": personal.role,
            "Basic": salary.basic,
            "HouseAllowance": salary.house_allowance,
            "FixedAllowance": salary.fixed_allowance,
            "Tax": salary.tax,
            "Deduction": salary.deduction,
            "Bonus": salary.bonuse,
            "StockOptions": salary.stack_options,
            "NetSalary": salary.net_salary,
            "GrossSalary": salary.gross_salary,
            "TargetsCompleted": salary.targets_completed,
            "TargetToBeCompleted": salary.target_to_be_completed,
            "WorkingDays": salary.WorkingDays,
            "PresentDays": salary.PresentDays,
            }

def get_net_salary_in_words(employee_id, month, year):
    key = f"{month.strip().capitalize()}_{year}"
    SalaryModel = monthly_models.get(key)

    if not SalaryModel:
        return f"No salary table found for {month} {year}."

    try:
        result = (
            db.session.query(SalaryModel.net_salary)
            .filter(SalaryModel.EmployeeID== employee_id)
            .one()
        )
        amount = int(result[0])
        words = num2words(amount, to='cardinal', lang='en_IN')
        return words.title()
    except Exception as e:
        return f"Error fetching salary: {str(e)}"

    

def salary_lookup():
    employee_id = session.get('username')
    if not employee_id:
        return render_template('partials/ceo_salary.html', data={"error": "Session expired. Please sign in again."})

    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')
        data = get_user_salary_data(employee_id, month, year)
        data2 = fetching_data()
        net_pay_words = get_net_salary_in_words(employee_id, month, year)
        return render_template('partials/ceo_salary.html', data=data,month=month,year=year,data2=data2,net_pay_words=net_pay_words)
    else:
        return render_template('partials/ceo_salary.html', data=None)
    
public_key_to_display=""
#sign in Page
@app.route('/')
def home():
    return render_template("home.html", signed_in=session.get("signed_in", False))


# Shared Sign-In Route
@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    next_page = request.args.get('next') or request.form.get('next') or '/'
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        stmt = select(employee_detail).where(
            and_(
                or_(
                    employee_detail.EmployeeID == username,
                    employee_detail.email == username
                ),
            employee_detail.EmployeeID == password
            )
        )
        result = db.session.execute(stmt).fetchone()
        
        

# If credientials are true  the go for next page  Else  return same and notify invalid credientials
        if result:
            user = result[0]  # ✅ Define 'user' only if result exists
            session.permanent = True
            session['username'] = user.EmployeeID # Store username for later use
            #role = result.employee_detail.role  # Assuming Role is a column in your model
            session['logged_in'] = True
            return redirect(next_page)
        else:
            error = "Invalid credentials. Please try again."
            return render_template('sign_in_1.html', error=error, next=next_page)

    return render_template('sign_in_1.html', next=next_page)

        

# web page for displaying employee detail

@app.route('/emp_identity', methods=['GET', 'POST'])
def emp_identity():
    if not session.get('logged_in'):
        # The current URL path (e.g., '/payroll') is attached 
        # as the value for the 'next' parameter.
        return redirect(url_for('sign_in', next=request.path)) 
    data = fetching_data()
    return render_template('emp_identiy.html',data=data)  

# web page for displaying employee payroll

@app.route('/payroll', methods=['GET', 'POST'])
@app.route('/salary', methods=['GET', 'POST'])
def payroll():
    employee_id = session.get('username')
    if not session.get('logged_in'):
        return redirect(url_for('sign_in', next=request.path))

    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')
        data = get_user_salary_data(employee_id, month, year)
        data2 = fetching_data()
        net_pay_words = get_net_salary_in_words(employee_id, month, year)

        # If it's an AJAX request, return only the payslip partial
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render_template('partials/payslip.html', data=data, data2=data2, month=month, year=year, net_pay_words=net_pay_words)

        # Otherwise, render full page
        return render_template('ceo_salary.html', data=data, data2=data2, month=month, year=year, net_pay_words=net_pay_words)

    return render_template('ceo_salary.html')

# web page for dispklaing employee tax

@app.route('/tax', methods=['GET', 'POST'])
def tax():
 
    return render_template('payroll_clean.html')

# web page for dispklaing employee quantum_ai




# web page for dispklaing employee quantum_ai


@app.route('/quantum_encryption', methods=['GET', 'POST'])
def quantum_encryption():
    import math
    import pandas as pd
    import random
    import time
    import matplotlib
    matplotlib.use('Agg')  # Use non-GUI backend suitable for web apps
    import matplotlib.pyplot as plt
    import io
    import base64
    from flask import render_template

    # Helper: Convert matplotlib figure to base64 HTML
    def fig_to_html(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return f'<img src="data:image/png;base64,{img_base64}" />'

    # Step 1: Generate Payroll Dataset
    num_records = 1_000_000
    payroll_data = pd.DataFrame({
        "Emp_ID": [f"E{str(i).zfill(7)}" for i in range(1, num_records + 1)],
        "Name": [f"Emp_{i}" for i in range(1, num_records + 1)],
        "Department": random.choices(["IT", "HR", "Finance", "Admin"], k=num_records),
        "Salary": [random.randint(30_000, 90_000) for _ in range(num_records)]
    })
    for _ in range(100):
        idx = random.randint(0, num_records - 1)
        payroll_data.loc[idx, "Salary"] = 999999  # simulate anomaly

    # Step 2: Define Algorithms
    algorithms = {
        "RSA (Classical Encryption)": {"time_complexity": "O(N^3)", "type": "Classical"},
        "Shor (Quantum Factoring)": {"time_complexity": "O((log N)^3)", "type": "Quantum"},
        "Grover (Quantum Search)": {"time_complexity": "O(√N)", "type": "Quantum"},
    }

    # Step 3: Search Simulations
    def classical_anomaly_search(data):
        start = time.time()
        anomalies = data[data["Salary"] > 200000]
        end = time.time()
        return anomalies, end - start

    def grover_simulated_search(data):
        start = time.time()
        time.sleep(math.sqrt(len(data)) / 30000)  # simulate quantum speed
        anomalies = data[data["Salary"] > 200000]
        end = time.time()
        return anomalies, end - start

    classical_anomalies, t_classical = classical_anomaly_search(payroll_data)
    grover_anomalies, t_grover = grover_simulated_search(payroll_data)
    speed_gain = t_classical / t_grover if t_grover > 0 else float("inf")

    # Step 4: Visualizations

    # Salary Distribution
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.hist(payroll_data["Salary"], bins=50, color="skyblue", edgecolor="black")
    ax1.axvline(200000, color="red", linestyle="--", label="Anomaly Threshold")
    ax1.set_title("Salary Distribution in Payroll Dataset (10 Lakh Records)")
    ax1.set_xlabel("Salary (₹)")
    ax1.set_ylabel("Number of Employees")
    ax1.legend()
    ax1.grid(True)
    salary_plot = fig_to_html(fig1)

    # Algorithm Speed Comparison
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    ax2.bar(["Classical Search", "Grover Search"], [t_classical, t_grover], color=["orange", "green"])
    ax2.set_title("Algorithm Speed Comparison")
    ax2.set_ylabel("Time (seconds)")
    ax2.text(0, t_classical, f"{t_classical:.3f}s", ha="center", va="bottom")
    ax2.text(1, t_grover, f"{t_grover:.3f}s", ha="center", va="bottom")
    speed_plot = fig_to_html(fig2)

    # Department-wise Average Salary
    fig3, ax3 = plt.subplots(figsize=(7, 5))
    dept_avg = payroll_data.groupby("Department")["Salary"].mean().sort_values()
    dept_avg.plot(kind="bar", color="teal", edgecolor="black", ax=ax3)
    ax3.set_title("Average Salary per Department")
    ax3.set_ylabel("Average Salary (₹)")
    ax3.set_xlabel("Department")
    ax3.grid(True, axis="y")
    dept_plot = fig_to_html(fig3)

    # Step 5: Render HTML
    return render_template("quantum_encryption.html",
        algorithms=algorithms,
        t_classical=t_classical,
        t_grover=t_grover,
        speed_gain=speed_gain,
        anomalies=grover_anomalies.head().to_html(classes="table table-bordered", border=0),
        salary_plot=salary_plot,
        speed_plot=speed_plot,
        dept_plot=dept_plot
    )

# web page for dispklaing employee quantum_ai



@app.route('/risk_engine', methods=['GET', 'POST'])
def risk_engine():
    import random
    import math

    TOTAL_RECORDS = 1_000_000
    records_processed = random.randint(900_000, 1_000_000)
    anomalies_detected = random.randint(50, 100)
    quantum_progress = random.randint(80, 100)
    encryption_progress = random.randint(80, 100)

    def progress_bar(current, total, length=30):
        filled = int((current / total) * length)
        bar = "█" * filled + "░" * (length - filled)
        percent = (current / total) * 100
        return bar, percent

    rec_bar, rec_pct = progress_bar(records_processed, TOTAL_RECORDS)
    anom_bar, _ = progress_bar(anomalies_detected, 100)
    quantum_bar, _ = progress_bar(quantum_progress, 100)
    encrypt_bar, _ = progress_bar(encryption_progress, 100)

    return render_template("risk_engine.html",
        rec_bar=rec_bar, rec_pct=rec_pct,
        records_processed=records_processed,
        anomalies_detected=anomalies_detected,
        quantum_bar=quantum_bar,
        encrypt_bar=encrypt_bar,
        quantum_progress=quantum_progress,
        encryption_progress=encryption_progress,
        anom_bar=anom_bar
        
    )

# web page for dispklaing employee quantum_ai



@app.route('/assistant', methods=['GET', 'POST'])
def assistant():
    if request.method == 'GET':
        return open('chatbot.html').read(), 200, {'Content-Type': 'text/html'}

    body       = request.get_json(force=True, silent=True) or {}
    message    = body.get('message', '').strip()
    session_id = body.get('session_id', 'default')
    do_stream  = body.get('stream', True)   # frontend sends stream:true

    if not message:
        return jsonify({'error': 'message is required'}), 400

    # ── Streaming proxy ───────────────────────────────────────────────────────
    if do_stream:
        def generate():
            try:
                with requests.post(
                    f'{LM_STUDIO_SERVER}/chat',
                    json={'message': message, 'session_id': session_id, 'stream': True},
                    stream=True,
                    timeout=(10, 300),   # connect=10s, read=300s
                ) as r:
                    for chunk in r.iter_content(chunk_size=None):
                        yield chunk
            except requests.exceptions.ConnectionError:
                yield b'data: {"error": "Cannot connect to LM Studio backend"}\n\n'
            except Exception as e:
                yield f'data: {{"error": "{str(e)}"}}\n\n'.encode()

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
            }
        )

    # ── Non-streaming fallback ────────────────────────────────────────────────
    try:
        resp = requests.post(
            f'{LM_STUDIO_SERVER}/chat',
            json={'message': message, 'session_id': session_id, 'stream': False},
            timeout=300,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/assistant/reset', methods=['POST'])
def assistant_reset():
    body = request.get_json(force=True, silent=True) or {}
    try:
        resp = requests.post(f'{LM_STUDIO_SERVER}/reset', json=body, timeout=10)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. ROUTE TO HANDLE THE API CALL (MATCHES chatbot.js)
# ... existing routes ...

@app.route('/api/chat', methods=['POST'])    # ← ADD THIS
def handle_chat():
    data = request.get_json()
    messages = data.get('messages', [])
    if not messages:
        return jsonify({"reply": "No message received"}), 400
    user_message = messages[-1]['content']
    try:
        bot_response = chat(user_message)
        return jsonify({"reply": bot_response})
    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        return jsonify({"reply": f"Error: {str(e)}"}), 500



# web page for displaying employee quantum_ai

@app.route('/settlement', methods=['GET', 'POST'])
def settlement():
    if not session.get('logged_in'):
        # The current URL path (e.g., '/payroll') is attached 
        # as the value for the 'next' parameter.
        return redirect(url_for('sign_in', next=request.path)) 
    import time, random, os, uuid
    import pandas as pd
    import numpy as np

    # Simulation config
    TOTAL_RECORDS = 200_000
    CHUNK_SIZE = 25_000
    EMP_POOL = pd.DataFrame({
        "emp_id": [f"E{100000+i}" for i in range(8000)],
        "name": [f"Emp_{i}" for i in range(8000)],
        "gross_pay": np.random.randint(20000, 250000, size=8000),
    })
    EMP_POOL["deductions"] = (EMP_POOL["gross_pay"] * np.random.uniform(0.05, 0.3, size=8000)).astype(int)
    EMP_POOL["net_pay"] = EMP_POOL["gross_pay"] - EMP_POOL["deductions"]

    records_processed = 0
    anomalies_found = 0
    quantum_progress = 0
    encryption_progress = 0
    forensic_logs = []
    final_settlements = []

    # Main simulation loop
    while records_processed < TOTAL_RECORDS:
        to_process = min(CHUNK_SIZE, TOTAL_RECORDS - records_processed)
        records_processed += to_process

        base_lambda = np.random.choice([0.1, 0.3, 0.6, 1.2], p=[0.6,0.25,0.1,0.05])
        new_anoms = np.random.poisson(lam=base_lambda * (to_process/10000.0))
        anomalies_found += int(new_anoms)

        quantum_progress = min(100, quantum_progress + random.randint(2,8))
        encryption_progress = min(100, encryption_progress + random.randint(3,12))

        for _ in range(int(new_anoms)):
            choice = EMP_POOL.sample(1).iloc[0]
            severity = random.choices(["Low","Medium","High","Critical"], weights=[55,28,12,5])[0]
            score = round(random.uniform(0.4, 0.99) if severity in ["High","Critical"] else random.uniform(0.05,0.6), 3)
            issue = random.choice([
                "Duplicate Payment", "Salary Spike", "Tax Mismatch", "Inactive Employee Paid",
                "Bank Account Mismatch", "Overtime Fraud", "Incorrect Tax Code", "Manual Override"
            ])
            rec_idx = records_processed - random.randint(0, to_process-1)
            forensic_logs.append({
                "forensic_id": str(uuid.uuid4()),
                "emp_id": choice["emp_id"],
                "name": choice["name"],
                "record_index": int(rec_idx),
                "issue": issue,
                "severity": severity,
                "risk_score": float(score),
                "detected_at": pd.Timestamp.now()
            })

        if random.random() < 0.065:
            sample = EMP_POOL.sample(1).iloc[0]
            arrears = int(sample["net_pay"] * random.uniform(0.1, 2.0))
            tax_adj = int(arrears * random.uniform(0.05, 0.2))
            final_net = max(0, int(sample["net_pay"] + arrears - tax_adj))
            final_settlements.append({
                "settlement_id": str(uuid.uuid4()),
                "emp_id": sample["emp_id"],
                "name": sample["name"],
                "base_net_pay": int(sample["net_pay"]),
                "arrears": arrears,
                "tax_adjustment": tax_adj,
                "final_payout": final_net,
                "approved": random.choice([True, False]),
                "generated_at": pd.Timestamp.now()
            })

    # Ensure minimum data for display
    while len(forensic_logs) < 8:
        choice = EMP_POOL.sample(1).iloc[0]
        forensic_logs.append({
            "forensic_id": str(uuid.uuid4()),
            "emp_id": choice["emp_id"],
            "name": choice["name"],
            "record_index": random.randint(0, TOTAL_RECORDS),
            "issue": "Manual Override",
            "severity": "Medium",
            "risk_score": round(random.uniform(0.4, 0.6), 3),
            "detected_at": pd.Timestamp.now()
        })

    while len(final_settlements) < 8:
        sample = EMP_POOL.sample(1).iloc[0]
        arrears = int(sample["net_pay"] * 1.2)
        tax_adj = int(arrears * 0.1)
        final_net = sample["net_pay"] + arrears - tax_adj
        final_settlements.append({
            "settlement_id": str(uuid.uuid4()),
            "emp_id": sample["emp_id"],
            "name": sample["name"],
            "base_net_pay": int(sample["net_pay"]),
            "arrears": arrears,
            "tax_adjustment": tax_adj,
            "final_payout": final_net,
            "approved": True,
            "generated_at": pd.Timestamp.now()
        })

    # Convert to DataFrames
    audit_df = pd.DataFrame(forensic_logs)
    settlement_df = pd.DataFrame(final_settlements)

    def recommend_action(sev, score):
        if sev == "Critical" or score > 0.85:
            return "Immediate Hold & Manual Review"
        if sev == "High" or score > 0.6:
            return "Flag for Audit Team"
        if sev == "Medium":
            return "Auto-check & Reconcile"
        return "Monitor / Low Priority"

    audit_df["recommended_action"] = audit_df.apply(lambda r: recommend_action(r["severity"], r["risk_score"]), axis=1)
    audit_df["detected_at"] = pd.to_datetime(audit_df["detected_at"])

    # Convert to HTML
    audit_html = audit_df.sort_values(by="detected_at", ascending=False).head(8).to_html(classes="table table-bordered", index=False)
    settle_html = settlement_df.sort_values(by="generated_at", ascending=False).head(8).to_html(classes="table table-bordered", index=False)


    return render_template('settlement.html',settle_html=settle_html)

# web page for dispklaing employee quantum_ai

@app.route('/forensic', methods=['GET'])
def forensic():
    if not session.get('logged_in'):
        return redirect(url_for('sign_in', next=request.path))

    import time, random, os, uuid
    import pandas as pd
    import numpy as np

    # Simulation config
    TOTAL_RECORDS = 200_000
    CHUNK_SIZE = 25_000
    EMP_POOL = pd.DataFrame({
        "emp_id": [f"E{100000+i}" for i in range(8000)],
        "name": [f"Emp_{i}" for i in range(8000)],
        "gross_pay": np.random.randint(20000, 250000, size=8000),
    })
    EMP_POOL["deductions"] = (EMP_POOL["gross_pay"] * np.random.uniform(0.05, 0.3, size=8000)).astype(int)
    EMP_POOL["net_pay"] = EMP_POOL["gross_pay"] - EMP_POOL["deductions"]

    records_processed = 0
    anomalies_found = 0
    quantum_progress = 0
    encryption_progress = 0
    forensic_logs = []
    final_settlements = []

    # Main simulation loop
    while records_processed < TOTAL_RECORDS:
        to_process = min(CHUNK_SIZE, TOTAL_RECORDS - records_processed)
        records_processed += to_process

        base_lambda = np.random.choice([0.1, 0.3, 0.6, 1.2], p=[0.6,0.25,0.1,0.05])
        new_anoms = np.random.poisson(lam=base_lambda * (to_process/10000.0))
        anomalies_found += int(new_anoms)

        quantum_progress = min(100, quantum_progress + random.randint(2,8))
        encryption_progress = min(100, encryption_progress + random.randint(3,12))

        for _ in range(int(new_anoms)):
            choice = EMP_POOL.sample(1).iloc[0]
            severity = random.choices(["Low","Medium","High","Critical"], weights=[55,28,12,5])[0]
            score = round(random.uniform(0.4, 0.99) if severity in ["High","Critical"] else random.uniform(0.05,0.6), 3)
            issue = random.choice([
                "Duplicate Payment", "Salary Spike", "Tax Mismatch", "Inactive Employee Paid",
                "Bank Account Mismatch", "Overtime Fraud", "Incorrect Tax Code", "Manual Override"
            ])
            rec_idx = records_processed - random.randint(0, to_process-1)
            forensic_logs.append({
                "forensic_id": str(uuid.uuid4()),
                "emp_id": choice["emp_id"],
                "name": choice["name"],
                "record_index": int(rec_idx),
                "issue": issue,
                "severity": severity,
                "risk_score": float(score),
                "detected_at": pd.Timestamp.now()
            })

        if random.random() < 0.065:
            sample = EMP_POOL.sample(1).iloc[0]
            arrears = int(sample["net_pay"] * random.uniform(0.1, 2.0))
            tax_adj = int(arrears * random.uniform(0.05, 0.2))
            final_net = max(0, int(sample["net_pay"] + arrears - tax_adj))
            final_settlements.append({
                "settlement_id": str(uuid.uuid4()),
                "emp_id": sample["emp_id"],
                "name": sample["name"],
                "base_net_pay": int(sample["net_pay"]),
                "arrears": arrears,
                "tax_adjustment": tax_adj,
                "final_payout": final_net,
                "approved": random.choice([True, False]),
                "generated_at": pd.Timestamp.now()
            })

    # Ensure minimum data for display
    while len(forensic_logs) < 8:
        choice = EMP_POOL.sample(1).iloc[0]
        forensic_logs.append({
            "forensic_id": str(uuid.uuid4()),
            "emp_id": choice["emp_id"],
            "name": choice["name"],
            "record_index": random.randint(0, TOTAL_RECORDS),
            "issue": "Manual Override",
            "severity": "Medium",
            "risk_score": round(random.uniform(0.4, 0.6), 3),
            "detected_at": pd.Timestamp.now()
        })

    while len(final_settlements) < 8:
        sample = EMP_POOL.sample(1).iloc[0]
        arrears = int(sample["net_pay"] * 1.2)
        tax_adj = int(arrears * 0.1)
        final_net = sample["net_pay"] + arrears - tax_adj
        final_settlements.append({
            "settlement_id": str(uuid.uuid4()),
            "emp_id": sample["emp_id"],
            "name": sample["name"],
            "base_net_pay": int(sample["net_pay"]),
            "arrears": arrears,
            "tax_adjustment": tax_adj,
            "final_payout": final_net,
            "approved": True,
            "generated_at": pd.Timestamp.now()
        })

    # Convert to DataFrames
    audit_df = pd.DataFrame(forensic_logs)
    settlement_df = pd.DataFrame(final_settlements)

    def recommend_action(sev, score):
        if sev == "Critical" or score > 0.85:
            return "Immediate Hold & Manual Review"
        if sev == "High" or score > 0.6:
            return "Flag for Audit Team"
        if sev == "Medium":
            return "Auto-check & Reconcile"
        return "Monitor / Low Priority"

    audit_df["recommended_action"] = audit_df.apply(lambda r: recommend_action(r["severity"], r["risk_score"]), axis=1)
    audit_df["detected_at"] = pd.to_datetime(audit_df["detected_at"])

    # Convert to HTML
    audit_html = audit_df.sort_values(by="detected_at", ascending=False).head(8).to_html(classes="table table-bordered", index=False)
    settle_html = settlement_df.sort_values(by="generated_at", ascending=False).head(8).to_html(classes="table table-bordered", index=False)

    return render_template("forensic.html",
        records_processed=records_processed,
        anomalies_found=anomalies_found,
        quantum_progress=quantum_progress,
        encryption_progress=encryption_progress,
        audit_html=audit_html,
        settle_html=settle_html
    )

@app.route('/demo_signin', methods=['GET', 'POST'])
def demo_signin():
    return render_template('demo_signin.html')

# Uploading file

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"message": "❌ No file part in request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "❌ No file selected."}), 400

    if file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        return jsonify({"message": f"✅ File saved as: {filename}"})

    return jsonify({"message": "❌ Upload failed."}), 500

# download file
@app.route("/generate-pdf", methods=["GET"])
def generate_pdf():
    pdf_buffer, result = build_payroll_pdf(upload_dir="uploads")
    if pdf_buffer is None:
        return jsonify({"error": result}), 400
    return send_file(pdf_buffer, mimetype="application/pdf",
                     as_attachment=True, download_name=result)


#  Post-Quantum Cryptography

@app.route("/encrypt", methods=["POST"])
def encrypt_message():
    data = request.get_json()          # data is a dict
    message = data.get("message", "")  # safely get the message string
    encrypt, decrypt = pqc(message)    # pass the actual string
    return jsonify({"enc": encrypt, "dec": decrypt})

# Quantum-Safe Digital Signatures 
# --- Sign In Route ---

@app.route("/security_sign")
def security_sign():
    return render_template("security_sign.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    stmt = select(employee_detail).where(
            and_(
                or_(
                    employee_detail.EmployeeID == username,
                    employee_detail.email == username
                ),
            employee_detail.EmployeeID == password
            )
        )
    result = db.session.execute(stmt).fetchone()

    if result:
        user = result[0]  # ✅ Define 'user' only if result exists
        session['username_qsign'] = user.EmployeeID
        session["signed_in"] = True
        return jsonify({"status": "success", "redirect": url_for("home")})
    return jsonify({"status": "error"}), 401

@app.route("/check_session")
def check_session():
    return jsonify({"signed_in": bool(session.get("signed_in"))})

@app.route("/upload_from_web", methods=["POST"])
def upload_file_from_web():
    if "file" not in request.files:
        return jsonify({"message": "No file uploaded"}), 400

    file = request.files["file"]

    import os
    os.makedirs("./signature_upload", exist_ok=True)

    # Save uploaded file
    filepath = os.path.join("./signature_upload", file.filename)
    file.save(filepath)
    print("File saved:", filepath)

    # Get most recent file in upload folder
    folder = r"C:\Users\paran\vsc\final_project\Final_Year_project\flask 3.0\signature_upload"
    latest_file = max(
        (os.path.join(folder, f) for f in os.listdir(folder)),
        key=os.path.getmtime
    )

    employee_id = session.get("username_qsign")
    signature, public_key, data,public_key_to_display = qds_sign(latest_file, employee_id)
   

    # Create a dedicated subfolder for this file inside signed_files
    base_name = os.path.splitext(os.path.basename(latest_file))[0]
    target_folder = os.path.join("./signed_files", base_name)
    os.makedirs(target_folder, exist_ok=True)

    # Build paths inside the subfolder
    signed_filepath = os.path.join(target_folder, f"signed_{base_name}.bin")
    sig_path = os.path.join(target_folder, f"{base_name}.sig")
    pubkey_path = os.path.join(target_folder, f"{base_name}.pub")

    # Save signed file data
    with open(signed_filepath, "wb") as f:
        f.write(data)

    # Save signature separately
    with open(sig_path, "wb") as f:
        f.write(signature)

    # Save public key separately
    with open(pubkey_path, "wb") as f:
        f.write(public_key)

    print("Signed file saved in:", target_folder)

    return jsonify({
    "message": f"File {file.filename} uploaded and signed successfully",
    "public_key": public_key_to_display
    })


@app.route("/verify_file", methods=["GET", "POST"])
def verify_file_route():
    if request.method == "POST":
        signature = request.files.get("signature")
        public_key = request.files.get("public_key")
        document = request.files.get("document")

        if not signature or not public_key or not document:
            return jsonify({"message": "Missing files", "status": "error"}), 400

        signature_bytes = signature.read()
        public_key_bytes = public_key.read()
        document_bytes = document.read()

        valid = verify_file(document_bytes, signature_bytes, public_key_bytes)

        # Return JSON for AJAX requests
        return jsonify({
            "message": "Signature verified successfully" if valid else "Signature verification failed",
            "status": "success" if valid else "failure"
        })

    # For GET requests (like when you visit /verify_file in the browser),
    # render the HTML template
    return render_template("verify_document.html")

@app.route("/qkd", methods=["GET", "POST"])
def qkd():
    if not session.get('logged_in'):
        # The current URL path (e.g., '/payroll') is attached 
        # as the value for the 'next' parameter.
        return redirect(url_for('sign_in', next=request.path)) 
    return render_template('qkd_test.html')


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.run(debug=True)