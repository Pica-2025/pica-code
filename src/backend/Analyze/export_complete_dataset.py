
import sys
import csv
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional

DB_PATH = Path(__file__).parent.parent / "database.db"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "exports"

EXPORT_FIELDS = [
    "user_id",
    "username",
    "role",

    "session_id",
    "session_status",
    "session_started_at",
    "session_finished_at",

    "task_id",
    "round_number",
    "target_index",
    "target_filename",
    "ground_truth",
    "model_type",
    "user_difficulty_rating",
    "admin_difficulty_rating",
    "task_status",
    "task_created_at",

    "version_id",
    "version_number",
    "prompt",
    "prompt_time_seconds",
    "prompt_length",
    "image_path",
    "generation_type",
    "is_final",
    "version_created_at",

    "user_manual_score",
    "dino_score",
    "hsv_score",
    "structure_score",
    "ai_similarity_score",
    "style_score",
    "object_count_score",
    "perspective_score",
    "depth_background_score",
    "average_star_score",
    "detailed_review",

    "session_duration_seconds",
    "is_first_round",
    "total_rounds_in_task",
    "is_last_round"
]

def build_query(
    user_ids: Optional[List[str]] = None,
    session_ids: Optional[List[str]] = None,
    session_statuses: List[str] = ["finished"]
) -> str:

    query = """
    SELECT
        -- User 信息
        u.user_id,
        u.username,
        u.role,

        -- Session 信息
        s.session_id,
        s.status as session_status,
        s.started_at as session_started_at,
        s.finished_at as session_finished_at,

        -- Task 信息
        t.task_id,
        t.round_number,
        t.target_index,
        t.target_filename,
        t.ground_truth,
        t.model_type,
        t.user_difficulty_rating,
        t.admin_difficulty_rating,
        t.status as task_status,
        t.created_at as task_created_at,

        -- Version 信息
        v.version_id,
        v.version_number,
        v.prompt,
        v.prompt_time_seconds,
        LENGTH(v.prompt) as prompt_length,
        v.image_path,
        v.generation_type,
        CASE WHEN v.is_final = 1 THEN 'True' ELSE 'False' END as is_final,
        v.created_at as version_created_at,

        -- 评分信息
        v.user_manual_score,
        v.dino_score,
        v.hsv_score,
        v.structure_score,
        v.ai_similarity_score,
        r.style_score,
        r.object_count_score,
        r.perspective_score,
        r.depth_background_score,

        -- 计算平均星级评分
        CAST((COALESCE(r.style_score, 0) +
              COALESCE(r.object_count_score, 0) +
              COALESCE(r.perspective_score, 0) +
              COALESCE(r.depth_background_score, 0)) / 4.0 AS REAL) as average_star_score,

        r.detailed_review,

        -- 统计字段
        CAST((julianday(s.finished_at) - julianday(s.started_at)) * 86400 AS REAL) as session_duration_seconds,

        -- 判断是否第一轮
        CASE WHEN v.version_number = 1 THEN 'True' ELSE 'False' END as is_first_round,

        -- 总轮数（查询该task的最大version_number）
        (SELECT MAX(v2.version_number)
         FROM image_versions v2
         WHERE v2.task_id = t.task_id) as total_rounds_in_task,

        -- 判断是否最后一轮
        CASE WHEN v.version_number = (
            SELECT MAX(v3.version_number)
            FROM image_versions v3
            WHERE v3.task_id = t.task_id
        ) THEN 'True' ELSE 'False' END as is_last_round

    FROM users u
    INNER JOIN sessions s ON u.user_id = s.user_id
    INNER JOIN tasks t ON s.session_id = t.session_id
    INNER JOIN image_versions v ON t.task_id = v.task_id
    LEFT JOIN ratings r ON v.version_id = r.version_id

    WHERE 1=1
    ORDER BY
        u.user_id,
        s.started_at,
        t.round_number,
        v.version_number
    导出数据到CSV

    Returns:
        导出的行数
