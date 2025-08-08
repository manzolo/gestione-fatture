from sqlalchemy import Column, Integer, ForeignKey, Float, Boolean, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
import enum # Import the enum module

Base = declarative_base()

from sqlalchemy import Column, Integer, BigInteger, Boolean, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
import enum # Import the enum module

Base = declarative_base()

# Database model definition for requests
class Client(Base):
    __tablename__ = "client"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    address = Column(String(256))
    tax_code = Column(String(64))
    email = Column(String(128))
    phone = Column(String(64))
    invoice_id = Column(Integer, ForeignKey("invoice.id"), nullable=True)

class Invoice(Base):
    __tablename__ = "invoice"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('client.id'), nullable=False)
    number = Column(String(64), nullable=False, unique=True)
    date = Column(String(20), nullable=False)
    due_date = Column(String(20))
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    is_paid = Column(Boolean, default=False)
    item_id = Column(Integer, ForeignKey("invoice_item.id"), nullable=True)

class InvoiceItem(Base):
    __tablename__ = "invoice_item"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoice.id'), nullable=False)
    description = Column(String(256), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
