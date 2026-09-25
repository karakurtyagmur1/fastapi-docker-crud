from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base
class Urun(Base):
    __tablename__ ="urunler"
    id =Column(Integer, primary_key=True, index=True)
    isim = Column(String, nullable=False)
    fiyat = Column(Float, nullable=False)
    stokta_mi = Column(Boolean, default=True)
    aciklama = Column(String, nullable=True)

class Kullanici(Base):
    __tablename__ = "kullanicilar"

    id = Column(Integer, primary_key= True, index= True)
    kullanici_adi = Column(String, unique=True, index=True)
    sifre = Column(String, nullable=False) #buraya hashlenmiş şifre gelcek