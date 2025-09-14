import streamlit as st
import json
import os
from datetime import datetime
from components.knowledge_base import KnowledgeBase
from utils.auth import check_password
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

st.set_page_config(
    page_title="データ管理",
    page_icon="💾",
    layout="wide"
)

if not check_password(require_admin=True):
    st.stop()

st.title("💾 データ管理")
st.markdown("教材データのエクスポート・インポート")

def init_knowledge_base():
    return KnowledgeBase()

kb = init_knowledge_base()

tab1, tab2 = st.tabs(["📤 エクスポート", "📥 インポート"])

with tab1:
    st.header("データエクスポート")
    st.info("現在のChromaDBに登録されている全教材をJSONファイルとしてダウンロードします。")
    
    if st.button("📤 教材データをエクスポート", type="primary"):
        try:
            # ChromaDBから全データを取得
            all_data = kb.collection.get()
            
            if all_data and all_data['metadatas']:
                # 教材ごとにまとめる
                contents = {}
                for i, metadata in enumerate(all_data['metadatas']):
                    key = f"{metadata.get('chapter', '')}_{metadata.get('lesson', '')}_{metadata.get('title', '')}"
                    
                    if key not in contents:
                        contents[key] = {
                            'chapter': metadata.get('chapter', ''),
                            'chapter_order': metadata.get('chapter_order', 0),
                            'lesson': metadata.get('lesson', ''),
                            'lesson_order': metadata.get('lesson_order', 0),
                            'title': metadata.get('title', ''),
                            'doc_type': metadata.get('doc_type', 'text'),
                            'url': metadata.get('url', ''),
                            'youtube_url': metadata.get('youtube_url', ''),
                            'chunks': []
                        }
                    
                    contents[key]['chunks'].append({
                        'index': metadata.get('chunk_index', 0),
                        'content': all_data['documents'][i]
                    })
                
                # チャンクを結合して完全なコンテンツを復元
                export_data = []
                for key, data in contents.items():
                    chunks = sorted(data['chunks'], key=lambda x: x['index'])
                    full_content = '\n'.join([c['content'] for c in chunks])
                    
                    export_data.append({
                        'chapter': data['chapter'],
                        'chapter_order': data['chapter_order'],
                        'lesson': data['lesson'],
                        'lesson_order': data['lesson_order'],
                        'title': data['title'],
                        'doc_type': data['doc_type'],
                        'url': data['url'],
                        'youtube_url': data['youtube_url'],
                        'content': full_content
                    })
                
                # JSONとして出力
                json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                
                # ダウンロードボタン
                st.download_button(
                    label="📥 JSONファイルをダウンロード",
                    data=json_str,
                    file_name=f"blog_qa_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                st.success(f"✅ {len(export_data)}件の教材データをエクスポートしました。")
                
                # プレビュー
                with st.expander("データプレビュー"):
                    st.json(export_data[:2])  # 最初の2件だけ表示
            else:
                st.warning("エクスポートする教材データがありません。")
                
        except Exception as e:
            st.error(f"エクスポート中にエラーが発生しました: {str(e)}")

with tab2:
    st.header("データインポート")
    st.warning("⚠️ インポートすると既存のデータは全て削除されます。")
    
    uploaded_file = st.file_uploader("JSONファイルを選択", type=['json'])
    
    if uploaded_file is not None:
        try:
            # JSONファイルを読み込み
            json_data = json.loads(uploaded_file.read())
            
            # データプレビュー
            st.write(f"📊 {len(json_data)}件の教材データが見つかりました。")
            
            # データフレームで表示
            df_preview = pd.DataFrame(json_data)[['chapter', 'lesson', 'title', 'doc_type']]
            st.dataframe(df_preview)
            
            if st.button("📥 インポート実行", type="primary"):
                with st.spinner("インポート中..."):
                    # 既存データをクリア
                    kb.clear_all()
                    
                    # 新しいデータを追加
                    success_count = 0
                    for item in json_data:
                        try:
                            kb.add_document(
                                content=item['content'],
                                title=item['title'],
                                url=item.get('url', ''),
                                doc_type=item.get('doc_type', 'text'),
                                chapter=item.get('chapter', ''),
                                lesson=item.get('lesson', ''),
                                chapter_order=item.get('chapter_order', 0),
                                lesson_order=item.get('lesson_order', 0),
                                youtube_url=item.get('youtube_url', '')
                            )
                            success_count += 1
                        except Exception as e:
                            st.error(f"エラー: {item['title']} - {str(e)}")
                    
                    st.success(f"✅ {success_count}/{len(json_data)}件の教材をインポートしました。")
                    st.balloons()
                    
        except json.JSONDecodeError:
            st.error("無効なJSONファイルです。")
        except Exception as e:
            st.error(f"インポート中にエラーが発生しました: {str(e)}")

st.sidebar.info("""
**💡 使い方:**

**エクスポート:**
1. 現在の教材データをJSONファイルとして保存
2. バックアップや他環境への移行に使用

**インポート:**
1. JSONファイルから教材データを復元
2. **注意**: 既存データは全て削除されます

**推奨ワークフロー:**
1. ローカルで教材を登録
2. エクスポートしてJSONファイルを保存
3. Streamlit Cloudでインポート
""")