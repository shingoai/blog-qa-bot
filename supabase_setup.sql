-- Supabaseデータベース設定SQL
-- このSQLをSupabaseのSQL Editorで実行してください

-- 教材コンテンツテーブル
CREATE TABLE IF NOT EXISTS contents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    chapter TEXT NOT NULL,
    chapter_order INTEGER DEFAULT 0,
    lesson TEXT NOT NULL,
    lesson_order INTEGER DEFAULT 0,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    doc_type TEXT DEFAULT 'text',
    url TEXT,
    youtube_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    
    -- 重複防止のためのユニーク制約
    UNIQUE(chapter, lesson, title)
);

-- ベクトル埋め込みテーブル（検索用）
CREATE TABLE IF NOT EXISTS content_embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    content_id UUID REFERENCES contents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536), -- OpenAI embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    
    -- インデックス
    UNIQUE(content_id, chunk_index)
);

-- 質問ログテーブル
CREATE TABLE IF NOT EXISTS question_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    urls TEXT[],
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    user_rating INTEGER, -- 将来的な評価機能用
    session_id TEXT
);

-- 更新日時の自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_contents_updated_at 
    BEFORE UPDATE ON contents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- インデックスの作成（検索パフォーマンス向上）
CREATE INDEX IF NOT EXISTS idx_contents_chapter_lesson 
    ON contents(chapter, lesson);
CREATE INDEX IF NOT EXISTS idx_contents_created_at 
    ON contents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_question_logs_timestamp 
    ON question_logs(timestamp DESC);

-- ベクトル検索用の拡張機能（pgvector）を有効化
CREATE EXTENSION IF NOT EXISTS vector;

-- コメント
COMMENT ON TABLE contents IS 'ブログスクールの教材コンテンツ';
COMMENT ON TABLE content_embeddings IS '教材の埋め込みベクトル（検索用）';
COMMENT ON TABLE question_logs IS 'ユーザーからの質問と回答のログ';