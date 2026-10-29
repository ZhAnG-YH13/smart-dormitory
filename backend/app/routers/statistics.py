"""数据统计路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
from typing import Optional
from ..database import get_db
from ..utils.auth import get_current_user, require_roles
from ..models import *
from .. import config

import sys
sys.path.insert(0, str(config.BASE_DIR))
from ai.face_engine import get_system_info

router = APIRouter(prefix="/api/stats", tags=["数据统计"])


@router.get("/dashboard")
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """首页数据"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_students = db.query(func.count(Student.id)).filter(Student.is_deleted == False).scalar() or 0
    face_registered = db.query(func.count(FaceProfile.id)).filter(
        FaceProfile.face_status == "registered"
    ).scalar() or 0
    total_cameras = db.query(func.count(CameraDevice.id)).filter(
        CameraDevice.is_deleted == False
    ).scalar() or 0
    online_cameras = db.query(func.count(CameraDevice.id)).filter(
        CameraDevice.is_deleted == False, CameraDevice.device_status == "online"
    ).scalar() or 0

    today_total = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.occurred_at >= today_start
    ).scalar() or 0
    today_in = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.occurred_at >= today_start, AccessRecord.direction == "IN",
        AccessRecord.verify_result == "success"
    ).scalar() or 0
    today_out = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.occurred_at >= today_start, AccessRecord.direction == "OUT",
        AccessRecord.verify_result == "success"
    ).scalar() or 0

    pending_abnormal = db.query(func.count(AbnormalEvent.id)).filter(
        AbnormalEvent.status == "pending"
    ).scalar() or 0

    # 在寝学生数
    present_count = db.query(func.count(PresenceStatus.id)).filter(
        PresenceStatus.is_present == True
    ).scalar() or 0

    # 最近7天门禁趋势
    trend = []
    for i in range(6, -1, -1):
        d_start = today_start - timedelta(days=i)
        d_end = d_start + timedelta(days=1)
        cnt = db.query(func.count(AccessRecord.id)).filter(
            AccessRecord.occurred_at >= d_start,
            AccessRecord.occurred_at < d_end,
            AccessRecord.verify_result == "success",
        ).scalar() or 0
        trend.append({"date": d_start.strftime("%m-%d"), "count": cnt})

    return {
        "total_students": total_students,
        "face_registered": face_registered,
        "face_register_rate": round(face_registered / total_students, 4) if total_students else 0.0,
        "total_cameras": total_cameras,
        "online_cameras": online_cameras,
        "online_rate": round(online_cameras / total_cameras, 4) if total_cameras else 0.0,
        "today_total": today_total,
        "today_in": today_in,
        "today_out": today_out,
        "present_count": present_count,
        "pending_abnormal": pending_abnormal,
        "week_trend": trend,
    }


@router.get("/students")
def student_stats(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin", "counselor")),
):
    total = db.query(func.count(Student.id)).filter(Student.is_deleted == False).scalar() or 0
    face_registered = db.query(func.count(FaceProfile.id)).filter(FaceProfile.face_status == "registered").scalar() or 0
    info_complete = db.query(func.count(Student.id)).filter(
        Student.is_deleted == False, Student.info_complete >= 80
    ).scalar() or 0

    # 按学院分组
    colleges = db.query(
        College.name.label("college_name"),
        func.count(Student.id).label("cnt"),
    ).join(Major, Major.college_id == College.id
    ).join(Grade, Grade.major_id == Major.id
    ).join(ClassInfo, ClassInfo.grade_id == Grade.id
    ).join(Student, Student.class_id == ClassInfo.id
    ).filter(Student.is_deleted == False
    ).group_by(College.id).all()

    # 性别比例
    males = db.query(func.count(Student.id)).filter(
        Student.is_deleted == False, Student.gender == "男"
    ).scalar() or 0

    return {
        "total": total,
        "face_registered": face_registered,
        "face_register_rate": round(face_registered / total, 4) if total else 0.0,
        "info_complete_count": info_complete,
        "info_complete_rate": round(info_complete / total, 4) if total else 0.0,
        "male_count": males,
        "female_count": total - males,
        "colleges": [{"college_name": c, "count": n} for c, n in colleges],
    }


