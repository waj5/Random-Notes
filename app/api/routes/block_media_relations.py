from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.schemas.block_media_relation import (
    BlockMediaRelationCreate,
    BlockMediaRelationPublic,
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


@router.post("/", response_model=BlockMediaRelationPublic)
def create_block_media_relation_api(
    note_id: int,
    block_id: int,
    data: BlockMediaRelationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_block_media_relation(session, current_user, note_id, block_id, data)


@router.get("/", response_model=list[BlockMediaRelationPublic])
def list_block_media_relations_api(
    note_id: int,
    block_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_block_media_relations(session, current_user, note_id, block_id)


@router.delete("/{relation_id}")
def delete_block_media_relation_api(
    note_id: int,
    block_id: int,
    relation_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return delete_block_media_relation(session, current_user, note_id, block_id, relation_id)