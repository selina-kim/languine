from flask import Flask
from src.routes.dictionary import *
from src.routes.translate import *
from dotenv import load_dotenv

load_dotenv()

def create_app():    
    app = Flask(__name__) 
    print("Test")

    app.config['JSON_AS_ASCII'] = False

    app.register_blueprint(define_bp)
    app.register_blueprint(translate_bp)

    return app

app = create_app()
