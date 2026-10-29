"""消息通知服务 - 异常自动反馈

任务书要求: 异常产生后必须自动反馈给相关人员
- 设备异常 -> 学校管理员
- 学生相关异常(人脸未注册/验证失败/门禁异常) -> 学生本人 + 所属辅导员 + 管理员
- 异常处理结果 -> 上报人/管理员
"""
from sqlalchemy.orm import Session
from ..models import MessageNotification, AbnormalEvent, Student, ClassInfo, SysUser

# 异常类型 -> 消息类型映射
EVENT_MSG_TYPE = {
    "device_error": "device_error",
    "image_quality": "image_quality",
    "ai_recognition": "face_verify_error",
    "business": "access_abnormal",
}

# 异常类型 -> 中文名
EVENT_LABEL = {
    "device_error": "设备异常",
    "image_quality": "图像质量异常",
    "ai_recognition": "AI识别异常",
    "business": "业务异常",
}


def create_message(
    db: Session,
    title: str,
    content: str,
    message_type: str,
    recipient_role: str,
    recipient_id: int = None,
    recipient_class_id: int = None,
    related_event_id: int = None,
) -> MessageNotification:
    """创建一条消息通知"""
    msg = MessageNotification(
        title=title,
        content=content,
        message_type=message_type,
        recipient_role=recipient_role,
        recipient_id=recipient_id,
        recipient_class_id=recipient_class_id,
        related_event_id=related_event_id,
        is_read=False,
    )
    db.add(msg)
    return msg


def notify_abnormal(db: Session, event: AbnormalEvent) -> int:
    """异常自动反馈: 按异常类型与关联学生分发消息, 返回生成的消息条数"""
    label = EVENT_LABEL.get(event.event_type, "异常")
    msg_type = EVENT_MSG_TYPE.get(event.event_type, "system_notice")
    title = f"【{label}】{event.event_no}"
    lines = [
        f"异常编号：{event.event_no}",
        f"异常类型：{label}",
        f"异常原因：{event.event_reason or '-'}",
    ]
    if event.camera_code:
        lines.append(f"摄像头：{event.camera_code}")
    if event.student_no:
        lines.append(f"学生学号：{event.student_no}")
    if event.event_detail:
        lines.append(f"详情：{event.event_detail}")
    lines.append(f"等级：{'高' if event.severity == 3 else ('中' if event.severity == 2 else '低')}")
    lines.append("状态：待处理")
    content = "\n".join(lines)

    count = 0
    # 1. 管理员必收
    create_message(db, title, content, msg_type, "admin", related_event_id=event.id)
    count += 1

    # 2. 学生相关异常: 通知学生本人与辅导员
    if event.student_id:
        student = db.query(Student).filter(Student.id == event.student_id).first()
        if student:
            if student.user_id:
                create_message(
                    db, title,
                    content + f"\n\n提示：请检查您的个人信息与人脸注册状态，如有疑问请联系辅导员。",
                    msg_type, "student", recipient_id=student.user_id,
                    recipient_class_id=student.class_id,
                    related_event_id=event.id,
                )
                count += 1
            if student.class_id:
                ci = db.query(ClassInfo).filter(ClassInfo.id == student.class_id).first()
                if ci and ci.counselor_id:
                    create_message(
                        db, title,
                        content + f"\n\n该学生属于您负责的班级：{ci.name}",
                        msg_type, "counselor", recipient_id=ci.counselor_id,
                        recipient_class_id=ci.id,
                        related_event_id=event.id,
                    )
                    count += 1

    event.auto_feedback_sent = True
    return count


def notify_handle_result(db: Session, event: AbnormalEvent, handler_name: str,
                         handle_result: str, handle_note: str = None) -> None:
    """异常处理完成后反馈结果"""
    label = EVENT_LABEL.get(event.event_type, "异常")
    title = f"【处理结果】{event.event_no}"
    content = "\n".join([
        f"异常编号：{event.event_no}",
        f"异常类型：{label}",
        f"处理人：{handler_name}",
        f"处理结果：{handle_result}",
        f"处理说明：{handle_note or '-'}",
        f"当前状态：{event.status}",
    ])
    create_message(db, title, content, "handle_result", "admin", related_event_id=event.id)
    if event.student_id:
        student = db.query(Student).filter(Student.id == event.student_id).first()
        if student and student.user_id:
            create_message(db, title, content, "handle_result", "student",
                           recipient_id=student.user_id, related_event_id=event.id)
