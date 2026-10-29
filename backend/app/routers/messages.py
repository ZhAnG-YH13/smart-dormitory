"""消息中心路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from datetime import datetime
from typing import Optional
from ..database import get_db
from ..utils.auth import get_current_user, require_roles
from ..models import *
from .. import config

import sys
sys.path.insert(0, str(config.BASE_DIR))

router = APIRouter(prefix="/api/messages", tags=["消息中心"])


def _msg_to_dict(m: MessageNotification) -> dict:
    return {
        "id": m.id, "title": m.title, "content": m.content or "",
        "message_type": m.message_type or "",
        "recipient_role": m.recipient_role or "",
        "is_read": m.is_read,
        "read_at": m.read_at.isoformat() if m.read_at else None,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _visible_messages(db: Session, user: SysUser):
    """当前用户可见的消息范围 (后端强制数据隔离)"""
    role, uid = user.role, user.id
    if role == "admin":
        return db.query(MessageNotification).filter(
            MessageNotification.recipient_role.in_(["admin", "all"])
        )
    if role == "counselor":
        conds = [
            MessageNotification.recipient_id == uid,
            MessageNotification.recipient_role == "all",
        ]
        if user.counselor_class_id:
            conds.append(and_(
                MessageNotification.recipient_role == "counselor",
                MessageNotification.recipient_class_id == user.counselor_class_id,
            ))
        return db.query(MessageNotification).filter(or_(*conds))
    # 学生: 只能看到发给自己的消息, 以及全局公告
    return db.query(MessageNotification).filter(
        or_(
            MessageNotification.recipient_id == uid,
            MessageNotification.recipient_role == "all",
        )
    )


@router.get("")
def list_messages(
    message_type: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """消息列表 (按角色过滤)"""
    q = _visible_messages(db, current_user)

    if message_type: q = q.filter(MessageNotification.message_type == message_type)
    if is_read is not None: q = q.filter(MessageNotification.is_read == is_read)

    total = q.count()
    items = q.order_by(MessageNotification.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "items": [_msg_to_dict(m) for m in items],
            "page": page, "limit": limit}


@router.post("/{mid}/read")
def mark_read(
    mid: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    m = _visible_messages(db, current_user).filter(MessageNotification.id == mid).first()
    if not m: raise HTTPException(status_code=404, detail="消息不存在")
    if not m.is_read:
        m.is_read = True
        m.read_at = datetime.now()
        db.commit()
    return {"success": True}


@router.post("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = _visible_messages(db, current_user).filter(MessageNotification.is_read == False)
    count = q.count()
    q.update({"is_read": True, "read_at": datetime.now()}, synchronize_session=False)
    db.commit()
    return {"success": True, "marked_count": count}


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    role = current_user.role
    uid = current_user.id

    q = _visible_messages(db, current_user).filter(MessageNotification.is_read == False)
    cnt = q.count() or 0

    # 按类型聚合
    by_type = q.with_entities(
        MessageNotification.message_type,
        func.count(MessageNotification.id)
    ).group_by(MessageNotification.message_type).all()

    return {
        "unread_count": cnt,
        "by_type": [{
            "message_type": t or "unknown", "count": c
        } for t, c in by_type],
    }
