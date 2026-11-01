"""人脸管理路由"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from ..database import get_db
from ..utils.auth import get_current_user, require_roles
from ..models import *
from .. import config

import sys
sys.path.insert(0, str(config.BASE_DIR))
from ai.face_engine import register_face, verify_face, embedding_to_json, json_to_embedding, get_system_info

import os
import uuid
import time

router = APIRouter(prefix="/api/face", tags=["人脸管理"])


def _ensure_face_dir():
    os.makedirs(config.FACE_UPLOAD_DIR, exist_ok=True)


def _create_face_profile_if_absent(db: Session, student_id: int) -> FaceProfile:
    fp = db.query(FaceProfile).filter(FaceProfile.student_id == student_id).first()
    if not fp:
        fp = FaceProfile(student_id=student_id, face_status="unregistered")
        db.add(fp); db.flush()
    return fp


@router.post("/register")
async def face_register(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """上传图片注册人脸"""
    # 确定学生
    if current_user.role == "student" and current_user.student:
        student = current_user.student
    else:
        raise HTTPException(status_code=403, detail="仅学生本人可注册人脸")

    # 读取文件
    content = await file.read()
    if len(content) > config.MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片过大(最大10MB)")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    if ext not in config.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: {ext}")

    # 保存图片
    _ensure_face_dir()
    filename = f"{student.student_no}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    save_path = os.path.join(config.FACE_UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(content)

    fp = _create_face_profile_if_absent(db, student.id)
    fp.face_status = "registering"
    fp.face_image_path = save_path
    db.commit()

    # 调用AI注册
    try:
        result = register_face(content, source="bytes")
    except Exception as e:
        fp.face_status = "failed"
        db.commit()
        return {"success": False, "msg": f"AI引擎异常: {e}"}

    if result.success:
        fp.face_status = "registered"
        fp.face_embedding = embedding_to_json(result.embedding)
        fp.embedding_model = "face_recognition"
        fp.face_quality_score = result.quality_score
        fp.face_count = result.face_count
        fp.face_image_path = save_path
    else:
        fp.face_status = "failed"
        fp.face_quality_score = result.quality_score
        fp.face_embedding = None

    db.commit()

    return {
        "success": result.success,
        "msg": "注册成功" if result.success else f"注册失败: {result.reason} - {result.detail}",
        "face_status": fp.face_status,
        "quality_score": result.quality_score,
        "face_count": result.face_count,
        "reason": result.reason,
        "detail": result.detail,
    }


@router.get("/status")
def face_status(
    student_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """查询人脸注册状态"""
    if current_user.role == "student":
        if not current_user.student:
            return {"face_status": "unregistered"}
        sid = current_user.student.id
    elif student_id:
        sid = student_id
    else:
        raise HTTPException(status_code=400, detail="请传入 student_id")

    fp = db.query(FaceProfile).filter(FaceProfile.student_id == sid).first()
    if not fp:
        return {"face_status": "unregistered", "registered": False}

    return {
        "face_status": fp.face_status,
        "registered": fp.face_status == "registered",
        "quality_score": fp.face_quality_score,
        "verify_count": fp.verify_count,
        "verify_success_count": fp.verify_success_count,
        "last_verify_time": fp.last_verify_time.isoformat() if fp.last_verify_time else None,
        "registered_at": fp.created_at.isoformat() if fp.face_status == "registered" else None,
    }


@router.post("/verify")
async def face_verify(
    file: UploadFile = File(...),
    student_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """人脸验证"""
    if current_user.role == "student" and not student_id:
        if not current_user.student:
            raise HTTPException(status_code=400, detail="未关联学生")
        sid = current_user.student.id
    elif student_id:
        sid = student_id
    else:
        raise HTTPException(status_code=400, detail="请传入 student_id")

    fp = db.query(FaceProfile).filter(FaceProfile.student_id == sid, FaceProfile.face_status == "registered").first()
    if not fp:
        raise HTTPException(status_code=400, detail="该学生未注册人脸")

    content = await file.read()
    registered_emb = json_to_embedding(fp.face_embedding)

    result = verify_face(content, registered_emb, source="bytes")
    similarity = float(getattr(result, "similarity", 0.0) or 0.0)

    fp.verify_count += 1
    fp.last_verify_time = datetime.now()
    if similarity >= config.FACE_SIMILARITY_THRESHOLD:
        fp.verify_success_count += 1
    db.commit()

    return {
        "success": bool(result.success and similarity >= config.FACE_SIMILARITY_THRESHOLD),
        "similarity": round(similarity, 4),
        "threshold": config.FACE_SIMILARITY_THRESHOLD,
        "quality_score": result.quality_score,
        "reason": result.reason,
        "detail": result.detail,
    }


def _match_and_record(db: Session, content: bytes, camera: Optional[CameraDevice] = None,
                      cooldown_seconds: int = 0) -> dict:
    """与所有已注册人脸比对, 成功/失败均写门禁记录, 返回识别结果"""
    profiles = db.query(FaceProfile).filter(FaceProfile.face_status == "registered").all()

    best_match = None
    best_similarity = 0.0
    started = time.perf_counter()

    for fp in profiles:
        try:
            registered_emb = json_to_embedding(fp.face_embedding)
            result = verify_face(content, registered_emb, source="bytes")
            similarity = float(getattr(result, "similarity", 0.0) or 0.0)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = fp
        except Exception:
            continue

    recognition_ms = round((time.perf_counter() - started) * 1000, 2)
    now = datetime.now()

    if best_match and best_similarity >= config.FACE_SIMILARITY_THRESHOLD:
        student = db.query(Student).filter(Student.id == best_match.student_id).first()

        # 实时模式冷却: 同一学生短时间内重复识别不重复写记录/异常
        if cooldown_seconds > 0 and camera:
            recent = db.query(AccessRecord).filter(
                AccessRecord.student_id == student.id,
                AccessRecord.camera_id == camera.id,
                AccessRecord.verify_result == "success",
                AccessRecord.occurred_at >= now - timedelta(seconds=cooldown_seconds),
            ).first()
            if recent:
                return {
                    "success": True,
                    "similarity": round(best_similarity, 4),
                    "student": {"id": student.id, "student_no": student.student_no, "name": student.name},
                    "direction": camera.direction,
                    "access_record_id": recent.id,
                    "presence": camera.direction == "IN",
                    "recognition_ms": recognition_ms,
                    "duplicate": True,
                    "cooldown": True,
                }

        from ..services.access_service import check_duplicate_access
        duplicate = check_duplicate_access(db, student, camera)

        best_match.verify_count += 1
        best_match.verify_success_count += 1
        best_match.last_verify_time = now

        camera_dir = camera.direction if camera else "IN"
        building = camera.building if camera else None
        record = AccessRecord(
            student_id=student.id,
            student_no=student.student_no,
            student_name=student.name,
            camera_id=camera.id if camera else None,
            camera_code=camera.camera_code if camera else None,
            building_id=building.id if building else None,
            building_name=building.name if building else "",
            direction=camera_dir,
            similarity=best_similarity,
            recognition_ms=recognition_ms,
            verify_result="success",
            recognition_mode="realtime",
            occurred_at=now,
        )
        db.add(record)
        db.flush()

        ps = db.query(PresenceStatus).filter(PresenceStatus.student_id == student.id).first()
        if not ps:
            ps = PresenceStatus(student_id=student.id)
            db.add(ps); db.flush()
        ps.is_present = (camera_dir == "IN")
        ps.last_direction = camera_dir
        ps.last_access_time = now
        ps.last_access_record_id = record.id
        db.commit()

        return {
            "success": True,
            "similarity": round(best_similarity, 4),
            "student": {"id": student.id, "student_no": student.student_no, "name": student.name},
            "direction": camera_dir,
            "access_record_id": record.id,
            "presence": ps.is_present,
            "recognition_ms": recognition_ms,
            "duplicate": bool(duplicate),
        }

    # 失败分支
    matched_student = None
    if best_match:
        matched_student = db.query(Student).filter(Student.id == best_match.student_id).first()

    if camera:
        # 冷却: 同一摄像头短时间内重复失败不重复建记录/异常, 避免刷屏
        if cooldown_seconds > 0:
            recent_fail = db.query(AccessRecord).filter(
                AccessRecord.camera_id == camera.id,
                AccessRecord.verify_result == "failed",
                AccessRecord.occurred_at >= now - timedelta(seconds=cooldown_seconds),
            ).first()
            if recent_fail:
                return {
                    "success": False,
                    "similarity": round(float(best_similarity), 4),
                    "threshold": config.FACE_SIMILARITY_THRESHOLD,
                    "reason": "FACE_MISMATCH" if best_match else "NO_MATCH_FOUND",
                    "detail": "未匹配到可信的已注册人脸",
                    "cooldown": True,
                }

        record = AccessRecord(
            student_id=matched_student.id if matched_student else None,
            student_no=matched_student.student_no if matched_student else "",
            student_name=matched_student.name if matched_student else "未知",
            camera_id=camera.id,
            camera_code=camera.camera_code,
            building_id=camera.building.id if camera.building else None,
            building_name=camera.building.name if camera.building else "",
            direction=camera.direction if camera else "IN",
            similarity=float(best_similarity),
            recognition_ms=recognition_ms,
            verify_result="failed",
            recognition_mode="realtime",
            occurred_at=now,
        )
        db.add(record)

        ab = AbnormalEvent(
            event_no=f"AB{now.strftime('%Y%m%d%H%M%S%f')[:18]}",
            event_type="ai_recognition",
            event_reason="FACE_MISMATCH",
            event_detail=f"相似度 {float(best_similarity):.4f} < 阈值 {config.FACE_SIMILARITY_THRESHOLD}",
            camera_id=camera.id,
            camera_code=camera.camera_code,
            student_id=matched_student.id if matched_student else None,
            student_no=matched_student.student_no if matched_student else None,
            severity=2,
            status="pending",
            occurred_at=now,
        )
        db.add(ab)
        from ..services.notify import notify_abnormal
        notify_abnormal(db, ab)

    db.commit()

    return {
        "success": False,
        "similarity": round(float(best_similarity), 4),
        "threshold": config.FACE_SIMILARITY_THRESHOLD,
        "reason": "FACE_MISMATCH" if best_match else "NO_MATCH_FOUND",
        "detail": "未匹配到可信的已注册人脸",
    }


@router.post("/batch-verify")
async def face_batch_verify(
    file: UploadFile = File(...),
    camera_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """批量验证 (用于门禁 - 与所有已注册人脸比较)"""
    content = await file.read()
    camera = db.query(CameraDevice).filter(CameraDevice.id == camera_id).first() if camera_id else None
    return _match_and_record(db, content, camera)


@router.get("/terminal-cameras")
def terminal_cameras(db: Session = Depends(get_db)):
    """门禁终端可选的摄像头列表 (公开, 终端设备无需登录)"""
    cams = db.query(CameraDevice).filter(
        CameraDevice.is_deleted == False
    ).order_by(CameraDevice.id).all()
    return {"items": [
        {
            "id": c.id,
            "camera_code": c.camera_code,
            "name": c.name,
            "building": c.building.name if c.building else "",
            "direction": c.direction,
            "device_status": c.device_status,
        } for c in cams
    ]}


@router.post("/terminal-verify")
async def terminal_verify(
    file: UploadFile = File(...),
    camera_code: str = Form(...),
    db: Session = Depends(get_db),
):
    """门禁终端实时刷脸 (公开接口, 由设备端调用; 内置冷却避免重复记录)"""
    camera = db.query(CameraDevice).filter(
        CameraDevice.camera_code == camera_code, CameraDevice.is_deleted == False
    ).first()
    if not camera:
        raise HTTPException(status_code=404, detail=f"门禁设备不存在: {camera_code}")

    content = await file.read()
    result = _match_and_record(db, content, camera, cooldown_seconds=8)
    result["camera"] = {
        "id": camera.id,
        "camera_code": camera.camera_code,
        "name": camera.name,
        "building": camera.building.name if camera.building else "",
        "direction": camera.direction,
        "device_status": camera.device_status,
    }
    return result


@router.delete("/cancel")
def face_cancel(
    student_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """注销人脸"""
    if current_user.role == "student":
        if not current_user.student:
            raise HTTPException(status_code=400, detail="未关联学生")
        sid = current_user.student.id
    elif student_id:
        sid = student_id
    else:
        raise HTTPException(status_code=400, detail="请传入 student_id")

    fp = db.query(FaceProfile).filter(FaceProfile.student_id == sid).first()
    if not fp:
        raise HTTPException(status_code=404, detail="人脸档案不存在")

    fp.face_status = "cancelled"
    fp.face_embedding = None
    fp.face_quality_score = 0.0
    db.commit()

    return {"success": True, "face_status": fp.face_status}
