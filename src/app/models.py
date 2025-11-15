# src/app/models.py
from flask_login import UserMixin
from datetime import datetime
from . import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Financial
    balance = db.Column(db.Float, default=0.0)
    total_deposits = db.Column(db.Float, default=0.0)
    total_withdrawals = db.Column(db.Float, default=0.0)
    total_earnings = db.Column(db.Float, default=0.0)

    # KYC
    kyc_status = db.Column(db.String(20), default='pending')

    # Admin privilege
    is_admin = db.Column(db.Boolean, default=False)

    # Relationships
    kycs = db.relationship('KYCLog', backref='user', lazy=True)
    deposits = db.relationship('Deposit', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.username} | Admin: {self.is_admin}>"


class KYCLog(db.Model):
    __tablename__ = 'kyc_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    id_number = db.Column(db.String(100), nullable=False)
    document_path = db.Column(db.String(300))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<KYCLog User:{self.user_id} Status:{self.status}>"


class Deposit(db.Model):
    __tablename__ = 'deposit'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    amount = db.Column(db.Float, nullable=False)
    network = db.Column(db.String(50), default='TRC20')
    tx_hash = db.Column(db.String(200), nullable=True)

    status = db.Column(db.String(20), default='pending')  
    # statuses: pending ? approved ? credited

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def approve(self):
        """
        Admin approves deposit:
        - Set deposit.status = approved
        - Add to user.balance
        - Add to user.total_deposits
        """
        if self.status == "approved":
            return False  # Avoid double-crediting

        self.status = "approved"
        self.user.balance += self.amount
        self.user.total_deposits += self.amount

        db.session.commit()
        return True

    def __repr__(self):
        return f"<Deposit User:{self.user_id} Amount:{self.amount} Status:{self.status}>"