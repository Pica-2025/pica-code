
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=50, description="用户ID")
    role: str = Field(default="tester", description="角色：tester 或 admin")

    @field_validator('role')
    def validate_role(cls, v):
        if v not in ['tester', 'admin']:
            raise ValueError('角色必须是 tester 或 admin')
        return v

class UserCreate(UserBase):
    username: str = Field(..., min_length=2, max_length=50, description="用户名（显示名称）")
    password: str = Field(..., min_length=6, max_length=50, description="密码")

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码至少6位')
        return v

class UserLogin(BaseModel):
    username: str = Field(..., description="用户ID")
    password: str = Field(..., description="密码")

class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user_id: str
    role: str

class SessionBase(BaseModel):
    status: str = Field(default="active", description="会话状态")

    @field_validator('status')
    def validate_status(cls, v):
        if v not in ['active', 'finished', 'interrupted']:
            raise ValueError('状态必须是 active, finished 或 interrupted')
        return v

class SessionCreate(BaseModel):
    pass

class SessionResponse(SessionBase):
    id: int
    session_id: str
    user_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TaskBase(BaseModel):
    round_number: int = Field(..., ge=1, description="第几轮")

    @field_validator('round_number')
    @classmethod
    def validate_round_number(cls, v: int) -> int:
        from config import TASKS_PER_SESSION
        if v < 1 or v > TASKS_PER_SESSION:
            raise ValueError(f'轮数必须在 1 到 {TASKS_PER_SESSION} 之间')
        return v

class TaskResponse(BaseModel):
    id: int
    task_id: str
    session_id: str
    round_number: int
    target_index: int
    target_filename: str
    target_image_url: str
    target_sha256: Optional[str] = None

    ground_truth: Optional[str] = None

    user_difficulty_rating: Optional[str] = None

    difficulty: Optional[str] = None

    status: str
    created_at: datetime
    generated_image_url: Optional[str] = None
    has_final_version: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)

class TaskSubmit(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="完整的提示词")
    time_spent_seconds: int = Field(default=0, ge=0, description="输入提示词花费的时间（秒）")
    difficulty_rating: Optional[str] = Field(None, description="用户难度评级（easy/medium/hard）")

    @field_validator('difficulty_rating')
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['easy', 'medium', 'hard']:
            raise ValueError('难度评级必须是 easy, medium 或 hard')
        return v

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    message: str
    image_url: Optional[str] = None
    progress: int = Field(default=0, ge=0, le=100, description="进度百分比")

class ImageVersionBase(BaseModel):
    version_number: int = Field(..., ge=1, description="版本号")
    prompt: str = Field(..., description="生成提示词")

    @field_validator('version_number')
    @classmethod
    def validate_version_number(cls, v: int) -> int:
        from config import MAX_VERSIONS_PER_TASK
        if v < 1 or v > MAX_VERSIONS_PER_TASK:
            raise ValueError(f'版本号必须在 1 到 {MAX_VERSIONS_PER_TASK} 之间')
        return v

class UserManualScoreUpdate(BaseModel):
    user_manual_score: int = Field(..., ge=0, le=100, description="相似度评分(0-100, 0表示未评分)")

    @field_validator('user_manual_score')
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError('评分必须在0-100之间')
        return v

class ImageVersionFinalize(BaseModel):
    confirm: bool = Field(default=True, description="确认标记为最终版本")

class RatingBase(BaseModel):
    style_score: int = Field(..., ge=0, le=7, description="画风风格评分(0-7星，0表示未评分)")
    object_count_score: int = Field(..., ge=0, le=7, description="物件数量评分(0-7星，0表示未评分)")
    perspective_score: int = Field(..., ge=0, le=7, description="角度方位评分(0-7星，0表示未评分)")
    depth_background_score: int = Field(..., ge=0, le=7, description="景深背景评分(0-7星，0表示未评分)")
    detailed_review: str = Field(..., max_length=2000, description="细节评价（可选）")

class RatingCreate(RatingBase):

    @field_validator('style_score', 'object_count_score', 'perspective_score', 'depth_background_score')
    @classmethod
    def validate_score(cls, v: int) -> int:
        from config import MIN_RATING_SCORE, MAX_RATING_SCORE
        if v < MIN_RATING_SCORE or v > MAX_RATING_SCORE:
            raise ValueError(f'评分必须是{MIN_RATING_SCORE}-{MAX_RATING_SCORE}星')
        return v

    @field_validator('detailed_review')
    @classmethod
    def validate_review(cls, v: str) -> str:
        v = v.strip()
        return v if v else '无'

