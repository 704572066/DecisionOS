import logging
from datetime import datetime

from sqlalchemy import delete, select, text

from app.db.session import SessionLocal
from app.knowledge.parser import chunk_text, parse_file
from app.models.entities import KnowledgeItem, KnowledgeSource
from app.retrieval.embedding import embedding_provider
from app.retrieval.vector_store import literal

logger = logging.getLogger("decisionos.knowledge")


async def process_source(source_id: str, workspace_id: str) -> None:
    db = SessionLocal()
    try:
        source = db.scalar(select(KnowledgeSource).where(
            KnowledgeSource.id == source_id,
            KnowledgeSource.workspace_id == workspace_id,
        ))
        if not source:
            return
        source.status = "processing"
        source.error_message = ""
        source.updated_at = datetime.utcnow()
        db.commit()

        parsed = parse_file(source.storage_path)
        chunks = chunk_text(parsed)
        db.execute(delete(KnowledgeItem).where(
            KnowledgeItem.workspace_id == workspace_id,
            KnowledgeItem.source_type == "upload",
            KnowledgeItem.source_id == source.id,
        ))
        items = []
        for index, content in enumerate(chunks, 1):
            item = KnowledgeItem(
                workspace_id=workspace_id,
                project_id=source.project_id,
                object_type=source.object_type,
                title=source.name if len(chunks) == 1 else f"{source.name} · {index}",
                content=content,
                source_type="upload",
                source_id=source.id,
            )
            db.add(item)
            items.append(item)
        db.flush()

        if embedding_provider.enabled and items:
            embeddings = await embedding_provider.embed_many([
                f"{item.object_type}\n{item.title}\n{item.content}" for item in items
            ])
            if len(embeddings) != len(items):
                raise RuntimeError("Embedding result count mismatch")
            for item, embedded in zip(items, embeddings):
                db.execute(text("""
                    UPDATE knowledge_items
                    SET embedding=CAST(:embedding AS vector), embedding_model=:model, embedded_at=NOW()
                    WHERE id=:id AND workspace_id=:workspace_id
                """), {"embedding": literal(embedded.vector), "model": embedded.model,
                         "id": item.id, "workspace_id": workspace_id})

        source.summary = parsed[:500]
        source.item_count = len(items)
        source.status = "ready"
        source.updated_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        db.rollback()
        source = db.scalar(select(KnowledgeSource).where(
            KnowledgeSource.id == source_id,
            KnowledgeSource.workspace_id == workspace_id,
        ))
        if source:
            source.status = "failed"
            source.error_message = str(exc)[:2000]
            source.updated_at = datetime.utcnow()
            db.commit()
        logger.exception("Knowledge source processing failed", extra={"sourceId": source_id})
    finally:
        db.close()

