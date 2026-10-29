"""门禁记录路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, timedelta, date
from typing import Optional
from ..database import get_db
from ..utils.auth import get_current_user, require_roles
from ..models import *
from .. import config

import sys
sys.path.insert(0, str(config.BASE_DIR))

router = APIRouter(tags=["门禁记录"])


def _record_to_dict(r: AccessRecord) -> dict:
    return {
        "id": r.id, "student_id": r.student_id,
        "student_no": r.student_no, "student_name": r.student_name,
        "camera_id": r.camera_id, "camera_code": r.camera_code,
        "building_id": r.building_id, "building_name": r.building_name,
        "direction": r.direction, "similarity": r.similarity,
        "verify_result": r.verify_result,
        "recognition_mode": r.recognition_mode,
        "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
    }


def _presence_to_dict(p: PresenceStatus, db: Session = None) -> dict:
    d = {
        "id": p.id, "student_id": p.student_id,
        "is_present": p.is_present, "last_direction": p.last_direction,
        "last_access_time": p.last_access_time.isoformat() if p.last_access_time else None,
    }
    if db:
        s = db.query(Student).filter(Student.id == p.student_id).first()
        if s:
            d["student_no"] = s.student_no
            d["student_name"] = s.name
            d["class_id"] = s.class_id
            ci = db.query(ClassInfo).filter(ClassInfo.id == s.class_id).first() if s.class_id else None
            d["class_name"] = ci.name if ci else ""
            d["room_number"] = s.dormitory_room.room_number if s.dormitory_room else ""
    return d


@router.get("/api/access/records")
def list_access_records(
    student_id: Optional[int] = Query(None),
    camera_id: Optional[int] = Query(None),
    direction: Optional[str] = Query(None),
    verify_result: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """门禁记录列表"""
    q = db.query(AccessRecord)

    if current_user.role == "student":
        if not current_user.student:
            return {"total": 0, "items": [], "page": page, "limit": limit}
        q = q.filter(AccessRecord.student_id == current_user.student.id)
    elif current_user.role == "counselor":
        if current_user.counselor_class_id:
            # 辅导员看自己班级学生的记录
            class_ids = [current_user.counselor_class_id]
            student_ids = [s.id for s in db.query(Student).filter(
                Student.class_id.in_(class_ids), Student.is_deleted == False
            ).all()]
            q = q.filter(AccessRecord.student_id.in_(student_ids))

    if student_id: q = q.filter(AccessRecord.student_id == student_id)
    if camera_id: q = q.filter(AccessRecord.camera_id == camera_id)
    if direction: q = q.filter(AccessRecord.direction == direction)
    if verify_result: q = q.filter(AccessRecord.verify_result == verify_result)
    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            q = q.filter(AccessRecord.occurred_at >= sd)
        except ValueError:
            raise HTTPException(status_code=400, detail="start_date 格式错误 (YYYY-MM-DD)")
    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            q = q.filter(AccessRecord.occurred_at < ed)
        except ValueError:
            raise HTTPException(status_code=400, detail="end_date 格式错误 (YYYY-MM-DD)")

    total = q.count()
    items = q.order_by(AccessRecord.occurred_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "items": [_record_to_dict(r) for r in items],
            "page": page, "limit": limit}


@router.get("/api/access/today")
def today_access_stats(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """今日进出统计"""
    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    base = db.query(AccessRecord).filter(AccessRecord.occurred_at >= start)

    total = base.count()
    success = base.filter(AccessRecord.verify_result == "success").count()
    failed = total - success

    in_cnt = base.filter(AccessRecord.direction == "IN", AccessRecord.verify_result == "success").count()
    out_cnt = base.filter(AccessRecord.direction == "OUT", AccessRecord.verify_result == "success").count()

    # 各时段流量 (2小时一段)
    hourly = []
    for h in range(0, 24, 2):
        h_start = start + timedelta(hours=h)
        h_end = h_start + timedelta(hours=2)
        cnt = db.query(func.count(AccessRecord.id)).filter(
            AccessRecord.occurred_at >= h_start, AccessRecord.occurred_at < h_end,
            AccessRecord.verify_result == "success",
        ).scalar() or 0
        hourly.append({"hour": f"{h:02d}-{h+2:02d}", "count": cnt})

    # 按摄像头统计
    cam_stats = db.query(
        AccessRecord.camera_code,
        func.count(AccessRecord.id).label("cnt")
    ).filter(
        AccessRecord.occurred_at >= start,
        AccessRecord.verify_result == "success",
    ).group_by(AccessRecord.camera_code).all()

    return {
        "date": now.strftime("%Y-%m-%d"),
        "total": total, "success": success, "failed": failed,
        "success_rate": round(success / total, 4) if total > 0 else 0.0,
        "in_count": in_cnt, "out_count": out_cnt,
        "hourly_flow": hourly,
        "camera_stats": [{"camera_code": c, "count": n} for c, n in cam_stats],
    }


@router.get("/api/presence")
def list_presence(
    class_id: Optional[int] = Query(None),
    is_present: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """在寝状态列表"""
    q = db.query(PresenceStatus).join(Student, Student.id == PresenceStatus.student_id)
    q = q.filter(Student.is_deleted == False)

    if current_user.role == "counselor" and current_user.counselor_class_id:
        q = q.filter(Student.class_id == current_user.counselor_class_id)
    elif current_user.role == "student":
        if not current_user.student:
            return {"total": 0, "items": []}
        q = q.filter(PresenceStatus.student_id == current_user.student.id)

    if class_id: q = q.filter(Student.class_id == class_id)
    if is_present is not None: q = q.filter(PresenceStatus.is_present == is_present)

    total = q.count()
    items = q.order_by(PresenceStatus.id.asc()).offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "items": [_presence_to_dict(p, db) for p in items],
            "page": page, "limit": limit}
