from sqlalchemy import Column, Integer, String, Boolean, ARRAY, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

# SINGLE Base declaration
Base = declarative_base()

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    display_name = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password = Column(String)
    tenant_id = Column(Integer, ForeignKey('tenants.id'))
    
    # This ensures username is unique PER TENANT (correct implementation)
    __table_args__ = (
        UniqueConstraint('username', 'tenant_id', name='user_tenant_uc'),
    )

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    answer = Column(Boolean)
    tenant_id = Column(Integer, ForeignKey('tenants.id'))

class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"
    id = Column(Integer, primary_key=True, index=True)
    answers = Column(ARRAY(Boolean))
    score = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    tenant_id = Column(Integer, ForeignKey('tenants.id'))