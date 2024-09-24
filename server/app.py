from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import numpy as np
import psycopg2
from controllers.user_controller import user_login
from controllers.simulation_controller import Simulation
from server.config.db import create_tables

app = Flask(__name__)
CORS(app)

simulation:Simulation

@app.route('/')
def index():
    return "I'm alive!"

# API routes
@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username', '').lower()
    user_data = user_login(username)
    
    if user_data is None:
        return jsonify({"error": "Username is required"}), 400
    
    session['user_id'] = user_data['user_id']
    session['username'] = user_data['username']

    return jsonify({"message": "Logged in successfully", "username": username}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/simulation', methods=['GET'])
def get_simulation_state():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    state = simulation.get_simulation_state()
    return jsonify(state)

@app.route('/api/simulation/update', methods=['POST'])
def update_simulation():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    simulation.update()
    return jsonify({'message': 'Simulation updated successfully'})

@app.route('/api/simulation/reset', methods=['POST'])
def reset_simulation():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    simulation.reset()
    return jsonify({'message': 'Simulation reset successfully'})

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)  # Set to False in production