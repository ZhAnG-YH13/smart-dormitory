# 智慧宿舍人脸门禁与学生管理系统

基于 **人脸识别** 的智慧宿舍门禁与学生管理平台，包含完整的前后端实现与真实运行的 AI 人脸识别模块。系统覆盖「学生导入 → 自动建号 → 首次登录 → 完善信息 → 人脸注册 → 人脸验证 → 门禁通行 → 在寝状态 → 异常检测 → 自动反馈 → 异常处理 → 数据统计」的完整业务闭环。

---

## 一、技术栈

| 层次 | 技术 |
| --- | --- |
| 后端框架 | Python 3.12 + FastAPI + Uvicorn |
| ORM / 数据库 | SQLAlchemy 2.x + SQLite |
| 认证授权 | JWT（python-jose）+ bcrypt（passlib） |
| AI 人脸识别 | face_recognition（dlib 128 维特征）+ OpenCV（Haar 级联回退） |
| Excel 导入导出 | openpyxl |
| 前端框架 | Vue 3（`<script setup>`）+ Vite 5 |
| UI 组件 | Element Plus + @element-plus/icons-vue |
| 状态管理 / 路由 | Pinia + Vue Router 4 |
| 图表 | ECharts |
| HTTP | Axios |

---

## 二、目录结构

```
smart-dormitory/
├── backend/
│   ├── ai/
│   │   └── face_engine.py          # AI 人脸检测/质量评估/特征提取/注册/验证（独立封装）
│   ├── app/
│   │   ├── config.py               # 配置（数据库、JWT、阈值、上传目录等，与代码分离）
│   │   ├── database.py             # 引擎、会话、Base、初始化
│   │   ├── main.py                 # FastAPI 入口 + 种子数据
│   │   ├── models/__init__.py      # 全部数据模型（22 张表）
│   │   ├── routers/                # 认证/学生/组织/宿舍/人脸/摄像头/门禁/异常/统计/消息/系统
│   │   ├── services/               # 异常通知、门禁重复通行检测等业务服务
│   │   └── utils/auth.py           # 密码加密、JWT、角色依赖校验
│   └── requirements.txt
├── database/
│   └── schema.sql                  # 完整建表 DDL（由模型自动建库后导出）
├── frontend/
│   ├── src/
│   │   ├── api/                    # Axios 封装与接口
│   │   ├── layouts/MainLayout.vue  # 侧边栏/顶栏框架
│   │   ├── router/index.js         # 角色路由与导航守卫
│   │   ├── stores/user.js          # 登录态、角色、未读消息
│   │   └── views/
│   │       ├── Login.vue
│   │       ├── admin/              # 管理员 13 个页面
│   │       ├── counselor/          # 辅导员 5 个页面
│   │       ├── student/            # 学生 4 个页面
│   │       └── common/             # 消息中心、个人中心
│   ├── vite.config.js              # 代理 /api、/uploads → 后端 8000
│   └── package.json
└── README.md
```

---

## 三、快速启动

### 1. 启动后端

