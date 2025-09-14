import streamlit as st
import os
from components.knowledge_base_supabase import KnowledgeBaseSupabase as KnowledgeBase
from utils.auth import check_password
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="教材管理",
    page_icon="📚",
    layout="wide"
)

if not check_password(require_admin=True):
    st.stop()

st.title("📚 教材管理")
st.markdown("章とレッスンごとに教材を整理して管理します。")

def init_knowledge_base():
    return KnowledgeBase()

kb = init_knowledge_base()

tab1, tab2, tab3, tab4 = st.tabs(["📝 コンテンツ追加", "📂 章・レッスン一覧", "📊 統計情報", "⚙️ 管理"])

with tab1:
    st.header("新しいコンテンツを追加")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 章・レッスン情報")
        chapter = st.text_input("章の名前", placeholder="例: 第1章 ブログの基礎")
        chapter_order = st.number_input("章の順番", min_value=1, value=1)
        lesson = st.text_input("レッスン名", placeholder="例: レッスン1 WordPressの設定")
        lesson_order = st.number_input("レッスンの順番", min_value=1, value=1)
    
    with col2:
        st.subheader("📄 コンテンツ情報")
        title = st.text_input("コンテンツタイトル", placeholder="例: WordPressの初期設定方法")
        doc_type = st.selectbox("コンテンツタイプ", ["text", "video"], 
                                format_func=lambda x: "📄 テキスト" if x == "text" else "🎥 動画文字起こし")
        url = st.text_input("Utage URL (オプション)", placeholder="https://utage.example.com/lesson1")
        
        # 動画の場合はYouTube URLも入力可能
        youtube_url = ""
        if doc_type == "video":
            youtube_url = st.text_input("YouTube URL (オプション)", placeholder="https://www.youtube.com/watch?v=...")
    
    content = st.text_area(
        "コンテンツ内容",
        height=400,
        placeholder="テキストまたは動画の文字起こしを貼り付けてください..."
    )
    
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("📤 追加", type="primary", use_container_width=True):
            if chapter and lesson and title and content:
                with st.spinner("ナレッジベースに追加中..."):
                    try:
                        kb.add_document(
                            content=content,
                            title=title,
                            url=url,
                            doc_type=doc_type,
                            chapter=chapter,
                            lesson=lesson,
                            chapter_order=chapter_order,
                            lesson_order=lesson_order,
                            youtube_url=youtube_url if doc_type == "video" else None
                        )
                        st.success(f"✅ {chapter} / {lesson} / {title} を追加しました！")
                        st.balloons()
                    except Exception as e:
                        st.error(f"エラー: {str(e)}")
            else:
                st.warning("すべての必須項目を入力してください。")
    
    with col2:
        if st.button("🔄 フォームをクリア", use_container_width=True):
            st.rerun()

with tab2:
    st.header("📂 登録済みの章とレッスン")
    
    chapters_data = kb.get_chapters_and_lessons()
    
    if chapters_data:
        # 章を順番でソート
        sorted_chapters = sorted(chapters_data.items(), key=lambda x: x[1]['order'])
        
        for chapter_name, chapter_info in sorted_chapters:
            with st.expander(f"📖 {chapter_name} (順番: {chapter_info['order']})", expanded=False):
                if chapter_info['lessons']:
                    # レッスンを順番でソート
                    sorted_lessons = sorted(chapter_info['lessons'].items(), 
                                          key=lambda x: x[1]['order'])
                    
                    for lesson_name, lesson_info in sorted_lessons:
                        st.markdown(f"**📝 {lesson_name}** (順番: {lesson_info['order']})")
                        
                        # コンテンツタイプのアイコン表示
                        doc_types_icons = []
                        for doc_type in lesson_info['doc_types']:
                            if doc_type == 'text':
                                doc_types_icons.append("📄 テキスト")
                            elif doc_type == 'video':
                                doc_types_icons.append("🎥 動画")
                        
                        if doc_types_icons:
                            st.caption(f"コンテンツ: {', '.join(doc_types_icons)}")
                        
                        st.divider()
                else:
                    st.info("まだレッスンが登録されていません。")
    else:
        st.info("まだコンテンツが登録されていません。「コンテンツ追加」タブから追加してください。")

