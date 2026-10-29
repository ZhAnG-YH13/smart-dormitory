"""AI 人脸识别模块 - 真实运行

包含:
1. 人脸检测 (OpenCV Haar级联 + face_recognition HOG/CNN)
2. 人脸质量评估 (亮度、模糊度、人脸大小)
3. 人脸特征提取 (face_recognition 128维embedding)
4. 人脸注册
5. 人脸验证

要求: 必须真实运行，不允许固定结果模拟
"""
import io
import json
import base64
import numpy as np
from PIL import Image
import cv2

# 延迟导入 face_recognition，避免在未安装时影响其他模块
try:
    import face_recognition
    FACE_RECOG_AVAILABLE = True
except ImportError:
    FACE_RECOG_AVAILABLE = False
    print("[WARNING] face_recognition not installed, face verification will use fallback")


class FaceQualityError(Exception):
    """人脸质量不达标异常"""
    def __init__(self, reason: str, detail: str = ""):
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}")


class FaceResult:
    """人脸识别结果封装"""
    def __init__(self):
        self.success = False
        self.embedding = None
        self.face_location = None  # (top, right, bottom, left)
        self.face_count = 0
        self.quality_score = 0.0
        self.reason = ""
        self.detail = ""

    def to_dict(self):
        return {
            "success": self.success,
            "face_count": self.face_count,
            "quality_score": round(self.quality_score, 4),
            "reason": self.reason,
            "detail": self.detail,
            "has_embedding": self.embedding is not None
        }


def _pil_to_cv2(image: Image.Image) -> np.ndarray:
    """PIL Image 转 OpenCV BGR"""
    rgb = np.array(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _bytes_to_cv2(data: bytes) -> np.ndarray:
    """字节转 OpenCV 图像"""
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图像")
    return img


def _base64_to_cv2(b64_str: str) -> np.ndarray:
    """Base64 转 OpenCV 图像"""
    # 去掉 data:image/xxx;base64, 前缀
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    data = base64.b64decode(b64_str)
    return _bytes_to_cv2(data)


def evaluate_quality(img: np.ndarray, face_location=None) -> tuple[float, list[str]]:
    """评估图像质量，返回 (综合评分, 问题列表)"""
    issues = []
    score = 100.0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    # 1. 亮度检查
    mean_brightness = np.mean(gray)
    if mean_brightness < 40:
        issues.append("图像过暗")
        score -= 30
    elif mean_brightness > 230:
        issues.append("图像过曝")
        score -= 30

    # 2. 模糊度检查 (Laplacian方差)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 50:
        issues.append("图像严重模糊")
        score -= 35
    elif laplacian_var < 100:
        issues.append("图像略模糊")
        score -= 15

    # 3. 人脸大小检查
    if face_location:
        top, right, bottom, left = face_location
        face_w = right - left
        face_h = bottom - top
        face_area_ratio = (face_w * face_h) / (w * h)
        if face_area_ratio < 0.02:
            issues.append("人脸过小")
            score -= 25
        elif face_area_ratio > 0.5:
            issues.append("人脸过大")
            score -= 10

    # 4. 分辨率检查
    if min(h, w) < 200:
        issues.append("图像分辨率过低")
        score -= 20

    return max(0, min(100, score)), issues


def detect_faces(img: np.ndarray, model: str = "hog") -> list:
    """
    检测人脸位置

    Args:
        img: OpenCV BGR 图像
        model: 'hog' 速度快, 'cnn' 精度高

    Returns:
        face_locations: [(top, right, bottom, left), ...]
    """
    if not FACE_RECOG_AVAILABLE:
        # 使用 OpenCV Haar Cascade 作为备选
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
        return [(int(y), int(x + w), int(y + h), int(x)) for (x, y, w, h) in faces]

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return face_recognition.face_locations(rgb, model=model)


def extract_embedding(img: np.ndarray, face_location=None) -> np.ndarray | None:
    """
    提取人脸特征向量 (128维)

    Args:
        img: OpenCV BGR 图像
        face_location: 可选，已知人脸位置

    Returns:
        embedding: np.ndarray (128,) 或 None
    """
    if not FACE_RECOG_AVAILABLE:
        # 备选：基于直方图的简单特征
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if face_location:
            top, right, bottom, left = face_location
            face = gray[top:bottom, left:right]
        else:
            face = gray
        face = cv2.resize(face, (32, 32))
        # 扩展到128维作为伪特征
        features = face.flatten().astype(np.float32)[:1024]
        return features[:128]  # 截断到128维

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb, known_face_locations=[face_location] if face_location else None)
    if encodings:
        return encodings[0]
    return None


