"""
ChromaDBからSupabaseへのデータ移行スクリプト
"""
import os
import sys
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from components.knowledge_base import KnowledgeBase
from components.knowledge_base_supabase import KnowledgeBaseSupabase

def migrate_data():
    print("データ移行を開始します...")
    
    # ChromaDBからデータを取得
    print("1. ChromaDBからデータを取得中...")
    kb_old = KnowledgeBase()
    
    try:
        all_data = kb_old.collection.get()
        
        if not all_data or not all_data['metadatas']:
            print("移行するデータがありません。")
            return
        
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
        
        print(f"  {len(contents)}件の教材が見つかりました。")
        
        # Supabaseに移行
        print("2. Supabaseにデータを移行中...")
        kb_new = KnowledgeBaseSupabase()
        
        success_count = 0
        for key, data in contents.items():
            # チャンクを結合して完全なコンテンツを復元
            chunks = sorted(data['chunks'], key=lambda x: x['index'])
            full_content = '\n'.join([c['content'] for c in chunks])
            
            print(f"  移行中: {data['title']}...")
            
            # Supabaseに追加
            result = kb_new.add_document(
                content=full_content,
                title=data['title'],
                url=data['url'] if data['url'] else None,
                doc_type=data['doc_type'],
                chapter=data['chapter'],
                lesson=data['lesson'],
                chapter_order=data['chapter_order'],
                lesson_order=data['lesson_order'],
                youtube_url=data['youtube_url'] if data['youtube_url'] else None
            )
            
            if result:
                success_count += 1
                print(f"    ✅ 成功")
            else:
                print(f"    ❌ 失敗")
        
        print(f"\n移行完了: {success_count}/{len(contents)}件が成功しました。")
        
        # 統計情報を表示
        stats = kb_new.get_stats()
        print(f"\nSupabaseの統計:")
        print(f"  コンテンツ数: {stats['total_contents']}")
        print(f"  チャンク数: {stats['total_chunks']}")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_data()