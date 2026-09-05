from datetime import datetime
from database.db import db


class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_value(cls, key, default=None):
        record = cls.query.filter_by(setting_key=key).first()
        return record.setting_value if record else default

    @classmethod
    def set_value(cls, key, value, description=None):
        record = cls.query.filter_by(setting_key=key).first()
        if record:
            record.setting_value = str(value)
            if description:
                record.description = description
        else:
            record = cls(setting_key=key, setting_value=str(value), description=description)
            db.session.add(record)
        db.session.commit()
        return record
