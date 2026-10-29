# 数据库配置
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 数据库
DATABASE_URL = f"sqlite:///{BASE_DIR / 'dormitory.db'}"

# JWT 配置
SECRET_KEY = "smart-dormitory-secret-key-change-in-production-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# 人脸注册阈值
FACE_SIMILARITY_THRESHOLD = 0.6
FACE_QUALITY_THRESHOLD = 0.4

# 默认密码
DEFAULT_PASSWORD = "123456"

# 文件上传
UPLOAD_DIR = BASE_DIR / "uploads"
FACE_UPLOAD_DIR = UPLOAD_DIR / "faces"
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "bmp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

# CORS
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000", "*"]

# 管理员默认账号
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME = "系统管理员"
