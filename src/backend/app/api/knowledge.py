from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentIdentity, get_current_identity
from app.auth.ownership import owned_project
from app.core.config import settings
from app.db.session import get_db
from app.knowledge.parser import SUPPORTED_SUFFIXES
from app.knowledge.processor import process_source
from app.knowledge.storage import remove_file, source_path
from app.models.entities import KnowledgeItem, KnowledgeSource

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
ALLOWED_TYPES = {"policy", "decision", "document", "evidence"}


def owned_source(db: Session, workspace_id: str, source_id: str) -> KnowledgeSource:
    source = db.scalar(select(KnowledgeSource).where(
        KnowledgeSource.id == source_id,
        KnowledgeSource.workspace_id == workspace_id,
    ))
    if not source:
        raise HTTPException(404, "Knowledge source not found")
    return source


def source_json(source: KnowledgeSource, include_content: bool = False, db: Session | None = None):
    result = {
        "id": source.id, "projectId": source.project_id, "objectType": source.object_type,
        "name": source.name, "filename": source.filename, "mediaType": source.media_type,
        "sizeBytes": source.size_bytes, "status": source.status, "summary": source.summary,
        "errorMessage": source.error_message, "itemCount": source.item_count,
        "createdAt": source.created_at.isoformat(), "updatedAt": source.updated_at.isoformat(),
    }
    if include_content and db is not None:
        result["items"] = [{"id": item.id, "title": item.title, "content": item.content}
            for item in db.scalars(select(KnowledgeItem).where(
                KnowledgeItem.workspace_id == source.workspace_id,
                KnowledgeItem.source_type == "upload",
                KnowledgeItem.source_id == source.id,
            ).order_by(KnowledgeItem.created_at)).all()]
    return result


@router.get("")
def list_knowledge(objectType: str | None = None, status: str | None = None,
                   db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    stmt = select(KnowledgeSource).where(KnowledgeSource.workspace_id == identity.workspace.id)
    if objectType:
        stmt = stmt.where(KnowledgeSource.object_type == objectType)
    if status:
        stmt = stmt.where(KnowledgeSource.status == status)
    return [source_json(source) for source in db.scalars(stmt.order_by(KnowledgeSource.updated_at.desc())).all()]


@router.get("/{source_id}")
def get_knowledge(source_id: str, db: Session = Depends(get_db),
                  identity: CurrentIdentity = Depends(get_current_identity)):
    return source_json(owned_source(db, identity.workspace.id, source_id), True, db)


@router.post("", status_code=202)
async def upload_knowledge(background_tasks: BackgroundTasks, file: UploadFile = File(...),
                           name: str = Form(""), objectType: str = Form("document"),
                           projectId: str | None = Form(None), db: Session = Depends(get_db),
                           identity: CurrentIdentity = Depends(get_current_identity)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(415, "Supported file types: PDF, DOCX, TXT, Markdown")
    if objectType not in ALLOWED_TYPES:
        raise HTTPException(400, "Invalid knowledge type")
    if projectId:
        owned_project(db, identity.workspace.id, projectId)
    content = await file.read(settings.knowledge_max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.knowledge_max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.knowledge_max_upload_mb} MB")
    if not content:
        raise HTTPException(400, "File is empty")
    source = KnowledgeSource(
        workspace_id=identity.workspace.id, project_id=projectId or None, object_type=objectType,
        name=(name.strip() or Path(file.filename or "knowledge").stem)[:240],
        filename=(file.filename or "knowledge")[:500], media_type=(file.content_type or "application/octet-stream")[:160],
        storage_path="", size_bytes=len(content), status="uploaded",
    )
    db.add(source)
    db.flush()
    path = source_path(identity.workspace.id, source.id, suffix)
    path.write_bytes(content)
    source.storage_path = str(path)
    db.commit()
    db.refresh(source)
    background_tasks.add_task(process_source, source.id, identity.workspace.id)
    return source_json(source)


@router.post("/{source_id}/reprocess", status_code=202)
def reprocess_knowledge(source_id: str, background_tasks: BackgroundTasks,
                        db: Session = Depends(get_db), identity: CurrentIdentity = Depends(get_current_identity)):
    source = owned_source(db, identity.workspace.id, source_id)
    if source.status == "processing":
        raise HTTPException(409, "Knowledge source is already processing")
    source.status = "uploaded"
    source.error_message = ""
    db.commit()
    background_tasks.add_task(process_source, source.id, identity.workspace.id)
    return source_json(source)


@router.delete("/{source_id}", status_code=204)
def delete_knowledge(source_id: str, db: Session = Depends(get_db),
                     identity: CurrentIdentity = Depends(get_current_identity)):
    source = owned_source(db, identity.workspace.id, source_id)
    db.execute(delete(KnowledgeItem).where(
        KnowledgeItem.workspace_id == identity.workspace.id,
        KnowledgeItem.source_type == "upload",
        KnowledgeItem.source_id == source.id,
    ))
    path = source.storage_path
    db.delete(source)
    db.commit()
    remove_file(path)

