"""摄像头管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from ..database import get_db
from ..utils.auth import get_current_user, require_roles
from ..models import *
from .. import config

import sys
sys.path.insert(0, str(config.BASE_DIR))

router = APIRouter(prefix="/api/cameras", tags=["摄像头管理"])


def _camera_to_dict(c: CameraDevice, db: Session = None) -> dict:
    d = {
        "id": c.id, "camera_code": c.camera_code, "name": c.name,
        "location": c.location or "", "direction": c.direction,
        "building_id": c.building_id, "stream_url": c.stream_url or "",
        "device_status": c.device_status,
        "last_heartbeat": c.last_heartbeat.isoformat() if c.last_heartbeat else None,
        "fps": c.fps, "recognition_success_rate": c.recognition_success_rate,
        "health_score": c.health_score,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
    if db:
        b = db.query(DormitoryBuilding).filter(DormitoryBuilding.id == c.building_id).first()
        d["building_name"] = b.name if b else ""
    return d


@router.get("")
def list_cameras(
    building_id: Optional[int] = Query(None),
    device_status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(CameraDevice).filter(CameraDevice.is_deleted == False)
    if building_id: q = q.filter(CameraDevice.building_id == building_id)
    if device_status: q = q.filter(CameraDevice.device_status == device_status)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(CameraDevice.name.like(like) | CameraDevice.camera_code.like(like))

    total = q.count()
    items = q.order_by(CameraDevice.id.asc()).offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "items": [_camera_to_dict(c, db) for c in items],
            "page": page, "limit": limit}


@router.post("")
def create_camera(data: dict, db: Session = Depends(get_db),
                  current_user: SysUser = Depends(require_roles("admin"))):
    if not data.get("camera_code") or not data.get("name") or not data.get("direction"):
        raise HTTPException(status_code=400, detail="camera_code/name/direction 必填")
    if data["direction"] not in ("IN", "OUT"):
        raise HTTPException(status_code=400, detail="direction 必须是 IN 或 OUT")
    if db.query(CameraDevice).filter(CameraDevice.camera_code == data["camera_code"], CameraDevice.is_deleted == False).first():
        raise HTTPException(status_code=400, detail="camera_code 已存在")

    c = CameraDevice(
        camera_code=data["camera_code"],
        name=data["name"],
        location=data.get("location"),
        direction=data["direction"],
        building_id=data.get("building_id"),
        stream_url=data.get("stream_url"),
        device_status=data.get("device_status", "online"),
        last_heartbeat=datetime.now(),
    )
    db.add(c); db.commit(); db.refresh(c)
    return _camera_to_dict(c, db)


@router.put("/{cid}")
def update_camera(cid: int, data: dict, db: Session = Depends(get_db),
                  current_user: SysUser = Depends(require_roles("admin"))):
    c = db.query(CameraDevice).filter(CameraDevice.id == cid, CameraDevice.is_deleted == False).first()
    if not c: raise HTTPException(status_code=404, detail="摄像头不存在")
    for k, v in data.items():
        if hasattr(c, k) and k != "id": setattr(c, k, v)
    db.commit(); db.refresh(c)
    return _camera_to_dict(c, db)


@router.delete("/{cid}")
def delete_camera(cid: int, db: Session = Depends(get_db),
                  current_user: SysUser = Depends(require_roles("admin"))):
    c = db.query(CameraDevice).filter(CameraDevice.id == cid, CameraDevice.is_deleted == False).first()
    if not c: raise HTTPException(status_code=404, detail="摄像头不存在")
    c.is_deleted = True; db.commit()
    return {"success": True}


@router.post("/{cid}/simulate")
def simulate_access(
    cid: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """模拟门禁通行 (用于演示)"""
    camera = db.query(CameraDevice).filter(CameraDevice.id == cid, CameraDevice.is_deleted == False).first()
    if not camera: raise HTTPException(status_code=404, detail="摄像头不存在")

    student_id = data.get("student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id 必填")

    student = db.query(Student).filter(Student.id == student_id, Student.is_deleted == False).first()
    if not student: raise HTTPException(status_code=404, detail="学生不存在")

    # 是否有人脸注册
    fp = db.query(FaceProfile).filter(FaceProfile.student_id == student.id, FaceProfile.face_status == "registered").first()
    similarity = data.get("similarity") or (0.85 if fp else 0.3)
    verify_result = "success" if similarity >= config.FACE_SIMILARITY_THRESHOLD else "failed"

    # 重复识别过滤: 短时间同方向重复通行 -> 生成业务异常
    duplicate = None
    if verify_result == "success":
        from ..services.access_service import check_duplicate_access
        duplicate = check_duplicate_access(db, student, camera)

    building = camera.building
    record = AccessRecord(
        student_id=student.id,
        student_no=student.student_no,
        student_name=student.name,
        camera_id=camera.id,
        camera_code=camera.camera_code,
        building_id=building.id if building else None,
        building_name=building.name if building else "",
        direction=camera.direction,
        similarity=similarity,
        verify_result=verify_result,
        recognition_mode="simulate",
        occurred_at=datetime.now(),
    )
    db.add(record)
    db.flush()

    # 更新在寝状态
    ps = db.query(PresenceStatus).filter(PresenceStatus.student_id == student.id).first()
    if not ps:
        ps = PresenceStatus(student_id=student.id)
        db.add(ps); db.flush()
    if verify_result == "success":
        ps.is_present = (camera.direction == "IN")
    ps.last_direction = camera.direction
    ps.last_access_time = datetime.now()
    ps.last_access_record_id = record.id

    # 更新摄像头指标
    camera.last_heartbeat = datetime.now()
    camera.fps = 20.0
    total = db.query(func.count(AccessRecord.id)).filter(AccessRecord.camera_id == cid).scalar() or 0
    suc = db.query(func.count(AccessRecord.id)).filter(AccessRecord.camera_id == cid, AccessRecord.verify_result == "success").scalar() or 0
    camera.recognition_success_rate = round(suc / total, 4) if total > 0 else 0.0

    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "access_record_id": record.id,
        "direction": record.direction,
        "verify_result": verify_result,
        "similarity": similarity,
        "student_name": student.name,
        "presence_updated": verify_result == "success",
        "is_present": ps.is_present,
        "duplicate": bool(duplicate),
        "duplicate_tip": "检测到30秒内重复通行，已生成业务异常" if duplicate else "",
    }


@router.get("/{cid}/status")
def camera_status(
    cid: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """摄像头运行状态"""
    c = db.query(CameraDevice).filter(CameraDevice.id == cid, CameraDevice.is_deleted == False).first()
    if not c: raise HTTPException(status_code=404, detail="摄像头不存在")

    now = datetime.now()
    heartbeat_ok = c.last_heartbeat and (now - c.last_heartbeat) < timedelta(minutes=5)

    # 统计今日通行
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_total = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.camera_id == cid, AccessRecord.occurred_at >= today_start
    ).scalar() or 0
    today_success = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.camera_id == cid, AccessRecord.occurred_at >= today_start,
        AccessRecord.verify_result == "success"
    ).scalar() or 0

    return {
        "camera": _camera_to_dict(c, db),
        "heartbeat_ok": heartbeat_ok,
        "health_score": c.health_score,
        "today_total": today_total,
        "today_success": today_success,
        "today_failed": today_total - today_success,
        "recognition_success_rate_today": round(today_success / today_total, 4) if today_total > 0 else 0.0,
    }
