"""学生管理路由"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from datetime import datetime, timedelta
from typing import Optional
from ..database import get_db
from ..utils.auth import get_current_user, require_roles, hash_password
from ..models import *
from .. import config

import sys
sys.path.insert(0, str(config.BASE_DIR))

router = APIRouter(prefix="/api/students", tags=["学生管理"])


def _calc_info_complete(student: Student) -> int:
    """计算学生信息完整度 0-100"""
    total_fields = 10
    filled = 0
    if student.name: filled += 1
    if student.gender: filled += 1
    if student.phone: filled += 1
    if student.id_card: filled += 1
    if student.avatar_path: filled += 1
    if student.college_id: filled += 1
    if student.major_id: filled += 1
    if student.grade_id: filled += 1
    if student.class_id: filled += 1
    if student.room_id: filled += 1
    return int(round(filled / total_fields * 100))


def _student_to_dict(s: Student, db: Session = None) -> dict:
    """学生记录转字典"""
    d = {
        "id": s.id,
        "student_no": s.student_no,
        "name": s.name,
        "gender": s.gender or "",
        "phone": s.phone or "",
        "id_card": s.id_card or "",
        "avatar_path": s.avatar_path or "",
        "info_complete": s.info_complete,
        "college_id": s.college_id,
        "major_id": s.major_id,
        "grade_id": s.grade_id,
        "class_id": s.class_id,
        "building_id": s.building_id,
        "room_id": s.room_id,
        "user_id": s.user_id,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }
    if db:
        d["college_name"] = s.college.name if s.college else ""
        d["major_name"] = s.major.name if s.major else ""
        d["grade_name"] = s.grade.name if s.grade else ""
        d["class_name"] = s.class_info.name if s.class_info else ""
        d["building_name"] = s.building.name if s.building else ""
        d["room_number"] = s.dormitory_room.room_number if s.dormitory_room else ""
        fp = db.query(FaceProfile).filter(FaceProfile.student_id == s.id).first()
        d["face_status"] = fp.face_status if fp else "unregistered"
    return d


@router.get("")
def list_students(
    keyword: Optional[str] = Query(None),
    class_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=500),
    face_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """学生列表"""
    q = db.query(Student).filter(Student.is_deleted == False)

    # 角色权限过滤
    if current_user.role == "student":
        if not current_user.student:
            return {"total": 0, "items": [], "page": page, "limit": limit}
        return {
            "total": 1,
            "items": [_student_to_dict(current_user.student, db)],
            "page": 1,
            "limit": 1,
        }
    elif current_user.role == "counselor":
        if not current_user.counselor_class_id:
            return {"total": 0, "items": [], "page": page, "limit": limit}
        q = q.filter(Student.class_id == current_user.counselor_class_id)

    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(Student.name.like(like), Student.student_no.like(like), Student.phone.like(like)))
    if class_id:
        q = q.filter(Student.class_id == class_id)
    if face_status:
        q = q.outerjoin(FaceProfile, FaceProfile.student_id == Student.id)
        q = q.filter(FaceProfile.face_status == face_status)

    total = q.count()
    items = q.order_by(Student.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "items": [_student_to_dict(s, db) for s in items],
        "page": page,
        "limit": limit,
    }


@router.get("/{student_id}")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """学生详情"""
    s = db.query(Student).filter(Student.id == student_id, Student.is_deleted == False).first()
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")

    if current_user.role == "student":
        if not current_user.student or current_user.student.id != s.id:
            raise HTTPException(status_code=403, detail="权限不足")
    elif current_user.role == "counselor":
        if current_user.counselor_class_id != s.class_id:
            raise HTTPException(status_code=403, detail="权限不足")

    return _student_to_dict(s, db)


@router.post("")
def create_student(
    data: dict,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
):
    """创建学生"""
    if not data.get("student_no") or not data.get("name"):
        raise HTTPException(status_code=400, detail="学号和姓名必填")
    exists = db.query(Student).filter(Student.student_no == data["student_no"], Student.is_deleted == False).first()
    if exists:
        raise HTTPException(status_code=400, detail="学号已存在")

    s = Student(
        student_no=data["student_no"],
        name=data["name"],
        gender=data.get("gender"),
        phone=data.get("phone"),
        id_card=data.get("id_card"),
        avatar_path=data.get("avatar_path"),
        college_id=data.get("college_id"),
        major_id=data.get("major_id"),
        grade_id=data.get("grade_id"),
        class_id=data.get("class_id"),
        building_id=data.get("building_id"),
        room_id=data.get("room_id"),
        user_id=data.get("user_id"),
    )
    db.add(s)
    db.flush()
    s.info_complete = _calc_info_complete(s)
    db.commit()

    log = SysLog(user_id=current_user.id, username=current_user.username,
                 action="CREATE_STUDENT", target=f"student_id={s.id}",
                 detail=f"创建学生 {s.student_no} {s.name}")
    db.add(log)
    db.commit()
    return {"success": True, "data": _student_to_dict(s, db)}


@router.put("/{student_id}")
def update_student(
    student_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """更新学生"""
    s = db.query(Student).filter(Student.id == student_id, Student.is_deleted == False).first()
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")

    if current_user.role == "student":
        if not current_user.student or current_user.student.id != s.id:
            raise HTTPException(status_code=403, detail="权限不足")
        # 学生本人不能改学号、班级、院系
        for k in ("student_no", "class_id", "college_id", "major_id", "grade_id"):
            data.pop(k, None)
    elif current_user.role == "counselor":
        if current_user.counselor_class_id != s.class_id:
            raise HTTPException(status_code=403, detail="权限不足")

    for k, v in data.items():
        if hasattr(s, k) and k != "id":
            setattr(s, k, v)

    s.info_complete = _calc_info_complete(s)
    db.commit()

    log = SysLog(user_id=current_user.id, username=current_user.username,
                 action="UPDATE_STUDENT", target=f"student_id={s.id}",
                 detail=f"更新学生 {s.student_no}")
    db.add(log)
    db.commit()
    return {"success": True, "data": _student_to_dict(s, db)}


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
):
    """逻辑删除学生"""
    s = db.query(Student).filter(Student.id == student_id, Student.is_deleted == False).first()
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")
    s.is_deleted = True
    if s.user_id:
        u = db.query(SysUser).filter(SysUser.id == s.user_id).first()
        if u:
            u.is_deleted = True
    db.commit()

    log = SysLog(user_id=current_user.id, username=current_user.username,
                 action="DELETE_STUDENT", target=f"student_id={s.id}",
                 detail=f"删除学生 {s.student_no} {s.name}")
    db.add(log)
    db.commit()
    return {"success": True}


@router.post("/import")
async def import_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
):
    """批量导入学生 (.xlsx / .csv)"""
    fname = (file.filename or "").lower()
    if not (fname.endswith(".xlsx") or fname.endswith(".csv")):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 或 .csv 文件")

    content = await file.read()
    try:
        if fname.endswith(".csv"):
            import csv
            from io import StringIO
            text = content.decode("utf-8-sig")
            rows = [tuple(r) for r in csv.reader(StringIO(text)) if any((c or "").strip() for c in r)]
        else:
            import openpyxl
            from io import BytesIO
            wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {e}")

    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="Excel内容为空")

    header = [str(c).strip() if c else "" for c in rows[0]]
    success = 0
    fail = 0
    errors = []

    for idx, row in enumerate(rows[1:], start=2):
        try:
            row_dict = {header[i]: row[i] for i in range(len(header))}
            student_no = str(row_dict.get("学号", "") or row_dict.get("student_no", "")).strip()
            name = str(row_dict.get("姓名", "") or row_dict.get("name", "")).strip()
            if not student_no or not name:
                fail += 1
                errors.append(f"第{idx}行: 学号或姓名为空")
                continue

            exists = db.query(Student).filter(Student.student_no == student_no, Student.is_deleted == False).first()
            if exists:
                fail += 1
                errors.append(f"第{idx}行: 学号 {student_no} 已存在")
                continue

            s = Student(
                student_no=student_no,
                name=name,
                gender=str(row_dict.get("性别", "") or row_dict.get("gender", "") or "").strip() or None,
                phone=str(row_dict.get("手机号", "") or row_dict.get("phone", "") or "").strip() or None,
                id_card=str(row_dict.get("身份证", "") or row_dict.get("id_card", "") or "").strip() or None,
            )

            college_name = str(row_dict.get("学院", "") or row_dict.get("college", "") or "").strip()
            major_name = str(row_dict.get("专业", "") or row_dict.get("major", "") or "").strip()
            grade_name = str(row_dict.get("年级", "") or row_dict.get("grade", "") or "").strip()
            class_name = str(row_dict.get("班级", "") or row_dict.get("class", "") or "").strip()

            if college_name:
                c = db.query(College).filter(College.name == college_name).first()
                if not c:
                    c = College(name=college_name)
                    db.add(c); db.flush()
                s.college_id = c.id
                if major_name:
                    m = db.query(Major).filter(Major.name == major_name, Major.college_id == c.id).first()
                    if not m:
                        m = Major(name=major_name, college_id=c.id)
                        db.add(m); db.flush()
                    s.major_id = m.id
                    if grade_name:
                        g = db.query(Grade).filter(Grade.name == grade_name, Grade.major_id == m.id).first()
                        if not g:
                            g = Grade(name=grade_name, major_id=m.id)
                            db.add(g); db.flush()
                        s.grade_id = g.id
                        if class_name:
                            ci = db.query(ClassInfo).filter(ClassInfo.name == class_name, ClassInfo.grade_id == g.id).first()
                            if not ci:
                                ci = ClassInfo(name=class_name, grade_id=g.id)
                                db.add(ci); db.flush()
                            s.class_id = ci.id

            db.add(s)
            db.flush()
            s.info_complete = _calc_info_complete(s)
            success += 1
        except Exception as e:
            fail += 1
            errors.append(f"第{idx}行: {e}")

    db.commit()

    log = SysLog(user_id=current_user.id, username=current_user.username,
                 action="IMPORT_STUDENTS", detail=f"成功 {success}, 失败 {fail}")
    db.add(log)
    db.commit()

    return {"success_count": success, "fail_count": fail, "errors": errors[:20]}


@router.post("/create-accounts")
def create_accounts(
    data: dict,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
):
    """批量创建学生账号"""
    student_ids = data.get("student_ids") or []
    if not student_ids:
        raise HTTPException(status_code=400, detail="请选择学生")

    created = 0
    skipped = 0
    for sid in student_ids:
        s = db.query(Student).filter(Student.id == sid, Student.is_deleted == False).first()
        if not s:
            skipped += 1; continue
        if s.user_id:
            skipped += 1; continue
        if db.query(SysUser).filter(SysUser.username == s.student_no).first():
            skipped += 1; continue

        u = SysUser(
            username=s.student_no,
            password_hash=hash_password(config.DEFAULT_PASSWORD),
            real_name=s.name,
            phone=s.phone,
            role="student",
            student=s,
        )
        db.add(u)
        db.flush()
        s.user_id = u.id
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped, "default_password": config.DEFAULT_PASSWORD}


@router.get("/{student_id}/info-complete")
def student_info_complete(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """学生信息完整度详情"""
    s = db.query(Student).filter(Student.id == student_id, Student.is_deleted == False).first()
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")

    if current_user.role == "student":
        if not current_user.student or current_user.student.id != s.id:
            raise HTTPException(status_code=403, detail="权限不足")

    fields = [
        ("student_no", "学号", bool(s.student_no)),
        ("name", "姓名", bool(s.name)),
        ("gender", "性别", bool(s.gender)),
        ("phone", "手机号", bool(s.phone)),
        ("id_card", "身份证号", bool(s.id_card)),
        ("avatar_path", "头像", bool(s.avatar_path)),
        ("college_id", "学院", bool(s.college_id)),
        ("major_id", "专业", bool(s.major_id)),
        ("class_id", "班级", bool(s.class_id)),
        ("room_id", "宿舍", bool(s.room_id)),
    ]
    filled_count = sum(1 for _, _, ok in fields if ok)
    total = len(fields)

    fp = db.query(FaceProfile).filter(FaceProfile.student_id == s.id).first()
    face_registered = fp and fp.face_status == "registered"

    return {
        "student_id": s.id,
        "student_no": s.student_no,
        "name": s.name,
        "info_complete": s.info_complete,
        "filled_count": filled_count,
        "total_fields": total,
        "face_registered": face_registered,
        "face_status": fp.face_status if fp else "unregistered",
        "fields": [{"key": k, "label": lbl, "filled": ok} for k, lbl, ok in fields],
    }
