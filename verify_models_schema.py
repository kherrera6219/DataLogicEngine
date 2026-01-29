from extensions import db
from flask import Flask
import models

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        print('Database schema created successfully')
    except Exception as e:
        print(f'Error creating schema: {e}')
