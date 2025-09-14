-- Supabaseでベクトル検索を効率的に行うためのRPC関数
-- SQL Editorで実行してください

CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
  match_count int DEFAULT 5
)
RETURNS TABLE (
  content_id uuid,
  chunk_text text,
  title text,
  url text,
  youtube_url text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    e.content_id,
    e.chunk_text,
    c.title,
    c.url,
    c.youtube_url,
    1 - (e.embedding <=> query_embedding) AS similarity
  FROM content_embeddings e
  JOIN contents c ON e.content_id = c.id
  ORDER BY e.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;