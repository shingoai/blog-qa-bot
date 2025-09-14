import streamlit as st
import pandas as pd
from components.question_logger import QuestionLogger
from utils.auth import check_password
from datetime import datetime, timedelta
import json
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

st.set_page_config(
    page_title="質問分析",
    page_icon="📊",
    layout="wide"
)

if not check_password(require_admin=True):
    st.stop()

st.title("📊 質問分析ダッシュボード")
st.markdown("生徒からの質問を分析し、教材改善に活用します。")

@st.cache_resource
def init_logger():
    return QuestionLogger()

logger = init_logger()

# カテゴリ分類用のキーワード
CATEGORY_KEYWORDS = {
    "WordPress": ["wordpress", "wp", "プラグイン", "テーマ"],
    "SEO": ["seo", "検索", "キーワード", "順位", "google"],
    "タイトル": ["タイトル", "見出し", "題名", "件名"],
    "記事作成": ["記事", "執筆", "文章", "ライティング", "書き方"],
    "ブログ運営": ["運営", "収益", "アクセス", "pv", "広告"],
    "技術的な質問": ["エラー", "設定", "インストール", "バグ", "不具合"],
    "その他": []
}

def categorize_question(question):
    """質問をカテゴリに分類"""
    question_lower = question.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == "その他":
            continue
        for keyword in keywords:
            if keyword in question_lower:
                return category
    return "その他"

def extract_keywords(text, top_n=10):
    """テキストから頻出キーワードを抽出"""
    # 日本語の単語を抽出（簡易版）
    words = re.findall(r'[ぁ-んァ-ヶー一-龥]+', text)
    # 2文字以上の単語のみ
    words = [w for w in words if len(w) >= 2]
    # ストップワード除去（簡易版）
    stop_words = ['です', 'ます', 'こと', 'もの', 'これ', 'それ', 'あれ', 'という', 'ような']
    words = [w for w in words if w not in stop_words]
    
    word_count = Counter(words)
    return word_count.most_common(top_n)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 統計概要", "📊 詳細分析", "❓ よくある質問", 
    "🔍 質問検索", "🏷️ カテゴリ分析", "📥 エクスポート"
])

with tab1:
    st.header("統計概要")
    
    stats = logger.get_stats()
    all_logs = logger.get_all_logs()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総質問数", stats["total_questions"])
    
    with col2:
        st.metric("ユニークな質問", stats["unique_questions"])
    
    with col3:
        st.metric("平均質問/日", stats["avg_questions_per_day"])
    
    with col4:
        response_rate = (stats["unique_questions"] / stats["total_questions"] * 100) if stats["total_questions"] > 0 else 0
        st.metric("回答カバー率", f"{response_rate:.1f}%")
    
    st.divider()
    
    # 時系列グラフ
    if all_logs:
        st.subheader("📅 質問数の推移")
        
        # データフレーム作成
        df = pd.DataFrame(all_logs)
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_counts = df.groupby('date').size().reset_index(name='count')
        
        # グラフ作成
        fig = px.line(daily_counts, x='date', y='count', 
                     title='日別質問数',
                     labels={'date': '日付', 'count': '質問数'})
        fig.update_traces(mode='lines+markers')
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("🕐 最近の質問（直近10件）")
    recent_logs = logger.get_recent_logs(10)
    
    if recent_logs:
        for log in recent_logs:
            category = categorize_question(log['question'])
            with st.expander(f"[{category}] {log['question'][:50]}..."):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write("**質問:**", log['question'])
                    st.write("**回答:**", log['answer'][:200] + "...")
                with col2:
                    st.caption(f"📅 {log['timestamp'][:19]}")
                    st.caption(f"🏷️ {category}")
    else:
        st.info("まだ質問がありません。")

