def qds_sign(file_path,employee_id):
    from sqlalchemy import create_engine, MetaData, Table, select, update, text
    import oqs,ctypes

    
    # Connect to your SQLite database
    engine = create_engine("sqlite:///emp_pay.db")
    metadata = MetaData()
    
    # Reflect the table
    employees = Table("employee_detail", metadata, autoload_with=engine)

    # --- Step 2: Query public_key and secret_key ---
    stmt = (
        select(employees.c.public_key, employees.c.secret_key)
        .where(employees.c.EmployeeID == employee_id)
    )

    with engine.connect() as conn:
        results = conn.execute(stmt).fetchone()

    public_key_hex = results.public_key
    secret_key_hex = results.secret_key

    def load_file_as_bytes(file_path):
        """Read any file (PDF, XML, DOCX, etc.) as bytes"""
        with open(file_path, "rb") as f:
            return f.read()

    def sign_file(file_path, algorithm="Dilithium2"):
        """Sign a file and return signature + public key + file data"""
        data = load_file_as_bytes(file_path)

        with oqs.Signature(algorithm) as signer:
            # Generate key pair
            public_key = bytes.fromhex(public_key_hex)
            secret_key = bytes.fromhex(secret_key_hex)
            secret_key_ctypes = (ctypes.c_ubyte * len(secret_key))(*secret_key)



            signer.secret_key = secret_key_ctypes
            # Sign the file
            signature = signer.sign(data)
            print(f"Signature created for {file_path}, length: {len(signature)}")

            # Return signature, public key, and file data
            return signature, public_key, data
    signature, public_key, data = sign_file(file_path, algorithm="Dilithium2")
    return signature, public_key, data,public_key_hex


def verify_file(data, signature,public_key, algorithm="Dilithium2"):

    
    """Verify a file's signature using the public key"""
    import oqs,ctypes
    public_key_bytes = public_key
    public_key_ctypes = (ctypes.c_ubyte * len(public_key_bytes))(*public_key_bytes)

    verifier = oqs.Signature(algorithm)
    verifier.public_key = public_key_ctypes

    valid = verifier.verify(data, signature,public_key)

    with oqs.Signature(algorithm) as verifier:
        valid = verifier.verify(data, signature, public_key)
        if valid:
            print("✅ Verification successful")
        else:
            print("❌ Verification failed")
        return valid
    

