from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
# Postgres.app varsayılan bağlantı adresi:
# postgresql://kullanici_adi:sifre@host:port/veritabani_adi
# 'localhost' yerine 'host.docker.internal' yazıyoruz:
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://postgres:postgres@db:5432/fastapi_db"
# Veritabanı motorunu oluşturuyoruz
engine = create_engine(SQLALCHEMY_DATABASE_URL)
#Veritabanıyla konuşacağımız herbir işlem seansı (oturum)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#veritabanı modellerimizin miras alacağı anasınıf 
Base = declarative_base()
#FastAPI endpointlerine  veritabanı bağlantısını sağlayan fonksiyon
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
