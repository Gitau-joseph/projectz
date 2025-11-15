from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import qrcode
import math

from . import db
from .models import User, KYCLog, Deposit
from .config import WEEKLY_INTEREST_RATE, MIN_INVEST_DAYS

main = Blueprint('main', __name__)

# Upload directory for KYC documents + QR codes
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ===============================
# PUBLIC ROUTES
# ===============================

@main.route('/')
def home():
    return render_template('home.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        exists = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if exists:
            flash("Username or email already exists.", "danger")
            return redirect(url_for('main.register'))

        hashed = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for('main.login'))

    return render_template('register.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for('main.login'))

        login_user(user)
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('main.login'))


# ===============================
# USER DASHBOARD
# ===============================

@main.route('/dashboard')
@login_required
def dashboard():
    latest_kyc = KYCLog.query.filter_by(user_id=current_user.id) \
                             .order_by(KYCLog.id.desc()).first()

    deposits = Deposit.query.filter_by(user_id=current_user.id) \
                            .order_by(Deposit.timestamp.desc()).all()

    now = datetime.utcnow()

    # Compute deposit interest and withdrawal eligibility
    deposit_info = []
    total_earnings = 0
    for dep in deposits:
        if dep.status == "approved":
            weeks_elapsed = (now - dep.timestamp).days / 7
            interest = dep.amount * ((1 + WEEKLY_INTEREST_RATE) ** weeks_elapsed - 1) if weeks_elapsed > 0 else 0
            total_earnings += interest
            eligible_withdrawal = (now - dep.timestamp).days >= MIN_INVEST_DAYS
        else:
            interest = 0
            eligible_withdrawal = False

        deposit_info.append({
            "deposit": dep,
            "interest": interest,
            "eligible_withdrawal": eligible_withdrawal
        })

    current_user.total_earnings = total_earnings
    db.session.commit()

    return render_template("dashboard.html",
                           user=current_user,
                           latest_kyc=latest_kyc,
                           deposit_info=deposit_info)


# ===============================
# KYC SUBMISSION
# ===============================

@main.route('/kyc', methods=['GET', 'POST'])
@login_required
def kyc():
    if request.method == 'POST':
        full_name = request.form.get("full_name", "").strip()
        id_number = request.form.get("id_number", "").strip()
        file = request.files.get("document")

        if not full_name or not id_number or not file:
            flash("All fields are required including upload.", "danger")
            return redirect(url_for('main.kyc'))

        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, f"{current_user.id}_{filename}")
        file.save(save_path)

        entry = KYCLog(
            user_id=current_user.id,
            full_name=full_name,
            id_number=id_number,
            document_path=save_path,
            status="pending",
            timestamp=datetime.utcnow()
        )

        db.session.add(entry)
        current_user.kyc_status = "pending"
        db.session.commit()

        flash("KYC submitted. Wait for approval.", "success")
        return redirect(url_for('main.dashboard'))

    latest_kyc = KYCLog.query.filter_by(user_id=current_user.id) \
                             .order_by(KYCLog.id.desc()).first()

    return render_template("kyc.html", latest_kyc=latest_kyc)


# ===============================
# DEPOSITS
# ===============================

@main.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if current_user.kyc_status != "approved":
        flash("You must complete KYC before depositing.", "danger")
        return redirect(url_for('main.kyc'))

    deposit_address = current_app.config.get("BINANCE_MASTER_ADDRESS")
    network = current_app.config.get("BINANCE_NETWORK", "TRC20")

    if not deposit_address:
        flash("Deposit address not configured. Contact admin.", "danger")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        amount = request.form.get("amount")
        tx_hash = request.form.get("tx_hash", "").strip()

        try:
            amount_f = float(amount)
            if amount_f <= 0:
                raise ValueError()
        except:
            flash("Enter a valid amount.", "danger")
            return redirect(url_for("main.deposit"))

        dep = Deposit(
            user_id=current_user.id,
            amount=amount_f,
            tx_hash=tx_hash or None,
            network=network,
            status="pending",
            timestamp=datetime.utcnow(),
        )

        db.session.add(dep)
        db.session.commit()

        flash("Deposit submitted. Admin will review.", "success")
        return redirect(url_for("main.dashboard"))

    # Generate QR Code
    qr_img = qrcode.make(deposit_address)
    qr_path = os.path.join(UPLOAD_FOLDER, f"{current_user.id}_deposit_qr.png")
    qr_img.save(qr_path)

    qr_url = url_for("static", filename=f"uploads/{current_user.id}_deposit_qr.png")

    return render_template("deposit.html",
                           deposit_address=deposit_address,
                           network=network,
                           qr_url=qr_url)


