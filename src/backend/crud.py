
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime
import uuid

from models import User, Session as SessionModel, Task, ImageVersion, Rating
from schemas import UserCreate, RatingCreate
from auth import hash_password

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()

def get_user_by_db_id(db: Session, id: int) -> Optional[User]:
    return db.query(User).filter(User.id == id).first()

def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()

def get_users_by_role(db: Session, role: str) -> List[User]:
    return db.query(User).filter(User.role == role).all()

def create_user(db: Session, user_data: UserCreate) -> User:
    hashed_password = hash_password(user_data.password)

    db_user = User(
        user_id=user_data.user_id,
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def update_user_password(db: Session, user_id: str, new_password: str) -> bool:
    user = get_user_by_id(db, user_id)
    if not user:
        return False

    user.password_hash = hash_password(new_password)
    db.commit()

    return True

def delete_user(db: Session, user_id: str) -> bool:
    user = get_user_by_id(db, user_id)
    if not user:
        return False

    db.delete(user)
    db.commit()

    return True

def count_users(db: Session) -> int:
    return db.query(User).count()

def get_session_by_id(db: Session, session_id: str) -> Optional[SessionModel]:
    return db.query(SessionModel).filter(SessionModel.session_id == session_id).first()

def get_sessions_by_user(db: Session, user_id: str) -> List[SessionModel]:
    return db.query(SessionModel).filter(SessionModel.user_id == user_id).all()

def get_active_session_by_user(db: Session, user_id: str) -> Optional[SessionModel]:
    return db.query(SessionModel).filter(
        and_(
            SessionModel.user_id == user_id,
            SessionModel.status == "active"
        )
    ).first()

def create_session(db: Session, user_id: str) -> SessionModel:
    session_id = str(uuid.uuid4())

    db_session = SessionModel(
        session_id=session_id,
        user_id=user_id,
        status="active"
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return db_session

def update_session_status(db: Session, session_id: str, status: str) -> bool:
    session = get_session_by_id(db, session_id)
    if not session:
        return False

    session.status = status

    if status == "finished":
        session.finished_at = datetime.utcnow()

    db.commit()

    return True

def count_sessions(db: Session, status: Optional[str] = None) -> int:
    query = db.query(SessionModel)
    if status:
        query = query.filter(SessionModel.status == status)
    return query.count()

def get_task_by_id(db: Session, task_id: str) -> Optional[Task]:
    return db.query(Task).filter(Task.task_id == task_id).first()

def get_tasks_by_session(db: Session, session_id: str) -> List[Task]:
    return db.query(Task).filter(
        Task.session_id == session_id
    ).order_by(Task.round_number).all()

def create_task(
    db: Session,
    session_id: str,
    round_number: int,
    target_index: int,
    target_filename: str,
    target_sha256: str = "",
    ground_truth: str = "",
    difficulty: str = "medium",
    model_type: str = "qwen",
    user_difficulty_rating: str = None,
    admin_difficulty_rating: float = None
) -> Task:
    task_id = str(uuid.uuid4())

    db_task = Task(
        task_id=task_id,
        session_id=session_id,
        round_number=round_number,
        target_index=target_index,
        target_filename=target_filename,
        target_sha256=target_sha256,
        ground_truth=ground_truth,
        difficulty=difficulty,
        model_type=model_type,
        user_difficulty_rating=user_difficulty_rating,
        admin_difficulty_rating=admin_difficulty_rating,
        status="pending"
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task

def update_task_status(db: Session, task_id: str, status: str, error_message: str = None) -> bool:
    task = get_task_by_id(db, task_id)
    if not task:
        return False

    task.status = status

    if error_message and hasattr(task, 'error_message'):
        task.error_message = error_message

    db.commit()

    return True

def count_tasks(db: Session, session_id: Optional[str] = None, status: Optional[str] = None) -> int:
    query = db.query(Task)
    if session_id:
        query = query.filter(Task.session_id == session_id)
    if status:
        query = query.filter(Task.status == status)
    return query.count()

def get_version_by_id(db: Session, version_id: str) -> Optional[ImageVersion]:
    return db.query(ImageVersion).filter(ImageVersion.version_id == version_id).first()

def get_versions_by_task(db: Session, task_id: str) -> List[ImageVersion]:
    return db.query(ImageVersion).filter(
        ImageVersion.task_id == task_id
    ).order_by(ImageVersion.version_number).all()

def get_latest_version(db: Session, task_id: str) -> Optional[ImageVersion]:
    return db.query(ImageVersion).filter(
        ImageVersion.task_id == task_id
    ).order_by(ImageVersion.version_number.desc()).first()

def create_image_version(
    db: Session,
    task_id: str,
    version_number: int,
    prompt: str,
    image_path: str,
    generation_type: str,
    prompt_time_seconds: int = 0,
    model_type: str = "qwen"
) -> ImageVersion:
    existing = db.query(ImageVersion).filter(
        ImageVersion.task_id == task_id,
        ImageVersion.version_number == version_number
    ).first()

    if existing:
        print(f"⚠️ 警告: version 已存在 task_id={task_id[:8]}..., version={version_number}")
        print(f"   返回已有记录: version_id={existing.version_id}")
        return existing

    version = ImageVersion(
        version_id=str(uuid.uuid4()),
        task_id=task_id,
        version_number=version_number,
        prompt=prompt,
        prompt_time_seconds=prompt_time_seconds,
        image_path=image_path,
        generation_type=generation_type,
        model_type=model_type,
        wise_suggestions=None,
        wise_generated=False,
        wise_error=None
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version

def finalize_version(db: Session, version_id: str) -> bool:
    version = get_version_by_id(db, version_id)
    if not version:
        return False

    version.is_final = True
    version.locked = True
    db.commit()

    return True

def count_versions(db: Session, task_id: Optional[str] = None) -> int:
    query = db.query(ImageVersion)
    if task_id:
        query = query.filter(ImageVersion.task_id == task_id)
    return query.count()

def get_rating_by_id(db: Session, rating_id: str) -> Optional[Rating]:
    return db.query(Rating).filter(Rating.rating_id == rating_id).first()

def get_rating_by_version(db: Session, version_id: str) -> Optional[Rating]:
    return db.query(Rating).filter(
        Rating.version_id == version_id
    ).order_by(Rating.created_at.desc()).first()

def create_rating(
    db: Session,
    version_id: str,
    rating_data: RatingCreate
) -> Rating:
    existing = db.query(Rating).filter(
        Rating.version_id == version_id
    ).first()

    if existing:
        existing.style_score = rating_data.style_score
        existing.object_count_score = rating_data.object_count_score
        existing.perspective_score = rating_data.perspective_score
        existing.depth_background_score = rating_data.depth_background_score
        existing.detailed_review = rating_data.detailed_review
        db.commit()
        db.refresh(existing)
        return existing

    rating = Rating(
        rating_id=str(uuid.uuid4()),
        version_id=version_id,
        style_score=rating_data.style_score,
        object_count_score=rating_data.object_count_score,
        perspective_score=rating_data.perspective_score,
        depth_background_score=rating_data.depth_background_score,
        detailed_review=rating_data.detailed_review
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating
def get_average_rating(db: Session, task_id: Optional[str] = None) -> float:
    query = db.query(
        func.avg(
            (Rating.style_score + Rating.object_count_score +
             Rating.perspective_score + Rating.depth_background_score) / 4.0
        )
    )

    if task_id:
        query = query.join(ImageVersion).filter(ImageVersion.task_id == task_id)

    result = query.scalar()
    return float(result) if result else 0.0

def get_session_progress(db: Session, session_id: str) -> dict:
    tasks = get_tasks_by_session(db, session_id)
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "completed")
    pending = sum(1 for t in tasks if t.status == "pending")
    failed = sum(1 for t in tasks if t.status == "failed")

    percentage = (completed / total * 100) if total > 0 else 0

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "failed": failed,
        "percentage": round(percentage, 1)
    }

def get_user_statistics(db: Session, user_id: str) -> dict:
    sessions = get_sessions_by_user(db, user_id)
    total_sessions = len(sessions)
    active_sessions = sum(1 for s in sessions if s.status == "active")
    finished_sessions = sum(1 for s in sessions if s.status == "finished")

    all_tasks = []
    for session in sessions:
        all_tasks.extend(get_tasks_by_session(db, session.session_id))

    total_tasks = len(all_tasks)
    completed_tasks = sum(1 for t in all_tasks if t.status == "completed")

    total_images = 0
    all_ratings = []
    for task in all_tasks:
        versions = get_versions_by_task(db, task.task_id)
        total_images += len(versions)
        for ver in versions:
            rating = get_rating_by_version(db, ver.version_id)
            if rating:
                all_ratings.append(rating.score)

    average_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0.0

    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "finished_sessions": finished_sessions,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "total_images": total_images,
        "average_rating": round(average_rating, 2)
    }

def get_system_statistics(db: Session) -> dict:
    return {
        "total_users": count_users(db),
        "total_sessions": count_sessions(db),
        "active_sessions": count_sessions(db, "active"),
        "completed_sessions": count_sessions(db, "finished"),
        "total_tasks": count_tasks(db),
        "completed_tasks": count_tasks(db, status="completed"),
        "total_images": count_versions(db),
        "average_rating": get_average_rating(db)
    }

if __name__ == "__main__":
    print("=" * 60)
    print("CRUD函数封装完成")
    print("=" * 60)
    print("\n可用的CRUD函数分类：")
    print("\n【User相关】")
    print("  - get_user_by_id")
    print("  - get_all_users")
    print("  - create_user")
    print("  - update_user_password")
    print("  - delete_user")
    print("  - count_users")

    print("\n【Session相关】")
    print("  - get_session_by_id")
    print("  - get_sessions_by_user")
    print("  - get_active_session_by_user")
    print("  - create_session")
    print("  - update_session_status")
    print("  - count_sessions")

    print("\n【Task相关】")
    print("  - get_task_by_id")
    print("  - get_tasks_by_session")
    print("  - create_task")
    print("  - update_task_status")
    print("  - count_tasks")

    print("\n【ImageVersion相关】")
    print("  - get_version_by_id")
    print("  - get_versions_by_task")
    print("  - get_latest_version")
    print("  - create_image_version")
    print("  - finalize_version")
    print("  - count_versions")

    print("\n【Rating相关】")
    print("  - get_rating_by_id")
    print("  - get_rating_by_version")
    print("  - create_rating")
    print("  - get_average_rating")

    print("\n【复合查询】")
    print("  - get_session_progress")
    print("  - get_user_statistics")
    print("  - get_system_statistics")
