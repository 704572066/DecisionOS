CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS embedding vector(1536);
ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS embedding_model varchar(160);
ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS embedded_at timestamptz;
CREATE INDEX IF NOT EXISTS ix_knowledge_items_embedding_hnsw_1536
ON knowledge_items USING hnsw (embedding vector_cosine_ops);
