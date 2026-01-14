import os
from flask import Flask
from routes.dictionary import *
from routes.translate import *
from routes.auth import auth_bp
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flask_cors import CORS

load_dotenv()
jwt = JWTManager()

def create_app():    
    app = Flask(__name__) 
    print("Test")

    app.config['JSON_AS_ASCII'] = False
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    jwt.init_app(app)
    CORS(app)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return {'error': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Authorization header missing'}, 401

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(define_bp)
    app.register_blueprint(translate_bp)

    return app

app = create_app()
