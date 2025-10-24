from flask import Flask

def temp():    
    app = Flask(__name__) 
    print("Test")
    
    return app

app = temp()