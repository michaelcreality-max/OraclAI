# auth_system.py

"""
Backend Architecture for Authentication System

This module implements JWT authentication, database models, and session management for a multi-domain system.
"""

import jwt
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auth_system.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    domains = db.relationship('Domain', backref='owner', lazy=True)

class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# JWT Secret Key
SECRET_KEY = "your_secret_key"

# Create User
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    new_user = User(username=data['username'], password=data['password'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully!'}), 201

# JWT Token Generation
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.password == data['password']:
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, SECRET_KEY)
        return jsonify({'token': token})
    return jsonify({'message': 'Invalid credentials!'}), 401

# Token Authentication
@app.route('/protected', methods=['GET'])
def protected():
    token = request.args.get('token')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 403
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return jsonify({'message': 'Protected content', 'user_id': data['user_id']})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid Token!'}), 401

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)