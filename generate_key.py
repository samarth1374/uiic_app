from cryptography.fernet import Fernet

key = Fernet.generate_key()
with open("fernet_key.key", "wb") as f:
    f.write(key)

print("✅ Master Fernet key created as fernet_key.key")
