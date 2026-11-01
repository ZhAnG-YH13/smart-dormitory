"""智慧宿舍人脸门禁与学生管理系统 - FastAPI 入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
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

        # 7. 创建宿舍楼 (1~100号楼均可选) 和示例宿舍房间
        if db.query(DormitoryBuilding).count() == 0:
            for i in range(1, 101):
                db.add(DormitoryBuilding(name=f"{i}号楼", code=f"B{i}", floors=6))
            db.flush()

            # 仅 1/2/7号楼预置示例房间(101~640), 其余房间按学生填写的三位房号自动创建
            for b in db.query(DormitoryBuilding).filter(
                DormitoryBuilding.name.in_(["1号楼", "2号楼", "7号楼"])
            ).all():
                for floor in range(1, 7):
                    for room in range(1, 41):
                        db.add(DormitoryRoom(
                            building_id=b.id,
                            room_number=f"{floor}{room:02d}",
                            capacity=4
                        ))
            db.flush()
            print("[SEED] 创建宿舍楼(1~100号楼)和示例宿舍房间")
        else:
            # 兼容已有数据库: 补齐缺失的 1~100号楼
            existing_names = {b.name for b in db.query(DormitoryBuilding).all()}
            added = 0
            for i in range(1, 101):
                name = f"{i}号楼"
                if name not in existing_names:
                    db.add(DormitoryBuilding(name=name, code=f"B{i}", floors=6))
                    added += 1
            db.flush()
            if added:
                print(f"[SEED] 补齐宿舍楼: 新增 {added} 栋")

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

            surnames = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴", "徐", "孙"]
            given_names = ["伟", "芳", "娜", "敏", "静", "强", "磊", "洋", "勇", "艳", "杰", "娟", "涛", "明", "超"]

            buildings = db.query(DormitoryBuilding).all()
            majors_all = db.query(Major).filter(Major.is_deleted == False).all()

            # 按楼栋分组房间, 首位学生分配到 7号楼 231 室
            rooms_by_building = {
                b.id: db.query(DormitoryRoom).filter(DormitoryRoom.building_id == b.id)
                .order_by(DormitoryRoom.room_number).all()
                for b in buildings
            }
            b7 = next((b for b in buildings if b.name == "7号楼"), buildings[0])
            room_231 = next((r for r in rooms_by_building.get(b7.id, []) if r.room_number == "231"), None)
            # 只有预置了房间的楼栋才用于自动分配, 避免出现"有楼无房"
            room_buildings = [b for b in buildings if rooms_by_building.get(b.id)] or buildings

            students_created = 0
            for i in range(10):
                class_info = classes[i % len(classes)]
                if i == 0 and room_231:
                    building, room = b7, room_231
                else:
                    building = room_buildings[(i - 1) % len(room_buildings)]
                    bl = rooms_by_building.get(building.id) or []
                    room = bl[(i - 1) % len(bl)] if bl else None
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

                # 人脸档案初始为未注册, 需学生本人真实上传照片完成注册
                if i % 4 != 0:
                    db.add(FaceProfile(
                        student_id=student.id,
                        face_status="unregistered",
                        face_quality_score=0.0
                    ))

                students_created += 1

            print(f"[SEED] 创建示例学生: {students_created} 人")

        # 10. 创建摄像头
        if db.query(CameraDevice).count() == 0:
            buildings = db.query(DormitoryBuilding).all()
            if buildings:
                b1 = next((b for b in buildings if b.name == "1号楼"), buildings[0])
                b7 = next((b for b in buildings if b.name == "7号楼"), buildings[0])
                cams = [
                    ("CAM001", "东门入口", "IN", b1),
                    ("CAM002", "东门出口", "OUT", b1),
                    ("CAM003", "西门入口", "IN", b1),
                    ("CAM004", "西门出口", "OUT", b1),
                    ("CAM005", "东门入口", "IN", b7),
                    ("CAM006", "东门出口", "OUT", b7),
                ]
                for code, spot, direction, b in cams:
                    db.add(CameraDevice(
                        camera_code=code,
                        name=f"{b.name}{spot}",
                        location=b.name,
                        direction=direction,
                        building_id=b.id,
                        device_status="online"
                    ))
                print("[SEED] 创建摄像头: 6 个")

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


LANDING_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>智慧宿舍人脸门禁与学生管理系统 · 后端服务</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    min-height: 100vh;
    font-family: "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
    color: #e8eef7;
    background: radial-gradient(1200px 600px at 10% -10%, #1e3a5f 0%, transparent 60%),
                radial-gradient(900px 500px at 100% 0%, #14364f 0%, transparent 55%),
                linear-gradient(160deg, #0d1726 0%, #111f30 55%, #0b1520 100%);
    display: flex;
    justify-content: center;
    padding: 40px 18px 60px;
  }
  .wrap { width: 100%; max-width: 980px; }
  .hero { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }
  .logo {
    width: 56px; height: 56px; border-radius: 16px;
    background: linear-gradient(135deg, #409eff, #2b6fd6);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; box-shadow: 0 10px 30px rgba(64, 158, 255, .35);
  }
  h1 { font-size: 24px; font-weight: 700; letter-spacing: .5px; }
  .sub { margin-top: 6px; font-size: 13px; color: #8ba3bf; }
  .status { display: flex; gap: 10px; flex-wrap: wrap; margin: 22px 0 26px; }
  .chip {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 7px 14px; border-radius: 999px; font-size: 12.5px;
    background: rgba(255, 255, 255, .06); border: 1px solid rgba(255, 255, 255, .1);
    color: #b9cbe0;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 10px #22c55e; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
  .card {
    background: rgba(255, 255, 255, .045);
    border: 1px solid rgba(255, 255, 255, .09);
    border-radius: 16px; padding: 18px 20px;
    backdrop-filter: blur(6px);
    transition: transform .2s ease, border-color .2s ease;
  }
  .card:hover { transform: translateY(-2px); border-color: rgba(64, 158, 255, .5); }
  .card h2 { font-size: 15px; margin-bottom: 8px; color: #fff; }
  .card p { font-size: 12.5px; line-height: 1.7; color: #93a9c2; }
  .links { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }
  .btn {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 11px 18px; border-radius: 10px; text-decoration: none;
    font-size: 13.5px; font-weight: 600; color: #fff;
    background: linear-gradient(135deg, #409eff, #2f7bdb);
    box-shadow: 0 8px 22px rgba(64, 158, 255, .3);
  }
  .btn.ghost {
    background: rgba(255, 255, 255, .06); color: #cfe0f2;
    border: 1px solid rgba(255, 255, 255, .14); box-shadow: none;
  }
  .section-title { font-size: 13px; letter-spacing: 1px; color: #7d94ad; margin: 26px 0 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, .07); }
  th { color: #8da6c0; font-weight: 500; }
  td code { color: #7cc6ff; background: rgba(64, 158, 255, .12); padding: 2px 6px; border-radius: 6px; }
  .api { font-size: 12px; color: #9fb6cd; line-height: 2; }
  .api code { color: #7cc6ff; }
  footer { margin-top: 32px; text-align: center; font-size: 11.5px; color: #5e7488; }
  @media (max-width: 560px) {
    h1 { font-size: 19px; }
    .logo { width: 46px; height: 46px; font-size: 21px; }
    .links .btn { flex: 1 1 100%; justify-content: center; }
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <div class="logo">🏛️</div>
    <div>
      <h1>智慧宿舍人脸门禁与学生管理系统</h1>
      <div class="sub">Smart Dormitory Face Access &amp; Student Management · 后端服务</div>
    </div>
  </div>

  <div class="status">
    <span class="chip"><span class="dot"></span>服务运行中</span>
    <span class="chip">版本 v1.0.0</span>
    <span class="chip">FastAPI + SQLAlchemy</span>
    <span class="chip">AI 引擎 face_recognition (dlib 128D)</span>
    <span class="chip">数据库 SQLite</span>
  </div>

  <div class="links">
    <a class="btn" href="/docs">📘 打开接口文档 Swagger</a>
    <a class="btn ghost" href="/redoc">📄 ReDoc 文档</a>
    <a class="btn ghost" id="front-link" href="http://localhost:5173">🖥️ 进入前端系统</a>
    <a class="btn ghost" href="/health">❤️ 健康检查</a>
  </div>

  <div class="grid">
    <div class="card">
      <h2>👤 三类角色权限</h2>
      <p>学校管理员（全校）、辅导员（仅本班）、学生（仅本人）。权限由后端 JWT + 角色校验强制执行，前端只做展示。</p>
    </div>
    <div class="card">
      <h2>🧠 真实人脸识别</h2>
      <p>检测 → 质量评估 → 128 维特征提取 → 相似度比对 → 阈值判定（0.6）。含模糊、过暗、过曝、多脸、无人脸等判定。</p>
    </div>
    <div class="card">
      <h2>🚪 门禁与在寝状态</h2>
      <p>刷脸成功写入 IN/OUT 记录，实时更新在寝状态；30 秒内重复通行自动产生业务异常。</p>
    </div>
    <div class="card">
      <h2>⚠️ 异常闭环</h2>
      <p>设备 / 图像质量 / AI 识别 / 业务四类异常，自动生成原因、推送消息给管理员与相关学生，并支持处理与结果回推。</p>
    </div>
  </div>

  <div class="section-title">演示账号</div>
  <div class="card">
    <table>
      <tr><th>角色</th><th>用户名</th><th>密码</th><th>说明</th></tr>
      <tr><td>学校管理员</td><td><code>admin</code></td><td><code>admin123</code></td><td>全校数据、导入建号、设备与异常管理</td></tr>
      <tr><td>辅导员</td><td><code>counselor01</code></td><td><code>123456</code></td><td>仅本班学生、在寝与异常</td></tr>
      <tr><td>学生</td><td><code>20231001</code></td><td><code>123456</code></td><td>本人信息、人脸注册、个人门禁记录</td></tr>
    </table>
  </div>

  <div class="section-title">接口分组</div>
  <div class="card api">
    <code>/api/auth</code> 登录 / 当前用户 / 修改密码 &nbsp;·&nbsp;
    <code>/api/students</code> 学生与导入建号 &nbsp;·&nbsp;
    <code>/api/face</code> 注册 / 验证 / 批量验证<br />
    <code>/api/cameras</code> 设备管理 / 模拟通行 &nbsp;·&nbsp;
    <code>/api/access</code> 门禁记录 &nbsp;·&nbsp;
    <code>/api/abnormals</code> 异常与处理<br />
    <code>/api/stats</code> 学生 / 门禁 / 班级 / AI / 设备 / 异常统计 &nbsp;·&nbsp;
    <code>/api/messages</code> 消息通知 &nbsp;·&nbsp;
    <code>/api/logs</code> 操作日志
  </div>

  <footer>智慧宿舍人脸门禁与学生管理系统 · 人工智能课程实践</footer>
</div>
<script>
  // 手机/局域网访问时，前端地址跟随当前主机名
  var host = location.hostname || 'localhost';
  document.getElementById('front-link').href = 'http://' + host + ':5173';
</script>
</body>
</html>
"""


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

    # 后端控制台首页（浏览器直接访问 8000 时展示）
    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTMLResponse(content=LANDING_PAGE)

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
