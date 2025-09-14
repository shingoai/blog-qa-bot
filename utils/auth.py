import streamlit as st
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

def check_password():
    def password_entered():
        if hashlib.sha256(st.session_state["password"].encode()).hexdigest() == hashlib.sha256(os.getenv("AUTH_PASSWORD", "blog2024").encode()).hexdigest():
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "パスワードを入力してください",
            type="password",
            on_change=password_entered,
            key="password"
        )
        return False
    
    elif not st.session_state["password_correct"]:
        st.text_input(
            "パスワードを入力してください",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("パスワードが間違っています")
        return False
    
    else:
        return True