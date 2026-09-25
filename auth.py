from datetime import datetime, timedelta, timezone
from jose import jwt
import bcrypt

# Ayarlar
SECRET_KEY = "super_gizli_anahtarim_cok_guvenli"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 1. Düz şifreyi alıp Bcrypt ile doğrudan hash'leyen fonksiyon
def sifre_hashle(sifre: str) -> str:
    # bcrypt metinleri bayt (bytes) olarak işler, şifreyi 72 bayt ile sınırlar
    pwd_bytes = sifre.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

# 2. Şifre doğrulama fonksiyonu
def sifre_dogrula(duz_sifre: str, hashli_sifre: str) -> bool:
    pwd_bytes = duz_sifre.encode('utf-8')[:72]
    hash_bytes = hashli_sifre.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)

# 3. JWT Token üretme fonksiyonu
def token_olustur(data: dict) -> str:
    to_encode = data.copy()
    sure_sonu = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": sure_sonu})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)