from sqlalchemy import create_engine, MetaData, Table, select, update, text
import oqs

# Connect to your SQLite database
engine = create_engine("sqlite:///emp_pay.db")
metadata = MetaData()

# Reflect the table
employees = Table("employee_detail", metadata, autoload_with=engine)

# --- Step 1: Ensure columns exist ---
with engine.begin() as conn:
    # Add signature_scheme column if missing
    if "signature_scheme" not in employees.c:
        conn.execute(text("ALTER TABLE employee_detail ADD COLUMN signature_scheme TEXT"))
    # Add public_key column if missing
    if "public_key" not in employees.c:
        conn.execute(text("ALTER TABLE employee_detail ADD COLUMN public_key TEXT"))
    if "secret_key" not in employees.c:
        conn.execute(text("ALTER TABLE employee_detail ADD COLUMN secret_key TEXT"))

# Refresh metadata after altering
metadata = MetaData()
employees = Table("employee_detail", metadata, autoload_with=engine)

# --- Step 2: Query EmployeeID and Department ---
stmt = select(employees.c.EmployeeID, employees.c.Department)
with engine.connect() as conn:
    results = conn.execute(stmt).fetchall()

employeeid = [row.EmployeeID for row in results]
dept = [row.Department for row in results]

# Collect unique departments
unique_depts = []
for h in dept:
    if h not in unique_depts:
        unique_depts.append(h)
print("Departments:", unique_depts)

# Collect HR employee IDs
eid = []
for i, j in zip(employeeid, dept):
    if j == "HR":
        eid.append(i)
        print("HR Employee:", i)
print("Total HR employees:", len(eid))

# --- Step 3: Generate keys ---
secret_keys = []  # keep secret keys in memory only

with engine.begin() as conn:  # begin transaction
    for empid in eid:
        sig = oqs.Signature("Dilithium2")
        public_key = sig.generate_keypair()
        secret_key = sig.export_secret_key()

        # Update DB with scheme + public key only
        stmt = (
            update(employees)
            .where(employees.c.EmployeeID == empid)
            .values(
                signature_scheme="Dilithium2",
                public_key=public_key.hex(),
                secret_key=secret_key.hex()
            )
        )
        conn.execute(stmt)

        # Keep secret key in memory list
        secret_keys.append((empid, secret_key.hex()))

        print(f"Public key stored for EmployeeID {empid}")

# --- Step 4: Print secret keys list ---
print("\nSecret keys (in memory only):")
for empid, sk in secret_keys:
    print(f"EmployeeID {empid}: {sk[:64]}...")  # truncated for readability'''

