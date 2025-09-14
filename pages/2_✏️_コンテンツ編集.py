import streamlit as st
import os
from components.knowledge_base_supabase import KnowledgeBaseSupabase as KnowledgeBase
from utils.auth import check_password
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="コンテンツ編集",
    page_icon="✏️",
    layout="wide"
)

if not check_password(require_admin=True):
    st.stop()

st.title("✏️ コンテンツ編集・削除")
st.markdown("既存のコンテンツを編集または削除します。")

def init_knowledge_base():
    return KnowledgeBase()

kb = init_knowledge_base()

# セッション状態の初期化
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'selected_content' not in st.session_state:
    st.session_state.selected_content = None

# 章とレッスンの選択
st.header("📂 コンテンツを選択")

chapters_data = kb.get_chapters_and_lessons()

if not chapters_data:
    st.info("まだコンテンツが登録されていません。「教材管理」ページから追加してください。")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    # 章の選択
    chapter_names = sorted(chapters_data.keys(), key=lambda x: chapters_data[x]['order'])
    selected_chapter = st.selectbox(
        "章を選択",
        chapter_names,
        format_func=lambda x: f"{x} (順番: {chapters_data[x]['order']})"
    )

with col2:
    # レッスンの選択
    if selected_chapter:
        lessons = chapters_data[selected_chapter]['lessons']
        if lessons:
            lesson_names = sorted(lessons.keys(), key=lambda x: lessons[x]['order'])
            selected_lesson = st.selectbox(
                "レッスンを選択",
                lesson_names,
                format_func=lambda x: f"{x} (順番: {lessons[x]['order']})"
            )
        else:
            st.info("この章にはレッスンがありません。")
            st.stop()

st.divider()

# 選択されたレッスンのコンテンツを表示
if selected_chapter and selected_lesson:
    contents = kb.get_content_by_chapter_lesson(selected_chapter, selected_lesson)
    
    if contents:
        st.header("📄 コンテンツ一覧")
        
        for content in contents:
            with st.expander(f"📝 {content['title']} ({content['doc_type']})", expanded=False):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**タイプ:** {'📄 テキスト' if content['doc_type'] == 'text' else '🎥 動画'}")
                    if content['url']:
                        st.markdown(f"**Utage URL:** {content['url']}")
                    if content.get('youtube_url') and content['youtube_url']:
                        st.markdown(f"**YouTube URL:** {content['youtube_url']}")
                
                with col2:
                    if st.button(f"✏️ 編集", key=f"edit_{content['id']}"):
                        st.session_state.edit_mode = True
                        st.session_state.selected_content = content
                        st.session_state.selected_chapter = selected_chapter
                        st.session_state.selected_lesson = selected_lesson
                        st.rerun()
                
                with col3:
                    if st.button(f"🗑️ 削除", key=f"delete_{content['id']}", type="secondary"):
                        if st.checkbox(f"本当に「{content['title']}」を削除しますか？", key=f"confirm_{content['id']}"):
                            if kb.delete_content(selected_chapter, selected_lesson, content['title']):
                                st.success(f"✅ 「{content['title']}」を削除しました。")
                                st.rerun()
                            else:
                                st.error("削除に失敗しました。")
                
                # コンテンツの一部を表示
                st.text_area("コンテンツプレビュー", content['content'][:500] + "...", height=150, disabled=True, key=f"preview_{content['id']}")
    else:
        st.info("このレッスンにはコンテンツがありません。")

st.divider()

# 編集モード
if st.session_state.edit_mode and st.session_state.selected_content:
    st.header("📝 コンテンツを編集")
    
    content = st.session_state.selected_content
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 章・レッスン情報")
        new_chapter = st.text_input("章の名前", value=st.session_state.selected_chapter)
        new_chapter_order = st.number_input("章の順番", min_value=1, value=content['chapter_order'])
        new_lesson = st.text_input("レッスン名", value=st.session_state.selected_lesson)
        new_lesson_order = st.number_input("レッスンの順番", min_value=1, value=content['lesson_order'])
    
    with col2:
        st.subheader("📄 コンテンツ情報")
        new_title = st.text_input("コンテンツタイトル", value=content['title'])
        new_doc_type = st.selectbox(
            "コンテンツタイプ", 
            ["text", "video"],
            index=0 if content['doc_type'] == "text" else 1,
            format_func=lambda x: "📄 テキスト" if x == "text" else "🎥 動画文字起こし"
        )
        new_url = st.text_input("Utage URL (オプション)", value=content.get('url', ''))
        
        # 動画の場合はYouTube URLも編集可能
        new_youtube_url = ""
        if new_doc_type == "video":
            new_youtube_url = st.text_input("YouTube URL (オプション)", value=content.get('youtube_url', ''))
    
    new_content = st.text_area(
        "コンテンツ内容",
        value=content['content'],
        height=400
    )
    
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        if st.button("💾 保存", type="primary", use_container_width=True):
            if new_chapter and new_lesson and new_title and new_content:
                with st.spinner("更新中..."):
                    kb.update_content(
                        old_chapter=st.session_state.selected_chapter,
                        old_lesson=st.session_state.selected_lesson,
                        old_title=content['title'],
                        new_content=new_content,
                        new_title=new_title,
                        new_url=new_url,
                        new_doc_type=new_doc_type,
                        new_chapter=new_chapter,
                        new_lesson=new_lesson,
                        new_chapter_order=new_chapter_order,
                        new_lesson_order=new_lesson_order,
                        new_youtube_url=new_youtube_url if new_doc_type == "video" else None
                    )
                    st.success(f"✅ 「{new_title}」を更新しました！")
                    st.session_state.edit_mode = False
                    st.session_state.selected_content = None
                    st.rerun()
            else:
                st.warning("すべての必須項目を入力してください。")
    
    with col2:
        if st.button("❌ キャンセル", use_container_width=True):
            st.session_state.edit_mode = False
            st.session_state.selected_content = None
            st.rerun()

st.sidebar.info("""
**💡 使い方:**

1. **コンテンツ選択**: 章とレッスンを選択してコンテンツを表示
2. **編集**: ✏️ボタンでコンテンツを編集
3. **削除**: 🗑️ボタンでコンテンツを削除
4. **章・レッスンの移動**: 編集時に章やレッスンを変更可能

**⚠️ 注意:**
- 削除は取り消せません
- 編集後は自動的に保存されます
""")