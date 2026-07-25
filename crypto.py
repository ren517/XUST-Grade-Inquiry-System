from cryptography.fernet import Fernet
import os

KEY_FILE = "key.key"


def load_key():

    if not os.path.exists(KEY_FILE):

        key = Fernet.generate_key()

        with open(KEY_FILE, "wb") as f:
            f.write(key)

    with open(KEY_FILE, "rb") as f:

        return f.read()


fernet = Fernet(load_key())


def encrypt_password(password):

    encrypted = fernet.encrypt(password.encode("utf-8"))

    return encrypted.decode("utf-8")


def decrypt_password(password):

    decrypted = fernet.decrypt(password.encode("utf-8"))

    return decrypted.decode("utf-8")