with tab3:
    st.header("📊 ナレッジベース統計")
    
    stats = kb.get_stats()
    chapters_data = kb.get_chapters_and_lessons()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("コンテンツ数", stats["total_contents"], help="実際に登録されているコンテンツの数")
    
    with col2:
        st.metric("チャンク総数", stats["total_chunks"], help="検索用に分割された断片の総数")
    
    with col3:
        st.metric("章の数", len(chapters_data))
    
    with col4:
        total_lessons = sum(len(chapter['lessons']) for chapter in chapters_data.values())
        st.metric("レッスン数", total_lessons)
    
    if chapters_data:
        st.divider()
        st.subheader("📈 詳細統計")
        
        # 各章のレッスン数を表示
        for chapter_name, chapter_info in sorted(chapters_data.items(), key=lambda x: x[1]['order']):
            lesson_count = len(chapter_info['lessons'])
            st.markdown(f"- **{chapter_name}**: {lesson_count} レッスン")
        
        # チャンクの平均数を表示
        if stats["total_contents"] > 0:
            avg_chunks = stats["total_chunks"] / stats["total_contents"]
            st.divider()
            st.info(f"💡 1コンテンツあたり平均 {avg_chunks:.1f} チャンクに分割されています")

with tab4:
    st.header("⚙️ データ管理")
    
    st.warning("⚠️ 注意: 以下の操作は取り消せません。")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗑️ データの削除")
        
        confirm = st.checkbox("すべてのデータを削除することを確認します")
        
        if st.button("⚠️ すべてのデータを削除", type="secondary", disabled=not confirm):
            with st.spinner("削除中..."):
                kb.clear_all()
                st.success("すべてのデータを削除しました。")
                st.rerun()
    
    with col2:
        st.subheader("📥 サンプルデータ")
        
        if st.button("📤 サンプルデータを追加"):
            with st.spinner("サンプルデータを追加中..."):
                try:
                    # サンプルデータの追加
                    sample_data = [
                        {
                            "chapter": "第1章 ブログの基礎",
                            "chapter_order": 1,
                            "lesson": "レッスン1 ブログとは",
                            "lesson_order": 1,
                            "title": "ブログの基本概念",
                            "content": "ブログとは、個人や企業が情報を発信するためのウェブサイトの一種です。定期的に更新される記事形式のコンテンツが特徴で、読者とのコミュニケーションツールとしても活用されています。",
                            "doc_type": "text"
                        },
                        {
                            "chapter": "第1章 ブログの基礎",
                            "chapter_order": 1,
                            "lesson": "レッスン2 WordPressの設定",
                            "lesson_order": 2,
                            "title": "WordPressインストール動画",
                            "content": "こんにちは、今日はWordPressのインストール方法について説明します。まず、レンタルサーバーにログインして、コントロールパネルを開いてください。",
                            "doc_type": "video",
                            "youtube_url": "https://www.youtube.com/watch?v=example123"
                        },
                        {
                            "chapter": "第2章 コンテンツ作成",
                            "chapter_order": 2,
                            "lesson": "レッスン1 記事の書き方",
                            "lesson_order": 1,
                            "title": "効果的な記事の構成",
                            "content": "読まれる記事を書くためには、明確な構成が重要です。導入、本文、結論の3部構成を基本として、読者の興味を引く見出しを設定しましょう。",
                            "doc_type": "text"
                        }
                    ]
                    
                    for data in sample_data:
                        kb.add_document(
                            content=data["content"],
                            title=data["title"],
                            doc_type=data["doc_type"],
                            chapter=data["chapter"],
                            lesson=data["lesson"],
                            chapter_order=data["chapter_order"],
                            lesson_order=data["lesson_order"],
                            youtube_url=data.get("youtube_url")
                        )
                    
                    st.success("✅ サンプルデータを追加しました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"エラー: {str(e)}")

st.sidebar.info("""
**💡 使い方のヒント:**

1. **章とレッスンで整理**: コンテンツを章とレッスンに分けて体系的に管理
2. **順番を設定**: 章とレッスンに順番を設定して学習順序を明確に
3. **複数のコンテンツタイプ**: テキストと動画の両方を同じレッスンに追加可能
4. **URLリンク**: Utageの該当ページへのリンクを設定可能

**📚 推奨される構成例:**
- 第1章 ブログの基礎
  - レッスン1 ブログとは
  - レッスン2 WordPressの設定
- 第2章 コンテンツ作成
  - レッスン1 記事の書き方
  - レッスン2 SEO対策
""")