@router.get("/access")
def access_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    now = datetime.now()
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    total = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.occurred_at >= start
    ).scalar() or 0
    success = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.occurred_at >= start, AccessRecord.verify_result == "success"
    ).scalar() or 0

    in_cnt = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.occurred_at >= start, AccessRecord.direction == "IN",
        AccessRecord.verify_result == "success",
    ).scalar() or 0
    out_cnt = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.occurred_at >= start, AccessRecord.direction == "OUT",
        AccessRecord.verify_result == "success",
    ).scalar() or 0

    # 每日明细
    daily = []
    for i in range(days):
        d_start = start + timedelta(days=i)
        d_end = d_start + timedelta(days=1)
        d_total = db.query(func.count(AccessRecord.id)).filter(
            AccessRecord.occurred_at >= d_start, AccessRecord.occurred_at < d_end
        ).scalar() or 0
        d_success = db.query(func.count(AccessRecord.id)).filter(
            AccessRecord.occurred_at >= d_start, AccessRecord.occurred_at < d_end,
            AccessRecord.verify_result == "success",
        ).scalar() or 0
        daily.append({
            "date": d_start.strftime("%Y-%m-%d"),
            "total": d_total,
            "success": d_success,
            "failed": d_total - d_success,
        })

    # 各时段流量 (全天)
    hourly = []
    for h in range(24):
        h_records = db.query(func.count(AccessRecord.id)).filter(
            func.extract("hour", AccessRecord.occurred_at) == h,
            AccessRecord.verify_result == "success",
        ).scalar() or 0
        hourly.append({"hour": h, "count": h_records})

    # 各宿舍楼门禁统计
    by_building = []
    for b in db.query(DormitoryBuilding).filter(DormitoryBuilding.is_deleted == False).all():
        b_total = db.query(func.count(AccessRecord.id)).filter(
            AccessRecord.occurred_at >= start, AccessRecord.building_id == b.id
        ).scalar() or 0
        b_success = db.query(func.count(AccessRecord.id)).filter(
            AccessRecord.occurred_at >= start, AccessRecord.building_id == b.id,
            AccessRecord.verify_result == "success",
        ).scalar() or 0
        by_building.append({
            "building_id": b.id, "building_name": b.name,
            "total": b_total, "success": b_success,
            "failed": b_total - b_success,
            "success_rate": round(b_success / b_total, 4) if b_total else 0.0,
        })

    return {
        "days": days, "start_date": start.strftime("%Y-%m-%d"), "end_date": now.strftime("%Y-%m-%d"),
        "total": total, "success": success, "failed": total - success,
        "success_rate": round(success / total, 4) if total else 0.0,
        "in_count": in_cnt, "out_count": out_cnt,
        "daily": daily, "hourly": hourly, "by_building": by_building,
    }


@router.get("/classes")
def class_stats(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin", "counselor")),
):
    """班级统计"""
    q = db.query(ClassInfo).filter(ClassInfo.is_deleted == False)

    # 辅导员只看自己班级
    if current_user.role == "counselor" and current_user.counselor_class_id:
        q = q.filter(ClassInfo.id == current_user.counselor_class_id)

    classes = []
    for c in q.all():
        total = db.query(func.count(Student.id)).filter(
            Student.class_id == c.id, Student.is_deleted == False
        ).scalar() or 0
        fr = db.query(func.count(FaceProfile.id)).join(Student, Student.id == FaceProfile.student_id).filter(
            Student.class_id == c.id, FaceProfile.face_status == "registered"
        ).scalar() or 0

        class_students = db.query(Student.id).filter(
            Student.class_id == c.id, Student.is_deleted == False
        ).all()
        ids = [s.id for s in class_students]
        present = 0
        if ids:
            present = db.query(func.count(PresenceStatus.id)).filter(
                PresenceStatus.student_id.in_(ids), PresenceStatus.is_present == True
            ).scalar() or 0
        incomplete = db.query(func.count(Student.id)).filter(
            Student.class_id == c.id, Student.is_deleted == False,
            Student.info_complete < 80
        ).scalar() or 0

        classes.append({
            "class_id": c.id, "class_name": c.name,
            "total_students": total, "face_registered": fr,
            "face_register_rate": round(fr / total, 4) if total else 0.0,
            "unregistered_face": total - fr,
            "present_count": present,
            "not_present_count": total - present,
            "info_incomplete": incomplete,
            "info_complete_rate": round((total - incomplete) / total, 4) if total else 0.0,
        })
    return {"total_classes": len(classes), "classes": classes}


