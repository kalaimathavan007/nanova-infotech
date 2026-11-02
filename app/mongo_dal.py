from bson import ObjectId
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from app.mongodb import get_mongo_db
from app.auth import get_password_hash
from app.database import SessionLocal
from app import models

# Helper to format MongoDB document _id to string id
def format_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    return doc

def format_doc_list(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    for d in docs:
        d["id"] = str(d["_id"])
        result.append(d)
    return result

# --- INITIALIZATION & INDEXES ---
def init_mongo_db():
    db = get_mongo_db()
    if db is None:
        # Fallback to SQL DB seeding for admin user only
        db_sql = SessionLocal()
        try:
            admin_email = "rajalingamrajesh70@gmail.com"
            admin_user = db_sql.query(models.User).filter(models.User.email == admin_email).first()
            if not admin_user:
                db_sql.add(models.User(
                    email=admin_email,
                    hashed_password=get_password_hash("nanova1234"),
                    full_name="Rajalingam Rajesh",
                    role="admin"
                ))
                db_sql.commit()
        finally:
            db_sql.close()
        return

    # Unique Indexes in MongoDB
    try:
        db.users.create_index("email", unique=True)
        db.teams.create_index("name", unique=True)
    except Exception as e:
        pass

    # Seed Admin Settings if not present
    setting = db.admin_settings.find_one()
    if not setting:
        db.admin_settings.insert_one({
            "incubation_name": "Nanova Infotech",
            "allowed_admin_emails": "kalaimathavan007@gmail.com, admin@nanovainfotech.com",
            "announcement": "Welcome to Nanova Infotech Workspace! Teams please submit your daily attendance and stay connected in Chat.",
            "updated_at": datetime.utcnow()
        })

    # Seed Master Admin User ONLY
    admin_email = "kalaimathavan007@gmail.com"
    admin_user = db.users.find_one({"email": admin_email})
    if not admin_user:
        db.users.insert_one({
            "email": admin_email,
            "hashed_password": get_password_hash("nanova1234"),
            "full_name": "Master Admin (Kalai)",
            "role": "admin",
            "team_id": None,
            "created_at": datetime.utcnow()
        })
    else:
        db.users.update_one(
            {"email": admin_email},
            {"$set": {"hashed_password": get_password_hash("nanova1234"), "role": "admin"}}
        )

# --- USER OPERATIONS ---
def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            u = db_sql.query(models.User).filter(models.User.email == email.strip().lower()).first()
            if u:
                return {
                    "id": str(u.id),
                    "_id": str(u.id),
                    "email": u.email,
                    "hashed_password": u.hashed_password,
                    "full_name": u.full_name,
                    "role": u.role,
                    "team_id": str(u.team_id) if u.team_id else None
                }
            return None
        finally:
            db_sql.close()

    user = db.users.find_one({"email": email.strip().lower()})
    return format_doc(user)

def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_mongo_db()
    user_data["email"] = user_data["email"].strip().lower()
    user_data["created_at"] = datetime.utcnow()

    if db is None:
        db_sql = SessionLocal()
        try:
            tid = int(user_data["team_id"]) if user_data.get("team_id") and str(user_data["team_id"]).isdigit() else None
            new_u = models.User(
                email=user_data["email"],
                hashed_password=user_data["hashed_password"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                team_id=tid
            )
            db_sql.add(new_u)
            db_sql.commit()
            db_sql.refresh(new_u)
            user_data["id"] = str(new_u.id)
            return user_data
        finally:
            db_sql.close()

    res = db.users.insert_one(user_data)
    user_data["id"] = str(res.inserted_id)
    return user_data

def update_user_role(email: str, role: str):
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            u = db_sql.query(models.User).filter(models.User.email == email.strip().lower()).first()
            if u:
                u.role = role
                db_sql.commit()
        finally:
            db_sql.close()
        return

    db.users.update_one({"email": email.strip().lower()}, {"$set": {"role": role}})

# --- TEAM OPERATIONS ---
def find_team_by_name(name: str) -> Optional[Dict[str, Any]]:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            t = db_sql.query(models.Team).filter(models.Team.name == name.strip()).first()
            if t:
                return {
                    "id": str(t.id),
                    "_id": str(t.id),
                    "name": t.name,
                    "idea_title": t.idea_title,
                    "description": t.description,
                    "domain": t.domain,
                    "status": t.status
                }
            return None
        finally:
            db_sql.close()

    team = db.teams.find_one({"name": name.strip()})
    return format_doc(team)

def find_team_by_id(team_id: str) -> Optional[Dict[str, Any]]:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            tid = int(team_id) if str(team_id).isdigit() else 1
            t = db_sql.query(models.Team).filter(models.Team.id == tid).first()
            if t:
                return {
                    "id": str(t.id),
                    "_id": str(t.id),
                    "name": t.name,
                    "idea_title": t.idea_title,
                    "description": t.description,
                    "domain": t.domain,
                    "status": t.status
                }
            return None
        finally:
            db_sql.close()

    try:
        team = db.teams.find_one({"_id": ObjectId(team_id)})
        return format_doc(team)
    except Exception:
        return None

def create_team_mongo(team_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_mongo_db()
    team_data["created_at"] = datetime.utcnow()

    if db is None:
        db_sql = SessionLocal()
        try:
            new_t = models.Team(
                name=team_data["name"],
                idea_title=team_data.get("idea_title"),
                description=team_data.get("description"),
                domain=team_data.get("domain"),
                status=team_data.get("status", "Incubated")
            )
            db_sql.add(new_t)
            db_sql.commit()
            db_sql.refresh(new_t)
            team_data["id"] = str(new_t.id)
            return team_data
        finally:
            db_sql.close()

    res = db.teams.insert_one(team_data)
    team_data["id"] = str(res.inserted_id)
    return team_data

def list_all_teams_mongo() -> List[Dict[str, Any]]:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            teams_sql = db_sql.query(models.Team).all()
            res = []
            for t in teams_sql:
                m_list = [{"id": str(m.id), "team_id": str(t.id), "name": m.name, "email": m.email, "role_in_team": m.role_in_team, "phone": m.phone} for m in t.members]
                res.append({
                    "id": str(t.id),
                    "name": t.name,
                    "idea_title": t.idea_title,
                    "description": t.description,
                    "domain": t.domain,
                    "status": t.status,
                    "members_count": len(m_list),
                    "members": m_list
                })
            return res
        finally:
            db_sql.close()

    teams = list(db.teams.find().sort("created_at", -1))
    result = []
    for t in teams:
        t_id = str(t["_id"])
        members = list(db.team_members.find({"team_id": t_id}))
        formatted_members = format_doc_list(members)

        t["id"] = t_id
        t["members_count"] = len(formatted_members)
        t["members"] = formatted_members
        result.append(t)
    return result

def update_team_mongo(team_id: str, update_fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            tid = int(team_id) if str(team_id).isdigit() else 1
            t = db_sql.query(models.Team).filter(models.Team.id == tid).first()
            if t:
                if "name" in update_fields: t.name = update_fields["name"]
                if "idea_title" in update_fields: t.idea_title = update_fields["idea_title"]
                if "description" in update_fields: t.description = update_fields["description"]
                if "domain" in update_fields: t.domain = update_fields["domain"]
                if "status" in update_fields: t.status = update_fields["status"]
                db_sql.commit()
                return find_team_by_id(team_id)
            return None
        finally:
            db_sql.close()

    try:
        db.teams.update_one({"_id": ObjectId(team_id)}, {"$set": update_fields})
        return find_team_by_id(team_id)
    except Exception:
        return None

def delete_team_mongo(team_id: str) -> bool:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            tid = int(team_id) if str(team_id).isdigit() else 1
            t = db_sql.query(models.Team).filter(models.Team.id == tid).first()
            if t:
                db_sql.delete(t)
                db_sql.commit()
                return True
            return False
        finally:
            db_sql.close()

    try:
        db.teams.delete_one({"_id": ObjectId(team_id)})
        db.team_members.delete_many({"team_id": team_id})
        db.attendances.delete_many({"team_id": team_id})
        db.messages.delete_many({"team_id": team_id})
        db.users.update_many({"team_id": team_id}, {"$set": {"team_id": None}})
        return True
    except Exception:
        return False

# --- MEMBER OPERATIONS ---
def add_team_member_mongo(member_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_mongo_db()
    member_data["added_at"] = datetime.utcnow()

    if db is None:
        db_sql = SessionLocal()
        try:
            tid = int(member_data["team_id"]) if str(member_data["team_id"]).isdigit() else 1
            new_m = models.TeamMember(
                team_id=tid,
                name=member_data["name"],
                email=member_data.get("email"),
                role_in_team=member_data.get("role_in_team", "Member"),
                phone=member_data.get("phone")
            )
            db_sql.add(new_m)
            db_sql.commit()
            db_sql.refresh(new_m)
            member_data["id"] = str(new_m.id)
            return member_data
        finally:
            db_sql.close()

    res = db.team_members.insert_one(member_data)
    member_data["id"] = str(res.inserted_id)
    return member_data

def delete_team_member_mongo(member_id: str) -> bool:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            mid = int(member_id) if str(member_id).isdigit() else 1
            m = db_sql.query(models.TeamMember).filter(models.TeamMember.id == mid).first()
            if m:
                db_sql.delete(m)
                db_sql.commit()
                return True
            return False
        finally:
            db_sql.close()

    try:
        res = db.team_members.delete_one({"_id": ObjectId(member_id)})
        return res.deleted_count > 0
    except Exception:
        return False

# --- ATTENDANCE OPERATIONS ---
def submit_attendance_mongo(att_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_mongo_db()
    att_data["submitted_at"] = datetime.utcnow()

    if db is None:
        db_sql = SessionLocal()
        try:
            tid = int(att_data["team_id"]) if str(att_data["team_id"]).isdigit() else 1
            uid = int(att_data["user_id"]) if str(att_data["user_id"]).isdigit() else None
            rec = models.Attendance(
                team_id=tid,
                user_id=uid,
                date=att_data["date"],
                status=att_data["status"],
                work_summary=att_data.get("work_summary")
            )
            db_sql.add(rec)
            db_sql.commit()
            db_sql.refresh(rec)
            att_data["id"] = str(rec.id)
            return att_data
        finally:
            db_sql.close()

    existing = db.attendances.find_one({"team_id": att_data["team_id"], "date": att_data["date"]})
    if existing:
        db.attendances.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "status": att_data["status"],
                "work_summary": att_data["work_summary"],
                "submitted_by_name": att_data.get("submitted_by_name", "Member"),
                "submitted_at": datetime.utcnow()
            }}
        )
        existing["status"] = att_data["status"]
        existing["work_summary"] = att_data["work_summary"]
        return format_doc(existing)
    else:
        res = db.attendances.insert_one(att_data)
        att_data["id"] = str(res.inserted_id)
        return att_data

def get_attendance_mongo(target_date: Optional[str] = None, team_id: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            q = db_sql.query(models.Attendance)
            if target_date: q = q.filter(models.Attendance.date == target_date)
            if team_id and str(team_id).isdigit(): q = q.filter(models.Attendance.team_id == int(team_id))
            recs = q.all()
            return [{"id": str(r.id), "team_id": str(r.team_id), "user_id": str(r.user_id), "submitted_by_name": r.submitted_by_user.full_name if r.submitted_by_user else "Member", "date": r.date, "status": r.status, "work_summary": r.work_summary, "submitted_at": str(r.submitted_at)} for r in recs]
        finally:
            db_sql.close()

    query = {}
    if target_date: query["date"] = target_date
    if team_id: query["team_id"] = team_id

    records = list(db.attendances.find(query).sort("submitted_at", -1))
    return format_doc_list(records)

# --- MESSAGING OPERATIONS ---
def send_message_mongo(msg_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_mongo_db()
    msg_data["created_at"] = datetime.utcnow()
    msg_data["is_read"] = False

    if db is None:
        db_sql = SessionLocal()
        try:
            tid = int(msg_data["team_id"]) if str(msg_data["team_id"]).isdigit() else 1
            uid = int(msg_data["sender_id"]) if str(msg_data["sender_id"]).isdigit() else None
            m = models.Message(
                team_id=tid,
                sender_id=uid,
                sender_name=msg_data.get("sender_name", "User"),
                sender_role=msg_data.get("sender_role", "user"),
                content=msg_data["content"]
            )
            db_sql.add(m)
            db_sql.commit()
            db_sql.refresh(m)
            msg_data["id"] = str(m.id)
            return msg_data
        finally:
            db_sql.close()

    res = db.messages.insert_one(msg_data)
    msg_data["id"] = str(res.inserted_id)
    return msg_data

def get_team_messages_mongo(team_id: str) -> List[Dict[str, Any]]:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            tid = int(team_id) if str(team_id).isdigit() else 1
            msgs = db_sql.query(models.Message).filter(models.Message.team_id == tid).all()
            return [{"id": str(m.id), "team_id": str(m.team_id), "sender_id": str(m.sender_id), "sender_name": m.sender_name, "sender_role": m.sender_role, "content": m.content, "created_at": str(m.created_at)} for m in msgs]
        finally:
            db_sql.close()

    messages = list(db.messages.find({"team_id": team_id}).sort("created_at", 1))
    return format_doc_list(messages)

# --- SETTINGS OPERATIONS ---
def get_admin_settings_mongo() -> Dict[str, Any]:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            s = db_sql.query(models.AdminSetting).first()
            if s:
                return {
                    "id": str(s.id),
                    "incubation_name": s.incubation_name,
                    "allowed_admin_emails": s.allowed_admin_emails,
                    "announcement": s.announcement
                }
            return {
                "id": "1",
                "incubation_name": "Nanova Infotech",
                "allowed_admin_emails": "kalaimathavan007@gmail.com, admin@nanovainfotech.com",
                "announcement": "Welcome to Nanova Infotech Portal."
            }
        finally:
            db_sql.close()

    setting = db.admin_settings.find_one()
    if not setting:
        res = db.admin_settings.insert_one({
            "incubation_name": "Nanova Infotech",
            "allowed_admin_emails": "kalaimathavan007@gmail.com, admin@nanovainfotech.com",
            "announcement": "Welcome to the Nanova Infotech Portal! Teams please submit your daily attendance on time.",
            "updated_at": datetime.utcnow()
        })
        setting = db.admin_settings.find_one({"_id": res.inserted_id})
    return format_doc(setting)

def update_admin_settings_mongo(update_fields: Dict[str, Any]) -> Dict[str, Any]:
    db = get_mongo_db()
    update_fields["updated_at"] = datetime.utcnow()

    if db is None:
        db_sql = SessionLocal()
        try:
            s = db_sql.query(models.AdminSetting).first()
            if s:
                if "incubation_name" in update_fields: s.incubation_name = update_fields["incubation_name"]
                if "allowed_admin_emails" in update_fields: s.allowed_admin_emails = update_fields["allowed_admin_emails"]
                if "announcement" in update_fields: s.announcement = update_fields["announcement"]
                db_sql.commit()
            return get_admin_settings_mongo()
        finally:
            db_sql.close()

    setting = db.admin_settings.find_one()
    if setting:
        db.admin_settings.update_one({"_id": setting["_id"]}, {"$set": update_fields})
    else:
        db.admin_settings.insert_one(update_fields)
    return get_admin_settings_mongo()

def get_stats_mongo() -> Dict[str, Any]:
    db = get_mongo_db()
    if db is None:
        db_sql = SessionLocal()
        try:
            tt = db_sql.query(models.Team).count()
            tu = db_sql.query(models.User).count()
            tm = db_sql.query(models.TeamMember).count()
            today_str = date.today().strftime("%Y-%m-%d")
            ta = db_sql.query(models.Attendance).filter(models.Attendance.date == today_str).count()
            s = get_admin_settings_mongo()
            return {
                "total_teams": tt,
                "total_users": tu,
                "total_members": tm,
                "today_attendance_count": ta,
                "announcement": s.get("announcement", "Welcome to Nanova Infotech Portal.")
            }
        finally:
            db_sql.close()

    total_teams = db.teams.count_documents({})
    total_users = db.users.count_documents({})
    total_members = db.team_members.count_documents({})
    today_str = date.today().strftime("%Y-%m-%d")
    today_attendance_count = db.attendances.count_documents({"date": today_str})
    setting = get_admin_settings_mongo()

    return {
        "total_teams": total_teams,
        "total_users": total_users,
        "total_members": total_members,
        "today_attendance_count": today_attendance_count,
        "announcement": setting.get("announcement", "Welcome to Nanova Infotech Portal.")
    }
