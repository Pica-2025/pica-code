from dotenv import load_dotenv
load_dotenv()
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"
TARGETS_DIR = DATA_DIR / "targets"
GENERATIONS_DIR = DATA_DIR / "generations"
REVISIONS_DIR = DATA_DIR / "revisions"
THUMBS_DIR = DATA_DIR / "thumbs"
LOGS_DIR = DATA_DIR / "logs"
EXPORTS_DIR = DATA_DIR / "exports"
TEMP_DIR = DATA_DIR / "temp"

MANIFEST_PATH = DATA_DIR / "manifests" / "targets_manifest.csv"

DATABASE_URL = f"sqlite:///{BASE_DIR}/src/backend/database.db"

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-please-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1200"))

MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 50

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    print("⚠️  警告: DASHSCOPE_API_KEY 未设置")
    print("请运行: export DASHSCOPE_API_KEY=sk-xxx")
    print("或在 .env 文件中添加: DASHSCOPE_API_KEY=sk-xxx")
    print("获取API Key: https://help.aliyun.com/zh/model-studio/get-api-key")

QWEN_MODEL_NAME = os.getenv("QWEN_MODEL_NAME", "qwen-image-plus")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️  警告: GEMINI_API_KEY 未设置")
    print("请运行: export GEMINI_API_KEY=your-key")
    print("或在 .env 文件中添加: GEMINI_API_KEY=your-key")

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3-pro-image-preview")

DEFAULT_QWEN_PARAMS = {
    "n": 1,
    "size": "1328*1328",
    "prompt_extend": False,
    "watermark": False,
    "seed": 14159265,
}

DEFAULT_GEMINI_PARAMS = {
    "temperature": 0.9,
    "top_p": 1.0,
    "top_k": 40,
    "max_output_tokens": 2048,
}

GENERATION_TIMEOUT = 3000
MODIFY_TIMEOUT = 3000

TASKS_PER_SESSION = 10

QWEN_TASKS_COUNT = 5
GEMINI_TASKS_COUNT = 5

QWEN_TARGET_RANGE = (1, 30)
GEMINI_TARGET_RANGE = (31, 60)

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

EASY_TASKS_COUNT = 4
HARD_TASKS_COUNT = 3

MAX_REVISIONS_PER_TASK = 7
MAX_VERSIONS_PER_TASK = 8

MIN_RATING_SCORE = 0
MAX_RATING_SCORE = 7

RATING_DIMENSIONS = {
    "style": {
        "name": "画风风格",
        "description": "生成图与目标图的整体画风、艺术风格的一致性"
    },
    "object_count": {
        "name": "物件数量",
        "description": "生成图中物体数量与目标图的符合程度"
    },
    "perspective": {
        "name": "角度方位",
        "description": "物体的摆放位置、角度、方向与目标图的一致性"
    },
    "depth_background": {
        "name": "景深背景",
        "description": "背景、景深、空间感与目标图的符合程度"
    }
}

STAR_MEANINGS = {
    1: "完全不符 - 严重偏离目标",
    2: "很不符 - 明显差异",
    3: "不太符 - 有较大差异",
    4: "基本符合 - 可接受但有改进空间",
    5: "较符合 - 比较接近目标",
    6: "很符合 - 非常接近目标",
    7: "完全符合 - 几乎一模一样"
}

JPG_QUALITY = 95

THUMBNAIL_MAX_SIZE = (300, 300)

MAX_IMAGE_SIZE = (1920, 1920)

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

DEFAULT_ADMIN_ID = os.getenv("DEFAULT_ADMIN_ID", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

def ensure_directories():
    directories = [
        DATA_DIR,
        TARGETS_DIR,
        GENERATIONS_DIR,
        REVISIONS_DIR,
        THUMBS_DIR,
        LOGS_DIR,
        EXPORTS_DIR,
        TEMP_DIR,
        DATA_DIR / "manifests"
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ 目录已就绪: {directory}")

def validate_config():
    errors = []

    if not MANIFEST_PATH.exists():
        errors.append(f"Manifest文件不存在: {MANIFEST_PATH}")

    if not BASE_DIR.exists():
        errors.append(f"项目根目录不存在: {BASE_DIR}")

    if QWEN_TASKS_COUNT + GEMINI_TASKS_COUNT != TASKS_PER_SESSION:
        errors.append(
            f"双模型任务数量配置错误: {QWEN_TASKS_COUNT} + {GEMINI_TASKS_COUNT} "
            f"!= {TASKS_PER_SESSION}"
        )

    if not DASHSCOPE_API_KEY:
        errors.append(
            "DashScope API Key未设置。"
            "请运行: export DASHSCOPE_API_KEY=sk-xxx"
        )

    if errors:
        print("❌ 配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        raise ValueError("配置文件有误，请检查 config.py")

    print("✓ 配置验证通过")

if __name__ == "__main__":
    ensure_directories()
    validate_config()
    print("\n配置文件加载成功！")
    print(f"项目根目录: {BASE_DIR}")
    print(f"数据库路径: {DATABASE_URL}")
    print(f"Qwen-Image API: {'已配置' if DASHSCOPE_API_KEY else '未配置'}")
