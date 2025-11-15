from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .models import User, KYCLog
from . import db

admin = Blueprint('admin', __name__)

# ?? Restrict access to admins
@admin.before_request
def restrict_to_admins():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('main.dashboard'))

# ?? Admin dashboard: view users and KYC logs
@admin.route('/admin')
@login_required
def admin_dashboard():
    users = User.query.all()
    kycs = KYCLog.query.all()
    return render_template('admin_dashboard.html', users=users, kycs=kycs)

# ? Approve a KYC submission
@admin.route('/admin/kyc/approve/<int:kyc_id>')
@login_required
def approve_kyc(kyc_id):
    kyc = KYCLog.query.get_or_404(kyc_id)
    kyc.status = 'approved'
    kyc.user.kyc_status = 'approved'
    db.session.commit()
    flash(f"KYC for {kyc.user.username} approved ?", "success")
    return redirect(url_for('admin.admin_dashboard'))

# ? Reject a KYC submission
@admin.route('/admin/kyc/reject/<int:kyc_id>')
@login_required
def reject_kyc(kyc_id):
    kyc = KYCLog.query.get_or_404(kyc_id)
    kyc.status = 'rejected'
    kyc.user.kyc_status = 'rejected'
    db.session.commit()
    flash(f"KYC for {kyc.user.username} rejected ?", "danger")
    return redirect(url_for('admin.admin_dashboard'))

# ?? Credit user balance
@admin.route('/admin/credit/<int:user_id>', methods=['POST'])
@login_required
def credit_user(user_id):
    user = User.query.get_or_404(user_id)
    amount = request.form.get('amount', type=float)
    if amount and amount > 0:
        user.balance += amount
        user.total_deposits += amount
        db.session.commit()
        flash(f"{amount:.2f} credited to {user.username}'s account ?", "success")
    else:
        flash("Invalid amount", "danger")
    return redirect(url_for('admin.admin_dashboard'))

# ?? Debit user balance
@admin.route('/admin/debit/<int:user_id>', methods=['POST'])
@login_required
def debit_user(user_id):
    user = User.query.get_or_404(user_id)
    amount = request.form.get('amount', type=float)
    if amount and 0 < amount <= user.balance:
        user.balance -= amount
        user.total_withdrawals += amount
        db.session.commit()
        flash(f"{amount:.2f} debited from {user.username}'s account ?", "success")
    else:
        flash("Invalid amount or insufficient balance", "danger")
    return redirect(url_for('admin.admin_dashboard'))
