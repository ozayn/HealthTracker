from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    google_id = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    profile_pic = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integrations = db.relationship('Integration', back_populates='user', cascade='all, delete-orphan')
    health_data = db.relationship('HealthData', back_populates='user', cascade='all, delete-orphan')
    blood_tests = db.relationship('BloodTest', back_populates='user', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'profile_pic': self.profile_pic,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Integration(db.Model):
    __tablename__ = 'integrations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # fitbit, oura, clue
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='integrations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'is_active': self.is_active,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class HealthData(db.Model):
    __tablename__ = 'health_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    data_type = db.Column(db.String(100), nullable=False)  # steps, heart_rate, sleep, activity, etc.
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float)
    unit = db.Column(db.String(50))
    extra_data = db.Column(db.JSON)  # Additional data specific to provider
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='health_data')
    
    # Indexes for faster queries
    __table_args__ = (
        db.Index('idx_user_date', 'user_id', 'date'),
        db.Index('idx_user_type_date', 'user_id', 'data_type', 'date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'data_type': self.data_type,
            'date': self.date.isoformat() if self.date else None,
            'value': self.value,
            'unit': self.unit,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BloodTest(db.Model):
    __tablename__ = 'blood_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_date = db.Column(db.Date, nullable=False)
    lab_name = db.Column(db.String(255))
    notes = db.Column(db.Text)
    file_path = db.Column(db.String(500))  # Path to uploaded file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='blood_tests')
    markers = db.relationship('BloodMarker', back_populates='blood_test', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'test_date': self.test_date.isoformat() if self.test_date else None,
            'lab_name': self.lab_name,
            'notes': self.notes,
            'file_path': self.file_path,
            'markers': [marker.to_dict() for marker in self.markers],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BloodMarker(db.Model):
    __tablename__ = 'blood_markers'
    
    id = db.Column(db.Integer, primary_key=True)
    blood_test_id = db.Column(db.Integer, db.ForeignKey('blood_tests.id'), nullable=False)
    marker_name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50))
    reference_range_low = db.Column(db.Float)
    reference_range_high = db.Column(db.Float)
    is_abnormal = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    
    # Relationships
    blood_test = db.relationship('BloodTest', back_populates='markers')
    
    def to_dict(self):
        return {
            'id': self.id,
            'marker_name': self.marker_name,
            'value': self.value,
            'unit': self.unit,
            'reference_range_low': self.reference_range_low,
            'reference_range_high': self.reference_range_high,
            'is_abnormal': self.is_abnormal,
            'notes': self.notes
        }

