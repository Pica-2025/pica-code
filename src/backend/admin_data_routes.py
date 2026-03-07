from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from models import User, Session as SessionModel, Task, ImageVersion, Rating
from auth import require_admin
from schemas import UserResponse
from tasks import get_target_image_url

router = APIRouter(prefix="/api/admin/data", tags=["管理员数据查看"])

@router.get("/users")
def get_all_users_with_sessions(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).filter(User.role == "tester").order_by(User.created_at.desc()).all()

    result = []
    for user in users:
        sessions = db.query(SessionModel).filter(
            SessionModel.user_id == user.user_id
        ).order_by(SessionModel.started_at.desc()).all()

        result.append({
            "user_id": user.user_id,
            "username": user.username,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "total_sessions": len(sessions),
            "sessions": [
                {
                    "session_id": s.session_id,
                    "status": s.status,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "finished_at": s.finished_at.isoformat() if s.finished_at else None,
                    "task_count": len(s.tasks) if s.tasks else 0
                }
                for s in sessions
            ]
        })

    return {"users": result, "total": len(result)}

@router.get("/sessions/{session_id}/tasks")
def get_session_all_tasks(
    session_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session不存在")

    tasks = db.query(Task).filter(
        Task.session_id == session_id
    ).order_by(Task.round_number).all()

    result = []
    for task in tasks:
        final_version = db.query(ImageVersion).filter(
            ImageVersion.task_id == task.task_id,
            ImageVersion.is_final == True
        ).first()

        if not final_version:
            final_version = db.query(ImageVersion).filter(
                ImageVersion.task_id == task.task_id
            ).order_by(ImageVersion.version_number.desc()).first()

        version_count = db.query(ImageVersion).filter(
            ImageVersion.task_id == task.task_id
        ).count()

        result.append({
            "task_id": task.task_id,
            "round_number": task.round_number,
            "target_index": task.target_index,
            "target_filename": task.target_filename,
            "target_image_url": get_target_image_url(task.target_filename),
            "ground_truth": task.ground_truth,

            "model_type": task.model_type,
            "difficulty": task.difficulty,
            "user_difficulty_rating": task.user_difficulty_rating,
            "admin_difficulty_rating": task.admin_difficulty_rating,

            "status": task.status,
            "version_count": version_count,

            "latest_version": {
                "version_id": final_version.version_id,
                "version_number": final_version.version_number,
                "image_url": f"/data/{final_version.image_path}",
                "is_final": final_version.is_final,

                "prompt": final_version.prompt,
                "prompt_length": len(final_version.prompt) if final_version.prompt else 0,
                "prompt_time_seconds": final_version.prompt_time_seconds,

                "user_manual_score": final_version.user_manual_score,
                "ai_similarity_score": final_version.ai_similarity_score,

                "model_type": final_version.model_type
            } if final_version else None
        })

    return {
        "session_id": session_id,
        "user_id": session.user_id,
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "finished_at": session.finished_at.isoformat() if session.finished_at else None,
        "tasks": result
    }

@router.get("/tasks/{task_id}/all-versions")
def get_task_all_versions(
    task_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    versions = db.query(ImageVersion).filter(
        ImageVersion.task_id == task_id
    ).order_by(ImageVersion.version_number).all()

    result_versions = []
    for version in versions:
        rating = version.rating

        version_data = {
            "version_id": version.version_id,
            "version_number": version.version_number,

            "prompt": version.prompt,
            "prompt_length": len(version.prompt) if version.prompt else 0,
            "prompt_time_seconds": version.prompt_time_seconds,

            "image_url": f"/data/{version.image_path}",
            "generation_type": version.generation_type,
            "model_type": version.model_type,
            "is_final": version.is_final,
            "created_at": version.created_at.isoformat() if version.created_at else None,

            "user_manual_score": version.user_manual_score,

            "dino_score": version.dino_score,
            "hsv_score": version.hsv_score,
            "structure_score": version.structure_score,
            "ai_similarity_score": version.ai_similarity_score,
            "ai_similarity_details": version.ai_similarity_details,

            "rating": {
                "rating_id": rating.rating_id,
                "style_score": rating.style_score,
                "object_count_score": rating.object_count_score,
                "perspective_score": rating.perspective_score,
                "depth_background_score": rating.depth_background_score,
                "average_score": round(
                    (rating.style_score + rating.object_count_score +
                     rating.perspective_score + rating.depth_background_score) / 4,
                    2
                ),
                "detailed_review": rating.detailed_review,
                "created_at": rating.created_at.isoformat() if rating.created_at else None
            } if rating else None
        }

        result_versions.append(version_data)

    return {
        "task_id": task_id,
        "round_number": task.round_number,
        "target_index": task.target_index,
        "target_filename": task.target_filename,
        "target_image_url": get_target_image_url(task.target_filename),
        "ground_truth": task.ground_truth,

        "model_type": task.model_type,
        "difficulty": task.difficulty,
        "user_difficulty_rating": task.user_difficulty_rating,
        "admin_difficulty_rating": task.admin_difficulty_rating,

        "status": task.status,
        "session_id": task.session_id,
        "total_versions": len(versions),
        "versions": result_versions
    }

@router.get("/statistics")
def get_detailed_statistics(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).filter(User.role == "tester").count()

    total_sessions = db.query(SessionModel).count()
    completed_sessions = db.query(SessionModel).filter(
        SessionModel.status == "finished"
    ).count()
    active_sessions = db.query(SessionModel).filter(
        SessionModel.status == "active"
    ).count()

    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.status == "completed").count()

    qwen_tasks = db.query(Task).filter(Task.model_type == "qwen").count()
    gemini_tasks = db.query(Task).filter(Task.model_type == "gemini").count()

    difficulty_stats = {}
    for level in ['easy', 'medium', 'hard']:
        count = db.query(Task).filter(Task.user_difficulty_rating == level).count()
        difficulty_stats[level] = count

    total_versions = db.query(ImageVersion).count()
    final_versions = db.query(ImageVersion).filter(
        ImageVersion.is_final == True
    ).count()

    qwen_versions = db.query(ImageVersion).filter(ImageVersion.model_type == "qwen").count()
    gemini_versions = db.query(ImageVersion).filter(ImageVersion.model_type == "gemini").count()

    total_ratings = db.query(Rating).count()

    all_ratings = db.query(Rating).all()
    if all_ratings:
        avg_style = sum(r.style_score for r in all_ratings) / len(all_ratings)
        avg_object = sum(r.object_count_score for r in all_ratings) / len(all_ratings)
        avg_perspective = sum(r.perspective_score for r in all_ratings) / len(all_ratings)
        avg_depth = sum(r.depth_background_score for r in all_ratings) / len(all_ratings)
        overall_avg = (avg_style + avg_object + avg_perspective + avg_depth) / 4
    else:
        avg_style = avg_object = avg_perspective = avg_depth = overall_avg = 0

    versions_with_score = db.query(ImageVersion).filter(
        ImageVersion.user_manual_score.isnot(None)
    ).all()

    avg_manual_score = 0
    if versions_with_score:
        avg_manual_score = sum(v.user_manual_score for v in versions_with_score) / len(versions_with_score)

    versions_with_ai_score = db.query(ImageVersion).filter(
        ImageVersion.ai_similarity_score.isnot(None)
    ).all()

    avg_ai_score = 0
    avg_dino_score = 0
    avg_hsv_score = 0
    avg_structure_score = 0

    if versions_with_ai_score:
        avg_ai_score = sum(v.ai_similarity_score for v in versions_with_ai_score) / len(versions_with_ai_score)

        dino_scores = [v.dino_score for v in versions_with_ai_score if v.dino_score is not None]
        hsv_scores = [v.hsv_score for v in versions_with_ai_score if v.hsv_score is not None]
        structure_scores = [v.structure_score for v in versions_with_ai_score if v.structure_score is not None]

        if dino_scores:
            avg_dino_score = sum(dino_scores) / len(dino_scores)
        if hsv_scores:
            avg_hsv_score = sum(hsv_scores) / len(hsv_scores)
        if structure_scores:
            avg_structure_score = sum(structure_scores) / len(structure_scores)

    return {
        "users": {
            "total": total_users
        },
        "sessions": {
            "total": total_sessions,
            "completed": completed_sessions,
            "active": active_sessions
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "by_model": {
                "qwen": qwen_tasks,
                "gemini": gemini_tasks
            },
            "by_difficulty": difficulty_stats
        },
        "versions": {
            "total": total_versions,
            "final": final_versions,
            "by_model": {
                "qwen": qwen_versions,
                "gemini": gemini_versions
            }
        },
        "ratings": {
            "total": total_ratings,
            "average_stars": {
                "style": round(avg_style, 2),
                "object_count": round(avg_object, 2),
                "perspective": round(avg_perspective, 2),
                "depth_background": round(avg_depth, 2),
                "overall": round(overall_avg, 2)
            }
        },
        "scores": {
            "manual_similarity": {
                "count": len(versions_with_score),
                "average": round(avg_manual_score, 2)
            },
            "ai_similarity": {
                "count": len(versions_with_ai_score),
                "average": round(avg_ai_score, 4),
                "dimensions": {
                    "dino": round(avg_dino_score, 4),
                    "hsv": round(avg_hsv_score, 4),
                    "structure": round(avg_structure_score, 4)
                }
            }
        }
    }

@router.put("/tasks/{task_id}/admin-difficulty")
def update_admin_difficulty_rating(
    task_id: str,
    difficulty_rating: float,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if difficulty_rating < 1 or difficulty_rating > 10:
        raise HTTPException(status_code=400, detail="难度评级必须在1-10之间")

    task.admin_difficulty_rating = difficulty_rating
    db.commit()

    return {
        "success": True,
        "task_id": task_id,
        "admin_difficulty_rating": difficulty_rating
    }
