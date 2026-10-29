"""数据库模型定义 - 智慧宿舍人脸门禁与学生管理系统"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from ..database import Base


class TimestampMixin:
    """时间戳混入"""
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)


# ============== 系统权限模块 ==============

class SysUser(Base, TimestampMixin):
    """系统用户表"""
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    real_name = Column(String(64), nullable=False)
    phone = Column(String(20))
    email = Column(String(128))
    role = Column(String(32), nullable=False, index=True)  # admin, counselor, student
    status = Column(Integer, default=1, nullable=False)  # 1启用, 0禁用
    must_change_password = Column(Boolean, default=False)
    counselor_class_id = Column(Integer, ForeignKey("class_info.id"), nullable=True)

    student = relationship("Student", back_populates="user", uselist=False)
    counselor_class = relationship("ClassInfo", foreign_keys=[counselor_class_id])


class SysLog(Base, TimestampMixin):
    """操作日志"""
    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("sys_user.id"))
    username = Column(String(64))
    action = Column(String(128), nullable=False)
    target = Column(String(256))
    detail = Column(Text)
    ip_address = Column(String(64))
    status = Column(Integer, default=1)


# ============== 组织架构模块 ==============

class College(Base, TimestampMixin):
    """学院"""
    __tablename__ = "college"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    code = Column(String(32))

    majors = relationship("Major", back_populates="college")


class Major(Base, TimestampMixin):
    """专业"""
    __tablename__ = "major"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    college_id = Column(Integer, ForeignKey("college.id"), nullable=False)

    college = relationship("College", back_populates="majors")
    grades = relationship("Grade", back_populates="major")


class Grade(Base, TimestampMixin):
    """年级"""
    __tablename__ = "grade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), nullable=False)  # 如 2023级
    major_id = Column(Integer, ForeignKey("major.id"), nullable=False)

    major = relationship("Major", back_populates="grades")
    classes = relationship("ClassInfo", back_populates="grade")


class ClassInfo(Base, TimestampMixin):
    """班级"""
    __tablename__ = "class_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    grade_id = Column(Integer, ForeignKey("grade.id"), nullable=False)
    counselor_id = Column(Integer, ForeignKey("sys_user.id"))

    grade = relationship("Grade", back_populates="classes")
    counselor = relationship("SysUser", foreign_keys=[counselor_id])
    students = relationship("Student", back_populates="class_info")


# ============== 宿舍模块 ==============

class DormitoryBuilding(Base, TimestampMixin):
    """宿舍楼"""
    __tablename__ = "dormitory_building"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)  # 如 1号楼
    code = Column(String(32))
    floors = Column(Integer, default=6)

    rooms = relationship("DormitoryRoom", back_populates="building")
    cameras = relationship("CameraDevice", back_populates="building")


class DormitoryRoom(Base, TimestampMixin):
    """宿舍房间"""
    __tablename__ = "dormitory_room"

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(Integer, ForeignKey("dormitory_building.id"), nullable=False)
    room_number = Column(String(16), nullable=False)  # 如 301
    capacity = Column(Integer, default=4)

    building = relationship("DormitoryBuilding", back_populates="rooms")
    students = relationship("Student", back_populates="dormitory_room")


# ============== 学生信息模块 ==============

class Student(Base, TimestampMixin):
    """学生信息"""
    __tablename__ = "student"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_no = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    gender = Column(String(8))
    phone = Column(String(20))
    id_card = Column(String(32))
    avatar_path = Column(String(256))
    info_complete = Column(Integer, default=0)  # 信息完整度 0-100

    college_id = Column(Integer, ForeignKey("college.id"))
    major_id = Column(Integer, ForeignKey("major.id"))
    grade_id = Column(Integer, ForeignKey("grade.id"))
    class_id = Column(Integer, ForeignKey("class_info.id"))
    building_id = Column(Integer, ForeignKey("dormitory_building.id"))
    room_id = Column(Integer, ForeignKey("dormitory_room.id"))

    user_id = Column(Integer, ForeignKey("sys_user.id"))

    user = relationship("SysUser", back_populates="student")
    class_info = relationship("ClassInfo", back_populates="students")
    dormitory_room = relationship("DormitoryRoom", back_populates="students")
    college = relationship("College")
    major = relationship("Major")
    grade = relationship("Grade")
    building = relationship("DormitoryBuilding")
    face_profile = relationship("FaceProfile", back_populates="student", uselist=False)
    presence_status = relationship("PresenceStatus", back_populates="student", uselist=False)
    access_records = relationship("AccessRecord", back_populates="student")


# ============== 人脸模块 ==============

class FaceProfile(Base, TimestampMixin):
    """人脸档案"""
    __tablename__ = "face_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("student.id"), unique=True, nullable=False)
    face_status = Column(String(16), default="unregistered", nullable=False, index=True)
    # unregistered, registering, registered, failed, cancelled

    face_image_path = Column(String(256))
    face_embedding = Column(Text)  # JSON序列化的特征向量
    embedding_model = Column(String(64))
    face_quality_score = Column(Float, default=0.0)
    face_count = Column(Integer, default=0)  # 多张人脸融合

    last_verify_time = Column(DateTime)
    verify_count = Column(Integer, default=0)
    verify_success_count = Column(Integer, default=0)

    student = relationship("Student", back_populates="face_profile")


# ============== 摄像头与门禁模块 ==============

class CameraDevice(Base, TimestampMixin):
    """摄像头设备"""
    __tablename__ = "camera_device"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    location = Column(String(256))
    direction = Column(String(8), nullable=False, index=True)  # IN, OUT
    building_id = Column(Integer, ForeignKey("dormitory_building.id"))

    stream_url = Column(String(512))
    device_status = Column(String(16), default="online", index=True)
    # online, offline, error, maintenance

    last_heartbeat = Column(DateTime)
    fps = Column(Float, default=0.0)
    recognition_success_rate = Column(Float, default=0.0)
    health_score = Column(Float, default=100.0)

    building = relationship("DormitoryBuilding", back_populates="cameras")
    access_records = relationship("AccessRecord", back_populates="camera")


class AccessRecord(Base, TimestampMixin):
    """门禁记录"""
    __tablename__ = "access_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=True, index=True)
    student_no = Column(String(32))
    student_name = Column(String(64))

    camera_id = Column(Integer, ForeignKey("camera_device.id"), nullable=False, index=True)
    camera_code = Column(String(32))
    building_id = Column(Integer, ForeignKey("dormitory_building.id"))
    building_name = Column(String(64))

    direction = Column(String(8), nullable=False, index=True)  # IN, OUT
    similarity = Column(Float, default=0.0)
    recognition_ms = Column(Float, default=0.0)  # AI识别耗时(毫秒)
    verify_result = Column(String(16), nullable=False, index=True)  # success, failed
    capture_image_path = Column(String(256))
    recognition_mode = Column(String(32))  # realtime, video, photo

    occurred_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

    student = relationship("Student", back_populates="access_records")
    camera = relationship("CameraDevice", back_populates="access_records")


class PresenceStatus(Base, TimestampMixin):
    """在寝状态"""
    __tablename__ = "presence_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("student.id"), unique=True, nullable=False)
    is_present = Column(Boolean, default=False, nullable=False, index=True)
    last_direction = Column(String(8))  # IN, OUT
    last_access_time = Column(DateTime)
    last_access_record_id = Column(Integer, ForeignKey("access_record.id"))

    student = relationship("Student", back_populates="presence_status")


# ============== 异常处理模块 ==============

class AbnormalEvent(Base, TimestampMixin):
    """异常事件"""
    __tablename__ = "abnormal_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_no = Column(String(32), unique=True, nullable=False, index=True)

    event_type = Column(String(32), nullable=False, index=True)
    # device_error, image_quality, ai_recognition, business

    event_reason = Column(String(128))
    event_detail = Column(Text)

    camera_id = Column(Integer, ForeignKey("camera_device.id"))
    camera_code = Column(String(32))
    student_id = Column(Integer, ForeignKey("student.id"))
    student_no = Column(String(32))

    severity = Column(Integer, default=2)  # 1低, 2中, 3高
    status = Column(String(16), default="pending", index=True)
    # pending, processing, resolved, closed, auto_recovered

    auto_feedback_sent = Column(Boolean, default=False)
    occurred_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

    handles = relationship("AbnormalHandle", back_populates="event")


class AbnormalHandle(Base, TimestampMixin):
    """异常处理记录"""
    __tablename__ = "abnormal_handle"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("abnormal_event.id"), nullable=False)
    handler_id = Column(Integer, ForeignKey("sys_user.id"))
    handler_name = Column(String(64))
    handle_type = Column(String(32))  # manual, auto_recover
    handle_result = Column(String(256))
    handle_note = Column(Text)

    event = relationship("AbnormalEvent", back_populates="handles")


# ============== 消息模块 ==============

class MessageNotification(Base, TimestampMixin):
    """消息通知"""
    __tablename__ = "message_notification"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)
    content = Column(Text)
    message_type = Column(String(32), index=True)
    # system_notice, info_complete_reminder, face_register_reminder,
    # device_error, face_verify_error, access_abnormal, handle_result

    recipient_role = Column(String(32), index=True)  # admin, counselor, student
    recipient_id = Column(Integer, index=True)
    recipient_class_id = Column(Integer, ForeignKey("class_info.id"))

    related_event_id = Column(Integer, ForeignKey("abnormal_event.id"))

    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)


# ============== 权限模型(角色/权限/关联) ==============

class SysRole(Base, TimestampMixin):
    """角色表"""
    __tablename__ = "sys_role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)  # admin / counselor / student
    name = Column(String(64), nullable=False)
    description = Column(String(256))


class SysPermission(Base, TimestampMixin):
    """权限表"""
    __tablename__ = "sys_permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    module = Column(String(64))
    description = Column(String(256))


class SysUserRole(Base):
    """用户-角色关联表"""
    __tablename__ = "sys_user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("sys_role.id"), nullable=False, index=True)


# ============== 宿舍分配与门禁点位 ==============

class StudentDormitory(Base, TimestampMixin):
    """学生宿舍分配记录(支持历史追溯)"""
    __tablename__ = "student_dormitory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False, index=True)
    building_id = Column(Integer, ForeignKey("dormitory_building.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("dormitory_room.id"), nullable=False)
    bed_no = Column(String(16))
    check_in_at = Column(DateTime, default=datetime.now)
    check_out_at = Column(DateTime)
    is_current = Column(Boolean, default=True, nullable=False, index=True)


class AccessPoint(Base, TimestampMixin):
    """门禁点位(摄像头与宿舍楼门的绑定关系)"""
    __tablename__ = "access_point"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    building_id = Column(Integer, ForeignKey("dormitory_building.id"))
    camera_id = Column(Integer, ForeignKey("camera_device.id"))
    direction = Column(String(8), nullable=False, index=True)
    status = Column(String(16), default="normal")  # normal, disabled, maintenance


class SystemConfig(Base, TimestampMixin):
    """系统配置表"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(64), unique=True, nullable=False, index=True)
    config_value = Column(String(512))
    description = Column(String(256))


# ============== 索引 ==============
Index("ix_access_record_occurred", AccessRecord.occurred_at.desc())
Index("ix_abnormal_status", AbnormalEvent.status, AbnormalEvent.event_type)
