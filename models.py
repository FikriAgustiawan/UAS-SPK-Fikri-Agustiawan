from sqlalchemy import String, Integer, Column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Gitar(Base):
    __tablename__ = "tbl_gitar"
    no = Column (Integer,primary_key=True)
    nama_gitar = Column (String)
    merk = Column (String)
    berat_gitar = Column (String)
    body_material = Column (String)
    scale_length = Column (String)
    tipe = Column (String)
    harga = Column (Integer)

    def _repr_(self):
        return f"Gitar(nama_gitar={self.nama_gitar!r}, merk={self.merk!r}, berat_gitar={self.berat_gitar!r}, body_material={self.body_material!r}, scale_length={self.scale_length!r}, tipe={self.tipe!r}, harga={self.harga!r})"