def register_face(image_input, source: str = "file") -> FaceResult:
    """
    人脸识别注册（上传/采集）完整流程

    Args:
        image_input: PIL.Image / bytes / base64 str / file path
        source: 'file', 'bytes', 'base64', 'path'

    Returns:
        FaceResult
    """
    result = FaceResult()

    # 1. 读取图像
    try:
        if source == "base64":
            img = _base64_to_cv2(image_input)
        elif source == "bytes":
            img = _bytes_to_cv2(image_input)
        elif source == "path":
            img = cv2.imread(image_input)
            if img is None:
                result.reason = "IMAGE_READ_ERROR"
                result.detail = "无法读取图片文件"
                return result
        elif isinstance(image_input, Image.Image):
            img = _pil_to_cv2(image_input)
        else:
            img = np.array(image_input)
    except Exception as e:
        result.reason = "IMAGE_READ_ERROR"
        result.detail = str(e)
        return result

    # 2. 人脸检测
    face_locations = detect_faces(img)
    result.face_count = len(face_locations)

    if len(face_locations) == 0:
        result.reason = "NO_FACE_DETECTED"
        result.detail = "未检测到人脸，请上传包含清晰人脸的照片"
        return result
    elif len(face_locations) > 1:
        result.reason = "MULTIPLE_FACES"
        result.detail = f"检测到 {len(face_locations)} 张人脸，请保证图片中只有本人"
        return result

    face_location = face_locations[0]
    result.face_location = face_location

    # 3. 质量评估
    quality_score, issues = evaluate_quality(img, face_location)
    result.quality_score = quality_score

    if quality_score < 50:
        if "图像严重模糊" in issues:
            result.reason = "FACE_TOO_BLUR"
            result.detail = "当前照片过于模糊，请重新拍摄"
        elif "图像过暗" in issues:
            result.reason = "FACE_TOO_DARK"
            result.detail = "图像过暗，请在光线充足处拍摄"
        elif "图像过曝" in issues:
            result.reason = "FACE_TOO_BRIGHT"
            result.detail = "图像过曝，请避免强光直射"
        elif "人脸过小" in issues:
            result.reason = "FACE_TOO_SMALL"
            result.detail = "人脸过小，请靠近摄像头"
        else:
            result.reason = "LOW_QUALITY"
            result.detail = f"图像质量较差: {', '.join(issues)}"
        return result

    # 4. 特征提取
    embedding = extract_embedding(img, face_location)
    if embedding is None:
        result.reason = "FEATURE_EXTRACT_FAILED"
        result.detail = "人脸特征提取失败，请更换照片重试"
        return result

    result.embedding = embedding
    result.success = True
    return result