# ===============================
# WITHDRAWAL CHECK
# ===============================

def can_withdraw(user: User):
    earliest_deposit = Deposit.query.filter_by(user_id=user.id, status="approved") \
                                    .order_by(Deposit.timestamp.asc()).first()
    if not earliest_deposit:
        return False, "No approved deposits yet."
    if (datetime.utcnow() - earliest_deposit.timestamp).days < MIN_INVEST_DAYS:
        return False, f"Deposits must be at least {MIN_INVEST_DAYS} days old to withdraw."
    return True, ""


# ===============================
# ADMIN DASHBOARD
# ===============================

@main.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('main.dashboard'))

    users = User.query.all()
    kycs = KYCLog.query.order_by(KYCLog.timestamp.desc()).all()
    deposits = Deposit.query.order_by(Deposit.timestamp.desc()).all()

    return render_template("admin_dashboard.html",
                           users=users,
                           kycs=kycs,
                           deposits=deposits)


# ===============================
# ADMIN: KYC APPROVAL
# ===============================

@main.route('/admin/approve_kyc/<int:kyc_id>')
@login_required
def approve_kyc(kyc_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('main.dashboard'))

    rec = KYCLog.query.get_or_404(kyc_id)
    rec.status = "approved"

    user = User.query.get(rec.user_id)
    user.kyc_status = "approved"

    db.session.commit()

    flash("KYC approved.", "success")
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/reject_kyc/<int:kyc_id>')
@login_required
def reject_kyc(kyc_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('main.dashboard'))

    rec = KYCLog.query.get_or_404(kyc_id)
    rec.status = "rejected"

    user = User.query.get(rec.user_id)
    user.kyc_status = "rejected"

    db.session.commit()

    flash("KYC rejected.", "danger")
    return redirect(url_for('main.admin_dashboard'))


# ===============================
# ADMIN: DEPOSIT APPROVAL
# ===============================

@main.route('/admin/approve_deposit/<int:deposit_id>')
@login_required
def approve_deposit(deposit_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('main.dashboard'))

    dep = Deposit.query.get_or_404(deposit_id)

    if dep.status == "approved":
        flash("Deposit already approved.", "info")
        return redirect(url_for('main.admin_dashboard'))

    # Update deposit
    dep.status = "approved"

    # Update user balance and deposit stats
    user = User.query.get(dep.user_id)
    user.balance += dep.amount
    user.total_deposits += dep.amount

    db.session.commit()

    flash(f"Deposit of {dep.amount} USDT approved & credited.", "success")
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/reject_deposit/<int:deposit_id>')
@login_required
def reject_deposit(deposit_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('main.dashboard'))

    dep = Deposit.query.get_or_404(deposit_id)
    dep.status = "rejected"

    db.session.commit()

    flash("Deposit rejected.", "danger")
    return redirect(url_for('main.admin_dashboard'))

from flask import request
from src.app import db
from src.app.models import User  # adjust if your User model is in a different file

@main.route("/make-me-admin")
def make_me_admin():
    """Temporary route to promote a user to admin on live Render deployment."""
    email = request.args.get("email")
    
    if not email:
        return "Email parameter is missing. Usage: /make-me-admin?email=youremail@example.com", 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return f"User with email {email} not found.", 404

    user.is_admin = True  # or user.role = "admin" depending on your model
    db.session.commit()

    return f"? {email} is now an admin!"

