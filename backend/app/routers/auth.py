"""认证 API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import SysUser, SysLog, Student, FaceProfile
from ..utils.auth import hash_password, verify_password, create_access_token, get_current_user
from .. import config

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: dict
    must_change_password: bool
    info_complete: int
    face_registered: bool


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(SysUser).filter(SysUser.username == req.username, SysUser.is_deleted == False).first()

    if not user:
        # 记录失败
        raise HTTPException(status_code=401, detail={"code": "USER_NOT_FOUND", "msg": "用户不存在"})

    if user.status != 1:
        raise HTTPException(status_code=403, detail={"code": "USER_DISABLED", "msg": "用户已禁用"})

    if not verify_password(req.password, user.password_hash):
        # 记录日志
        log = SysLog(user_id=user.id, username=user.username, action="LOGIN_FAILED", detail="密码错误")
        db.add(log)
        db.commit()
        raise HTTPException(status_code=401, detail={"code": "PASSWORD_ERROR", "msg": "密码错误"})

    # 创建 token
    token = create_access_token(data={"sub": user.id, "role": user.role})

    # 额外信息
    info_complete = 100
    face_registered = False
    if user.role == "student":
        student = db.query(Student).filter(Student.user_id == user.id).first()
        if student:
            info_complete = student.info_complete
            fp = db.query(FaceProfile).filter(FaceProfile.student_id == student.id).first()
            face_registered = bool(fp and fp.face_status == "registered")

    # 日志
    log = SysLog(user_id=user.id, username=user.username, action="LOGIN", detail=f"登录成功, 角色={user.role}")
    db.add(log)
    db.commit()

    return LoginResponse(
        token=token,
        user={
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "role": user.role,
            "phone": user.phone or "",
            "email": user.email or ""
        },
        must_change_password=user.must_change_password,
        info_complete=info_complete,
        face_registered=face_registered
    )


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, db: Session = Depends(get_db),
                    current_user: SysUser = Depends(get_current_user)):
    """修改密码"""
    if not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")

    current_user.password_hash = hash_password(req.new_password)
    current_user.must_change_password = False

    log = SysLog(user_id=current_user.id, username=current_user.username,
                 action="CHANGE_PASSWORD", detail="修改密码")
    db.add(log)
    db.commit()

    return {"success": True, "msg": "密码修改成功"}


@router.get("/me")
def get_me(current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    info_complete = 100
    face_registered = False
    class_info = None

    if current_user.role == "student":
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student:
            info_complete = student.info_complete
            fp = db.query(FaceProfile).filter(FaceProfile.student_id == student.id).first()
            face_registered = bool(fp and fp.face_status == "registered")
    elif current_user.role == "counselor" and current_user.counselor_class_id:
        from ..models import ClassInfo
        ci = db.query(ClassInfo).filter(ClassInfo.id == current_user.counselor_class_id).first()
        if ci:
            class_info = {"id": ci.id, "name": ci.name}

    return {
        "id": current_user.id,
        "username": current_user.username,
        "real_name": current_user.real_name,
        "role": current_user.role,
        "phone": current_user.phone or "",
        "email": current_user.email or "",
        "must_change_password": current_user.must_change_password,
        "info_complete": info_complete,
        "face_registered": face_registered,
        "class_info": class_info
    }
