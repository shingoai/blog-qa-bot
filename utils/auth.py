import streamlit as st
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

def check_password(require_admin=False):
    """
    パスワード認証
    require_admin=True: 管理者パスワードが必要（管理画面用）
    require_admin=False: ユーザーパスワードでOK（Q&Aページ用）
    """
    def password_entered():
        entered_password = st.session_state["password"]
        entered_hash = hashlib.sha256(entered_password.encode()).hexdigest()
        
        admin_password = os.getenv("ADMIN_PASSWORD", "admin2024")
        user_password = os.getenv("USER_PASSWORD", "blog2024")
        
        admin_hash = hashlib.sha256(admin_password.encode()).hexdigest()
        user_hash = hashlib.sha256(user_password.encode()).hexdigest()
        
        # 管理者パスワードは全ページにアクセス可能
        if entered_hash == admin_hash:
            st.session_state["password_correct"] = True
            st.session_state["is_admin"] = True
            del st.session_state["password"]
        # ユーザーパスワードは管理画面以外にアクセス可能
        elif not require_admin and entered_hash == user_hash:
            st.session_state["password_correct"] = True
            st.session_state["is_admin"] = False
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        if require_admin:
            st.info("🔒 管理者権限が必要です")
        st.text_input(
            "パスワードを入力してください",
            type="password",
            on_change=password_entered,
            key="password"
        )
        return False
    
    elif not st.session_state["password_correct"]:
        if require_admin:
            st.info("🔒 管理者権限が必要です")
        st.text_input(
            "パスワードを入力してください",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("パスワードが間違っています")
        return False
    
    # 管理画面へのアクセスチェック
    elif require_admin and not st.session_state.get("is_admin", False):
        st.error("⛔ このページには管理者権限が必要です")
        if st.button("ログアウトして再ログイン"):
            del st.session_state["password_correct"]
            del st.session_state["is_admin"]
            st.rerun()
        return False
    
    else:
        return True