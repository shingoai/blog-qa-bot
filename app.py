import streamlit as st
import openai
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import hashlib
import re
from components.knowledge_base import KnowledgeBase
from components.question_logger import QuestionLogger
from utils.auth import check_password

load_dotenv()

st.set_page_config(
    page_title="ブログスクール Q&Aボット",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

if not check_password():
    st.stop()

@st.cache_resource
def init_knowledge_base():
    return KnowledgeBase()

@st.cache_resource
def init_question_logger():
    return QuestionLogger()

kb = init_knowledge_base()
logger = init_question_logger()

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_youtube_urls(text):
    """テキストからYouTube URLを抽出"""
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+(?:&[\w=]*)?',
        r'https?://(?:www\.)?youtu\.be/[\w-]+(?:\?[\w=]*)?',
        r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',
        r'https?://(?:www\.)?youtube\.com/v/[\w-]+'
    ]
    
    urls = []
    for pattern in youtube_patterns:
        matches = re.findall(pattern, text)
        urls.extend(matches)
    
    return list(set(urls))  # 重複を除去

def extract_all_urls(text):
    """テキストから全てのURLを抽出（YouTube以外）"""
    # 一般的なURLパターン
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:[.,;!?](?=\s)|[^\s.,;!?])*'
    
    all_urls = re.findall(url_pattern, text)
    youtube_urls = extract_youtube_urls(text)
    
    # YouTube URL以外を返す
    other_urls = [url for url in all_urls if url not in youtube_urls]
    
    # URLの末尾の句読点を除去
    cleaned_urls = []
    for url in other_urls:
        # 末尾の句読点を除去
        url = re.sub(r'[.,;!?]+$', '', url)
        cleaned_urls.append(url)
    
    return list(set(cleaned_urls))  # 重複を除去

st.title("🎓 ブログスクール Q&Aボット")
st.markdown("教材に関する質問にお答えします。")

