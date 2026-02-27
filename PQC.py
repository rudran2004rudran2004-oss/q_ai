def pqc(text):
    import oqs, base64
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad

    kem = oqs.KeyEncapsulation("Kyber512")
    public_key = kem.generate_keypair()
    ciphertext, shared_secret_enc = kem.encap_secret(public_key)

    kem_dec = oqs.KeyEncapsulation("Kyber512", kem.export_secret_key())
    shared_secret_dec = kem_dec.decap_secret(ciphertext)

    print("Shared secrets match:", shared_secret_enc == shared_secret_dec)

    aes_key = shared_secret_enc[:32]  # AES-256 key
    message = text.encode()           # ✅ encode string to bytes
    cipher = AES.new(aes_key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(message, AES.block_size))

    encrypted_blob = base64.b64encode(cipher.iv + ct_bytes).decode()

    iv = cipher.iv
    cipher_dec = AES.new(aes_key, AES.MODE_CBC, iv)
    pt = unpad(cipher_dec.decrypt(ct_bytes), AES.block_size).decode()

    return encrypted_blob, pt



def quantum_safe_signature(message: str):
    import oqs
    # Initialize a quantum-safe signature scheme (Dilithium2)
    sig = oqs.Signature("Dilithium2")

    # Generate keypair
    public_key = sig.generate_keypair()
    secret_key = sig.export_secret_key()

    # Sign the message
    signature = sig.sign(message.encode())

    # Verify the signature
    is_valid = sig.verify(message.encode(), signature, public_key)

    # Print results

    # Return values if needed
    return {
        "public_key": public_key.hex(),
        "signature": signature.hex(),
        "valid": is_valid
    }

# Example usage
quantum_safe_signature("srisriram")