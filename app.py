import streamlit as st
import sqlite3
import re

# ====== Database Setup ======
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Existing users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')
conn.commit()


# ====== Streamlit UI ======
st.set_page_config(
    page_title="Movie App Login",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hides the sidebar navigation completely
hide_menu = """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_menu, unsafe_allow_html=True)

def is_password_strong(password):
    # At least 8 characters, one uppercase, one lowercase, one digit, one special character
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&* etc.)."
    return True, ""

# ====== Utility Functions ======
def register_user(username, password):
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    return cursor.fetchone() is not None


if 'mode' not in st.session_state:
    st.session_state.mode = 'login'  # can be 'login', 'signup', or 'dashboard'

st.title("🎬 Movie Recommendation System")
st.subheader("Welcome to your personalized movie world")

# ====== LOGIN FLOW ======
if st.session_state.mode == 'login':
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button(":blue[Login]"):
        if authenticate_user(username, password):
            st.session_state.logged_in = True  # Add this flag
            st.session_state.username = username  # Optional: Store username
            st.switch_page("pages/dashboard.py")
        else:
            st.error("Invalid username or password.")


    st.markdown("No account? Don’t worry")
    if st.button(":green[Create one right now]"):
        st.session_state.mode = 'signup'
        st.rerun()

# ====== SIGNUP FLOW ======
elif st.session_state.mode == 'signup':
    st.header("Sign Up")
    new_username = st.text_input("Create Username")
    new_password = st.text_input("Create Password", type="password")

    if st.button(":blue[Sign Up]"):
        # Password validation
        is_strong, feedback = is_password_strong(new_password)
        if not is_strong:
            st.error(feedback)
        elif register_user(new_username, new_password):
            st.success("✅ Account created successfully! Redirecting to login...")
            st.session_state.mode = 'login'
            st.rerun()
        else:
            st.error("❌ Username already exists. Try a different one.")

    if st.button("Back to Login"):
        st.session_state.mode = 'login'
        st.rerun()
