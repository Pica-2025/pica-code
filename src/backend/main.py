from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import uuid
from database import get_db, init_db
from models import User, Session as SessionModel, Task, ImageVersion, Rating
from schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    SessionResponse, SessionDetailResponse,
    TaskResponse, TaskSubmit, TaskStatusResponse, TaskDetailResponse,
    ImageVersionDetailResponse, UserManualScoreUpdate,
    RatingCreate, RatingResponse,
    MessageResponse, AdminStatsResponse,
    ExpertScoreUpdate, TargetImagesResponse, GeneratedImagesForTargetResponse
)
from auth import (
    authenticate_user, create_access_token, get_current_user,
    get_current_active_user, require_admin, require_tester
)
from crud import (
    get_user_by_id, create_user, count_users,
    get_session_by_id, get_sessions_by_user, get_active_session_by_user,
    create_session, update_session_status, get_session_progress,
    get_task_by_id, get_tasks_by_session, update_task_status,
    get_version_by_id, get_versions_by_task, get_latest_version,
    create_image_version, finalize_version,
    get_rating_by_version, create_rating,
    get_user_statistics, get_system_statistics
)
from tasks import assign_tasks_to_session, get_target_image_url
from config import (
    DATA_DIR, GENERATIONS_DIR, REVISIONS_DIR, RATING_DIMENSIONS,
    BASE_DIR
)

from admin_data_routes import router as admin_data_router

