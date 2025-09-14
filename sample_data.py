"""
サンプルデータ投入スクリプト
初期テスト用の教材データを投入します
"""

from components.knowledge_base import KnowledgeBase
import os
from dotenv import load_dotenv

load_dotenv()

def add_sample_data():
    kb = KnowledgeBase()
    
    sample_materials = [
        {
            "title": "ブログの基本構成",
            "content": """
            ブログ記事の基本構成について説明します。
            
            1. タイトル
            - 読者の興味を引く
            - SEOキーワードを含める
            - 30文字以内が理想
            
            2. 導入文
            - 記事の概要を説明
            - 読者の課題に共感
            - この記事で得られるメリットを提示
            
            3. 本文
            - 見出しを使って構造化
            - 1段落は3-4行程度
            - 具体例を交える
            
            4. まとめ
            - 要点を整理
            - 次のアクションを促す
            - 関連記事へのリンク
            """,
            "url": "https://utage.example.com/lesson/blog-structure",
            "doc_type": "text"
        },
        {
            "title": "SEOライティングの基礎",
            "content": """
            SEOを意識したライティングの基本テクニックを紹介します。
            
            キーワード選定：
            - 検索ボリュームを調査
            - 競合性を確認
            - ロングテールキーワードを狙う
            
            タイトルの付け方：
            - メインキーワードを前半に配置
            - 数字を使う（例：5つの方法）
            - 感情に訴える言葉を使う
            
            見出しの最適化：
            - H2、H3タグを適切に使用
            - キーワードを自然に含める
            - 階層構造を意識する
            
            内部リンク：
            - 関連記事へリンク
            - アンカーテキストを工夫
            - 3-5個程度が適切
            """,
            "url": "https://utage.example.com/lesson/seo-writing",
            "doc_type": "text"
        },
        {
            "title": "WordPressの初期設定（動画文字起こし）",
            "content": """
            今回はWordPressの初期設定について解説していきます。
            
            まず最初に、WordPressをインストールしたら必ず行うべき設定があります。
            
            一つ目は、パーマリンク設定です。
            設定メニューから「パーマリンク」を選択して、「投稿名」を選ぶことをおすすめします。
            これによってURLが分かりやすくなり、SEO的にも有利になります。
            
            二つ目は、プラグインのインストールです。
            最低限必要なプラグインとして、
            - Yoast SEO：SEO対策
            - Akismet：スパム対策
            - BackWPup：バックアップ
            これらは必ず入れておきましょう。
            
            三つ目は、テーマの選択です。
            無料テーマでおすすめなのは「Cocoon」です。
            日本語対応で、SEO対策も充実しています。
            
            最後に、プロフィール設定も忘れずに行いましょう。
            ユーザー名とニックネームを別にすることで、セキュリティが向上します。
            """,
            "url": "https://utage.example.com/video/wordpress-setup",
            "doc_type": "video"
        }
    ]
    
    print("サンプルデータを投入中...")
    
    for material in sample_materials:
        kb.add_document(
            content=material["content"],
            title=material["title"],
            url=material["url"],
            doc_type=material["doc_type"]
        )
        print(f"✅ {material['title']} を追加しました")
    
    stats = kb.get_stats()
    print(f"\n投入完了！合計 {stats['total_documents']} 件のドキュメントが登録されています。")

if __name__ == "__main__":
    add_sample_data()