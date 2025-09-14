import os
from typing import List, Dict, Optional
from supabase import create_client, Client
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import json

class KnowledgeBaseSupabase:
    def __init__(self):
        # Supabaseクライアントの初期化
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(url, key)
        
        # OpenAI Embeddingsの初期化
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # テキスト分割器の初期化
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "、", " ", ""]
        )
    
    def add_document(self, content: str, title: str, url: str = None, doc_type: str = "text",
                    chapter: str = None, lesson: str = None, chapter_order: int = 0,
                    lesson_order: int = 0, youtube_url: str = None):
        """教材を追加"""
        try:
            # 1. contentsテーブルに保存
            content_data = {
                "chapter": chapter or "",
                "chapter_order": chapter_order,
                "lesson": lesson or "",
                "lesson_order": lesson_order,
                "title": title,
                "content": content,
                "doc_type": doc_type,
                "url": url or None,
                "youtube_url": youtube_url or None
            }
            
            # Upsert（存在する場合は更新、しない場合は新規作成）
            result = self.supabase.table("contents").upsert(
                content_data,
                on_conflict="chapter,lesson,title"
            ).execute()
            
            if not result.data:
                raise Exception("Failed to insert content")
            
            content_id = result.data[0]["id"]
            
            # 2. テキストをチャンクに分割
            chunks = self.text_splitter.split_text(content)
            
            # 3. 既存のembeddingsを削除
            self.supabase.table("content_embeddings").delete().eq(
                "content_id", content_id
            ).execute()
            
            # 4. 各チャンクのembeddingを作成して保存
            embeddings_data = []
            for i, chunk in enumerate(chunks):
                embedding = self.embeddings.embed_query(chunk)
                
                embeddings_data.append({
                    "content_id": content_id,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "embedding": embedding
                })
            
            # バッチ挿入
            if embeddings_data:
                self.supabase.table("content_embeddings").insert(
                    embeddings_data
                ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error adding document: {str(e)}")
            return False
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """質問に対して関連する教材を検索"""
        try:
            # クエリのembeddingを生成
            query_embedding = self.embeddings.embed_query(query)
            
            # まずRPC関数を試す
            try:
                results = self.supabase.rpc(
                    "match_documents",
                    {
                        "query_embedding": query_embedding,
                        "match_count": n_results
                    }
                ).execute()
                
                if results.data:
                    # RPC関数の結果を正しい形式に変換
                    docs = []
                    for item in results.data:
                        docs.append({
                            'content': item.get('chunk_text', ''),
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'youtube_url': item.get('youtube_url', ''),
                            'score': 1 - item.get('similarity', 0)
                        })
                    return docs
            except:
                pass  # RPC関数がない場合は次の方法を試す
            
            # RPC関数がない場合は全embeddings取得して手動で類似度計算
            embeddings_result = self.supabase.table("content_embeddings").select(
                "*, contents!inner(*)"
            ).limit(100).execute()
            
            if embeddings_result.data:
                import numpy as np
                
                docs = []
                for item in embeddings_result.data:
                    if item.get('embedding') and item.get('contents'):
                        # コサイン類似度を計算
                        try:
                            similarity = np.dot(query_embedding, item['embedding']) / (
                                np.linalg.norm(query_embedding) * np.linalg.norm(item['embedding'])
                            )
                        except:
                            similarity = 0
                        
                        docs.append({
                            'content': item.get('chunk_text', ''),
                            'title': item['contents'].get('title', ''),
                            'url': item['contents'].get('url', ''),
                            'youtube_url': item['contents'].get('youtube_url', ''),
                            'score': 1 - similarity  # 距離に変換
                        })
                
                # スコアでソート
                docs.sort(key=lambda x: x['score'])
                return docs[:n_results]
            
            return []
            
        except Exception as e:
            print(f"Error searching: {str(e)}")
            # エラー時は空のリストを返す
            return []
    
    def get_chapters_and_lessons(self):
        """章とレッスンの一覧を取得"""
        try:
            result = self.supabase.table("contents").select(
                "chapter, chapter_order, lesson, lesson_order, doc_type"
            ).execute()
            
            chapters = {}
            for item in result.data:
                chapter = item['chapter']
                lesson = item['lesson']
                
                if chapter not in chapters:
                    chapters[chapter] = {
                        'order': item['chapter_order'],
                        'lessons': {}
                    }
                
                if lesson not in chapters[chapter]['lessons']:
                    chapters[chapter]['lessons'][lesson] = {
                        'order': item['lesson_order'],
                        'doc_types': set()
                    }
                
                chapters[chapter]['lessons'][lesson]['doc_types'].add(item['doc_type'])
            
            # Setをlistに変換
            for chapter in chapters.values():
                for lesson in chapter['lessons'].values():
                    lesson['doc_types'] = list(lesson['doc_types'])
            
            return chapters
            
        except Exception as e:
            print(f"Error getting chapters: {str(e)}")
            return {}
    
    def get_content_by_chapter_lesson(self, chapter: str, lesson: str):
        """特定の章とレッスンのコンテンツを取得"""
        try:
            result = self.supabase.table("contents").select("*").eq(
                "chapter", chapter
            ).eq("lesson", lesson).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting content: {str(e)}")
            return []
    
    def delete_content(self, chapter: str, lesson: str, title: str):
        """コンテンツを削除"""
        try:
            result = self.supabase.table("contents").delete().eq(
                "chapter", chapter
            ).eq("lesson", lesson).eq("title", title).execute()
            
            return True if result.data else False
            
        except Exception as e:
            print(f"Error deleting content: {str(e)}")
            return False
    
    def update_content(self, old_chapter: str, old_lesson: str, old_title: str,
                      new_content: str = None, new_title: str = None,
                      new_url: str = None, new_doc_type: str = None,
                      new_chapter: str = None, new_lesson: str = None,
                      new_chapter_order: int = None, new_lesson_order: int = None,
                      new_youtube_url: str = None):
        """コンテンツを更新"""
        try:
            # 既存のコンテンツを取得
            existing = self.supabase.table("contents").select("*").eq(
                "chapter", old_chapter
            ).eq("lesson", old_lesson).eq("title", old_title).execute()
            
            if not existing.data:
                return False
            
            content_id = existing.data[0]["id"]
            
            # 更新データを準備
            update_data = {}
            if new_content is not None:
                update_data["content"] = new_content
            if new_title is not None:
                update_data["title"] = new_title
            if new_url is not None:
                update_data["url"] = new_url
            if new_doc_type is not None:
                update_data["doc_type"] = new_doc_type
            if new_chapter is not None:
                update_data["chapter"] = new_chapter
            if new_lesson is not None:
                update_data["lesson"] = new_lesson
            if new_chapter_order is not None:
                update_data["chapter_order"] = new_chapter_order
            if new_lesson_order is not None:
                update_data["lesson_order"] = new_lesson_order
            if new_youtube_url is not None:
                update_data["youtube_url"] = new_youtube_url
            
            # コンテンツを更新
            self.supabase.table("contents").update(update_data).eq(
                "id", content_id
            ).execute()
            
            # コンテンツが更新された場合は埋め込みも更新
            if new_content:
                # 既存のembeddingsを削除
                self.supabase.table("content_embeddings").delete().eq(
                    "content_id", content_id
                ).execute()
                
                # 新しいembeddingsを作成
                chunks = self.text_splitter.split_text(new_content)
                embeddings_data = []
                
                for i, chunk in enumerate(chunks):
                    embedding = self.embeddings.embed_query(chunk)
                    embeddings_data.append({
                        "content_id": content_id,
                        "chunk_index": i,
                        "chunk_text": chunk,
                        "embedding": embedding
                    })
                
                if embeddings_data:
                    self.supabase.table("content_embeddings").insert(
                        embeddings_data
                    ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error updating content: {str(e)}")
            return False
    
    def clear_all(self):
        """全データを削除"""
        try:
            # contentsを削除（カスケードでembeddingsも削除される）
            self.supabase.table("contents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            return True
        except Exception as e:
            print(f"Error clearing all: {str(e)}")
            return False
    
    def get_stats(self):
        """統計情報を取得"""
        try:
            contents_result = self.supabase.table("contents").select("id", count="exact").execute()
            embeddings_result = self.supabase.table("content_embeddings").select("id", count="exact").execute()
            
            return {
                "total_contents": contents_result.count if contents_result else 0,
                "total_chunks": embeddings_result.count if embeddings_result else 0,
                "collection_name": "Supabase Database"
            }
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
            return {
                "total_contents": 0,
                "total_chunks": 0,
                "collection_name": "Supabase Database"
            }