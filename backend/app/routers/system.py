"""系统管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from ..database import get_db
from ..utils.auth import get_current_user, require_roles, hash_password
from ..models import *
from .. import config

import sys
sys.path.insert(0, str(config.BASE_DIR))
from ai.face_engine import get_system_info

router = APIRouter(tags=["系统管理"])


def _user_to_dict(u: SysUser, db: Session = None) -> dict:
    d = {
        "id": u.id, "username": u.username, "real_name": u.real_name,
        "phone": u.phone or "", "email": u.email or "",
        "role": u.role, "status": u.status,
        "must_change_password": u.must_change_password,
        "counselor_class_id": u.counselor_class_id,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }
    if db and u.counselor_class_id:
        ci = db.query(ClassInfo).filter(ClassInfo.id == u.counselor_class_id).first()
        d["counselor_class_name"] = ci.name if ci else ""
    return d


# ========== 用户管理 (admin only) ==========

@router.get("/api/users")
def list_users(
    role: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
):
    q = db.query(SysUser).filter(SysUser.is_deleted == False)
    if role: q = q.filter(SysUser.role == role)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(SysUser.username.like(like), SysUser.real_name.like(like)))
    total = q.count()
    items = q.order_by(SysUser.id.asc()).offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "items": [_user_to_dict(u, db) for u in items],
            "page": page, "limit": limit}


@router.post("/api/users")
def create_user(
    data: dict,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
):
    username = data.get("username")
    real_name = data.get("real_name")
    role = data.get("role")
    password = data.get("password") or config.DEFAULT_PASSWORD

    if not username or not real_name or not role:
        raise HTTPException(status_code=400, detail="username/real_name/role 必填")
    if role not in ("admin", "counselor", "student"):
        raise HTTPException(status_code=400, detail="role 非法")
    if db.query(SysUser).filter(SysUser.username == username, SysUser.is_deleted == False).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    u = SysUser(
        username=username,
        password_hash=hash_password(password),
        real_name=real_name,
        phone=data.get("phone"),
        email=data.get("email"),
        role=role,
        status=data.get("status", 1),
        must_change_password=data.get("must_change_password", False),
        counselor_class_id=data.get("counselor_class_id"),
    )
    db.add(u); db.commit(); db.refresh(u)

    log = SysLog(user_id=current_user.id, username=current_user.username,
                 action="CREATE_USER", target=f"user_id={u.id}",
                 detail=f"创建用户 {u.username} ({u.role})")
    db.add(log); db.commit()
    return _user_to_dict(u, db)


@router.put("/api/users/{uid}")
def update_user(
    uid: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
):
    u = db.query(SysUser).filter(SysUser.id == uid, SysUser.is_deleted == False).first()
    if not u: raise HTTPException(status_code=404, detail="用户不存在")

    for k, v in data.items():
        if hasattr(u, k) and k not in ("id", "username", "password_hash"):
            setattr(u, k, v)

    db.commit(); db.refresh(u)

    log = SysLog(user_id=current_user.id, username=current_user.username,
                 action="UPDATE_USER", target=f"user_id={u.id}")
    db.add(log); db.commit()
    return _user_to_dict(u, db)


@router.delete("/api/users/{uid}")
def delete_user(
    uid: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
):
    if uid == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    u = db.query(SysUser).filter(SysUser.id == uid, SysUser.is_deleted == False).first()
    if not u: raise HTTPException(status_code=404, detail="用户不存在")
    u.is_deleted = True; db.commit()

    log = SysLog(user_id=current_user.id, username=current_user.username,
                 action="DELETE_USER", target=f"user_id={uid}")
    db.add(log); db.commit()
    return {"success": True}


@router.post("/api/users/{uid}/reset-password")
def reset_user_password(
    uid: int,
    data: dict = {},
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
):
    u = db.query(SysUser).filter(SysUser.id == uid, SysUser.is_deleted == False).first()
    if not u: raise HTTPException(status_code=404, detail="用户不存在")

    new_pwd = data.get("new_password") or config.DEFAULT_PASSWORD
    u.password_hash = hash_password(new_pwd)
    u.must_change_password = data.get("must_change_password", True)
    db.commit()

    log = SysLog(user_id=current_user.id, username=current_user.username,
                 action="RESET_PASSWORD", target=f"user_id={uid}")
    db.add(log); db.commit()
    return {"success": True, "default_password": new_pwd}


# ========== 操作日志 ==========

@router.get("/api/logs")
def list_logs(
    action: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
):
    q = db.query(SysLog).filter(SysLog.is_deleted == False)
    if action: q = q.filter(SysLog.action.like(f"%{action}%"))
    if username: q = q.filter(SysLog.username == username)

    total = q.count()
    items = q.order_by(SysLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": l.id, "user_id": l.user_id, "username": l.username or "",
                "action": l.action, "target": l.target or "",
                "detail": l.detail or "", "ip_address": l.ip_address or "",
                "status": l.status,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in items
        ],
        "page": page, "limit": limit,
    }


# ========== 系统信息 ==========

@router.get("/api/system/info")
def system_info(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    try:
        ai_info = get_system_info()
    except Exception as e:
        ai_info = {"error": str(e), "face_recognition_available": False}

    # 数据库统计
    total_users = db.query(func.count(SysUser.id)).filter(SysUser.is_deleted == False).scalar() or 0
    total_students = db.query(func.count(Student.id)).filter(Student.is_deleted == False).scalar() or 0
    total_cameras = db.query(func.count(CameraDevice.id)).filter(CameraDevice.is_deleted == False).scalar() or 0
    face_registered = db.query(func.count(FaceProfile.id)).filter(FaceProfile.face_status == "registered").scalar() or 0
    pending_abnormal = db.query(func.count(AbnormalEvent.id)).filter(AbnormalEvent.status == "pending").scalar() or 0

    return {
        "app": {
            "name": "智慧宿舍人脸门禁与学生管理系统",
            "version": "1.0.0",
            "base_dir": str(config.BASE_DIR),
            "face_threshold": config.FACE_SIMILARITY_THRESHOLD,
        },
        "ai_module": ai_info,
        "database": {
            "users": total_users,
            "students": total_students,
            "cameras": total_cameras,
            "face_registered": face_registered,
            "pending_abnormal": pending_abnormal,
        },
        "server_time": datetime.now().isoformat(),
    }
