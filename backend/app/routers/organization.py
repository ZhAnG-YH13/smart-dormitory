"""组织架构路由 (学院/专业/年级/班级)"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from ..database import get_db
from ..utils.auth import get_current_user, require_roles
from ..models import *
from .. import config

import sys
sys.path.insert(0, str(config.BASE_DIR))

router = APIRouter(prefix="/api", tags=["组织架构"])


def _college_to_dict(c: College, db: Session = None) -> dict:
    return {
        "id": c.id, "name": c.name, "code": c.code or "",
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _major_to_dict(m: Major, db: Session = None) -> dict:
    d = {"id": m.id, "name": m.name, "college_id": m.college_id}
    if db:
        c = db.query(College).filter(College.id == m.college_id).first()
        d["college_name"] = c.name if c else ""
    return d


def _grade_to_dict(g: Grade, db: Session = None) -> dict:
    d = {"id": g.id, "name": g.name, "major_id": g.major_id}
    if db:
        m = db.query(Major).filter(Major.id == g.major_id).first()
        d["major_name"] = m.name if m else ""
        if m:
            c = db.query(College).filter(College.id == m.college_id).first()
            d["college_name"] = c.name if c else ""
    return d


def _class_to_dict(c: ClassInfo, db: Session = None) -> dict:
    d = {
        "id": c.id, "name": c.name, "grade_id": c.grade_id,
        "counselor_id": c.counselor_id,
    }
    if db:
        g = db.query(Grade).filter(Grade.id == c.grade_id).first()
        d["grade_name"] = g.name if g else ""
        if g:
            m = db.query(Major).filter(Major.id == g.major_id).first()
            d["major_name"] = m.name if m else ""
            if m:
                col = db.query(College).filter(College.id == m.college_id).first()
                d["college_name"] = col.name if col else ""
        if c.counselor_id:
            u = db.query(SysUser).filter(SysUser.id == c.counselor_id).first()
            d["counselor_name"] = u.real_name if u else ""
        else:
            d["counselor_name"] = ""
        d["student_count"] = db.query(Student).filter(
            Student.class_id == c.id, Student.is_deleted == False
        ).count()
    return d


# ========== 学院 ==========

@router.get("/colleges")
def list_colleges(
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(College).filter(College.is_deleted == False)
    if keyword:
        q = q.filter(College.name.like(f"%{keyword}%"))
    return [_college_to_dict(c) for c in q.order_by(College.id.asc()).all()]


@router.post("/colleges")
def create_college(data: dict, db: Session = Depends(get_db),
                   current_user: SysUser = Depends(require_roles("admin"))):
    if not data.get("name"):
        raise HTTPException(status_code=400, detail="名称必填")
    if db.query(College).filter(College.name == data["name"], College.is_deleted == False).first():
        raise HTTPException(status_code=400, detail="学院已存在")
    c = College(name=data["name"], code=data.get("code"))
    db.add(c); db.commit()
    db.refresh(c)
    return _college_to_dict(c)


@router.put("/colleges/{cid}")
def update_college(cid: int, data: dict, db: Session = Depends(get_db),
                   current_user: SysUser = Depends(require_roles("admin"))):
    c = db.query(College).filter(College.id == cid, College.is_deleted == False).first()
    if not c: raise HTTPException(status_code=404, detail="学院不存在")
    for k, v in data.items():
        if hasattr(c, k) and k != "id": setattr(c, k, v)
    db.commit(); db.refresh(c)
    return _college_to_dict(c)


@router.delete("/colleges/{cid}")
def delete_college(cid: int, db: Session = Depends(get_db),
                   current_user: SysUser = Depends(require_roles("admin"))):
    c = db.query(College).filter(College.id == cid, College.is_deleted == False).first()
    if not c: raise HTTPException(status_code=404, detail="学院不存在")
    major_count = db.query(Major).filter(Major.college_id == cid, Major.is_deleted == False).count()
    if major_count > 0:
        raise HTTPException(status_code=400, detail="该学院下还有专业，无法删除")
    c.is_deleted = True; db.commit()
    return {"success": True}


# ========== 专业 ==========

@router.get("/majors")
def list_majors(
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(Major).filter(Major.is_deleted == False)
    if college_id: q = q.filter(Major.college_id == college_id)
    return [_major_to_dict(m, db) for m in q.order_by(Major.id.asc()).all()]


@router.post("/majors")
def create_major(data: dict, db: Session = Depends(get_db),
                 current_user: SysUser = Depends(require_roles("admin"))):
    if not data.get("name") or not data.get("college_id"):
        raise HTTPException(status_code=400, detail="名称和学院必填")
    m = Major(name=data["name"], college_id=data["college_id"])
    db.add(m); db.commit(); db.refresh(m)
    return _major_to_dict(m, db)


@router.put("/majors/{mid}")
def update_major(mid: int, data: dict, db: Session = Depends(get_db),
                 current_user: SysUser = Depends(require_roles("admin"))):
    m = db.query(Major).filter(Major.id == mid, Major.is_deleted == False).first()
    if not m: raise HTTPException(status_code=404, detail="专业不存在")
    for k, v in data.items():
        if hasattr(m, k) and k != "id": setattr(m, k, v)
    db.commit(); db.refresh(m)
    return _major_to_dict(m, db)


@router.delete("/majors/{mid}")
def delete_major(mid: int, db: Session = Depends(get_db),
                 current_user: SysUser = Depends(require_roles("admin"))):
    m = db.query(Major).filter(Major.id == mid, Major.is_deleted == False).first()
    if not m: raise HTTPException(status_code=404, detail="专业不存在")
    gc = db.query(Grade).filter(Grade.major_id == mid, Grade.is_deleted == False).count()
    if gc > 0: raise HTTPException(status_code=400, detail="该专业下还有年级")
    m.is_deleted = True; db.commit()
    return {"success": True}


# ========== 年级 ==========

@router.get("/grades")
def list_grades(
    major_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(Grade).filter(Grade.is_deleted == False)
    if major_id: q = q.filter(Grade.major_id == major_id)
    return [_grade_to_dict(g, db) for g in q.order_by(Grade.id.asc()).all()]


@router.post("/grades")
def create_grade(data: dict, db: Session = Depends(get_db),
                 current_user: SysUser = Depends(require_roles("admin"))):
    if not data.get("name") or not data.get("major_id"):
        raise HTTPException(status_code=400, detail="名称和专业必填")
    g = Grade(name=data["name"], major_id=data["major_id"])
    db.add(g); db.commit(); db.refresh(g)
    return _grade_to_dict(g, db)


@router.put("/grades/{gid}")
def update_grade(gid: int, data: dict, db: Session = Depends(get_db),
                 current_user: SysUser = Depends(require_roles("admin"))):
    g = db.query(Grade).filter(Grade.id == gid, Grade.is_deleted == False).first()
    if not g: raise HTTPException(status_code=404, detail="年级不存在")
    for k, v in data.items():
        if hasattr(g, k) and k != "id": setattr(g, k, v)
    db.commit(); db.refresh(g)
    return _grade_to_dict(g, db)


@router.delete("/grades/{gid}")
def delete_grade(gid: int, db: Session = Depends(get_db),
                 current_user: SysUser = Depends(require_roles("admin"))):
    g = db.query(Grade).filter(Grade.id == gid, Grade.is_deleted == False).first()
    if not g: raise HTTPException(status_code=404, detail="年级不存在")
    cc = db.query(ClassInfo).filter(ClassInfo.grade_id == gid, ClassInfo.is_deleted == False).count()
    if cc > 0: raise HTTPException(status_code=400, detail="该年级下还有班级")
    g.is_deleted = True; db.commit()
    return {"success": True}


# ========== 班级 ==========

@router.get("/classes")
def list_classes(
    grade_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(ClassInfo).filter(ClassInfo.is_deleted == False)
    if grade_id: q = q.filter(ClassInfo.grade_id == grade_id)
    if keyword: q = q.filter(ClassInfo.name.like(f"%{keyword}%"))

    # 辅导员只看自己班级
    if current_user.role == "counselor" and current_user.counselor_class_id:
        q = q.filter(ClassInfo.id == current_user.counselor_class_id)

    return [_class_to_dict(c, db) for c in q.order_by(ClassInfo.id.asc()).all()]


@router.post("/classes")
def create_class(data: dict, db: Session = Depends(get_db),
                 current_user: SysUser = Depends(require_roles("admin"))):
    if not data.get("name") or not data.get("grade_id"):
        raise HTTPException(status_code=400, detail="名称和年级必填")
    c = ClassInfo(name=data["name"], grade_id=data["grade_id"], counselor_id=data.get("counselor_id"))
    db.add(c); db.commit(); db.refresh(c)
    return _class_to_dict(c, db)


@router.put("/classes/{cid}")
def update_class(cid: int, data: dict, db: Session = Depends(get_db),
                 current_user: SysUser = Depends(require_roles("admin"))):
    c = db.query(ClassInfo).filter(ClassInfo.id == cid, ClassInfo.is_deleted == False).first()
    if not c: raise HTTPException(status_code=404, detail="班级不存在")
    for k, v in data.items():
        if hasattr(c, k) and k != "id": setattr(c, k, v)
    db.commit(); db.refresh(c)
    return _class_to_dict(c, db)


@router.delete("/classes/{cid}")
def delete_class(cid: int, db: Session = Depends(get_db),
                 current_user: SysUser = Depends(require_roles("admin"))):
    c = db.query(ClassInfo).filter(ClassInfo.id == cid, ClassInfo.is_deleted == False).first()
    if not c: raise HTTPException(status_code=404, detail="班级不存在")
    sc = db.query(Student).filter(Student.class_id == cid, Student.is_deleted == False).count()
    if sc > 0: raise HTTPException(status_code=400, detail="该班级下还有学生")
    c.is_deleted = True; db.commit()
    return {"success": True}


@router.get("/classes/{cid}/students")
def list_class_students(
    cid: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """班级下的学生列表"""
    c = db.query(ClassInfo).filter(ClassInfo.id == cid, ClassInfo.is_deleted == False).first()
    if not c: raise HTTPException(status_code=404, detail="班级不存在")

    q = db.query(Student).filter(Student.class_id == cid, Student.is_deleted == False)
    total = q.count()
    items = q.order_by(Student.id.desc()).offset((page - 1) * limit).limit(limit).all()

    def s_to_dict(s):
        fp = db.query(FaceProfile).filter(FaceProfile.student_id == s.id).first()
        return {
            "id": s.id, "student_no": s.student_no, "name": s.name,
            "gender": s.gender or "", "phone": s.phone or "",
            "face_status": fp.face_status if fp else "unregistered",
            "info_complete": s.info_complete,
        }

    return {"total": total, "items": [s_to_dict(s) for s in items],
            "class_name": c.name, "page": page, "limit": limit}
