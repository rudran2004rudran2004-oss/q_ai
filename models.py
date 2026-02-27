# models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, Table

#initializing the SQLAlchemy ORM and linking it to your Flask app
db = SQLAlchemy()

def reflect_tables(app):
    with app.app_context():
        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        print("✅ Available tables:", metadata.tables.keys())

        if 'employee_detail' in metadata.tables:
            employee_detail = Table('employee_detail', metadata, autoload_with=db.engine)
            return employee_detail
        else:
            raise Exception("❌ Table 'employee_detail' not found in metadata.")

#SQLAlchemy ORM Mapping
class employee_detail(db.Model):
    __tablename__ = 'employee_detail'
    EmployeeID = db.Column(db.String, primary_key=True)
    Level = db.Column(db.Text)
    role = db.Column(db.Text)
    Department = db.Column(db.Text)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    JoiningDate = db.Column(db.Text)
    Account_Number = db.Column(db.Integer)
    Phone_Number = db.Column(db.Integer)
    email = db.Column(db.String)

class jan_2025(db.Model):
    __tablename__ = 'January_2025'  # 👈 matches your actual table name
#defines a column in that table and its data type
    EmployeeID=db.Column(db.String, primary_key=True)
    basic= db.Column(db.INTEGER)
    house_allowance= db.Column(db.INTEGER)
    fixed_allowance= db.Column(db.INTEGER)
    tax= db.Column(db.INTEGER)
    deduction = db.Column(db.VARCHAR)
    bonuse = db.Column(db.VARCHAR)
    stack_options = db.Column(db.VARCHAR)
    net_salary= db.Column(db.INTEGER)
    gross_salary= db.Column(db.INTEGER)
    target_to_be_completed = db.Column(db.VARCHAR)
    targets_completed = db.Column(db.VARCHAR)
    WorkingDays= db.Column(db.INTEGER)
    PresentDays= db.Column(db.INTEGER)
    # Add other fields only if needed for querying

class feb_2025(db.Model):
    __tablename__ = 'February_2025'  # 👈 matches your actual table name
#defines a column in that table and its data type
    EmployeeID=db.Column(db.String, primary_key=True)
    basic= db.Column(db.INTEGER)
    house_allowance= db.Column(db.INTEGER)
    fixed_allowance= db.Column(db.INTEGER)
    tax= db.Column(db.INTEGER)
    deduction = db.Column(db.VARCHAR)
    bonuse = db.Column(db.VARCHAR)
    stack_options = db.Column(db.VARCHAR)
    net_salary= db.Column(db.INTEGER)
    gross_salary= db.Column(db.INTEGER)
    target_to_be_completed = db.Column(db.VARCHAR)
    targets_completed = db.Column(db.VARCHAR)
    WorkingDays= db.Column(db.INTEGER)
    PresentDays= db.Column(db.INTEGER)

class mar_2025(db.Model):
    __tablename__ = 'March_2025'  # 👈 matches your actual table name
#defines a column in that table and its data type
    EmployeeID=db.Column(db.String, primary_key=True)
    basic= db.Column(db.INTEGER)
    house_allowance= db.Column(db.INTEGER)
    fixed_allowance= db.Column(db.INTEGER)
    tax= db.Column(db.INTEGER)
    deduction = db.Column(db.VARCHAR)
    bonuse = db.Column(db.VARCHAR)
    stack_options = db.Column(db.VARCHAR)
    net_salary= db.Column(db.INTEGER)
    gross_salary= db.Column(db.INTEGER)
    target_to_be_completed = db.Column(db.VARCHAR)
    targets_completed = db.Column(db.VARCHAR)
    WorkingDays= db.Column(db.INTEGER)
    PresentDays= db.Column(db.INTEGER)
class apr_2025(db.Model):
    __tablename__ = 'April_2025'
    EmployeeID = db.Column(db.String, primary_key=True)
    basic = db.Column(db.Integer)
    house_allowance = db.Column(db.Integer)
    fixed_allowance = db.Column(db.Integer)
    tax = db.Column(db.Integer)
    deduction = db.Column(db.String)
    bonuse = db.Column(db.String)
    stack_options = db.Column(db.String)
    net_salary = db.Column(db.Integer)
    gross_salary = db.Column(db.Integer)
    target_to_be_completed = db.Column(db.String)
    targets_completed = db.Column(db.String)
    WorkingDays = db.Column(db.Integer)
    PresentDays = db.Column(db.Integer)

class may_2025(db.Model):
    __tablename__ = 'May_2025'
    EmployeeID = db.Column(db.String, primary_key=True)
    basic = db.Column(db.Integer)
    house_allowance = db.Column(db.Integer)
    fixed_allowance = db.Column(db.Integer)
    tax = db.Column(db.Integer)
    deduction = db.Column(db.String)
    bonuse = db.Column(db.String)
    stack_options = db.Column(db.String)
    net_salary = db.Column(db.Integer)
    gross_salary = db.Column(db.Integer)
    target_to_be_completed = db.Column(db.String)
    targets_completed = db.Column(db.String)
    WorkingDays = db.Column(db.Integer)
    PresentDays = db.Column(db.Integer)

