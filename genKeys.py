import os
import random
import string
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption, BestAvailableEncryption

# generate pub/priv key pair files
privKey1 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
passPhrase = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(32))
bytesPhrase = str.encode(passPhrase, 'utf-8')
privKey1PEM = privKey1.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, BestAvailableEncryption(bytesPhrase))
with open("keys/_PRIV_KEY.pem", "wb") as privPEM1:
    privPEM1.write(privKey1PEM)
    privPEM1.close()

with open("keys/_PRIV_PASSWORD.txt", "w") as privPass:
    privPass.write(passPhrase)
    privPass.close()

pubKey1 = privKey1.public_key()
pubKey1PEM = pubKey1.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

with open("keys/_PUB_KEY.pem", "wb") as pubPEM1:
    pubPEM1.write(pubKey1PEM)
    pubPEM1.close()
