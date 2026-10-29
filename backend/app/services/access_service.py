"""门禁业务服务: 重复通行检测 + 业务异常生成"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import AccessRecord, AbnormalEvent
from .notify import notify_abnormal

# 短时间重复通行判定窗口(秒)
DUPLICATE_WINDOW_SECONDS = 30


def find_recent_duplicate(db: Session, student_id: int, direction: str,
                          window_seconds: int = DUPLICATE_WINDOW_SECONDS):
    """查找窗口期内同方向的有效通行记录(用于重复识别过滤)"""
    if not student_id:
        return None
    since = datetime.now() - timedelta(seconds=window_seconds)
    return db.query(AccessRecord).filter(
        AccessRecord.student_id == student_id,
        AccessRecord.direction == direction,
        AccessRecord.verify_result == "success",
        AccessRecord.occurred_at >= since,
    ).order_by(AccessRecord.occurred_at.desc()).first()


def create_business_abnormal(db: Session, reason: str, detail: str,
                             camera=None, student=None, severity: int = 1):
    """生成业务异常并自动反馈"""
    event = AbnormalEvent(
        event_no=f"AB{datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}",
        event_type="business",
        event_reason=reason,
        event_detail=detail,
        camera_id=camera.id if camera else None,
        camera_code=camera.camera_code if camera else None,
        student_id=student.id if student else None,
        student_no=student.student_no if student else None,
        severity=severity,
        status="pending",
        occurred_at=datetime.now(),
    )
    db.add(event)
    db.flush()
    notify_abnormal(db, event)
    return event


def check_duplicate_access(db: Session, student, camera):
    """检测重复通行, 命中则生成业务异常, 返回命中记录或 None"""
    if camera is None or student is None:
        return None
    dup = find_recent_duplicate(db, student.id, camera.direction)
    if dup:
        create_business_abnormal(
            db,
            reason="DUPLICATE_ACCESS",
            detail=(f"学生 {student.name}({student.student_no}) 在 "
                    f"{DUPLICATE_WINDOW_SECONDS} 秒内重复通过 {camera.camera_code}"
                    f"({camera.direction}), 上一次时间 {dup.occurred_at.strftime('%H:%M:%S')}"),
            camera=camera,
            student=student,
            severity=1,
        )
    return dup
