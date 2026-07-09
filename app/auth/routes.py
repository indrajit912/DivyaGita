import random
from datetime import datetime, timezone, timedelta
from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash
from app.auth import auth
from app.auth.forms import LoginForm, RegisterForm, ResetPasswordRequestForm, ResetPasswordForm
from app.extensions import db
from app.models.user import User, Role, UserOTP
from app.services.email_service import EmailService

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Renders the registration form, creates user as inactive, and issues verification OTP."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user_role = Role.query.filter_by(name='Standard User').first()
        if not user_role:
            flash('System error: User roles are not initialized. Please contact support.', 'danger')
            return render_template('auth/register.html', form=form)
            
        user = User(
            name=form.name.data.strip(),
            username=form.username.data.lower().strip(),
            email=form.email.data.lower().strip(),
            contact_number=form.contact_number.data.strip() if form.contact_number.data else None,
            address=form.address.data.strip() if form.address.data else None,
            role_id=user_role.id,
            is_active=False,  # inactive until OTP verified
            is_email_verified=False
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # 1. Generate 6-digit verification code
        otp = f"{random.randint(100000, 999999)}"
        otp_hash = generate_password_hash(otp)
        
        # 2. Save OTP to DB
        otp_entry = UserOTP(
            user_id=user.id,
            otp_hash=otp_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
        )
        db.session.add(otp_entry)
        db.session.commit()
        
        # 3. Dispatch OTP via Hermes Email Service
        try:
            EmailService.send_otp_email(user.email, otp)
        except Exception as e:
            current_app.logger.error(f"Failed to send OTP email: {e}")
            
        session['verify_user_id'] = user.id
        flash('Account registered successfully! A 6-digit verification OTP has been sent to your email.', 'info')
        return redirect(url_for('auth.verify_otp'))
        
    return render_template('auth/register.html', form=form)

@auth.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verifies the registration OTP code and activates the account."""
    user_id = session.get('verify_user_id')
    if not user_id:
        flash('Session expired. Please register again.', 'warning')
        return redirect(url_for('auth.register'))
        
    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please register again.', 'danger')
        return redirect(url_for('auth.register'))

    if user.is_email_verified:
        flash('Your email is already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        
        # Fetch active OTP record
        otp_entry = UserOTP.query.filter_by(user_id=user.id).first()
        
        if not otp_entry:
            flash('No active verification code found. Please request a new one.', 'danger')
            return redirect(url_for('auth.verify_otp'))
            
        # Check expiry
        if otp_entry.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            db.session.delete(otp_entry)
            db.session.commit()
            flash('Verification code has expired. Please request a new code.', 'danger')
            return redirect(url_for('auth.verify_otp'))
            
        # Check attempts lockout
        if otp_entry.attempts >= 3:
            db.session.delete(otp_entry)
            db.session.commit()
            flash('Too many incorrect verification attempts. Please request a new OTP.', 'danger')
            return redirect(url_for('auth.verify_otp'))

        # Verify hash match
        from werkzeug.security import check_password_hash
        if check_password_hash(otp_entry.otp_hash, entered_otp):
            # Activate account
            user.is_active = True
            user.is_email_verified = True
            db.session.delete(otp_entry)
            db.session.commit()
            
            session.pop('verify_user_id', None)
            flash('Your account has been verified and activated successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            otp_entry.attempts += 1
            db.session.commit()
            attempts_left = 3 - otp_entry.attempts
            if attempts_left > 0:
                flash(f'Invalid verification code. You have {attempts_left} attempts remaining.', 'warning')
            else:
                db.session.delete(otp_entry)
                db.session.commit()
                flash('Too many incorrect verification attempts. Request a new OTP.', 'danger')
                
    return render_template('auth/verify_otp.html')

@auth.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Generates and sends a new registration OTP code."""
    user_id = session.get('verify_user_id')
    if not user_id:
        flash('Session expired. Please register again.', 'warning')
        return redirect(url_for('auth.register'))
        
    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please register again.', 'danger')
        return redirect(url_for('auth.register'))

    if user.is_email_verified:
        flash('This account is already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))
        
    # Rate Limiting (e.g. 60 seconds interval)
    existing_otp = UserOTP.query.filter_by(user_id=user.id).first()
    if existing_otp:
        time_elapsed = datetime.now(timezone.utc) - existing_otp.created_at.replace(tzinfo=timezone.utc)
        if time_elapsed.total_seconds() < 60:
            seconds_to_wait = int(60 - time_elapsed.total_seconds())
            flash(f'Please wait {seconds_to_wait} seconds before requesting another verification code.', 'warning')
            return redirect(url_for('auth.verify_otp'))
            
    # Delete old OTP entry
    if existing_otp:
        db.session.delete(existing_otp)
    
    # Create fresh OTP
    otp = f"{random.randint(100000, 999999)}"
    otp_hash = generate_password_hash(otp)
    
    otp_entry = UserOTP(
        user_id=user.id,
        otp_hash=otp_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    db.session.add(otp_entry)
    db.session.commit()
    
    try:
        EmailService.send_otp_email(user.email, otp)
    except Exception as e:
        current_app.logger.error(f"Failed to resend OTP: {e}")
        
    flash('A fresh verification OTP has been sent to your email address.', 'success')
    return redirect(url_for('auth.verify_otp'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticates users, enforces lockout rules, and verifies email status."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        login_input = form.username_or_email.data.lower().strip()
        user = User.query.filter((User.email == login_input) | (User.username == login_input)).first()
        
        if user:
            # 1. Enforce account lockout
            if user.lockout_until and user.lockout_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
                seconds_left = int((user.lockout_until.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds())
                minutes_left = (seconds_left // 60) + 1
                flash(f'Account locked due to consecutive failures. Try again in {minutes_left} minutes.', 'danger')
                return redirect(url_for('auth.login'))
 
            if user.check_password(form.password.data):
                # 2. Check email verification status
                if not user.is_email_verified:
                    session['verify_user_id'] = user.id
                    
                    # Check if previous OTP has expired
                    otp_entry = UserOTP.query.filter_by(user_id=user.id).first()
                    expired = not otp_entry or otp_entry.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
                    
                    if expired:
                        flash('Your email has not been verified, and the previous code expired. Please request a new OTP.', 'warning')
                    else:
                        flash('Your email has not been verified. Please enter the verification code sent to your email.', 'info')
                    return redirect(url_for('auth.verify_otp'))
                    
                # Account status checks
                if not user.is_active:
                    flash('This account is disabled. Please contact an administrator.', 'danger')
                    return redirect(url_for('auth.login'))
                
                # Reset lockouts on success
                user.failed_login_attempts = 0
                user.lockout_until = None
                user.last_login = datetime.now(timezone.utc)
                db.session.commit()
                
                # Log user in
                login_user(user, remember=form.remember_me.data)
                
                next_page = request.args.get('next')
                flash(f"Welcome back, {user.name}!", 'success')
                return redirect(next_page) if next_page and next_page.startswith('/') else redirect(url_for('main.index'))
            else:
                # Password failure lockout increment
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.lockout_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                    db.session.commit()
                    flash('Too many failed login attempts. Account locked for 15 minutes.', 'danger')
                else:
                    db.session.commit()
                    flash('Invalid username/email or password. Please try again.', 'danger')
        else:
            flash('Invalid username/email or password. Please try again.', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """Terminates session."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """Generates password reset URLs and sends emails via Hermes."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            reset_token = user.id
            reset_link = url_for('auth.reset_password', token=reset_token, _external=True)
            
            try:
                EmailService.send_password_reset_email(user.email, reset_link)
            except Exception as e:
                current_app.logger.error(f"Failed to send password reset email: {e}")
            
        flash('An email has been sent with instructions to reset your password if that account exists.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password_request.html', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Sets a new password."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    user = User.query.get(token)
    if not user:
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('auth.login'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.failed_login_attempts = 0
        user.lockout_until = None
        db.session.commit()
        
        flash('Your password has been reset successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form)