with st.sidebar:
    st.header("📚 情報")
    st.info("""
    このボットは教材の内容に基づいて回答します。
    
    **使い方:**
    1. 質問を入力してください
    2. Enterキーまたは送信ボタンをクリック
    3. AIが教材を参照して回答します
    """)
    
    if st.button("🔄 履歴をクリア"):
        st.session_state.messages = []
        st.rerun()
    
    with st.expander("📊 よく聞かれるトピック"):
        all_logs = logger.get_all_logs()
        if all_logs:
            from collections import Counter
            import re
            
            # 簡易的なトピック分類
            topics = {
                'タイトル': ['タイトル', '題名', '見出し', 'title'],
                'SEO': ['seo', '検索', 'キーワード', '順位'],
                'WordPress': ['wordpress', 'wp', 'プラグイン', 'テーマ'],
                '記事作成': ['記事', '書き方', 'ライティング', '文章'],
                'ブログ運営': ['運営', '収益', 'アクセス', 'pv']
            }
            
            topic_counts = Counter()
            
            for log in all_logs:
                question_lower = log['question'].lower()
                for topic, keywords in topics.items():
                    for keyword in keywords:
                        if keyword in question_lower:
                            topic_counts[topic] += 1
                            break
            
            if topic_counts:
                for topic, count in topic_counts.most_common(5):
                    st.write(f"• {topic} ({count}件)")
            else:
                st.write("まだ分析データがありません")
        else:
            st.write("まだ質問がありません")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("質問を入力してください..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("回答を生成中..."):
            try:
                relevant_docs = kb.search(prompt, n_results=5)
                
                context = "\n\n".join([doc['content'] for doc in relevant_docs])
                urls = [doc.get('url', '') for doc in relevant_docs if doc.get('url')]
                youtube_urls = [doc.get('youtube_url', '') for doc in relevant_docs if doc.get('youtube_url')]
                
                # テキストコンテンツ内からYouTube URLと資料URLを抽出
                extracted_youtube_urls = []
                extracted_other_urls = []
                for doc in relevant_docs:
                    found_youtube = extract_youtube_urls(doc['content'])
                    found_other = extract_all_urls(doc['content'])
                    extracted_youtube_urls.extend(found_youtube)
                    extracted_other_urls.extend(found_other)
                
                # 重複を除去して統合
                all_youtube_urls = list(set(youtube_urls + extracted_youtube_urls))
                all_other_urls = list(set(extracted_other_urls))
                
                # 参考リンク情報を整理
                reference_links = []
                for doc in relevant_docs:
                    doc_links = {
                        'title': doc.get('title', '無題'),
                        'links': []
                    }
                    
                    # Utage URL
                    if doc.get('url'):
                        doc_links['links'].append({
                            'type': 'utage',
                            'url': doc['url']
                        })
                    
                    # YouTube URL (メタデータ)
                    if doc.get('youtube_url'):
                        doc_links['links'].append({
                            'type': 'youtube',
                            'url': doc['youtube_url']
                        })
                    
                    # コンテンツ内のYouTube URL
                    content_youtube = extract_youtube_urls(doc['content'])
                    for url in content_youtube:
                        doc_links['links'].append({
                            'type': 'youtube',
                            'url': url
                        })
                    
                    # コンテンツ内の資料URL
                    content_other = extract_all_urls(doc['content'])
                    for url in content_other:
                        doc_links['links'].append({
                            'type': 'resource',
                            'url': url
                        })
                    
                    if doc_links['links']:
                        reference_links.append(doc_links)
                
                # リンク情報を含むプロンプト
                links_context = ""
                if reference_links:
                    links_context = "\n\n【参考リンク】\n"
                    for ref in reference_links:
                        links_context += f"\n教材「{ref['title']}」の関連リンク:\n"
                        for link in ref['links']:
                            if link['type'] == 'youtube':
                                links_context += f"- YouTube動画: {link['url']}\n"
                            elif link['type'] == 'resource':
                                links_context += f"- 参考資料: {link['url']}\n"
                            elif link['type'] == 'utage':
                                links_context += f"- Utageリンク: {link['url']}\n"
                
                system_prompt = f"""
                あなたはブログスクールの講師アシスタントです。
                以下の教材内容を【厳密に】参考にして、生徒の質問に答えてください。
                
                【重要な指示】
                1. 教材の内容を正確に理解し、その通りに伝える
                2. 教材の意図や文脈を正しく把握する
                3. 教材に書かれていることと逆の内容を言わない
                4. 勝手な解釈や創作をしない
                5. 教材の例示は、その意図（良い例/悪い例）を正確に理解して使用する
                6. 関連するURLがある場合は、説明の該当箇所に自然に埋め込んで紹介する
                
                【教材内容】
                {context}
                {links_context}
                
                【回答ルール】
                - 教材の内容を忠実に反映する
                - 「〜というタイトルのように」などの具体例は、教材に明記されているもののみ使用
                - 「驚きの事実」「知られざるエピソード」などのフレーズについて、教材で推奨/非推奨が明記されている場合はその通りに説明
                - 教材にない情報は「教材には記載がありません」と明確に伝える
                - 教材の文章をそのまま引用する場合は「教材では『〜』と説明されています」と明記
                - 参考リンクがある場合は、関連する説明の箇所で「詳しくは[こちらの動画]({url})をご覧ください」のように自然に紹介
                """
                
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                answer = response.choices[0].message.content
                
                # 参照した教材を表示
                if relevant_docs:
                    with st.expander("📚 参照した教材", expanded=False):
                        for i, doc in enumerate(relevant_docs[:3], 1):
                            st.markdown(f"**{i}. {doc.get('title', '無題')}**")
                            st.caption(f"関連度スコア: {1 - doc.get('score', 1):.2%}")
                            st.text(doc['content'][:200] + "...")
                            if doc.get('url'):
                                st.markdown(f"[Utageリンク]({doc['url']})")
                            if doc.get('youtube_url'):
                                st.markdown(f"[🎥 YouTube動画]({doc['youtube_url']})")
                            
                            # テキスト内のYouTube URLと資料URLも表示（URLを表示）
                            content_youtube_urls = extract_youtube_urls(doc['content'])
                            for url in content_youtube_urls:
                                st.markdown(f"🎬 YouTube: {url}")
                            
                            content_other_urls = extract_all_urls(doc['content'])
                            for url in content_other_urls:
                                # URLからドメインを抽出して表示
                                domain = url.split('/')[2] if len(url.split('/')) > 2 else url
                                st.markdown(f"📄 資料: {url}")
                            
                            st.divider()
                
                # 回答の最後には参考リンクを追加しない（本文中に埋め込まれているため）
                
                st.markdown(answer)
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                logger.log_question(prompt, answer, urls)
                
            except Exception as e:
                error_msg = f"エラーが発生しました: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})