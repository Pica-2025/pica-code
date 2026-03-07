from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path
from PIL import Image
from typing import Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL_NAME,
    GENERATION_TIMEOUT,
    GENERATIONS_DIR,
    REVISIONS_DIR,
    THUMBS_DIR,
    JPG_QUALITY,
    THUMBNAIL_MAX_SIZE,
    MAX_IMAGE_SIZE,
    DATA_DIR,
    TARGETS_DIR
)

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY 环境变量未设置！")

print(f"✓ Gemini API Key: {GEMINI_API_KEY[:15]}...")
print(f"✓ Gemini模型: {GEMINI_MODEL_NAME}")

generation_executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="gemini_gen_")
generation_lock = threading.Lock()
active_generations = {}

def create_thumbnail(source_path: Path, thumb_path: Path, max_size: Tuple[int, int] = THUMBNAIL_MAX_SIZE) -> Path:
    image = Image.open(source_path)

    if image.mode != 'RGB':
        image = image.convert('RGB')

    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(thumb_path, 'JPEG', quality=85, optimize=True)

    return thumb_path

async def generate_image_with_gemini(
    prompt: str,
    output_path: Path,
    task_id: str,
    negative_prompt: str = ""
) -> Tuple[Path, Path]:
    print(f"\n{'='*60}")
    print(f"[Gemini API调用]")
    print(f"  Prompt: {prompt[:150]}...")
    if negative_prompt:
        print(f"  Negative: {negative_prompt[:100]}...")
    print(f"{'='*60}\n")

    try:
        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt}\n\nNegative prompt: {negative_prompt}"

        print(f"  参数:")
        print(f"    • model: {GEMINI_MODEL_NAME}")
        print(f"  正在调用 Gemini API...")

        loop = asyncio.get_event_loop()

        def call_api():
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=GEMINI_API_KEY)

            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=[full_prompt],
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                    image_config=types.ImageConfig(
                        aspect_ratio="1:1",
                        image_size="1K"
                    )
                )
)

            generated_image = None
            for part in response.parts:
                if part.text is not None:
                    print(f"    • API返回文本: {part.text[:100]}")
                elif part.inline_data is not None:
                    generated_image = part.as_image()
                    print(f"    • 获取到生成图像")
                    break

            if generated_image is None:
                raise ValueError("API没有返回图像数据")

            return generated_image

        generated_image = await loop.run_in_executor(generation_executor, call_api)

        print(f"  ✓ API调用成功")
        print(f"  ✓ 图片生成成功")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        generated_image.save(str(output_path))
        print(f"    ✓ 已保存: {output_path}")

        thumb_filename = f"thumb_{output_path.name}"
        thumb_path = THUMBS_DIR / thumb_filename
        thumb_path = create_thumbnail(output_path, thumb_path)
        print(f"    ✓ 缩略图: {thumb_path}")

        print(f"\n{'='*60}")
        print(f"[生成完成]")
        print(f"  完整图片: {output_path}")
        print(f"  缩略图: {thumb_path}")
        print(f"{'='*60}\n")

        return output_path, thumb_path

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[生成失败!!!]")
        print(f"  错误类型: {type(e).__name__}")
        print(f"  错误: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        raise

def generate_and_update_db(
    task_id: str,
    prompt: str,
    output_path: Path,
    time_spent_seconds: int = 0,
    version_number: int = 1,
    generation_type: str = "initial"
):
    from database import SessionLocal
    import time

    print(f"[线程 {threading.current_thread().name}] 开始生成 task_id={task_id}")

    db = SessionLocal()

    try:
        start_time = time.time()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            full_path, thumb_path = loop.run_until_complete(
                generate_image_with_gemini(
                    prompt=prompt,
                    output_path=output_path,
                    task_id=task_id
                )
            )
        finally:
            loop.close()

        elapsed = int(time.time() - start_time)
        print(f"  [{task_id[:8]}] 生成耗时: {elapsed}秒")

        from crud import update_task_status, get_versions_by_task
        from models import ImageVersion, Task

        versions = get_versions_by_task(db, task_id)
        version = None
        for v in versions:
            if v.version_number == version_number:
                version = v
                break

        if not version:
            print(f"  [{task_id[:8]}] ❌ 找不到版本记录: version={version_number}")
            update_task_status(db, task_id, "failed")
            return

        print(f"  [{task_id[:8]}] ✅ 找到版本记录: version_id={version.version_id}")

        version.image_path = str(full_path.relative_to(DATA_DIR))
        db.commit()

        print(f"  [{task_id[:8]}] 图片路径已更新: {version.image_path}")

        print(f"  [{task_id[:8]}] 开始多维度相似度计算...")

        try:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if task:
                target_path = TARGETS_DIR / task.target_filename
                generated_path = full_path

                from auto_scorer_multi import compute_multi_dimensional_scores, get_score_details_json
                scores = compute_multi_dimensional_scores(target_path, generated_path, verbose=False)

                version.dino_score = scores["dino_score"]
                version.hsv_score = scores["hsv_score"]
                version.structure_score = scores["structure_score"]

                version.ai_similarity_score = scores["combined_score"]
                version.ai_similarity_details = get_score_details_json(scores)

                db.commit()

                print(f"  [{task_id[:8]}] ✅ 多维度分数:")
                print(f"    - DINO: {scores['dino_score']:.4f}")
                print(f"    - HSV:  {scores['hsv_score']:.4f}")
                print(f"    - Structure: {scores['structure_score']:.4f}")
                print(f"    - 综合: {scores['combined_score']:.2f}/100")
            else:
                print(f"  [{task_id[:8]}] ⚠️  找不到任务，跳过 AI 计算")

        except Exception as e:
            print(f"  [{task_id[:8]}] ⚠️  AI 计算失败: {e}")
            import traceback
            traceback.print_exc()

        update_task_status(db, task_id, "completed")
        db.commit()

        print(f"  [{task_id[:8]}] ✅ [生成成功!!!] 任务状态已更新为completed")

        with generation_lock:
            if task_id in active_generations:
                del active_generations[task_id]

    except Exception as e:
        print(f"  [{task_id[:8]}] ❌ [生成失败!!!] {str(e)}")
        import traceback
        traceback.print_exc()

        from crud import update_task_status
        update_task_status(db, task_id, "failed")
        db.commit()

        with generation_lock:
            if task_id in active_generations:
                del active_generations[task_id]

    finally:
        db.close()

async def generate_and_save_image(
    prompt: str,
    output_path: Path,
    reference_image_path: Path = None,
    task_id: str = None,
    time_spent_seconds: int = 0,
    version_number: int = 1,
    generation_type: str = "initial",
    **kwargs
) -> str:
    if not task_id:
        import uuid
        task_id = str(uuid.uuid4())

    print(f"\n[提交生成任务] task_id={task_id}, version={version_number}")

    with generation_lock:
        active_generations[task_id] = {
            'prompt': prompt,
            'output_path': output_path,
            'version_number': version_number,
            'created_at': datetime.utcnow()
        }

    generation_executor.submit(
        generate_and_update_db,
        task_id,
        prompt,
        output_path,
        time_spent_seconds,
        version_number,
        generation_type
    )

    print(f"  ✅ 已提交到线程池，后台生成中...\n")

    return task_id

async def test_gemini_api():
    print("="*60)
    print("Gemini 3 Pro Image API测试")
    print("="*60)

    prompt = "A cute cat sitting on a wooden chair in a cozy room"
    output_path = Path("/tmp/test_gemini_output.jpg")

    try:
        full_path, thumb_path = await generate_image_with_gemini(
            prompt=prompt,
            output_path=output_path,
            task_id="test_001"
        )
        print(f"\n✅ 测试成功！")
        print(f"   图片: {full_path}")
        print(f"   缩略图: {thumb_path}")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini_api())
