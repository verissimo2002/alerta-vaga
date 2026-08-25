from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), index=True, nullable=False)
    email = Column(String(255), nullable=False)
    telefone = Column(String(20), nullable=False)
    servico = Column(String(100), nullable=False)
    numero_passaporte = Column(String(50), nullable=True)
    codigo_consulado = Column(String(100),
