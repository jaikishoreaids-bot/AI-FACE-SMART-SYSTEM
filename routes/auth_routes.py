import functools
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.user import User
from models.activity_log import ActivityLog
from database.db import db

auth_bp = Blueprint('auth', __name__)


def login_required(view):
    """Decorator to require login for protected routes."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized. Please login.'}), 401
            return redirect(url_for('auth.login', next=request.url))
        return view(**kwargs)
    return wrapped_view


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact the administrator.', 'danger')
                return render_template('login.html')
                
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['role'] = user.role
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            ActivityLog.log('USER_LOGIN', f"User '{user.username}' logged in successfully.", ip_address=request.remote_addr)
            
            next_page = request.args.get('next')
            if next_page and not next_page.startswith('/login'):
                return redirect(next_page)
            return redirect(url_for('dashboard.dashboard_view'))
        else:
            flash('Invalid username/email or password.', 'danger')
            
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    ActivityLog.log('USER_LOGOUT', f"User '{username}' logged out.", ip_address=request.remote_addr)
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/auth/check')
def auth_check():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'full_name': session.get('full_name'),
                'role': session.get('role')
            }
        })
    return jsonify({'authenticated': False})
