from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

# generate pub/priv key pair files
privKey1 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
privKey1PEM = privKey1.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
with open("keys/_PRIV_KEY.pem", "wb") as privPEM1:
    privPEM1.write(privKey1PEM)
    privPEM1.close()

pubKey1 = privKey1.public_key()
pubKey1PEM = pubKey1.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

with open("keys/_PUB_KEY.pem", "wb") as pubPEM1:
    pubPEM1.write(pubKey1PEM)
    pubPEM1.close()
