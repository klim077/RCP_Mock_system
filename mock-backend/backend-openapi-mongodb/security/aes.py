from Crypto.Cipher import AES
import random
import string

# This is a 16 char key
# TODO: Remove from source control
key = 'SmartGym AES Key'

cipher = AES.new(key, AES.MODE_CBC, key)


def encrypt(value: str) -> str:
    cipher = AES.new(key, AES.MODE_CBC, key)
    salted = ''.join(random.choice(string.ascii_uppercase +
                     string.ascii_lowercase + string.digits) for _ in range(8))
    saltedtext = value + salted
    # TODO: Check for blocks of 16 before encrypt
    ciphertext = cipher.encrypt(saltedtext)
    return ciphertext


def decrypt(value: str) -> str:
    if (not isinstance(value, (bytes, bytearray))):
        return value
    cipher = AES.new(key, AES.MODE_CBC, key)
    result = cipher.decrypt(value)
    # Returns result without last 8 char (i.e. salt)
    return str(result[:-8], 'utf-8')