@router.get("/devices")
def device_stats(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    total = db.query(func.count(CameraDevice.id)).filter(CameraDevice.is_deleted == False).scalar() or 0
    online = db.query(func.count(CameraDevice.id)).filter(
        CameraDevice.is_deleted == False, CameraDevice.device_status == "online"
    ).scalar() or 0
    offline = db.query(func.count(CameraDevice.id)).filter(
        CameraDevice.is_deleted == False, CameraDevice.device_status == "offline"
    ).scalar() or 0
    error = db.query(func.count(CameraDevice.id)).filter(
        CameraDevice.is_deleted == False, CameraDevice.device_status == "error"
    ).scalar() or 0
    maintenance = db.query(func.count(CameraDevice.id)).filter(
        CameraDevice.is_deleted == False, CameraDevice.device_status == "maintenance"
    ).scalar() or 0

    avg_rate = db.query(func.avg(CameraDevice.recognition_success_rate)).filter(
        CameraDevice.is_deleted == False
    ).scalar() or 0.0

    buildings = db.query(
        DormitoryBuilding.name.label("name"),
        func.count(CameraDevice.id).label("cnt")
    ).join(CameraDevice, CameraDevice.building_id == DormitoryBuilding.id
    ).filter(CameraDevice.is_deleted == False
    ).group_by(DormitoryBuilding.id).all()

    return {
        "total": total, "online": online, "offline": offline,
        "error": error, "maintenance": maintenance,
        "online_rate": round(online / total, 4) if total else 0.0,
        "avg_recognition_success_rate": round(float(avg_rate), 4),
        "buildings": [{"name": n, "camera_count": c} for n, c in buildings],
    }


@router.get("/abnormals")
def abnormal_stats(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    total = db.query(func.count(AbnormalEvent.id)).scalar() or 0
    pending = db.query(func.count(AbnormalEvent.id)).filter(AbnormalEvent.status == "pending").scalar() or 0
    processing = db.query(func.count(AbnormalEvent.id)).filter(AbnormalEvent.status == "processing").scalar() or 0
    resolved = db.query(func.count(AbnormalEvent.id)).filter(AbnormalEvent.status == "resolved").scalar() or 0
    closed = db.query(func.count(AbnormalEvent.id)).filter(AbnormalEvent.status == "closed").scalar() or 0

    # 按类型分组
    by_type = db.query(
        AbnormalEvent.event_type,
        func.count(AbnormalEvent.id).label("cnt")
    ).group_by(AbnormalEvent.event_type).all()

    # 按严重度
    by_severity = db.query(
        AbnormalEvent.severity,
        func.count(AbnormalEvent.id).label("cnt")
    ).group_by(AbnormalEvent.severity).all()

    return {
        "total": total, "pending": pending, "processing": processing,
        "resolved": resolved, "closed": closed,
        "resolve_rate": round((resolved + closed) / total, 4) if total else 0.0,
        "by_type": [{"type": t, "count": c} for t, c in by_type],
        "by_severity": [{"severity": s, "count": c} for s, c in by_severity],
    }


@router.get("/ai")
def ai_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """AI 识别统计: 检测次数/成功/失败/未检测到人脸/平均识别耗时"""
    now = datetime.now()
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    total = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.occurred_at >= start
    ).scalar() or 0
    success = db.query(func.count(AccessRecord.id)).filter(
        AccessRecord.occurred_at >= start, AccessRecord.verify_result == "success"
    ).scalar() or 0
    failed = total - success

    no_face = db.query(func.count(AbnormalEvent.id)).filter(
        AbnormalEvent.occurred_at >= start,
        AbnormalEvent.event_reason.in_(["NO_FACE_DETECTED", "NO_MATCH_FOUND", "FACE_NOT_FOUND"])
    ).scalar() or 0

    avg_ms = db.query(func.avg(AccessRecord.recognition_ms)).filter(
        AccessRecord.occurred_at >= start, AccessRecord.recognition_ms > 0
    ).scalar()
    avg_ms = round(float(avg_ms), 2) if avg_ms else 0.0

    avg_sim = db.query(func.avg(AccessRecord.similarity)).filter(
        AccessRecord.occurred_at >= start, AccessRecord.verify_result == "success"
    ).scalar()
    avg_sim = round(float(avg_sim), 4) if avg_sim else 0.0

    # 每日识别趋势
    daily = []
    for i in range(days):
        d_start = start + timedelta(days=i)
        d_end = d_start + timedelta(days=1)
        d_total = db.query(func.count(AccessRecord.id)).filter(
            AccessRecord.occurred_at >= d_start, AccessRecord.occurred_at < d_end
        ).scalar() or 0
        d_success = db.query(func.count(AccessRecord.id)).filter(
            AccessRecord.occurred_at >= d_start, AccessRecord.occurred_at < d_end,
            AccessRecord.verify_result == "success",
        ).scalar() or 0
        daily.append({
            "date": d_start.strftime("%m-%d"),
            "detections": d_total, "success": d_success, "failed": d_total - d_success,
        })

    # 失败原因分布
    reasons = db.query(
        AbnormalEvent.event_reason, func.count(AbnormalEvent.id).label("cnt")
    ).filter(
        AbnormalEvent.occurred_at >= start,
        AbnormalEvent.event_type == "ai_recognition",
    ).group_by(AbnormalEvent.event_reason).all()

    try:
        engine = get_system_info()
    except Exception as e:
        engine = {"available": False, "error": str(e)}

    return {
        "days": days,
        "total_detections": total,
        "success_count": success,
        "fail_count": failed,
        "success_rate": round(success / total, 4) if total else 0.0,
        "no_face_count": no_face,
        "avg_recognition_ms": avg_ms,
        "avg_success_similarity": avg_sim,
        "similarity_threshold": config.FACE_SIMILARITY_THRESHOLD,
        "daily": daily,
        "fail_reasons": [{"reason": r or "UNKNOWN", "count": c} for r, c in reasons],
        "engine": engine,
    }
