import streamlit as st
import os
from components.knowledge_base import KnowledgeBase
from utils.auth import check_password
from dotenv import load_dotenv
import re

load_dotenv()

st.set_page_config(
    page_title="順番管理",
    page_icon="🔄",
    layout="wide"
)

# if not check_password():
#     st.stop()

st.title("🔄 章・レッスンの順番管理")
st.markdown("章やレッスンの表示順番を調整します。")

def init_knowledge_base():
    return KnowledgeBase()

kb = init_knowledge_base()

# 章とレッスンのデータを取得
chapters_data = kb.get_chapters_and_lessons()

if not chapters_data:
    st.info("まだコンテンツが登録されていません。")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📖 章の順番", "📝 レッスンの順番", "🔧 一括調整"])

with tab1:
    st.header("📖 章の順番を変更")
    
    # 章を順番でソート
    sorted_chapters = sorted(chapters_data.items(), key=lambda x: x[1]['order'])
    
    if sorted_chapters:
        st.info("章をドラッグして順番を変更することはできませんが、下記で新しい順番を設定できます。")
        
        # 章の順番変更フォーム
        with st.form("chapter_order_form"):
            new_orders = {}
            
            for i, (chapter_name, chapter_info) in enumerate(sorted_chapters):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"📖 {chapter_name}")
                with col2:
                    new_order = st.number_input(
                        "新しい順番",
                        min_value=1,
                        value=chapter_info['order'],
                        key=f"chapter_{chapter_name}"
                    )
                    new_orders[chapter_name] = new_order
            
            if st.form_submit_button("💾 章の順番を更新", type="primary"):
                # 各章のコンテンツを更新
                for chapter_name, new_order in new_orders.items():
                    for lesson_name in chapters_data[chapter_name]['lessons']:
                        contents = kb.get_content_by_chapter_lesson(chapter_name, lesson_name)
                        for content in contents:
                            kb.update_content(
                                old_chapter=chapter_name,
                                old_lesson=lesson_name,
                                old_title=content['title'],
                                new_content=content['content'],
                                new_title=content['title'],
                                new_url=content['url'],
                                new_doc_type=content['doc_type'],
                                new_chapter_order=new_order,
                                new_lesson_order=content['lesson_order'],
                                new_youtube_url=content.get('youtube_url')
                            )
                
                st.success("✅ 章の順番を更新しました！")
                st.rerun()
    else:
        st.info("章が登録されていません。")

with tab2:
    st.header("📝 レッスンの順番を変更")
    
    # 章を選択
    chapter_names = sorted(chapters_data.keys(), key=lambda x: chapters_data[x]['order'])
    selected_chapter = st.selectbox(
        "章を選択",
        chapter_names,
        format_func=lambda x: f"{x} (順番: {chapters_data[x]['order']})"
    )
    
    if selected_chapter:
        lessons = chapters_data[selected_chapter]['lessons']
        
        if lessons:
            sorted_lessons = sorted(lessons.items(), key=lambda x: x[1]['order'])
            
            # レッスン名から順番を自動抽出する機能
            st.info("💡 レッスン名に「順番: X」が含まれている場合、その順番を自動的に使用します。")
            
            with st.form("lesson_order_form"):
                new_lesson_orders = {}
                
                for i, (lesson_name, lesson_info) in enumerate(sorted_lessons):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.text(f"📝 {lesson_name}")
                    
                    with col2:
                        # レッスン名から順番を抽出
                        match = re.search(r'順番:\s*(\d+)', lesson_name)
                        default_order = int(match.group(1)) if match else lesson_info['order']
                        
                        new_order = st.number_input(
                            "新しい順番",
                            min_value=1,
                            value=default_order,
                            key=f"lesson_{lesson_name}"
                        )
                        new_lesson_orders[lesson_name] = new_order
                    
                    with col3:
                        if match:
                            st.caption(f"(名前から抽出: {match.group(1)})")
                
                if st.form_submit_button("💾 レッスンの順番を更新", type="primary"):
                    # 各レッスンのコンテンツを更新
                    for lesson_name, new_order in new_lesson_orders.items():
                        contents = kb.get_content_by_chapter_lesson(selected_chapter, lesson_name)
                        for content in contents:
                            kb.update_content(
                                old_chapter=selected_chapter,
                                old_lesson=lesson_name,
                                old_title=content['title'],
                                new_content=content['content'],
                                new_title=content['title'],
                                new_url=content['url'],
                                new_doc_type=content['doc_type'],
                                new_chapter_order=chapters_data[selected_chapter]['order'],
                                new_lesson_order=new_order,
                                new_youtube_url=content.get('youtube_url')
                            )
                    
                    st.success(f"✅ {selected_chapter}のレッスン順番を更新しました！")
                    st.rerun()
        else:
            st.info("この章にはレッスンがありません。")

