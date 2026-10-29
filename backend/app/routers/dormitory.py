"""宿舍管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..utils.auth import get_current_user, require_roles
from ..models import *
from .. import config

import sys
sys.path.insert(0, str(config.BASE_DIR))

router = APIRouter(prefix="/api", tags=["宿舍管理"])


# ========== 宿舍楼 ==========

def _building_to_dict(b: College, db: Session = None) -> dict:
    d = {"id": b.id, "name": b.name, "code": b.code or "", "floors": b.floors}
    if db:
        d["room_count"] = db.query(DormitoryRoom).filter(
            DormitoryRoom.building_id == b.id, DormitoryRoom.is_deleted == False
        ).count()
        d["student_count"] = db.query(Student).filter(
            Student.building_id == b.id, Student.is_deleted == False
        ).count()
    return d


def _room_to_dict(r: DormitoryRoom, db: Session = None) -> dict:
    d = {"id": r.id, "building_id": r.building_id, "room_number": r.room_number, "capacity": r.capacity}
    if db:
        b = db.query(DormitoryBuilding).filter(DormitoryBuilding.id == r.building_id).first()
        d["building_name"] = b.name if b else ""
        d["current_count"] = db.query(Student).filter(
            Student.room_id == r.id, Student.is_deleted == False
        ).count()
    return d


@router.get("/buildings")
def list_buildings(
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(DormitoryBuilding).filter(DormitoryBuilding.is_deleted == False)
    if keyword: q = q.filter(DormitoryBuilding.name.like(f"%{keyword}%"))
    return [_building_to_dict(b, db) for b in q.order_by(DormitoryBuilding.id.asc()).all()]


@router.post("/buildings")
def create_building(data: dict, db: Session = Depends(get_db),
                    current_user: SysUser = Depends(require_roles("admin"))):
    if not data.get("name"): raise HTTPException(status_code=400, detail="名称必填")
    b = DormitoryBuilding(name=data["name"], code=data.get("code"), floors=data.get("floors", 6))
    db.add(b); db.commit(); db.refresh(b)
    return _building_to_dict(b, db)


@router.put("/buildings/{bid}")
def update_building(bid: int, data: dict, db: Session = Depends(get_db),
                    current_user: SysUser = Depends(require_roles("admin"))):
    b = db.query(DormitoryBuilding).filter(DormitoryBuilding.id == bid, DormitoryBuilding.is_deleted == False).first()
    if not b: raise HTTPException(status_code=404, detail="宿舍楼不存在")
    for k, v in data.items():
        if hasattr(b, k) and k != "id": setattr(b, k, v)
    db.commit(); db.refresh(b)
    return _building_to_dict(b, db)


@router.delete("/buildings/{bid}")
def delete_building(bid: int, db: Session = Depends(get_db),
                    current_user: SysUser = Depends(require_roles("admin"))):
    b = db.query(DormitoryBuilding).filter(DormitoryBuilding.id == bid, DormitoryBuilding.is_deleted == False).first()
    if not b: raise HTTPException(status_code=404, detail="宿舍楼不存在")
    rc = db.query(DormitoryRoom).filter(DormitoryRoom.building_id == bid, DormitoryRoom.is_deleted == False).count()
    if rc > 0: raise HTTPException(status_code=400, detail="该楼下还有房间")
    b.is_deleted = True; db.commit()
    return {"success": True}


# ========== 房间 ==========

@router.get("/rooms")
def list_rooms(
    building_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(DormitoryRoom).filter(DormitoryRoom.is_deleted == False)
    if building_id: q = q.filter(DormitoryRoom.building_id == building_id)
    if keyword: q = q.filter(DormitoryRoom.room_number.like(f"%{keyword}%"))

    total = q.count()
    items = q.order_by(DormitoryRoom.id.asc()).offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "items": [_room_to_dict(r, db) for r in items], "page": page, "limit": limit}


@router.post("/rooms")
def create_room(data: dict, db: Session = Depends(get_db),
                current_user: SysUser = Depends(require_roles("admin"))):
    if not data.get("building_id") or not data.get("room_number"):
        raise HTTPException(status_code=400, detail="楼栋和房间号必填")
    r = DormitoryRoom(
        building_id=data["building_id"],
        room_number=data["room_number"],
        capacity=data.get("capacity", 4),
    )
    db.add(r); db.commit(); db.refresh(r)
    return _room_to_dict(r, db)


@router.put("/rooms/{rid}")
def update_room(rid: int, data: dict, db: Session = Depends(get_db),
                current_user: SysUser = Depends(require_roles("admin"))):
    r = db.query(DormitoryRoom).filter(DormitoryRoom.id == rid, DormitoryRoom.is_deleted == False).first()
    if not r: raise HTTPException(status_code=404, detail="房间不存在")
    for k, v in data.items():
        if hasattr(r, k) and k != "id": setattr(r, k, v)
    db.commit(); db.refresh(r)
    return _room_to_dict(r, db)


@router.delete("/rooms/{rid}")
def delete_room(rid: int, db: Session = Depends(get_db),
                current_user: SysUser = Depends(require_roles("admin"))):
    r = db.query(DormitoryRoom).filter(DormitoryRoom.id == rid, DormitoryRoom.is_deleted == False).first()
    if not r: raise HTTPException(status_code=404, detail="房间不存在")
    sc = db.query(Student).filter(Student.room_id == rid, Student.is_deleted == False).count()
    if sc > 0: raise HTTPException(status_code=400, detail="该房间还有学生")
    r.is_deleted = True; db.commit()
    return {"success": True}
