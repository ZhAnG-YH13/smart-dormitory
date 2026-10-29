"""异常处理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional
from ..database import get_db
from ..utils.auth import get_current_user, require_roles
from ..models import *
from .. import config

import sys
sys.path.insert(0, str(config.BASE_DIR))

router = APIRouter(prefix="/api/abnormals", tags=["异常处理"])


def _event_to_dict(e: AbnormalEvent, db: Session = None) -> dict:
    return {
        "id": e.id, "event_no": e.event_no,
        "event_type": e.event_type, "event_reason": e.event_reason or "",
        "event_detail": e.event_detail or "",
        "camera_id": e.camera_id, "camera_code": e.camera_code or "",
        "student_id": e.student_id, "student_no": e.student_no or "",
        "severity": e.severity, "status": e.status,
        "auto_feedback_sent": e.auto_feedback_sent,
        "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
        "handles_count": len(e.handles) if e.handles else 0,
    }


def _handle_to_dict(h: AbnormalHandle) -> dict:
    return {
        "id": h.id, "event_id": h.event_id,
        "handler_id": h.handler_id, "handler_name": h.handler_name or "",
        "handle_type": h.handle_type or "", "handle_result": h.handle_result or "",
        "handle_note": h.handle_note or "",
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }


@router.get("")
def list_abnormals(
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(AbnormalEvent)
    if event_type: q = q.filter(AbnormalEvent.event_type == event_type)
    if status: q = q.filter(AbnormalEvent.status == status)
    if severity: q = q.filter(AbnormalEvent.severity == severity)

    # 辅导员看自己班级
    if current_user.role == "counselor" and current_user.counselor_class_id:
        student_ids = [s.id for s in db.query(Student).filter(
            Student.class_id == current_user.counselor_class_id, Student.is_deleted == False
        ).all()]
        q = q.filter(AbnormalEvent.student_id.in_(student_ids) if student_ids else AbnormalEvent.id == -1)

    total = q.count()
    items = q.order_by(AbnormalEvent.occurred_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "items": [_event_to_dict(e, db) for e in items],
            "page": page, "limit": limit}


@router.get("/{eid}")
def get_abnormal(
    eid: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    e = db.query(AbnormalEvent).filter(AbnormalEvent.id == eid).first()
    if not e: raise HTTPException(status_code=404, detail="异常不存在")

    handles = db.query(AbnormalHandle).filter(AbnormalHandle.event_id == eid).order_by(AbnormalHandle.id.desc()).all()
    return {
        "event": _event_to_dict(e, db),
        "handles": [_handle_to_dict(h) for h in handles],
    }


@router.post("")
def create_abnormal(
    data: dict,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """创建异常 (系统自动或人工)"""
    event_type = data.get("event_type") or "business"
    event = AbnormalEvent(
        event_no=data.get("event_no") or f"AB{datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}",
        event_type=event_type,
        event_reason=data.get("event_reason"),
        event_detail=data.get("event_detail"),
        camera_id=data.get("camera_id"),
        camera_code=data.get("camera_code"),
        student_id=data.get("student_id"),
        student_no=data.get("student_no"),
        severity=data.get("severity", 2),
        status=data.get("status", "pending"),
        occurred_at=data.get("occurred_at") or datetime.now(),
    )
    db.add(event); db.flush()
    # 异常自动反馈: 生成消息通知管理员/辅导员/学生
    from ..services.notify import notify_abnormal
    notify_abnormal(db, event)
    db.commit(); db.refresh(event)
    return _event_to_dict(event, db)


@router.post("/{eid}/handle")
def handle_abnormal(
    eid: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """处理异常"""
    e = db.query(AbnormalEvent).filter(AbnormalEvent.id == eid).first()
    if not e: raise HTTPException(status_code=404, detail="异常不存在")

    handle = AbnormalHandle(
        event_id=eid,
        handler_id=current_user.id,
        handler_name=current_user.real_name,
        handle_type=data.get("handle_type", "manual"),
        handle_result=data.get("handle_result", "已处理"),
        handle_note=data.get("handle_note"),
    )
    db.add(handle)

    new_status = data.get("new_status", "processing")
    if new_status not in ("processing", "resolved", "pending"):
        raise HTTPException(status_code=400, detail="new_status 非法")
    e.status = new_status
    # 处理结果自动反馈
    from ..services.notify import notify_handle_result
    notify_handle_result(db, e, current_user.real_name,
                         handle.handle_result, handle.handle_note)

    db.commit()
    db.refresh(e)
    return {"success": True, "status": e.status, "event_status": e.status, "handle": _handle_to_dict(handle)}


@router.post("/{eid}/close")
def close_abnormal(
    eid: int,
    data: dict = {},
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """关闭异常"""
    e = db.query(AbnormalEvent).filter(AbnormalEvent.id == eid).first()
    if not e: raise HTTPException(status_code=404, detail="异常不存在")

    e.status = "closed"
    handle = AbnormalHandle(
        event_id=eid,
        handler_id=current_user.id,
        handler_name=current_user.real_name,
        handle_type="close",
        handle_result="已关闭",
        handle_note=data.get("note"),
    )
    db.add(handle)
    db.commit()
    return {"success": True, "event_status": "closed"}