with tab3:
    st.header("🔧 一括調整")
    
    st.subheader("📊 現在の順番を確認")
    
    # 現在の構造を表示
    for chapter_name, chapter_info in sorted(chapters_data.items(), key=lambda x: x[1]['order']):
        st.markdown(f"**📖 {chapter_name}** (順番: {chapter_info['order']})")
        
        if chapter_info['lessons']:
            for lesson_name, lesson_info in sorted(chapter_info['lessons'].items(), 
                                                  key=lambda x: x[1]['order']):
                # レッスン名から順番を抽出して表示
                match = re.search(r'順番:\s*(\d+)', lesson_name)
                name_order = f" (名前の順番: {match.group(1)})" if match else ""
                
                st.markdown(f"　　📝 {lesson_name} (順番: {lesson_info['order']}{name_order})")
    
    st.divider()
    
    st.subheader("🔄 順番の自動調整")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📖 章の順番を1から振り直す"):
            sorted_chapters = sorted(chapters_data.items(), key=lambda x: x[1]['order'])
            
            for i, (chapter_name, chapter_info) in enumerate(sorted_chapters, 1):
                for lesson_name in chapter_info['lessons']:
                    contents = kb.get_content_by_chapter_lesson(chapter_name, lesson_name)
                    for content in contents:
                        kb.update_content(
                            old_chapter=chapter_name,
                            old_lesson=lesson_name,
                            old_title=content['title'],
                            new_content=content['content'],
                            new_title=content['title'],
                            new_url=content['url'],
                            new_doc_type=content['doc_type'],
                            new_chapter_order=i,
                            new_lesson_order=content['lesson_order']
                        )
            
            st.success("✅ 章の順番を1から振り直しました！")
            st.rerun()
    
    with col2:
        if st.button("📝 全レッスンの順番を名前から自動設定"):
            for chapter_name, chapter_info in chapters_data.items():
                for lesson_name, lesson_info in chapter_info['lessons'].items():
                    # レッスン名から順番を抽出
                    match = re.search(r'順番:\s*(\d+)', lesson_name)
                    new_order = int(match.group(1)) if match else lesson_info['order']
                    
                    contents = kb.get_content_by_chapter_lesson(chapter_name, lesson_name)
                    for content in contents:
                        kb.update_content(
                            old_chapter=chapter_name,
                            old_lesson=lesson_name,
                            old_title=content['title'],
                            new_content=content['content'],
                            new_title=content['title'],
                            new_url=content['url'],
                            new_doc_type=content['doc_type'],
                            new_chapter_order=chapter_info['order'],
                            new_lesson_order=new_order,
                            new_youtube_url=content.get('youtube_url')
                        )
            
            st.success("✅ レッスン名から順番を自動設定しました！")
            st.rerun()

st.sidebar.info("""
**💡 順番管理のヒント:**

1. **章の順番**: 学習の流れに沿って設定
2. **レッスンの順番**: 各章内での学習順序を設定
3. **自動抽出**: レッスン名に「順番: X」が含まれていれば自動認識

**📝 レッスン名の例:**
- タイトル作成の基本 (順番: 1)
- タイトル作成の基本 (順番: 2)

この形式で名前を付けると、順番を自動的に認識します。
""")