```bash
cd backend

# 建议使用虚拟环境
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- 后端地址：<http://127.0.0.1:8000>
- 接口文档：<http://127.0.0.1:8000/docs>
- 首次启动自动建表并写入种子数据（管理员、辅导员、示例学生、宿舍楼、摄像头、角色权限、系统配置等）。
- 内置 3 栋宿舍楼（1号楼、2号楼、**7号楼**），每栋 6 层 × 40 间，房号规则「楼层 + 两位房号」（如 `101`、`**231**`），每栋配门禁摄像头；示例学生 `20231001` 分配在 **7号楼 231**。

> 可选：启用真实 dlib 人脸特征提取（默认已支持）
> ```bash
> pip install dlib-bin
> pip install --no-deps face_recognition==1.3.0
> pip install face_recognition_models "setuptools<81"
> ```
> 若安装失败，系统会自动回退到 OpenCV Haar 人脸检测方案，不影响其他功能。

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 <http://localhost:5173>（Vite 已将 `/api` 与 `/uploads` 代理到后端 8000 端口）。

---

## 四、演示账号

| 角色 | 账号 | 密码 | 说明 |
| --- | --- | --- | --- |
| 学校管理员 | `admin` | `admin123` | 全校最高权限 |
| 辅导员 | `counselor01` | `123456` | 仅管理所带班级 |
| 学生 | `20231001` ~ `20231010` | `123456` | 仅本人数据 |

---

## 五、三类角色与权限

| 角色 | 数据范围 | 主要能力 |
| --- | --- | --- |
| 学校管理员 | 全校 | 学生/组织/宿舍/摄像头/门禁/异常/统计/用户/日志全部管理 |
| 辅导员 | 仅本班 | 本班学生、在寝状态、门禁记录、异常处理 |
| 学生 | 仅本人 | 完善个人信息、人脸注册/验证、查看本人门禁记录与消息 |

> 权限校验全部在后端完成（`require_roles` + 数据范围过滤），前端路由守卫仅用于导航体验。

---

## 六、核心业务闭环

1. **学生导入**：管理员上传 Excel（学号、姓名、性别、班级等），自动解析并落库。
2. **自动建号**：为每个学生创建登录账号，初始密码 `123456`，标记需修改密码。
3. **首次登录**：学生登录后引导完善个人信息，系统计算信息完整度。
4. **人脸注册**：上传照片 → 质量评估（模糊/过暗/过曝/人脸过小/多张人脸）→ 提取 128 维特征入库。
5. **人脸验证 / 门禁通行**：摄像头抓拍 → 与已注册特征逐一比对 → 相似度≥阈值则放行，写入进出记录。
6. **在寝状态**：IN 判定在寝、OUT 判定离寝，实时更新 `presence_status`。
7. **异常检测与自动反馈**：
   - 设备异常（摄像头离线/故障）
   - 图像质量异常（模糊、过暗、过曝、人脸过小）
   - AI 识别异常（未检测到人脸、人脸不匹配）
   - 业务异常（30 秒内重复通行、信息不完整、未注册人脸通行等）
   
   异常生成后**自动向管理员/辅导员/学生推送消息**，形成「检测 → 反馈 → 处理 → 关闭」闭环。
8. **数据统计**：学生、门禁（含各楼栋、各时段）、班级（在寝/不在寝/人脸注册率/信息完整率）、AI（检测/成功/失败/未检测到人脸/平均识别耗时）、设备、异常六大维度。

---

## 七、AI 模块说明

`backend/ai/face_engine.py` 为独立封装的人脸识别引擎：

- **检测**：优先使用 `face_recognition`（dlib HOG），不可用时回退 OpenCV Haar Cascade。
- **质量评估**：亮度、Laplacian 清晰度、人脸面积占比、图像分辨率，输出 0~1 质量分。
- **特征提取**：dlib 128 维人脸向量（`embedding_to_json` / `json_to_embedding` 持久化）。
- **注册**：拒绝无人脸、多张人脸、过模糊、过暗、过曝、人脸过小、低质量图片。
- **验证**：欧氏距离换算相似度 `similarity = max(0, 1 - distance)`，阈值 `FACE_SIMILARITY_THRESHOLD = 0.6`。
- **耗时统计**：门禁批量识别记录 `recognition_ms`，用于 AI 统计报表。

> 所有识别均基于真实图像计算，不存在固定图片或预设结果。

---

## 八、数据库设计（22 张表）

`sys_user`、`sys_role`、`sys_permission`、`sys_user_role`、`college`、`major`、`grade`、`class_info`、`student`、`dormitory_building`、`dormitory_room`、`student_dormitory`、`face_profile`、`camera_device`、`access_point`、`access_record`、`presence_status`、`abnormal_event`、`abnormal_handle`、`message_notification`、`operation_log`、`system_config`。

设计要点：

- 主键自增；外键关联；唯一约束（如学号、用户名、角色/权限编码、配置键、用户-角色组合）。
- 通用字段：`created_at`、`updated_at`、`is_deleted`（逻辑删除）。
- 状态字段：账号状态、设备状态、人脸状态、异常状态、在寝状态等。
- 查询索引：门禁时间、异常状态+类型、学号、账号等。

完整 DDL 见 [`database/schema.sql`](database/schema.sql)。

---

## 九、主要 API

| 模块 | 路径 |
| --- | --- |
| 认证 | `POST /api/auth/login`、`POST /api/auth/change-password`、`GET /api/auth/me` |
| 学生 | `GET/POST/PUT/DELETE /api/students`、`POST /api/students/import`、`POST /api/students/create-accounts`、`GET /api/students/{id}/info-complete` |
| 组织 | `/api/colleges`、`/api/majors`、`/api/grades`、`/api/classes`（含 `/{id}/students`） |
| 宿舍 | `/api/buildings`、`/api/rooms` |
| 人脸 | `POST /api/face/register`、`GET /api/face/status`、`POST /api/face/verify`、`POST /api/face/batch-verify`、`DELETE /api/face/cancel` |
| 摄像头 | `GET/POST/PUT/DELETE /api/cameras`、`POST /api/cameras/{id}/simulate`、`GET /api/cameras/{id}/status` |
| 门禁 | `GET /api/access/records`、`GET /api/access/today`、`GET /api/presence` |
| 异常 | `GET/POST /api/abnormals`、`GET /api/abnormals/{id}`、`POST /api/abnormals/{id}/handle`、`POST /api/abnormals/{id}/close` |
| 统计 | `GET /api/stats/dashboard`、`/students`、`/access`、`/classes`、`/devices`、`/abnormals`、`/ai` |
| 消息 | `GET /api/messages`、`POST /api/messages/{id}/read`、`POST /api/messages/read-all`、`GET /api/messages/unread-count` |
| 系统 | `/api/users`、`/api/logs`、`/api/system/info` |

所有列表接口统一返回 `{ total, items, page, limit }`，支持分页与条件筛选。

---

## 十、答辩演示流程建议

1. 管理员登录 → 学生管理 → Excel 导入 100 名学生（自动建号）。
2. 学生 `20231001` 登录 → 完善个人信息 → 人脸注册（上传照片，查看质量分与 AI 返回）。
3. 管理员进入「门禁模拟」→ 选择摄像头与已注册学生 → 模拟进入宿舍（生成 IN 记录、在寝状态变为在寝）。
4. 再次模拟同一摄像头 → 触发「30 秒内重复通行」业务异常，并自动推送消息。
5. 模拟离开宿舍（OUT）→ 在寝状态更新。
6. 异常中心查看异常 → 填写处理意见 → 状态流转 → 学生/辅导员收到处理结果消息。
7. 数据统计页查看学生、门禁（各楼栋/各时段）、班级、AI、设备、异常六类报表。

---

## 十一、版本管理

项目使用 Git 管理，提交记录按功能模块拆分，便于回溯与答辩展示。
