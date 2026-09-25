from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from jose import JWTError, jwt

import models
import auth
from database import engine, get_db

# Veritabanında henüz olmayan tabloları (kullanicilar) otomatik oluşturur
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# --- PYDANTIC ŞEMALARI (Gelen/Giden Veri Kalıpları) ---
class KullaniciKayit(BaseModel):
    kullanici_adi: str
    sifre: str

class KullaniciYanit(BaseModel):
    id: int
    kullanici_adi: str

    class Config:
        from_attributes = True

class TokenYanit(BaseModel):
    access_token: str
    token_type: str

class UrunIstek(BaseModel):
    isim: str
    fiyat: float
    stokta_mi: bool = True
    aciklama: Optional[str] = None

class UrunYanit(BaseModel):
    id: int
    isim: str
    fiyat: float
    stokta_mi: bool
    aciklama: Optional[str] = None

    class Config:
        from_attributes = True


# --- GÜVENLİK KONTROLÜ (Korumalı kapıların bekçisi) ---
def token_kontrol(token: str = Depends(oauth2_scheme)):
    kimlik_hatasi = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz veya süresi dolmuş token!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise kimlik_hatasi
        return username
    except JWTError:
        raise kimlik_hatasi


# ==========================================
# 1. AUTH KAPILARI (Kayıt Ol & Giriş Yap)
# ==========================================

# KAYIT OLMA ENDPOINT'İ (POST /register)
@app.post("/register", response_model=KullaniciYanit, status_code=status.HTTP_201_CREATED)
def kayit_ol(kullanici_bilgi: KullaniciKayit, db: Session = Depends(get_db)):
    # 1. Aynı kullanıcı adı daha önce alınmış mı?
    mevcut_kullanici = db.query(models.Kullanici).filter(models.Kullanici.kullanici_adi == kullanici_bilgi.kullanici_adi).first()
    if mevcut_kullanici:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu kullanıcı adı zaten alınmış!")

    # 2. Şifreyi Bcrypt ile hash'le (kıymaya çevir)
    guvenli_sifre = auth.sifre_hashle(kullanici_bilgi.sifre)

    # 3. Veritabanına kaydet
    yeni_kullanici = models.Kullanici(
        kullanici_adi=kullanici_bilgi.kullanici_adi,
        sifre=guvenli_sifre
    )
    db.add(yeni_kullanici)
    db.commit()
    db.refresh(yeni_kullanici)

    return yeni_kullanici


# GİRİŞ YAPMA ENDPOINT'İ (POST /login)
@app.post("/login", response_model=TokenYanit)
def giris_yap(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Kullanıcı veritabanında var mı?
    kullanici = db.query(models.Kullanici).filter(models.Kullanici.kullanici_adi == form_data.username).first()
    
    # 2. Kullanıcı yoksa veya şifre eşleşmiyorsa hata ver
    if not kullanici or not auth.sifre_dogrula(form_data.password, kullanici.sifre):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kullanıcı adı veya şifre hatalı!"
        )

    # 3. Her şey doğruysa 30 dakikalık JWT token bas
    token = auth.token_olustur(data={"sub": kullanici.kullanici_adi})
    return {"access_token": token, "token_type": "bearer"}


# ==========================================
# 2. ÜRÜN KAPILARI (CRUD)
# ==========================================

# Herkese Açık: Ürünleri Listele
@app.get("/urunler", response_model=List[UrunYanit])
def urunleri_listele(db: Session = Depends(get_db)):
    return db.query(models.Urun).all()

# Herkese Açık: Tek Ürün Getir
@app.get("/urunler/{urun_id}", response_model=UrunYanit)
def urun_getir(urun_id: int, db: Session = Depends(get_db)):
    urun = db.query(models.Urun).filter(models.Urun.id == urun_id).first()
    if not urun:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı!")
    return urun

# KORUMALI: Ürün Ekle (Sadece token ile)
@app.post("/urunler", response_model=UrunYanit, status_code=status.HTTP_201_CREATED)
def urun_ekle(gelen_veri: UrunIstek, db: Session = Depends(get_db), aktif_kullanici: str = Depends(token_kontrol)):
    yeni_urun = models.Urun(
        isim=gelen_veri.isim,
        fiyat=gelen_veri.fiyat,
        stokta_mi=gelen_veri.stokta_mi,
        aciklama=gelen_veri.aciklama
    )
    db.add(yeni_urun)
    db.commit()
    db.refresh(yeni_urun)
    return yeni_urun

# KORUMALI: Ürün Güncelle (Sadece token ile)
@app.put("/urunler/{urun_id}", response_model=UrunYanit)
def urun_guncelle(urun_id: int, guncel_veri: UrunIstek, db: Session = Depends(get_db), aktif_kullanici: str = Depends(token_kontrol)):
    urun = db.query(models.Urun).filter(models.Urun.id == urun_id).first()
    if not urun:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı!")
    
    urun.isim = guncel_veri.isim
    urun.fiyat = guncel_veri.fiyat
    urun.stokta_mi = guncel_veri.stokta_mi
    urun.aciklama = guncel_veri.aciklama
    
    db.commit()
    db.refresh(urun)
    return urun

# KORUMALI: Ürün Sil (Sadece token ile)
@app.delete("/urunler/{urun_id}")
def urun_sil(urun_id: int, db: Session = Depends(get_db), aktif_kullanici: str = Depends(token_kontrol)):
    urun = db.query(models.Urun).filter(models.Urun.id == urun_id).first()
    if not urun:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı!")
    
    db.delete(urun)
    db.commit()
    return {"mesaj": f"{urun_id} numaralı ürün silindi."}