from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app.database import get_db
from app import models, schemas, mongo_dal
from app.auth import get_current_user, is_allowed_admin_email

router = APIRouter(prefix="/api/messages", tags=["Individual Messaging"])

@router.post("/group")
def send_group_message(
    msg_in: schemas.MessageCreate,
    current_user: models.User = Depends(get_current_user)
) -> Any:
    new_msg = mongo_dal.send_message_mongo({
        "team_id": "group_company_wide",
        "sender_id": str(current_user.id),
        "sender_name": current_user.full_name,
        "sender_role": current_user.role,
        "content": msg_in.content
    })
    return {
        "id": new_msg["id"],
        "team_id": "group_company_wide",
        "sender_id": str(current_user.id),
        "sender_name": current_user.full_name,
        "sender_role": current_user.role,
        "content": new_msg["content"],
        "is_read": False,
        "created_at": new_msg.get("created_at") or "2025-02-23T00:00:00"
    }

@router.get("/group")
def get_group_messages(
    current_user: models.User = Depends(get_current_user)
) -> Any:
    messages = mongo_dal.get_team_messages_mongo("group_company_wide")
    result = []
    for m in messages:
        result.append({
            "id": m["id"],
            "team_id": "group_company_wide",
            "sender_id": m.get("sender_id"),
            "sender_name": m.get("sender_name", "Member"),
            "sender_role": m.get("sender_role", "user"),
            "content": m.get("content"),
            "is_read": m.get("is_read", False),
            "created_at": m.get("created_at") or "2025-02-23T00:00:00"
        })
    return result

@router.post("/team/{team_id}")
def send_message_to_team(
    team_id: str,
    msg_in: schemas.MessageCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    team = mongo_dal.find_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found in MongoDB.")

    is_admin = is_allowed_admin_email(current_user.email, db)

    # Permission check: If non-admin, user can only send message for their own team
    if not is_admin:
        if str(current_user.team_id) != str(team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are only authorized to message your assigned team."
            )
        sender_role = "user"
    else:
        sender_role = "admin"

    new_msg = mongo_dal.send_message_mongo({
        "team_id": team_id,
        "sender_id": str(current_user.id),
        "sender_name": current_user.full_name,
        "sender_role": sender_role,
        "content": msg_in.content
    })

    return {
        "id": new_msg["id"],
        "team_id": team_id,
        "sender_id": str(current_user.id),
        "sender_name": current_user.full_name,
        "sender_role": sender_role,
        "content": new_msg["content"],
        "is_read": False,
        "created_at": new_msg.get("created_at") or "2025-02-23T00:00:00"
    }

@router.get("/team/{team_id}")
def get_team_messages(
    team_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    team = mongo_dal.find_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found in MongoDB.")

    is_admin = is_allowed_admin_email(current_user.email, db)

    # Permission check: Regular user can only access their own team's messages
    if not is_admin and str(current_user.team_id) != str(team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view messages for your own team."
        )

    messages = mongo_dal.get_team_messages_mongo(team_id)
    result = []
    for m in messages:
        result.append({
            "id": m["id"],
            "team_id": team_id,
            "sender_id": m.get("sender_id"),
            "sender_name": m.get("sender_name", "Member"),
            "sender_role": m.get("sender_role", "user"),
            "content": m.get("content"),
            "is_read": m.get("is_read", False),
            "created_at": m.get("created_at") or "2025-02-23T00:00:00"
        })

    return result
