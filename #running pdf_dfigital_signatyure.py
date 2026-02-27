#running pdf_dfigital_signatyure.py

# Example usage
from  pdf_digital_signature import qds_sign,verify_file

employee_id="EMP0000001"
file_path="C:/vsc/final_project/Final_Year_project/flask 3.0/Quantum_report_20251126_090409.pdf"
signature, public_key_hex, data = qds_sign(file_path, employee_id)

print("Signature (hex):", signature.hex()[:64], "...")  # truncated
print("Public Key (hex):", public_key_hex[:64], "...")  # truncated

valid = verify_file(data, signature,public_key_hex)

if valid:
    print("File signature verified ✅")
else:
    print("File signature invalid ❌")