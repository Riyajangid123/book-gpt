import psycopg2
from database.connection import get_connection

def create_user(username, email, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO book_users (username, email, password)
        VALUES (%s, %s, %s)
        RETURNING id, username, email;
    """, (username, email, password))

    user = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return user

def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM book_users
        WHERE email = %s;
    """, (email,))

    user = cur.fetchone()

    cur.close()
    conn.close()

    return user

def create_session(user_id, title="New Chat"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO book_sessions (user_id, title)
        VALUES (%s, %s)
        RETURNING id, title;
    """, (user_id, title))

    session = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return session

def get_sessions(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM book_sessions
        WHERE user_id = %s
        ORDER BY created_at DESC;
    """, (user_id,))

    sessions = cur.fetchall()

    cur.close()
    conn.close()

    return sessions

def save_message(session_id, user_id, role, message):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO book_messages (session_id, user_id, role, message)
        VALUES (%s, %s, %s, %s);
    """, (session_id, user_id, role, message))

    conn.commit()
    cur.close()
    conn.close()

def get_messages(session_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM book_messages
        WHERE session_id = %s
        ORDER BY created_at ASC;
    """, (session_id,))

    messages = cur.fetchall()

    cur.close()
    conn.close()

    return messages