from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.core.response import success_response
from app.schemas.block_media_relation import (
    BlockMediaRelationCreate,
)
from app.services.block_media_relation_services import (
    create_block_media_relation,
    list_block_media_relations,
    delete_block_media_relation,
)

router = APIRouter(
    prefix="/notes/{note_id}/blocks/{block_id}/media",
    tags=["block-media-relations"],
)


@router.post("/")
def create_block_media_relation_api(
    note_id: int,
    block_id: int,
    data: BlockMediaRelationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    block_media_relation = create_block_media_relation(session, current_user, note_id, block_id, data)
    return success_response(block_media_relation, "Block media relation created successfully")


@router.get("/")
def list_block_media_relations_api(
    note_id: int,
    block_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    block_media_relations = list_block_media_relations(session, current_user, note_id, block_id)
    return success_response(block_media_relations)


@router.delete("/{relation_id}")
def delete_block_media_relation_api(
    note_id: int,
    block_id: int,
    relation_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    block_media_relation = delete_block_media_relation(session, current_user, note_id, block_id, relation_id)
    return success_response(block_media_relation, "Block media relation deleted successfully")