from flask import request, jsonify, session
from server.config.db import get_db_connection

def user_login(username):
    
    if not username:
        return None
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if user exists, if not, create a new user
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    
    if user is None:
        cur.execute("INSERT INTO users (username) VALUES (%s) RETURNING id", (username,))
        user_id = cur.fetchone()[0]
        conn.commit()
    else:
        user_id = user[0]
    
    cur.close()
    conn.close()
    
    return {
        'user_id': user_id,
        'username': username,
    }