class jun_2025(db.Model):
    __tablename__ = 'June_2025'
    EmployeeID = db.Column(db.String, primary_key=True)
    basic = db.Column(db.Integer)
    house_allowance = db.Column(db.Integer)
    fixed_allowance = db.Column(db.Integer)
    tax = db.Column(db.Integer)
    deduction = db.Column(db.String)
    bonuse = db.Column(db.String)
    stack_options = db.Column(db.String)
    net_salary = db.Column(db.Integer)
    gross_salary = db.Column(db.Integer)
    target_to_be_completed = db.Column(db.String)
    targets_completed = db.Column(db.String)
    WorkingDays = db.Column(db.Integer)
    PresentDays = db.Column(db.Integer)

class jul_2025(db.Model):
    __tablename__ = 'July_2025'
    EmployeeID = db.Column(db.String, primary_key=True)
    basic = db.Column(db.Integer)
    house_allowance = db.Column(db.Integer)
    fixed_allowance = db.Column(db.Integer)
    tax = db.Column(db.Integer)
    deduction = db.Column(db.String)
    bonuse = db.Column(db.String)
    stack_options = db.Column(db.String)
    net_salary = db.Column(db.Integer)
    gross_salary = db.Column(db.Integer)
    target_to_be_completed = db.Column(db.String)
    targets_completed = db.Column(db.String)
    WorkingDays = db.Column(db.Integer)
    PresentDays = db.Column(db.Integer)

class aug_2025(db.Model):
    __tablename__ = 'August_2025'
    EmployeeID = db.Column(db.String, primary_key=True)
    basic = db.Column(db.Integer)
    house_allowance = db.Column(db.Integer)
    fixed_allowance = db.Column(db.Integer)
    tax = db.Column(db.Integer)
    deduction = db.Column(db.String)
    bonuse = db.Column(db.String)
    stack_options = db.Column(db.String)
    net_salary = db.Column(db.Integer)
    gross_salary = db.Column(db.Integer)
    target_to_be_completed = db.Column(db.String)
    targets_completed = db.Column(db.String)
    WorkingDays = db.Column(db.Integer)
    PresentDays = db.Column(db.Integer)

class sep_2025(db.Model):
    __tablename__ = 'September_2025'
    EmployeeID = db.Column(db.String, primary_key=True)
    basic = db.Column(db.Integer)
    house_allowance = db.Column(db.Integer)
    fixed_allowance = db.Column(db.Integer)
    tax = db.Column(db.Integer)
    deduction = db.Column(db.String)
    bonuse = db.Column(db.String)
    stack_options = db.Column(db.String)
    net_salary = db.Column(db.Integer)
    gross_salary = db.Column(db.Integer)
    target_to_be_completed = db.Column(db.String)
    targets_completed = db.Column(db.String)
    WorkingDays = db.Column(db.Integer)
    PresentDays = db.Column(db.Integer)

class oct_2025(db.Model):
    __tablename__ = 'October_2025'
    EmployeeID = db.Column(db.String, primary_key=True)
    basic = db.Column(db.Integer)
    house_allowance = db.Column(db.Integer)
    fixed_allowance = db.Column(db.Integer)
    tax = db.Column(db.Integer)
    deduction = db.Column(db.String)
    bonuse = db.Column(db.String)
    stack_options = db.Column(db.String)
    net_salary = db.Column(db.Integer)
    gross_salary = db.Column(db.Integer)
    target_to_be_completed = db.Column(db.String)
    targets_completed = db.Column(db.String)
    WorkingDays = db.Column(db.Integer)
    PresentDays = db.Column(db.Integer)

class nov_2025(db.Model):
    __tablename__ = 'November_2025'
    EmployeeID = db.Column(db.String, primary_key=True)
    basic = db.Column(db.Integer)
    house_allowance = db.Column(db.Integer)
    fixed_allowance = db.Column(db.Integer)
    tax = db.Column(db.Integer)
    deduction = db.Column(db.String)
    bonuse = db.Column(db.String)
    stack_options = db.Column(db.String)
    net_salary = db.Column(db.Integer)
    gross_salary = db.Column(db.Integer)
    target_to_be_completed = db.Column(db.String)
    targets_completed = db.Column(db.String)
    WorkingDays = db.Column(db.Integer)
    PresentDays = db.Column(db.Integer)

class dec_2025(db.Model):
    __tablename__ = 'December_2025'
    EmployeeID = db.Column(db.String, primary_key=True)
    basic = db.Column(db.Integer)
    house_allowance = db.Column(db.Integer)
    fixed_allowance = db.Column(db.Integer)
    tax = db.Column(db.Integer)
    deduction = db.Column(db.String)
    bonuse = db.Column(db.String)
    stack_options = db.Column(db.String)
    net_salary = db.Column(db.Integer)
    gross_salary = db.Column(db.Integer)
    target_to_be_completed = db.Column(db.String)
    targets_completed = db.Column(db.String)
    WorkingDays = db.Column(db.Integer)
    PresentDays = db.Column(db.Integer)