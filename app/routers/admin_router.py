from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import date as date_cls

from app.database import get_db, engine
from app import models, schemas, mongo_dal
from app.auth import get_current_admin
from app.mongodb import is_mongodb_connected
from app.config import MONGODB_URL, MONGODB_DB_NAME

router = APIRouter(prefix="/api/admin", tags=["Admin Management"])

@router.get("/stats", response_model=schemas.AdminDashboardStats)
def get_admin_stats(db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)) -> Any:
    return mongo_dal.get_stats_mongo()

@router.get("/settings", response_model=schemas.AdminSettingResponse)
def get_admin_settings(db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)) -> Any:
    setting = mongo_dal.get_admin_settings_mongo()
    return {
        "id": 1,
        "incubation_name": setting.get("incubation_name", "Nanova Infotech"),
        "allowed_admin_emails": setting.get("allowed_admin_emails", ""),
        "announcement": setting.get("announcement", ""),
        "updated_at": setting.get("updated_at") or "2025-02-23T00:00:00"
    }

@router.put("/settings", response_model=schemas.AdminSettingResponse)
def update_admin_settings(
    settings_in: schemas.AdminSettingUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
) -> Any:
    update_fields = {}
    if settings_in.incubation_name is not None:
        update_fields["incubation_name"] = settings_in.incubation_name
    if settings_in.allowed_admin_emails is not None:
        update_fields["allowed_admin_emails"] = settings_in.allowed_admin_emails
    if settings_in.announcement is not None:
        update_fields["announcement"] = settings_in.announcement

    setting = mongo_dal.update_admin_settings_mongo(update_fields)
    return {
        "id": 1,
        "incubation_name": setting.get("incubation_name", "Nanova Infotech"),
        "allowed_admin_emails": setting.get("allowed_admin_emails", ""),
        "announcement": setting.get("announcement", ""),
        "updated_at": setting.get("updated_at") or "2025-02-23T00:00:00"
    }

# --- Team Management ---

@router.post("/teams")
def create_team(team_in: schemas.TeamCreate, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)) -> Any:
    existing = mongo_dal.find_team_by_name(team_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="Team with this name already exists in MongoDB.")

    new_team = mongo_dal.create_team_mongo({
        "name": team_in.name,
        "idea_title": team_in.idea_title or f"{team_in.name} Project",
        "description": team_in.description or "",
        "domain": team_in.domain or "General Software",
        "status": team_in.status or "Incubated"
    })

    return {
        "id": new_team["id"],
        "name": new_team["name"],
        "idea_title": new_team.get("idea_title"),
        "description": new_team.get("description"),
        "domain": new_team.get("domain"),
        "status": new_team.get("status", "Incubated"),
        "created_at": new_team.get("created_at") or "2025-02-23T00:00:00",
        "members_count": 0,
        "members": []
    }

@router.get("/teams")
def list_teams(db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)) -> Any:
    teams = mongo_dal.list_all_teams_mongo()
    result = []
    for t in teams:
        members_formatted = []
        for m in t.get("members", []):
            members_formatted.append({
                "id": m["id"],
                "team_id": m.get("team_id"),
                "name": m["name"],
                "email": m.get("email"),
                "role_in_team": m.get("role_in_team", "Member"),
                "phone": m.get("phone"),
                "added_at": m.get("added_at") or "2025-02-23T00:00:00"
            })

        result.append({
            "id": t["id"],
            "name": t["name"],
            "idea_title": t.get("idea_title"),
            "description": t.get("description"),
            "domain": t.get("domain"),
            "status": t.get("status", "Incubated"),
            "created_at": t.get("created_at") or "2025-02-23T00:00:00",
            "members_count": len(members_formatted),
            "members": members_formatted
        })
    return result

@router.put("/teams/{team_id}")
def update_team(team_id: str, team_in: schemas.TeamUpdate, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)) -> Any:
    update_fields = {}
    if team_in.name is not None: update_fields["name"] = team_in.name
    if team_in.idea_title is not None: update_fields["idea_title"] = team_in.idea_title
    if team_in.description is not None: update_fields["description"] = team_in.description
    if team_in.domain is not None: update_fields["domain"] = team_in.domain
    if team_in.status is not None: update_fields["status"] = team_in.status

    updated = mongo_dal.update_team_mongo(team_id, update_fields)
    if not updated:
        raise HTTPException(status_code=404, detail="Team not found in MongoDB.")

    return {
        "id": updated["id"],
        "name": updated["name"],
        "idea_title": updated.get("idea_title"),
        "description": updated.get("description"),
        "domain": updated.get("domain"),
        "status": updated.get("status", "Incubated"),
        "created_at": updated.get("created_at") or "2025-02-23T00:00:00",
        "members_count": 0,
        "members": []
    }

@router.delete("/teams/{team_id}")
def delete_team(team_id: str, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)) -> Any:
    success = mongo_dal.delete_team_mongo(team_id)
    if not success:
        raise HTTPException(status_code=404, detail="Team not found or could not be deleted from MongoDB.")
    return {"message": "Team deleted successfully from MongoDB."}

# --- Member Management by Admin ---

@router.post("/teams/{team_id}/members")
def add_team_member(team_id: str, member_in: schemas.TeamMemberCreate, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)) -> Any:
    team = mongo_dal.find_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found in MongoDB.")

    new_member = mongo_dal.add_team_member_mongo({
        "team_id": team_id,
        "name": member_in.name,
        "email": member_in.email,
        "role_in_team": member_in.role_in_team,
        "phone": member_in.phone
    })

    return {
        "id": new_member["id"],
        "team_id": team_id,
        "name": new_member["name"],
        "email": new_member.get("email"),
        "role_in_team": new_member.get("role_in_team"),
        "phone": new_member.get("phone"),
        "added_at": new_member.get("added_at") or "2025-02-23T00:00:00"
    }

@router.delete("/members/{member_id}")
def remove_team_member(member_id: str, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)) -> Any:
    success = mongo_dal.delete_team_member_mongo(member_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found in MongoDB.")
    return {"message": "Member removed successfully from MongoDB."}

# --- Attendance Monitoring by Admin ---

@router.get("/attendance")
def get_all_attendance(
    target_date: Optional[str] = Query(None, description="Format YYYY-MM-DD"),
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
) -> Any:
    records = mongo_dal.get_attendance_mongo(target_date, team_id)
    result = []
    for r in records:
        team_doc = mongo_dal.find_team_by_id(r.get("team_id", ""))
        team_name = team_doc.get("name") if team_doc else "Team"

        result.append({
            "id": r["id"],
            "team_id": r.get("team_id"),
            "team_name": team_name,
            "user_id": r.get("user_id"),
            "submitted_by_name": r.get("submitted_by_name", "Team Member"),
            "date": r.get("date"),
            "status": r.get("status"),
            "work_summary": r.get("work_summary"),
            "submitted_at": r.get("submitted_at") or "2025-02-23T00:00:00"
        })
    return result

# --- Database Management & Export ---

@router.get("/database/export")
def export_database_json(db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)) -> Any:
    return mongo_dal.export_database_json_mongo() if hasattr(mongo_dal, 'export_database_json_mongo') else {
        "db_type": "mongodb",
        "mongodb_connected": is_mongodb_connected(),
        "mongodb_url": MONGODB_URL,
        "mongodb_db_name": MONGODB_DB_NAME,
        "teams_count": len(mongo_dal.list_all_teams_mongo()),
        "stats": mongo_dal.get_stats_mongo()
    }
