from flask import Flask
from routes import main
from db_connection import get_db_connection  # Importa de db_connection.py

app = Flask(__name__)
print("Flask app instance created")

app.register_blueprint(main)
print("Blueprint registrado")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