class RatingResponse(RatingBase):
    id: int
    rating_id: str
    version_id: str
    created_at: datetime

    ai_similarity_score: Optional[float] = None
    ai_similarity_details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SessionDetailResponse(SessionResponse):
    tasks: List[TaskResponse] = []

class ImageVersionDetailResponse(BaseModel):
    id: int
    version_id: str
    task_id: str
    version_number: int
    prompt: str
    prompt_time_seconds: int
    image_path: str
    image_url: str
    thumbnail_url: str
    generation_type: str
    is_final: bool
    locked: bool
    created_at: datetime

    user_manual_score: Optional[int] = Field(None, ge=0, le=100, description="用户手动相似度评分(0-100，0表示未评分)")

    expert_score_1: Optional[int] = Field(None, ge=0, le=100, description="专家1评分(0-100，0表示未评分)")
    expert_score_2: Optional[int] = Field(None, ge=0, le=100, description="专家2评分(0-100，0表示未评分)")

    dino_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="DINOv2特征相似度")
    hsv_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="HSV颜色相似度")
    structure_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="结构相似度")
    clip_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="CLIP相似度(保留)")

    ai_similarity_score: Optional[float] = None
    ai_similarity_details: Optional[str] = None

    wise_suggestions: Optional[List[dict]] = Field(
        default=None,
        description="Wise AI 提示词优化建议"
    )
    wise_generated: bool = Field(
        default=False,
        description="Wise 分析是否已完成"
    )
    wise_error: Optional[str] = Field(
        default=None,
        description="Wise 分析错误信息"
    )

    rating: Optional[RatingResponse] = None

    model_config = ConfigDict(from_attributes=True)

class TaskDetailResponse(TaskResponse):
    versions: List[ImageVersionDetailResponse] = []

class AdminStatsResponse(BaseModel):
    total_users: int
    total_sessions: int
    active_sessions: int
    completed_sessions: int
    total_tasks: int
    completed_tasks: int
    total_images: int
    average_rating: float

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int

class MessageResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

if __name__ == "__main__":
    print("=" * 60)
    print("Pydantic Schema 验证测试")
    print("=" * 60)

    print("\n测试1：有效的用户创建")
    try:
        user = UserCreate(
            user_id="test001",
            password="test123",
            role="tester"
        )
        print(f"✓ 验证通过: {user.model_dump()}")
    except Exception as e:
        print(f"✗ 验证失败: {e}")

    print("\n测试2：无效的密码（太短）")
    try:
        user = UserCreate(
            user_id="test001",
            password="123",
            role="tester"
        )
        print(f"✓ 验证通过: {user.model_dump()}")
    except Exception as e:
        print(f"✗ 验证失败: {e}")

    print("\n测试3：无效的角色")
    try:
        user = UserCreate(
            user_id="test001",
            password="test123",
            role="superuser"
        )
        print(f"✓ 验证通过: {user.model_dump()}")
    except Exception as e:
        print(f"✗ 验证失败: {e}")

    print("\n测试4：有效的评分")
    try:
        rating = RatingCreate(
            score=5,
            comment="不错",
            missing_elements="缺少云朵"
        )
        print(f"✓ 验证通过: {rating.model_dump()}")
    except Exception as e:
        print(f"✗ 验证失败: {e}")

    print("\n测试5：无效的评分（超出范围）")
    try:
        rating = RatingCreate(
            score=10,
            comment="完美"
        )
        print(f"✓ 验证通过: {rating.model_dump()}")
    except Exception as e:
        print(f"✗ 验证失败: {e}")

class ExpertScoreUpdate(BaseModel):
    expert_number: int = Field(..., ge=1, le=2, description="专家编号：1或2")
    score: int = Field(..., ge=0, le=100, description="评分(0-100)")

    @field_validator('expert_number')
    @classmethod
    def validate_expert_number(cls, v: int) -> int:
        if v not in [1, 2]:
            raise ValueError('专家编号必须是1或2')
        return v

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError('评分必须在0-100之间')
        return v

class TargetImagesResponse(BaseModel):
    targets: List[dict] = Field(..., description="目标图列表")

class GeneratedImagesForTargetResponse(BaseModel):
    target_index: int = Field(..., description="目标图索引")
    target_filename: str = Field(..., description="目标图文件名")
    target_image_url: str = Field(..., description="目标图URL")
    ground_truth: Optional[str] = Field(None, description="Ground truth描述")
    difficulty: Optional[str] = Field(None, description="难度")
    generated_images: List[ImageVersionDetailResponse] = Field(..., description="生成的图片列表")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
