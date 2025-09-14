import chromadb
import os
from typing import List, Dict
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import json

class KnowledgeBase:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        try:
            self.collection = self.client.get_collection("blog_school_docs")
        except:
            self.collection = self.client.create_collection(
                name="blog_school_docs",
                metadata={"hnsw:space": "cosine"}
            )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "、", " ", ""]
        )
    
    def add_document(self, content: str, title: str, url: str = None, doc_type: str = "text", 
                    chapter: str = None, lesson: str = None, chapter_order: int = 0, 
                    lesson_order: int = 0, youtube_url: str = None):
        chunks = self.text_splitter.split_text(content)
        
        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(f"{chapter}_{lesson}_{title}_{i}_{chunk[:50]}".encode()).hexdigest()
            
            metadata = {
                "title": title,
                "chunk_index": i,
                "doc_type": doc_type,
                "url": url or "",
                "youtube_url": youtube_url or "",
                "total_chunks": len(chunks),
                "chapter": chapter or "",
                "lesson": lesson or "",
                "chapter_order": chapter_order,
                "lesson_order": lesson_order
            }
            
            embedding = self.embeddings.embed_query(chunk)
            
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[metadata]
            )
    
    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        query_embedding = self.embeddings.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        docs = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                docs.append({
                    'content': doc,
                    'title': metadata.get('title', ''),
                    'url': metadata.get('url', ''),
                    'youtube_url': metadata.get('youtube_url', ''),
                    'score': results['distances'][0][i] if results['distances'] else 0
                })
        
        return docs
    
    def clear_all(self):
        try:
            self.client.delete_collection("blog_school_docs")
            self.collection = self.client.create_collection(
                name="blog_school_docs",
                metadata={"hnsw:space": "cosine"}
            )
        except:
            pass
    
    def get_stats(self):
        """統計情報を取得（コンテンツ数とチャンク数を分けて表示）"""
        try:
            all_data = self.collection.get()
            unique_contents = set()
            total_chunks = 0
            
            if all_data and all_data['metadatas']:
                for metadata in all_data['metadatas']:
                    # ユニークなコンテンツを識別（章+レッスン+タイトル）
                    content_key = f"{metadata.get('chapter', '')}_{metadata.get('lesson', '')}_{metadata.get('title', '')}"
                    unique_contents.add(content_key)
                    total_chunks += 1
            
            return {
                "total_contents": len(unique_contents),  # 実際のコンテンツ数
                "total_chunks": total_chunks,  # チャンク総数
                "collection_name": "blog_school_docs"
            }
        except:
            return {
                "total_contents": 0,
                "total_chunks": 0,
                "collection_name": "blog_school_docs"
            }
    
    def get_chapters_and_lessons(self):
        """章とレッスンの一覧を取得"""
        try:
            all_data = self.collection.get()
            chapters = {}
            
            if all_data and all_data['metadatas']:
                for metadata in all_data['metadatas']:
                    chapter = metadata.get('chapter', '')
                    lesson = metadata.get('lesson', '')
                    chapter_order = metadata.get('chapter_order', 0)
                    lesson_order = metadata.get('lesson_order', 0)
                    
                    if chapter:
                        if chapter not in chapters:
                            chapters[chapter] = {
                                'order': chapter_order,
                                'lessons': {}
                            }
                        
                        if lesson and lesson not in chapters[chapter]['lessons']:
                            chapters[chapter]['lessons'][lesson] = {
                                'order': lesson_order,
                                'doc_types': set()
                            }
                            
                        if lesson:
                            chapters[chapter]['lessons'][lesson]['doc_types'].add(
                                metadata.get('doc_type', 'text')
                            )
            
            # Convert sets to lists for JSON serialization
            for chapter in chapters.values():
                for lesson in chapter['lessons'].values():
                    lesson['doc_types'] = list(lesson['doc_types'])
            
            return chapters
        except Exception as e:
            return {}
    
    def get_content_by_chapter_lesson(self, chapter: str, lesson: str):
        """特定の章とレッスンのコンテンツを取得"""
        try:
            all_data = self.collection.get()
            contents = []
            
            if all_data and all_data['metadatas']:
                for i, metadata in enumerate(all_data['metadatas']):
                    if metadata.get('chapter') == chapter and metadata.get('lesson') == lesson:
                        if metadata.get('chunk_index', 0) == 0:  # 最初のチャンクのみ
                            content_data = {
                                'id': all_data['ids'][i],
                                'title': metadata.get('title', ''),
                                'doc_type': metadata.get('doc_type', 'text'),
                                'url': metadata.get('url', ''),
                                'youtube_url': metadata.get('youtube_url', ''),
                                'chapter_order': metadata.get('chapter_order', 0),
                                'lesson_order': metadata.get('lesson_order', 0),
                                'content': self._get_full_content(all_data, metadata.get('title'))
                            }
                            contents.append(content_data)
            
            return contents
        except Exception as e:
            return []
    
    def _get_full_content(self, all_data, title):
        """タイトルに基づいて全チャンクを結合"""
        chunks = []
        for i, metadata in enumerate(all_data['metadatas']):
            if metadata.get('title') == title:
                chunks.append((metadata.get('chunk_index', 0), all_data['documents'][i]))
        
        chunks.sort(key=lambda x: x[0])
        return '\n'.join([chunk[1] for chunk in chunks])
    
    def delete_content(self, chapter: str, lesson: str, title: str):
        """特定のコンテンツを削除"""
        try:
            all_data = self.collection.get()
            ids_to_delete = []
            
            if all_data and all_data['metadatas']:
                for i, metadata in enumerate(all_data['metadatas']):
                    if (metadata.get('chapter') == chapter and 
                        metadata.get('lesson') == lesson and 
                        metadata.get('title') == title):
                        ids_to_delete.append(all_data['ids'][i])
            
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                return True
            return False
        except Exception as e:
            return False
    
    def update_content(self, old_chapter: str, old_lesson: str, old_title: str,
                       new_content: str, new_title: str, new_url: str = None, 
                       new_doc_type: str = "text", new_chapter: str = None, 
                       new_lesson: str = None, new_chapter_order: int = 0, 
                       new_lesson_order: int = 0, new_youtube_url: str = None):
        """コンテンツを更新"""
        # まず古いコンテンツを削除
        self.delete_content(old_chapter, old_lesson, old_title)
        
        # 新しいコンテンツを追加
        self.add_document(
            content=new_content,
            title=new_title,
            url=new_url,
            doc_type=new_doc_type,
            chapter=new_chapter or old_chapter,
            lesson=new_lesson or old_lesson,
            chapter_order=new_chapter_order,
            lesson_order=new_lesson_order,
            youtube_url=new_youtube_url
        )