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
    """
    Health Data Model - PRESERVES ALL HISTORICAL USER DATA

    Data Retention Policy:
    - All health data is permanently stored per user
    - Data is never automatically deleted
    - Each record represents a unique measurement
    - Updates only occur for same date/type/provider combinations
    - Historical trends are always available for analysis
    """
    __tablename__ = 'health_data'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # oura, fitbit, clue, future sources
    data_type = db.Column(db.String(100), nullable=False)  # steps, heart_rate, sleep, temperature, etc.
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float)
    unit = db.Column(db.String(50))  # steps, bpm, hours, °C, %, etc.
    extra_data = db.Column(db.JSON)  # Additional provider-specific metadata
    source_version = db.Column(db.String(50))  # API version or data source version
    data_quality = db.Column(db.String(20))  # high, medium, low confidence in data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='health_data')

    # Indexes for optimal query performance
    __table_args__ = (
        db.Index('idx_user_date', 'user_id', 'date'),
        db.Index('idx_user_type_date', 'user_id', 'data_type', 'date'),
        db.Index('idx_user_provider', 'user_id', 'provider'),
        db.Index('idx_user_provider_date', 'user_id', 'provider', 'date'),
        db.Index('idx_user_provider_type', 'user_id', 'provider', 'data_type'),
        # Unique constraint prevents duplicate entries for same user/date/type/provider
        db.UniqueConstraint('user_id', 'provider', 'data_type', 'date', name='unique_user_provider_type_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'data_type': self.data_type,
            'date': self.date.isoformat() if self.date else None,
            'value': self.value,
            'unit': self.unit,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None
        }

    @staticmethod
    def get_user_data_summary(user_id):
        """Get comprehensive data summary for a user"""
        from sqlalchemy import func

        # Count records by provider and type
        provider_counts = db.session.query(
            HealthData.provider,
            HealthData.data_type,
            func.count(HealthData.id).label('count'),
            func.min(HealthData.date).label('earliest_date'),
            func.max(HealthData.date).label('latest_date')
        ).filter_by(user_id=user_id).group_by(
            HealthData.provider, HealthData.data_type
        ).all()

        # Get date range for user's data
        date_range = db.session.query(
            func.min(HealthData.date).label('first_date'),
            func.max(HealthData.date).label('last_date'),
            func.count(HealthData.id).label('total_records')
        ).filter_by(user_id=user_id).first()

        return {
            'total_records': date_range.total_records if date_range else 0,
            'date_range': {
                'first_date': date_range.first_date.isoformat() if date_range and date_range.first_date else None,
                'last_date': date_range.last_date.isoformat() if date_range and date_range.last_date else None,
            },
            'providers': [{
                'provider': p.provider,
                'data_type': p.data_type,
                'record_count': p.count,
                'date_range': {
                    'earliest': p.earliest_date.isoformat() if p.earliest_date else None,
                    'latest': p.latest_date.isoformat() if p.latest_date else None,
                }
            } for p in provider_counts]
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

