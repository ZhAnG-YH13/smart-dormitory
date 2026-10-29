"""智慧宿舍人脸门禁与学生管理系统 - FastAPI 入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
import os
import sys

# 添加项目根目录到 Python 路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.database import init_db, SessionLocal
from app.config import CORS_ORIGINS, UPLOAD_DIR, FACE_UPLOAD_DIR, ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_NAME, DEFAULT_PASSWORD
from app.utils.auth import hash_password
from app.models import (
    SysUser, College, Major, Grade, ClassInfo, DormitoryBuilding,
    DormitoryRoom, Student, CameraDevice, PresenceStatus, FaceProfile,
    SysRole, SysPermission, SysUserRole, StudentDormitory, AccessPoint, SystemConfig
)


def seed_initial_data():
    """初始化种子数据：管理员、组织架构、摄像头等"""
    db = SessionLocal()
    try:
        # 1. 创建管理员
        if not db.query(SysUser).filter(SysUser.username == ADMIN_USERNAME).first():
            admin = SysUser(
                username=ADMIN_USERNAME,
                password_hash=hash_password(ADMIN_PASSWORD),
                real_name=ADMIN_NAME,
                role="admin",
                phone="13800000000",
                status=1,
                must_change_password=False
            )
            db.add(admin)
            print(f"[SEED] 创建管理员: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")

        # 2. 创建示例辅导员
        if not db.query(SysUser).filter(SysUser.username == "counselor01").first():
            counselor = SysUser(
                username="counselor01",
                password_hash=hash_password("123456"),
                real_name="李辅导员",
                role="counselor",
                phone="13900000001",
                status=1
            )
            db.add(counselor)
            print("[SEED] 创建辅导员: counselor01 / 123456")

        # 3. 创建学院
        if db.query(College).count() == 0:
            colleges_data = [
                ("人工智能学院", "AI001"),
                ("计算机学院", "CS001"),
                ("电子信息学院", "EE001"),
            ]
            for name, code in colleges_data:
                db.add(College(name=name, code=code))
            db.flush()
            print(f"[SEED] 创建学院: {len(colleges_data)} 个")

        # 获取已有的学院
        colleges = db.query(College).filter(College.is_deleted == False).all()
        college_ai = colleges[0]  # 人工智能学院

        # 4. 创建专业
        if db.query(Major).count() == 0:
            majors_data = [
                ("人工智能专业", college_ai.id),
                ("计算机科学与技术", colleges[1].id if len(colleges) > 1 else college_ai.id),
                ("软件工程", colleges[1].id if len(colleges) > 1 else college_ai.id),
            ]
            for name, cid in majors_data:
                db.add(Major(name=name, college_id=cid))
            db.flush()
            print(f"[SEED] 创建专业: {len(majors_data)} 个")

        majors = db.query(Major).filter(Major.is_deleted == False).all()
        major_ai = majors[0]

        # 5. 创建年级
        if db.query(Grade).count() == 0:
            for name in ["2022级", "2023级", "2024级"]:
                db.add(Grade(name=name, major_id=major_ai.id))
            db.flush()
            print("[SEED] 创建年级: 3 个")

        grades = db.query(Grade).filter(Grade.is_deleted == False).all()

        # 6. 创建班级
        if db.query(ClassInfo).count() == 0:
            counselor_user = db.query(SysUser).filter(SysUser.username == "counselor01").first()
            for g in grades:
                for cls_name in [f"{g.name[:4]}01班", f"{g.name[:4]}02班"]:
                    ci = ClassInfo(name=cls_name, grade_id=g.id)
                    if counselor_user and g == grades[1]:  # 2023级由辅导员管理
                        ci.counselor_id = counselor_user.id
                        counselor_user.counselor_class_id = ci.id
                    db.add(ci)
            db.flush()
            print("[SEED] 创建班级: 6 个")

        # 7. 创建宿舍楼和宿舍
        if db.query(DormitoryBuilding).count() == 0:
            for bname in ["1号楼", "2号楼"]:
                b = DormitoryBuilding(name=bname, code=f"B{bname[0]}", floors=6)
                db.add(b)
            db.flush()

            buildings = db.query(DormitoryBuilding).all()
            for b in buildings:
                for floor in range(1, 5):
                    for room in range(1, 5):
                        db.add(DormitoryRoom(
                            building_id=b.id,
                            room_number=f"{floor}{room:02d}",
                            capacity=4
                        ))
            db.flush()
            print("[SEED] 创建宿舍楼和宿舍房间")

        # 8. 关联辅导员班级
        counselor_user = db.query(SysUser).filter(SysUser.username == "counselor01").first()
        if counselor_user and not counselor_user.counselor_class_id:
            cls_2301 = db.query(ClassInfo).filter(ClassInfo.name == "202301班").first()
            if cls_2301:
                counselor_user.counselor_class_id = cls_2301.id

        # 9. 创建示例学生 (10人)
        if db.query(Student).count() == 0:
            import random
            classes = db.query(ClassInfo).filter(ClassInfo.is_deleted == False).all()
            rooms = db.query(DormitoryRoom).all()

            surnames = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴", "徐", "孙"]
            given_names = ["伟", "芳", "娜", "敏", "静", "强", "磊", "洋", "勇", "艳", "杰", "娟", "涛", "明", "超"]

            buildings = db.query(DormitoryBuilding).all()
            majors_all = db.query(Major).filter(Major.is_deleted == False).all()

            students_created = 0
            for i in range(10):
                class_info = classes[i % len(classes)]
                room = rooms[i % len(rooms)]
                building = buildings[0]
                major = majors_all[i % len(majors_all)]
                college = db.query(College).filter(College.id == major.college_id).first()

                no = f"2023{1001+i:04d}"
                name = random.choice(surnames) + random.choice(given_names)

                # 创建用户账号
                user = SysUser(
                    username=no,
                    password_hash=hash_password(DEFAULT_PASSWORD),
                    real_name=name,
                    role="student",
                    phone=f"138{random.randint(10000000, 99999999)}",
                    status=1,
                    must_change_password=False
                )
                db.add(user)
                db.flush()

                # 创建学生记录
                student = Student(
                    student_no=no,
                    name=name,
                    gender="男" if i % 2 == 0 else "女",
                    phone=user.phone,
                    college_id=college.id if college else None,
                    major_id=major.id,
                    grade_id=class_info.grade_id,
                    class_id=class_info.id,
                    building_id=building.id,
                    room_id=room.id,
                    user_id=user.id,
                    info_complete=90 if i % 3 != 0 else 60
                )
                db.add(student)
                db.flush()

                # 初始化在寝状态
                db.add(PresenceStatus(student_id=student.id, is_present=(i % 2 == 0)))

                # 部分学生有人脸档案
                if i % 4 != 0:
                    db.add(FaceProfile(
                        student_id=student.id,
                        face_status="registered",
                        face_quality_score=0.85
                    ))

                students_created += 1

            print(f"[SEED] 创建示例学生: {students_created} 人")

        # 10. 创建摄像头
        if db.query(CameraDevice).count() == 0:
            buildings = db.query(DormitoryBuilding).all()
            if buildings:
                b = buildings[0]
                cams = [
                    ("CAM001", "1号楼东门入口", "IN", b.id),
                    ("CAM002", "1号楼东门出口", "OUT", b.id),
                    ("CAM003", "1号楼西门入口", "IN", b.id),
                    ("CAM004", "1号楼西门出口", "OUT", b.id),
                ]
                for code, name, direction, bid in cams:
                    db.add(CameraDevice(
                        camera_code=code,
                        name=name,
                        location=b.name + " " + name.split("东")[0].split("西")[0],
                        direction=direction,
                        building_id=bid,
                        device_status="online"
                    ))
                print("[SEED] 创建摄像头: 4 个")

        # 11. 角色 / 权限 / 用户角色关联
        if db.query(SysRole).count() == 0:
            roles_data = [
                ("admin", "学校管理员", "全校最高权限，管理所有数据"),
                ("counselor", "辅导员", "仅管理所带班级学生"),
                ("student", "学生", "仅查看和操作本人信息"),
            ]
            role_obj = {}
            for code, name, desc in roles_data:
                r = SysRole(code=code, name=name, description=desc)
                db.add(r); db.flush()
                role_obj[code] = r

            perms_data = [
                ("student:view", "查看学生", "student"),
                ("student:manage", "管理学生", "student"),
                ("student:import", "导入学生", "student"),
                ("face:register", "人脸注册", "face"),
                ("face:verify", "人脸验证", "face"),
                ("access:view", "查看门禁记录", "access"),
                ("access:simulate", "门禁模拟", "access"),
                ("abnormal:view", "查看异常", "abnormal"),
                ("abnormal:handle", "处理异常", "abnormal"),
                ("statistics:view", "查看统计", "statistics"),
                ("system:manage", "系统管理", "system"),
            ]
            for code, name, module in perms_data:
                db.add(SysPermission(code=code, name=name, module=module))
            db.flush()

            # 分配用户角色
            for u in db.query(SysUser).all():
                r = role_obj.get(u.role)
                if r:
                    db.add(SysUserRole(user_id=u.id, role_id=r.id))
            print("[SEED] 创建角色/权限/用户角色关联")

        # 12. 学生住宿记录
        if db.query(StudentDormitory).count() == 0:
            students_all = db.query(Student).filter(Student.is_deleted == False).all()
            for s in students_all:
                if s.room_id:
                    db.add(StudentDormitory(
                        student_id=s.id,
                        building_id=s.building_id,
                        room_id=s.room_id,
                        bed_no="1",
                        check_in_at=datetime.now(),
                        is_current=True,
                    ))
            print(f"[SEED] 创建学生住宿记录: {len(students_all)} 条")

        # 13. 门禁点位
        if db.query(AccessPoint).count() == 0:
            for cam in db.query(CameraDevice).all():
                db.add(AccessPoint(
                    code=f"AP{cam.camera_code}",
                    name=cam.name,
                    building_id=cam.building_id,
                    camera_id=cam.id,
                    direction=cam.direction,
                    status="normal",
                ))
            print("[SEED] 创建门禁点位")

        # 14. 系统配置
        if db.query(SystemConfig).count() == 0:
            configs = [
                ("face_similarity_threshold", "0.6", "人脸相似度阈值(0~1)"),
                ("face_quality_threshold", "0.4", "人脸图片质量阈值"),
                ("duplicate_window_seconds", "30", "重复通行判定窗口(秒)"),
                ("default_password", DEFAULT_PASSWORD, "学生初始密码"),
                ("info_complete_threshold", "80", "信息完整度达标阈值(%)"),
            ]
            for k, v, desc in configs:
                db.add(SystemConfig(config_key=k, config_value=v, description=desc))
            print("[SEED] 创建系统配置")

        db.commit()
    except Exception as e:
        print(f"[SEED] 初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时: 确保目录和数据库
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(FACE_UPLOAD_DIR, exist_ok=True)
    init_db()
    seed_initial_data()
    print("\n" + "=" * 60)
    print("  智慧宿舍人脸门禁与学生管理系统 启动完成")
    print(f"  后端地址: http://127.0.0.1:8000")
    print(f"  API文档: http://127.0.0.1:8000/docs")
    print(f"  管理员: admin / admin123")
    print(f"  辅导员: counselor01 / 123456")
    print(f"  学生:   20231001 / 123456")
    print("=" * 60 + "\n")
    yield


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="智慧宿舍人脸门禁与学生管理系统",
        description="基于人脸识别的智慧宿舍门禁管理系统 - 人工智能实践项目",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 静态文件
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    # 健康检查
    @app.get("/health")
    def health():
        return {"status": "ok", "service": "smart-dormitory", "version": "1.0.0"}

    # 包含所有路由
    from app.routers import auth, student, organization, dormitory, face, camera, access, abnormal, statistics, messages, system

    app.include_router(auth.router)
    app.include_router(student.router)
    app.include_router(organization.router)
    app.include_router(dormitory.router)
    app.include_router(face.router)
    app.include_router(camera.router)
    app.include_router(access.router)
    app.include_router(abnormal.router)
    app.include_router(statistics.router)
    app.include_router(messages.router)
    app.include_router(system.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