with tab2:
    st.header("📊 詳細分析")
    
    if all_logs:
        # 時間帯別分析
        st.subheader("⏰ 時間帯別質問数")
        df = pd.DataFrame(all_logs)
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        hourly_counts = df.groupby('hour').size().reset_index(name='count')
        
        fig = px.bar(hourly_counts, x='hour', y='count',
                    title='時間帯別質問数',
                    labels={'hour': '時間', 'count': '質問数'})
        st.plotly_chart(fig, use_container_width=True)
        
        # 曜日別分析
        st.subheader("📅 曜日別質問数")
        df['weekday'] = pd.to_datetime(df['timestamp']).dt.day_name()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_counts = df.groupby('weekday').size().reindex(weekday_order, fill_value=0).reset_index(name='count')
        weekday_counts['weekday_jp'] = ['月', '火', '水', '木', '金', '土', '日']
        
        fig = px.bar(weekday_counts, x='weekday_jp', y='count',
                    title='曜日別質問数',
                    labels={'weekday_jp': '曜日', 'count': '質問数'})
        st.plotly_chart(fig, use_container_width=True)
        
        # 質問の長さ分析
        st.subheader("📏 質問の長さ分布")
        df['question_length'] = df['question'].str.len()
        
        fig = px.histogram(df, x='question_length', nbins=20,
                          title='質問の文字数分布',
                          labels={'question_length': '文字数', 'count': '質問数'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("分析するデータがありません。")

with tab3:
    st.header("❓ よくある質問の傾向")
    
    if all_logs:
        # 質問のグループ化（類似質問をまとめる）
        question_groups = {}
        
        # キーワードベースでグループ化
        for log in all_logs:
            question = log['question']
            # 主要キーワードを抽出
            keywords = extract_keywords(question, 3)
            if keywords:
                main_keyword = keywords[0][0]  # 最頻出キーワード
                if main_keyword not in question_groups:
                    question_groups[main_keyword] = {
                        'questions': [],
                        'count': 0,
                        'category': categorize_question(question)
                    }
                question_groups[main_keyword]['questions'].append(question)
                question_groups[main_keyword]['count'] += 1
        
        # 頻度順にソート
        sorted_groups = sorted(question_groups.items(), key=lambda x: x[1]['count'], reverse=True)
        
        if sorted_groups:
            # 上位トピックの円グラフ
            top_topics = sorted_groups[:10]
            df_topics = pd.DataFrame([
                {'topic': topic, 'count': data['count']} 
                for topic, data in top_topics
            ])
            
            fig = px.pie(df_topics, values='count', names='topic',
                        title='よく質問されるトピック TOP 10')
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # トピック別詳細
            st.subheader("📌 よく質問されるトピック")
            
            for i, (topic, data) in enumerate(top_topics[:10], 1):
                with st.expander(f"{i}. 「{topic}」に関する質問 ({data['count']}件)"):
                    st.write(f"**カテゴリ:** {data['category']}")
                    st.write(f"**質問数:** {data['count']}件")
                    st.write("**代表的な質問:**")
                    
                    # ユニークな質問を表示（最大5件）
                    unique_questions = list(set(data['questions']))[:5]
                    for q in unique_questions:
                        st.write(f"• {q[:100]}...")
                    
                    # このトピックの回答改善提案
                    if data['count'] >= 3:
                        st.info(f"💡 「{topic}」に関する質問が多いため、この内容を教材で詳しく説明することをお勧めします。")
        
        # 全体的な傾向分析
        st.divider()
        st.subheader("📊 質問傾向の分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 単発質問 vs 繰り返し質問
            unique_questions = set([log['question'] for log in all_logs])
            repeat_rate = (1 - len(unique_questions) / len(all_logs)) * 100 if all_logs else 0
            
            st.metric("繰り返し質問率", f"{repeat_rate:.1f}%", 
                     help="同じ質問が繰り返される割合。高い場合は教材の改善が必要かもしれません。")
        
        with col2:
            # 平均質問長
            avg_length = sum(len(log['question']) for log in all_logs) / len(all_logs) if all_logs else 0
            st.metric("平均質問文字数", f"{avg_length:.0f}文字",
                     help="質問の複雑さの指標。長い質問が多い場合は、より詳細な説明が必要かもしれません。")
        
        # 改善提案
        st.divider()
        st.subheader("💡 教材改善の提案")
        
        suggestions = []
        
        # トピック別の提案
        for topic, data in sorted_groups[:5]:
            if data['count'] >= 3:
                suggestions.append(f"• 「{topic}」について専用のレッスンを追加")
        
        # カテゴリ別の提案
        categories = [categorize_question(log['question']) for log in all_logs]
        category_counts = Counter(categories)
        for category, count in category_counts.most_common(3):
            if count >= 5:
                suggestions.append(f"• {category}カテゴリの内容を充実")
        
        if suggestions:
            for suggestion in suggestions[:5]:
                st.write(suggestion)
        else:
            st.info("現在のところ、特に改善が必要な箇所は見つかりません。")
    else:
        st.info("まだデータがありません。")

with tab4:
    st.header("🔍 質問検索")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_keyword = st.text_input("検索キーワード", placeholder="例: WordPress, タイトル, SEO")
    with col2:
        search_category = st.selectbox("カテゴリフィルタ", ["すべて"] + list(CATEGORY_KEYWORDS.keys()))
    
    if search_keyword or search_category != "すべて":
        results = logger.search_logs(search_keyword) if search_keyword else logger.get_all_logs()
        
        # カテゴリフィルタ
        if search_category != "すべて":
            results = [log for log in results if categorize_question(log['question']) == search_category]
        
        if results:
            st.success(f"{len(results)}件の質問が見つかりました。")
            
            # ページネーション
            items_per_page = 10
            total_pages = (len(results) - 1) // items_per_page + 1
            page = st.number_input("ページ", min_value=1, max_value=total_pages, value=1)
            
            start_idx = (page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(results))
            
            for log in results[start_idx:end_idx]:
                category = categorize_question(log['question'])
                with st.expander(f"[{category}] {log['question'][:50]}..."):
                    st.write("**質問:**", log['question'])
                    st.write("**回答:**", log['answer'])
                    st.caption(f"📅 {log['timestamp'][:19]}")
        else:
            st.warning("該当する質問が見つかりませんでした。")

with tab5:
    st.header("🏷️ カテゴリ分析")
    
    if all_logs:
        # カテゴリ別集計
        categories = [categorize_question(log['question']) for log in all_logs]
        category_counts = Counter(categories)
        
        # 円グラフ
        st.subheader("カテゴリ別質問割合")
        df_cat = pd.DataFrame(category_counts.items(), columns=['category', 'count'])
        fig = px.pie(df_cat, values='count', names='category',
                    title='カテゴリ別質問の割合')
        st.plotly_chart(fig, use_container_width=True)
        
        # カテゴリ別詳細
        st.subheader("カテゴリ別詳細")
        for category, count in category_counts.most_common():
            with st.expander(f"{category} ({count}件)"):
                category_logs = [log for log in all_logs if categorize_question(log['question']) == category]
                
                # このカテゴリの最頻出キーワード
                all_text = " ".join([log['question'] for log in category_logs])
                keywords = extract_keywords(all_text, 5)
                
                if keywords:
                    st.write("**頻出キーワード:**")
                    keyword_str = ", ".join([f"{word} ({count}回)" for word, count in keywords])
                    st.write(keyword_str)
                
                st.write("**最近の質問:**")
                for log in category_logs[:3]:
                    st.write(f"• {log['question'][:100]}...")
        
        # キーワード分析
        st.divider()
        st.subheader("🔤 全体キーワード分析")
        all_questions = " ".join([log['question'] for log in all_logs])
        top_keywords = extract_keywords(all_questions, 20)
        
        if top_keywords:
            df_keywords = pd.DataFrame(top_keywords, columns=['keyword', 'count'])
            fig = px.bar(df_keywords.head(10), x='count', y='keyword', orientation='h',
                        title='頻出キーワード TOP 10',
                        labels={'keyword': 'キーワード', 'count': '出現回数'})
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("分析するデータがありません。")

with tab6:
    st.header("📥 データエクスポート")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 CSVでダウンロード", type="primary", use_container_width=True):
            filename = logger.export_to_csv()
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    csv_data = f.read()
                st.download_button(
                    label="💾 CSVファイルをダウンロード",
                    data=csv_data,
                    file_name=f"question_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                st.success("CSVファイルを生成しました。")
            else:
                st.warning("エクスポートするデータがありません。")
    
    with col2:
        if st.button("📥 JSONでダウンロード", type="primary", use_container_width=True):
            logs = logger.get_all_logs()
            if logs:
                json_data = json.dumps(logs, ensure_ascii=False, indent=2)
                st.download_button(
                    label="💾 JSONファイルをダウンロード",
                    data=json_data,
                    file_name=f"question_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                st.success("JSONファイルを生成しました。")
            else:
                st.warning("エクスポートするデータがありません。")
    
    with col3:
        if st.button("📥 分析レポート生成", type="primary", use_container_width=True):
            if all_logs:
                # 分析レポート作成
                report = f"""# 質問分析レポート
生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## 統計概要
- 総質問数: {stats['total_questions']}件
- ユニークな質問数: {stats['unique_questions']}件
- 1日あたりの平均質問数: {stats['avg_questions_per_day']}件

## カテゴリ別分析
"""
                categories = [categorize_question(log['question']) for log in all_logs]
                category_counts = Counter(categories)
                for cat, count in category_counts.most_common():
                    report += f"- {cat}: {count}件 ({count/len(all_logs)*100:.1f}%)\n"
                
                report += "\n## 頻出キーワード TOP 10\n"
                all_questions = " ".join([log['question'] for log in all_logs])
                top_keywords = extract_keywords(all_questions, 10)
                for keyword, count in top_keywords:
                    report += f"- {keyword}: {count}回\n"
                
                st.download_button(
                    label="💾 分析レポートをダウンロード",
                    data=report,
                    file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
                st.success("分析レポートを生成しました。")
            else:
                st.warning("分析するデータがありません。")

st.sidebar.info("""
**💡 分析のポイント:**

1. **カテゴリ分析**: 質問の傾向を把握
2. **時系列分析**: 質問が多い時間帯を特定
3. **キーワード分析**: 注目トピックを発見
4. **頻出質問**: 教材改善のヒント

定期的にレポートを生成して、教材改善に活用しましょう！
""")