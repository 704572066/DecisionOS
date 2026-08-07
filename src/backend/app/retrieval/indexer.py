import logging
from sqlalchemy import select, text
from app.models.entities import KnowledgeItem
from app.retrieval.embedding import embedding_provider
from app.retrieval.vector_store import literal

logger = logging.getLogger("decisionos.retrieval.indexer")

async def backfill_embeddings(db, project_id=None, batch_size=16, force=False):
    if not embedding_provider.enabled:
        return {"status":"disabled","message":"Embedding provider is not configured","processed":0}

    stmt = select(KnowledgeItem)
    if project_id:
        stmt = stmt.where(KnowledgeItem.project_id == project_id)
    items = list(db.scalars(stmt).all())

    if not force:
        ids = {
            row[0]
            for row in db.execute(
                text("SELECT id FROM knowledge_items WHERE embedding IS NULL AND (:p IS NULL OR project_id=:p)"),
                {"p": project_id},
            ).all()
        }
        items = [item for item in items if item.id in ids]

    processed = failed = 0
    for offset in range(0, len(items), batch_size):
        batch = items[offset:offset+batch_size]
        try:
            embeddings = await embedding_provider.embed_many(
                [f"{item.object_type}\n{item.title}\n{item.content}" for item in batch]
            )
            if len(embeddings) != len(batch):
                raise RuntimeError("Embedding result count mismatch")

            for item, embedded in zip(batch, embeddings):
                db.execute(
                    text("""
                    UPDATE knowledge_items
                    SET embedding=CAST(:embedding AS vector),
                        embedding_model=:model,
                        embedded_at=NOW()
                    WHERE id=:id
                    """),
                    {
                        "embedding": literal(embedded.vector),
                        "model": embedded.model,
                        "id": item.id,
                    },
                )
                processed += 1
            db.commit()
        except Exception:
            db.rollback()
            failed += len(batch)
            logger.exception("Embedding backfill batch failed")

    return {"status":"ok" if not failed else "partial","processed":processed,"failed":failed}
