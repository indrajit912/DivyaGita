from functools import wraps
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.admin import admin
from app.extensions import db
from app.models.user import User, Role
from app.models.gita import Explanation, Verse, Chapter

def admin_required(f):
    """Decorator to restrict access to administrator users only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@login_required
@admin_required
def dashboard():
    """Renders the Administrator Dashboard with system statistics."""
    total_users = User.query.count()
    total_explanations = Explanation.query.count()
    total_chapters = Chapter.query.count()
    total_verses = Verse.query.count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_explanations = Explanation.query.order_by(Explanation.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_explanations=total_explanations,
        total_chapters=total_chapters,
        total_verses=total_verses,
        recent_users=recent_users,
        recent_explanations=recent_explanations
    )

@admin.route('/users')
@login_required
@admin_required
def manage_users():
    """Displays a list of registered users and handles searching."""
    search_query = request.args.get('search', '').strip()
    
    query = User.query
    if search_query:
        query = query.filter(
            (User.username.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%')) |
            (User.name.ilike(f'%{search_query}%'))
        )
        
    users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/manage_users.html', users=users, search_query=search_query)

@admin.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Deactivates or activates a user account."""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash("You cannot deactivate your own administrator account.", "danger")
        return redirect(url_for('admin.manage_users'))
        
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activated" if user.is_active else "deactivated"
    flash(f"User account for '{user.username}' has been successfully {status}.", "success")
    return redirect(url_for('admin.manage_users'))

@admin.route('/explanations')
@login_required
@admin_required
def manage_explanations():
    """Lists all community explanations for moderation purposes."""
    explanations = Explanation.query.order_by(Explanation.created_at.desc()).all()
    return render_template('admin/manage_explanations.html', explanations=explanations)
