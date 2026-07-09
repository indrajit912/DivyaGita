import os
from flask import Flask, render_template, request, jsonify
from config import config_by_name
from app.extensions import db, migrate, login_manager, csrf

def create_app(config_name=None):
    """Flask Application Factory for DivyaGita."""
    app = Flask(__name__, instance_relative_config=True)
    
    if not config_name:
        is_debug = os.environ.get('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
        if is_debug:
            config_name = 'development'
        else:
            flask_env = os.environ.get('FLASK_ENV')
            if flask_env:
                config_name = flask_env
            else:
                config_name = 'production'
            
    app.config.from_object(config_by_name[config_name])
    
    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Flask-Login configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
        
    # Register Blueprints
    from app.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.gita.routes import gita as gita_blueprint
    app.register_blueprint(gita_blueprint, url_prefix='/gita')
    
    from app.admin.routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    # Global template context
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'current_year': datetime.now().year}
        
    # Error Handlers
    register_error_handlers(app)
    
    # Register CLI Commands
    from app.commands import setup_db_command, create_admin_command
    app.cli.add_command(setup_db_command)
    app.cli.add_command(create_admin_command)
    
    return app

def register_error_handlers(app):
    """Registers handlers for 400, 404, and 500 errors."""
    
    def wants_json_response():
        return request.path.startswith('/api/') or request.accept_mimetypes.best == 'application/json'

    @app.errorhandler(400)
    def bad_request(error):
        if wants_json_response():
            return jsonify({'error': 'Bad Request', 'message': str(error.description)}), 400
        return render_template('errors/400.html'), 400

    @app.errorhandler(404)
    def not_found(error):
        if wants_json_response():
            return jsonify({'error': 'Not Found', 'message': 'The requested resource was not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if wants_json_response():
            return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected server error occurred'}), 500
        return render_template('errors/500.html'), 500