app = FastAPI(
    title="Pica Image Generation Test System",
    description="图像生成测试系统API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_data_router)

app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

@app.post("/api/auth/login", response_model=TokenResponse, tags=["认证"])
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.username, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    access_token = create_access_token(
        data={"sub": user.user_id, "role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        role=user.role
    )

@app.post("/api/auth/logout", response_model=MessageResponse, tags=["认证"])
def logout(current_user: User = Depends(get_current_user)):
    return MessageResponse(message="登出成功")

from wise_tasks import generate_wise_suggestions_task

@app.post("/api/users", response_model=UserResponse, status_code=201, tags=["用户"])
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    existing = get_user_by_id(db, user_data.user_id)
    if existing:
        raise HTTPException(status_code=400, detail="用户ID已存在")

    new_user = create_user(db, user_data)
    return UserResponse.model_validate(new_user)

@app.get("/api/users", response_model=List[UserResponse], tags=["用户"])
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    users = db.query(User).all()
    return [UserResponse.model_validate(user) for user in users]

@app.get("/api/users/me", response_model=UserResponse, tags=["用户"])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

@app.get("/api/users/me/stats", tags=["用户"])
def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stats = get_user_statistics(db, current_user.user_id)
    return stats

@app.post("/api/sessions/start", response_model=SessionDetailResponse, tags=["Session"])
def start_new_session(
    current_user: User = Depends(require_tester),
    db: Session = Depends(get_db)
):
    active = get_active_session_by_user(db, current_user.user_id)
    if active:
        tasks = get_tasks_by_session(db, active.session_id)

        if not tasks:
            error_msg = f"Session {active.session_id} 数据异常：没有关联的任务"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        return SessionDetailResponse(
            id=active.id,
            session_id=active.session_id,
            user_id=active.user_id,
            status=active.status,
            started_at=active.started_at,
            finished_at=active.finished_at,
            tasks=[
                TaskResponse(
                    id=t.id,
                    task_id=t.task_id,
                    session_id=t.session_id,
                    round_number=t.round_number,
                    target_index=t.target_index,
                    target_filename=t.target_filename,
                    target_sha256=t.target_sha256,
                    difficulty=t.difficulty,
                    status=t.status,
                    created_at=t.created_at,
                    target_image_url=get_target_image_url(t.target_filename)
                ) for t in tasks
            ]
        )

    session = create_session(db, current_user.user_id)

    tasks = assign_tasks_to_session(db, session.session_id)

    return SessionDetailResponse(
        id=session.id,
        session_id=session.session_id,
        user_id=session.user_id,
        status=session.status,
        started_at=session.started_at,
        finished_at=session.finished_at,
        tasks=[
            TaskResponse(
                id=t.id,
                task_id=t.task_id,
                session_id=t.session_id,
                round_number=t.round_number,
                target_index=t.target_index,
                target_filename=t.target_filename,
                target_sha256=t.target_sha256,
                difficulty=t.difficulty,
                status=t.status,
                created_at=t.created_at,
                target_image_url=get_target_image_url(t.target_filename)
            ) for t in tasks
        ]
    )

@app.get("/api/sessions/{session_id}", response_model=SessionDetailResponse, tags=["Session"])
def get_session_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session不存在")

    if session.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此Session")

    tasks = get_tasks_by_session(db, session_id)

    task_responses = []
    for task in tasks:
        latest_version = get_latest_version(db, task.task_id)

        task_data = {
            "id": task.id,
            "task_id": task.task_id,
            "session_id": task.session_id,
            "round_number": task.round_number,
            "target_index": task.target_index,
            "target_filename": task.target_filename,
            "target_image_url": get_target_image_url(task.target_filename),
            "target_sha256": task.target_sha256,
            "difficulty": task.difficulty,
            "status": task.status,
            "created_at": task.created_at,
        }

        if latest_version:
            task_data["generated_image_url"] = f"/data/{latest_version.image_path}"

        versions = get_versions_by_task(db, task.task_id)
        task_data["has_final_version"] = any(v.is_final for v in versions)

        task_responses.append(task_data)

    response = SessionDetailResponse(
        id=session.id,
        session_id=session.session_id,
        user_id=session.user_id,
        status=session.status,
        started_at=session.started_at,
        finished_at=session.finished_at,
        tasks=task_responses
    )

    return response

@app.get("/api/sessions/{session_id}/progress", tags=["Session"])
def get_progress(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session不存在")

    if session.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问")

    progress = get_session_progress(db, session_id)
    return progress

@app.post("/api/sessions/{session_id}/finish", response_model=MessageResponse, tags=["Session"])
def finish_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session不存在")

    if session.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权操作")

    tasks = get_tasks_by_session(db, session_id)
    pending_tasks = [t for t in tasks if t.status == 'pending']
    processing_tasks = [t for t in tasks if t.status == 'processing']
    completed_tasks = [t for t in tasks if t.status == 'completed']
    failed_tasks = [t for t in tasks if t.status == 'failed']

    if pending_tasks or processing_tasks:
        raise HTTPException(
            status_code=400,
            detail=f"还有 {len(pending_tasks)} 个未提交任务，{len(processing_tasks)} 个生成中任务"
        )

    MIN_COMPLETED = 8
    if len(completed_tasks) < MIN_COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"至少需要 {MIN_COMPLETED} 个成功完成的任务，当前只有 {len(completed_tasks)} 个"
        )

    tasks_with_final = 0
    for task in completed_tasks:
        versions = get_versions_by_task(db, task.task_id)
        if any(v.is_final for v in versions):
            tasks_with_final += 1

    if tasks_with_final < len(completed_tasks):
        raise HTTPException(
            status_code=400,
            detail=f"所有成功完成的任务都必须标记最终版本（已标记 {tasks_with_final}/{len(completed_tasks)}）"
        )

    update_session_status(db, session_id, "finished")

    message = f"Session已完成！成功: {len(completed_tasks)}"
    if failed_tasks:
        message += f", 失败: {len(failed_tasks)}"

    return MessageResponse(message=message)

@app.post("/api/tasks/{task_id}/submit", response_model=MessageResponse, tags=["任务"])
async def submit_task(
    task_id: str,
    task_data: TaskSubmit,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if not task.user_difficulty_rating and task_data.difficulty_rating:
        if task_data.difficulty_rating in ['easy', 'medium', 'hard']:
            task.user_difficulty_rating = task_data.difficulty_rating
            db.commit()
            print(f"✅ 保存用户难度评级: {task_data.difficulty_rating}")

    existing_versions = get_versions_by_task(db, task_id)

    is_failed_retry = False
    failed_version_to_delete = None

    if task.status == "failed" and len(existing_versions) > 0:
        last_version = existing_versions[-1]
        if not last_version.image_path or last_version.image_path == "":
            is_failed_retry = True
            failed_version_to_delete = last_version
            print(f"🔄 检测到失败任务重试: task_id={task_id}, version={last_version.version_number}")

    effective_version_count = len(existing_versions) if not is_failed_retry else len(existing_versions) - 1
    if effective_version_count >= 8:
        raise HTTPException(status_code=400, detail="已达到最大版本数（8个）")

    update_task_status(db, task_id, "processing")

    if is_failed_retry:
        version_number = failed_version_to_delete.version_number
        generation_type = failed_version_to_delete.generation_type
        db.delete(failed_version_to_delete)
        db.commit()
        print(f"🗑️  已删除失败版本: version={version_number}")
    else:
        version_number = len(existing_versions) + 1
        if version_number == 1:
            generation_type = "initial"
        else:
            generation_type = "revision"

    if version_number == 1:
        output_path = GENERATIONS_DIR / f"gen_{task_id}_v1.jpg"
    else:
        output_path = REVISIONS_DIR / f"rev_{task_id}_v{version_number}.jpg"

    version = create_image_version(
        db=db,
        task_id=task_id,
        version_number=version_number,
        prompt=task_data.prompt,
        image_path="",
        generation_type=generation_type,
        prompt_time_seconds=task_data.time_spent_seconds,
        model_type=task.model_type
    )

    print(f"✅ 创建版本记录: version_id={version.version_id}, version={version_number}")

    background_tasks.add_task(
        generate_image_task,
        task_id=task_id,
        prompt=task_data.prompt,
        target_image_path=str(DATA_DIR / "targets" / task.target_filename),
        output_path=str(output_path),
        time_spent_seconds=task_data.time_spent_seconds,
        version_number=version_number,
        generation_type=generation_type,
        model_type=task.model_type
    )

    if not is_failed_retry:
        background_tasks.add_task(
            generate_wise_suggestions_task,
            version_id=version.version_id,
            prompt=task_data.prompt
        )
        print(f"🤖 已提交Wise分析任务: version_id={version.version_id[:8]}...")
    else:
        print(f"⏭️  失败重试，跳过Wise分析")

    return MessageResponse(message="任务已提交")

@app.get("/api/tasks/{task_id}/status", response_model=TaskStatusResponse, tags=["任务"])
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "completed":
        version = get_latest_version(db, task_id)
        image_url = f"/data/{version.image_path}" if version else None

        return TaskStatusResponse(
            task_id=task_id,
            status="completed",
            message="生成完成",
            image_url=image_url,
            progress=100
        )
    elif task.status == "processing":
        return TaskStatusResponse(
            task_id=task_id,
            status="processing",
            message="生成中...",
            progress=50
        )
    elif task.status == "failed":
        return TaskStatusResponse(
            task_id=task_id,
            status="failed",
            message="生成失败",
            progress=0
        )
    else:
        return TaskStatusResponse(
            task_id=task_id,
            status="pending",
            message="等待提交",
            progress=0
        )

@app.get("/api/tasks/{task_id}/detail", tags=["任务"])
def get_task_detail(
    task_id: str,
    db: Session = Depends(get_db)
):
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    versions = get_versions_by_task(db, task_id)

    version_responses = []
    for ver in versions:
        rating = get_rating_by_version(db, ver.version_id)

        version_data = ImageVersionDetailResponse(
            id=ver.id,
            version_id=ver.version_id,
            task_id=ver.task_id,
            version_number=ver.version_number,
            prompt=ver.prompt,
            prompt_time_seconds=ver.prompt_time_seconds,
            image_path=ver.image_path,
            image_url=f"/data/{ver.image_path}",
            thumbnail_url=f"/data/thumbs/thumb_{ver.image_path.split('/')[-1]}",
            generation_type=ver.generation_type,
            is_final=ver.is_final,
            locked=ver.locked,
            created_at=ver.created_at,

            user_manual_score=ver.user_manual_score,

            dino_score=ver.dino_score,
            hsv_score=ver.hsv_score,
            structure_score=ver.structure_score,
            clip_score=ver.clip_score,

            ai_similarity_score=ver.ai_similarity_score,
            ai_similarity_details=ver.ai_similarity_details,

            wise_suggestions=ver.wise_suggestions,
            wise_generated=ver.wise_generated,
            wise_error=ver.wise_error,

            rating=RatingResponse.model_validate(rating) if rating else None
        )
        version_responses.append(version_data)

    response = TaskDetailResponse(
        id=task.id,
        task_id=task.task_id,
        session_id=task.session_id,
        round_number=task.round_number,
        target_index=task.target_index,
        target_filename=task.target_filename,
        target_image_url=get_target_image_url(task.target_filename),
        target_sha256=task.target_sha256,
        difficulty=task.difficulty,
        status=task.status,
        created_at=task.created_at,
        versions=version_responses
    )

    return response

@app.post("/api/versions/{version_id}/rate", response_model=RatingResponse, tags=["图片版本"])
def rate_image_version(
    version_id: str,
    rating_data: RatingCreate,
    db: Session = Depends(get_db)
):
    version = get_version_by_id(db, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    existing_rating = get_rating_by_version(db, version_id)
    if existing_rating:
        existing_rating.style_score = rating_data.style_score
        existing_rating.object_count_score = rating_data.object_count_score
        existing_rating.perspective_score = rating_data.perspective_score
        existing_rating.depth_background_score = rating_data.depth_background_score
        existing_rating.detailed_review = rating_data.detailed_review
        db.commit()
        db.refresh(existing_rating)
        return RatingResponse.model_validate(existing_rating)

    rating = create_rating(db, version_id, rating_data)
    return RatingResponse.model_validate(rating)

@app.post("/api/versions/{version_id}/finalize", response_model=MessageResponse, tags=["图片版本"])
def mark_version_as_final(
    version_id: str,
    db: Session = Depends(get_db)
):
    version = get_version_by_id(db, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    finalize_version(db, version_id)
    return MessageResponse(message="已标记为最终版本")

@app.post("/api/versions/{version_id}/manual-score", response_model=MessageResponse, tags=["图片版本"])
def update_manual_score(
    version_id: str,
    score_data: UserManualScoreUpdate,
    db: Session = Depends(get_db)
):
    version = get_version_by_id(db, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    version.user_manual_score = score_data.user_manual_score
    db.commit()

    return MessageResponse(message="评分已保存")

@app.get("/api/versions/{version_id}/detail", response_model=ImageVersionDetailResponse, tags=["图片版本"])
def get_version_detail(
    version_id: str,
    db: Session = Depends(get_db)
):
    version = get_version_by_id(db, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    rating = get_rating_by_version(db, version_id)

    response = ImageVersionDetailResponse(
    id=version.id,
    version_id=version.version_id,
    task_id=version.task_id,
    version_number=version.version_number,
    prompt=version.prompt,
    prompt_time_seconds=version.prompt_time_seconds,
    image_path=version.image_path,
    image_url=f"/data/{version.image_path}",
    thumbnail_url=f"/data/thumbs/thumb_{version.image_path.split('/')[-1]}",
    generation_type=version.generation_type,
    is_final=version.is_final,
    locked=version.locked,
    created_at=version.created_at,
    rating=RatingResponse.model_validate(rating) if rating else None
)

    return response

@app.post("/api/versions/{version_id}/expert-score", response_model=MessageResponse, tags=["专家评分"])
def update_expert_score(
    version_id: str,
    score_data: ExpertScoreUpdate,
    db: Session = Depends(get_db)
):
    version = get_version_by_id(db, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    if score_data.expert_number == 1:
        version.expert_score_1 = score_data.score
    else:
        version.expert_score_2 = score_data.score

    db.commit()

    return MessageResponse(message=f"专家{score_data.expert_number}评分已保存")

@app.get("/api/expert-rating/targets", response_model=TargetImagesResponse, tags=["专家评分"])
def get_all_targets(
    db: Session = Depends(get_db)
):
    from manifest_loader import load_targets_manifest

    targets_df = load_targets_manifest()

    targets_list = []
    for _, row in targets_df.iterrows():
        target_info = {
            "target_index": int(row['index']),
            "target_filename": row['filename'],
            "target_image_url": f"/data/targets/{row['filename']}",
            "ground_truth": row.get('ground_truth', ''),
            "difficulty": row.get('difficulty', '')
        }
        targets_list.append(target_info)

    return TargetImagesResponse(targets=targets_list)

@app.get("/api/expert-rating/targets/{target_index}/images", response_model=GeneratedImagesForTargetResponse, tags=["专家评分"])
def get_generated_images_for_target(
    target_index: int,
    db: Session = Depends(get_db)
):
    from manifest_loader import load_targets_manifest
    from sqlalchemy import and_

    targets_df = load_targets_manifest()

    targets_df['index'] = targets_df['index'].astype(int)
    target_row = targets_df[targets_df['index'] == target_index]

    if target_row.empty:
        raise HTTPException(status_code=404, detail=f"目标图 index={target_index} 不存在")

    target_row = target_row.iloc[0]
    target_filename = target_row['filename']

    tasks = db.query(Task).filter(Task.target_index == target_index).all()

    print(f"✓ 找到 {len(tasks)} 个任务使用目标图 {target_index}")

    if not tasks:
        return GeneratedImagesForTargetResponse(
            target_index=target_index,
            target_filename=target_filename,
            target_image_url=f"/data/targets/{target_filename}",
            ground_truth=target_row.get('ground_truth', ''),
            difficulty=target_row.get('difficulty', ''),
            generated_images=[]
        )

    generated_images = []
    for task in tasks:
        versions = get_versions_by_task(db, task.task_id)
        for version in versions:
            if version.image_path and version.image_path != "":
                rating = get_rating_by_version(db, version.version_id)

                version_data = ImageVersionDetailResponse(
                    id=version.id,
                    version_id=version.version_id,
                    task_id=version.task_id,
                    version_number=version.version_number,
                    prompt=version.prompt,
                    prompt_time_seconds=version.prompt_time_seconds,
                    image_path=version.image_path,
                    image_url=f"/data/{version.image_path}",
                    thumbnail_url=f"/data/thumbs/thumb_{version.image_path.split('/')[-1]}",
                    generation_type=version.generation_type,
                    is_final=version.is_final,
                    locked=version.locked,
                    created_at=version.created_at,
                    user_manual_score=version.user_manual_score,
                    expert_score_1=version.expert_score_1,
                    expert_score_2=version.expert_score_2,
                    dino_score=version.dino_score,
                    hsv_score=version.hsv_score,
                    structure_score=version.structure_score,
                    clip_score=version.clip_score,
                    ai_similarity_score=version.ai_similarity_score,
                    ai_similarity_details=version.ai_similarity_details,
                    wise_suggestions=version.wise_suggestions,
                    wise_generated=version.wise_generated,
                    wise_error=version.wise_error,
                    rating=RatingResponse.model_validate(rating) if rating else None
                )
                generated_images.append(version_data)

    print(f"✓ 找到 {len(generated_images)} 个生成图")

    return GeneratedImagesForTargetResponse(
        target_index=target_index,
        target_filename=target_filename,
        target_image_url=f"/data/targets/{target_filename}",
        ground_truth=target_row.get('ground_truth', ''),
        difficulty=target_row.get('difficulty', ''),
        generated_images=generated_images
    )

@app.get("/api/admin/stats", response_model=AdminStatsResponse, tags=["管理员"])
def get_admin_statistics(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    stats = get_system_statistics(db)
    return AdminStatsResponse(**stats)

@app.get("/api/admin/users", tags=["管理员"])
def list_all_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    from crud import get_all_users
    users = get_all_users(db)
    return {
        "users": [UserResponse.model_validate(u) for u in users],
        "total": len(users)
    }

@app.get("/api/rating-dimensions", tags=["其他"])
def get_rating_dimensions():
    from config import RATING_DIMENSIONS, STAR_MEANINGS
    return {
        "dimensions": RATING_DIMENSIONS,
        "star_meanings": STAR_MEANINGS
    }

@app.get("/api/health", tags=["其他"])
def health_check():
    return {"status": "ok"}

async def generate_image_task(
    task_id: str,
    prompt: str,
    target_image_path: str,
    output_path: str,
    time_spent_seconds: int,
    version_number: int,
    generation_type: str,
    model_type: str = "qwen"
):
    from database import SessionLocal
    from pathlib import Path
    import traceback

    db = SessionLocal()
    try:
        print(f"\n{'='*60}")
        print(f"[生成任务开始]")
        print(f"  task_id: {task_id}")
        print(f"  version: {version_number}")
        print(f"  prompt: {prompt[:100]}...")
        print(f"{'='*60}\n")

        if model_type == "gemini":
            from gemini_client import generate_and_save_image
            print(f"  🎨 使用 Gemini 模型生成")
        else:
            from qwen_client import generate_and_save_image
            print(f"  🎨 使用 Qwen 模型生成")
        await generate_and_save_image(
            prompt=prompt,
            output_path=Path(output_path),
            reference_image_path=Path(target_image_path),
            task_id=task_id,
            time_spent_seconds=time_spent_seconds,
            version_number=version_number,
            generation_type=generation_type
        )

        print(f"  ✅ 已提交到生成队列")
        print(f"  ✅ 后台线程正在处理...\n")

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[提交失败]")
        print(f"  错误: {str(e)}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        update_task_status(db, task_id, "failed")
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    print("============================================================")
    print("Pica系统启动中...")
    print("============================================================")
    init_db()
    print("✓ 数据库初始化完成")

    try:
        from auto_scorer_dino import init_dino_model
        import asyncio

        print("⏳ 正在后台加载 DINO v2 模型...")

        await asyncio.to_thread(init_dino_model)

        print("✓ DINO v2 模型加载完成")

    except Exception as e:
        print(f"⚠️  模型加载失败: {e}")

    print("✓ API服务已启动")
    print("  访问文档: http://{host}:{port}/docs")
    print("============================================================")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
