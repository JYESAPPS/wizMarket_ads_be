# app/utils/kcb_crypto.py
import base64
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad


def _hex_iv_to_bytes(iv_hex: str) -> bytes:
    iv_hex = (iv_hex or "").strip()
    if len(iv_hex) != 32:
        raise ValueError("IV must be 32-hex (16 bytes)")
    return bytes.fromhex(iv_hex)

def _pkcs7_unpad(b: bytes) -> bytes:
    return unpad(b, 16, style='pkcs7')

def aes_cbc_pkcs7_b64_decrypt(b64_text: str, key: bytes, iv: bytes) -> bytes:
    data = base64.b64decode(b64_text)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    dec = cipher.decrypt(data)
    return _pkcs7_unpad(dec)

def derive_personal_key_from_enc_key(enc_key_b64: str, member_code: str, iv_hex: str) -> bytes:
    """
    step1: temp_key = 회원사코드(12) + '0000' (16바이트)
           enc_key_b64를 AES-CBC-PKCS7로 복호화 → 결과는 HEX(32) 문자열
           → bytes.fromhex(...) 하면 16바이트 개인키
    """
    temp_key = (member_code + "0000").encode("utf-8")  # 16 bytes
    iv = _hex_iv_to_bytes(iv_hex)
    dec_hex = aes_cbc_pkcs7_b64_decrypt(enc_key_b64, temp_key, iv).decode("ascii").strip()
    # dec_hex는 32-HEX (= 16 bytes key)
    return bytes.fromhex(dec_hex)
