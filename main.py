from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
from models import db
import os


def create_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.mood import mood_bp
    from routes.therapy import therapy_bp
    from routes.ai import ai_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(mood_bp)
    app.register_blueprint(therapy_bp)
    app.register_blueprint(ai_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'AI-Powered Mental Health Platform',
            'version': '1.0.0'
        }), 200

    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'message': 'Welcome to the AI-Powered Mental Health Platform API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'mood': '/api/mood',
                'therapy': '/api/therapy',
                'ai': '/api/ai'
            }
        }), 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    return app


if __name__ == '__main__':
    env = os.getenv('FLASK_ENV', 'development')
    app = create_app(env)
    app.run(host='0.0.0.0', port=5000, debug=(env == 'development'))