def verify_face(image_input, registered_embedding: np.ndarray, source: str = "base64") -> FaceResult:
    """
    人脸验证

    Args:
        image_input: 摄像头帧 / 图片
        registered_embedding: 已注册的特征向量
        source: 输入类型

    Returns:
        FaceResult (含 similarity)
    """
    result = FaceResult()

    # 1. 读取图像
    try:
        if source == "base64":
            img = _base64_to_cv2(image_input)
        elif source == "bytes":
            img = _bytes_to_cv2(image_input)
        elif isinstance(image_input, Image.Image):
            img = _pil_to_cv2(image_input)
        else:
            img = np.array(image_input)
    except Exception as e:
        result.reason = "IMAGE_READ_ERROR"
        result.detail = str(e)
        return result

    # 2. 人脸检测
    face_locations = detect_faces(img)
    result.face_count = len(face_locations)

    if len(face_locations) == 0:
        result.reason = "NO_FACE_DETECTED"
        result.detail = "未检测到人脸"
        return result

    face_location = face_locations[0]
    result.face_location = face_location

    # 3. 质量评估 (验证时不过度严格，只记录)
    quality_score, issues = evaluate_quality(img, face_location)
    result.quality_score = quality_score

    # 4. 特征提取
    embedding = extract_embedding(img, face_location)
    if embedding is None:
        result.reason = "FEATURE_EXTRACT_FAILED"
        result.detail = "特征提取失败"
        return result

    # 5. 相似度计算 (欧式距离 → 相似度)
    distance = np.linalg.norm(embedding - registered_embedding)
    # face_recognition 阈值: 0.6 对应距离阈值 0.6
    similarity = max(0.0, 1.0 - distance / 1.0)  # 归一化到 [0, 1]
    result.similarity = similarity
    result.embedding = embedding
    result.success = True
    return result


def embedding_to_json(embedding: np.ndarray) -> str:
    """特征向量序列化为JSON"""
    return json.dumps([round(float(x), 6) for x in embedding.tolist()])


def json_to_embedding(json_str: str) -> np.ndarray:
    """JSON反序列化为特征向量"""
    return np.array(json.loads(json_str), dtype=np.float32)


def draw_face_box(img: np.ndarray, face_location, label: str = "") -> np.ndarray:
    """在图像上绘制人脸框"""
    top, right, bottom, left = face_location
    cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
    if label:
        cv2.putText(img, label, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return img


class FaceRecognizer:
    """人脸识别器统一接口"""

    def __init__(self, model: str = "hog"):
        self.model = model
        self.available = FACE_RECOG_AVAILABLE
        self._registered = {}  # {student_id: embedding}

    def register(self, image_input, student_id: str, source: str = "file") -> FaceResult:
        """注册人脸"""
        result = register_face(image_input, source=source)
        if result.success:
            self._registered[student_id] = result.embedding
        return result

    def verify(self, image_input, source: str = "base64") -> tuple[str, FaceResult]:
        """
        验证人脸，返回 (student_id, result)
        """
        result = FaceResult()

        try:
            if source == "base64":
                img = _base64_to_cv2(image_input)
            elif source == "bytes":
                img = _bytes_to_cv2(image_input)
            else:
                img = np.array(image_input)
        except Exception as e:
            result.reason = "IMAGE_READ_ERROR"
            result.detail = str(e)
            return "", result

        face_locations = detect_faces(img, model=self.model)
        if not face_locations:
            result.reason = "NO_FACE_DETECTED"
            return "", result

        embedding = extract_embedding(img, face_locations[0])
        if embedding is None:
            result.reason = "FEATURE_EXTRACT_FAILED"
            return "", result

        # 与所有已注册人脸比较
        best_id = ""
        best_sim = 0.0
        for sid, reg_emb in self._registered.items():
            dist = np.linalg.norm(embedding - reg_emb)
            sim = max(0.0, 1.0 - dist)
            if sim > best_sim:
                best_sim = sim
                best_id = sid

        result.similarity = best_sim
        result.success = best_sim > 0.5
        return (best_id, result) if result.success else ("", result)


def get_system_info() -> dict:
    """获取AI系统信息"""
    info = {
        "face_recognition_available": FACE_RECOG_AVAILABLE,
        "opencv_version": cv2.__version__,
        "numpy_version": np.__version__,
        "backend": "face_recognition (dlib)" if FACE_RECOG_AVAILABLE else "opencv fallback",
    }
    if FACE_RECOG_AVAILABLE:
        info["model"] = "CNN (dlib)"
    return info
