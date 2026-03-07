from dotenv import load_dotenv
load_dotenv()

import os
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
from typing import Tuple, Optional
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import dashscope
from dashscope import ImageSynthesis
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime

from config import (
    DASHSCOPE_API_KEY,
    QWEN_MODEL_NAME,
    DEFAULT_QWEN_PARAMS,
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

if not DASHSCOPE_API_KEY:
    raise ValueError("❌ DASHSCOPE_API_KEY 环境变量未设置！")

dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

print(f"✓ DashScope API Key: {DASHSCOPE_API_KEY[:15]}...")
print(f"✓ Qwen模型: {QWEN_MODEL_NAME}")
print(f"✓ 固定种子: {DEFAULT_QWEN_PARAMS.get('seed', '随机')}")
print(f"✓ Prompt改写: {'关闭' if not DEFAULT_QWEN_PARAMS.get('prompt_extend', True) else '开启'}")

generation_executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="qwen_gen_")
generation_lock = threading.Lock()
active_generations = {}

def download_image_from_url(url: str, output_path: Path) -> Path:
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    image = Image.open(BytesIO(response.content))

    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        if image.mode in ('RGBA', 'LA'):
            background.paste(image, mask=image.split()[-1])
            image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    if image.width > MAX_IMAGE_SIZE[0] or image.height > MAX_IMAGE_SIZE[1]:
        image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, 'JPEG', quality=JPG_QUALITY, optimize=True)

    return output_path

def create_thumbnail(source_path: Path, thumb_path: Path, max_size: Tuple[int, int] = THUMBNAIL_MAX_SIZE) -> Path:
    image = Image.open(source_path)

    if image.mode != 'RGB':
        image = image.convert('RGB')

    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(thumb_path, 'JPEG', quality=85, optimize=True)

    return thumb_path

async def generate_image_with_qwen(
    prompt: str,
    output_path: Path,
    task_id: str,
    negative_prompt: str = "",
    size: str = None,
    seed: int = None
) -> Tuple[Path, Path]:
    print(f"\n{'='*60}")
    print(f"[Qwen-Image API调用]")
    print(f"  Prompt: {prompt[:150]}...")
    if negative_prompt:
        print(f"  Negative: {negative_prompt[:100]}...")
    print(f"{'='*60}\n")

    try:
        call_params = {
            'api_key': DASHSCOPE_API_KEY,
            'model': QWEN_MODEL_NAME,
            'prompt': prompt,
        }

        if 'n' in DEFAULT_QWEN_PARAMS:
            call_params['n'] = DEFAULT_QWEN_PARAMS['n']

        if size:
            call_params['size'] = size
        elif 'size' in DEFAULT_QWEN_PARAMS:
            call_params['size'] = DEFAULT_QWEN_PARAMS['size']

        if 'prompt_extend' in DEFAULT_QWEN_PARAMS:
            call_params['prompt_extend'] = DEFAULT_QWEN_PARAMS['prompt_extend']

        if 'watermark' in DEFAULT_QWEN_PARAMS:
            call_params['watermark'] = DEFAULT_QWEN_PARAMS['watermark']

        if seed is not None:
            call_params['seed'] = seed
        elif 'seed' in DEFAULT_QWEN_PARAMS:
            call_params['seed'] = DEFAULT_QWEN_PARAMS['seed']

        if negative_prompt:
            call_params['negative_prompt'] = negative_prompt

        print(f"  参数:")
        print(f"    • model: {call_params.get('model')}")
        print(f"    • size: {call_params.get('size')}")
        print(f"    • prompt_extend: {call_params.get('prompt_extend')}")
        print(f"    • seed: {call_params.get('seed', 'random')}")
        print(f"  正在调用 DashScope API...")

        loop = asyncio.get_event_loop()

        def call_api():
            return ImageSynthesis.call(**call_params)

        response = await loop.run_in_executor(generation_executor, call_api)

        if response.status_code != HTTPStatus.OK:
            error_msg = f"API调用失败: status_code={response.status_code}, code={response.code}, message={response.message}"
            print(f"  ❌ {error_msg}")
            raise RuntimeError(error_msg)

        print(f"  ✓ API调用成功")
        print(f"    task_id: {response.output.task_id}")
        print(f"    task_status: {response.output.task_status}")

        if not response.output.results or len(response.output.results) == 0:
            raise ValueError("API返回结果为空")

        result = response.output.results[0]
        image_url = result.url

        print(f"  ✓ 图片生成成功")
        print(f"    URL: {image_url[:100]}...")

        if call_params.get('prompt_extend') and hasattr(result, 'actual_prompt'):
            print(f"    改写后Prompt: {result.actual_prompt[:100]}...")

        print(f"  正在下载图片...")
        full_path = download_image_from_url(image_url, output_path)
        print(f"    ✓ 已保存: {full_path}")

        thumb_filename = f"thumb_{output_path.name}"
        thumb_path = THUMBS_DIR / thumb_filename
        thumb_path = create_thumbnail(full_path, thumb_path)
        print(f"    ✓ 缩略图: {thumb_path}")

        print(f"\n{'='*60}")
        print(f"[生成完成]")
        print(f"  完整图片: {full_path}")
        print(f"  缩略图: {thumb_path}")
        print(f"{'='*60}\n")

        return full_path, thumb_path

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
                generate_image_with_qwen(
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

        print(f"  [{task_id[:8]}] ✅ 完成！")

    except Exception as e:
        print(f"  [{task_id[:8]}] ❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()

        try:
            from crud import update_task_status
            update_task_status(db, task_id, "failed")
            db.commit()
        except:
            pass

    finally:
        db.close()

        with generation_lock:
            if task_id in active_generations:
                del active_generations[task_id]

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

async def test_qwen_api():
    print("="*60)
    print("Qwen-Image API测试")
    print("="*60)

    if not DASHSCOPE_API_KEY:
        print("✗ DASHSCOPE_API_KEY未设置")
        return

    print(f"✓ API Key已设置: {DASHSCOPE_API_KEY[:15]}...")
    print(f"✓ 模型: {QWEN_MODEL_NAME}")
    print(f"✓ 配置:")
    print(f"  - 固定种子: {DEFAULT_QWEN_PARAMS.get('seed', '随机')}")
    print(f"  - Prompt改写: {'开启' if DEFAULT_QWEN_PARAMS.get('prompt_extend', True) else '关闭'}")
    print(f"  - 图片尺寸: {DEFAULT_QWEN_PARAMS.get('size', '1328*1328')}")

    test_prompt = "一幅典雅庄重的中式对联，悬挂于古典厅堂中，房间布置宁静雅致，桌上摆放青花瓷器"
    test_output = GENERATIONS_DIR / "test_qwen.jpg"

    try:
        print("\n开始测试生成...")
        full_path, thumb_path = await generate_image_with_qwen(
            prompt=test_prompt,
            output_path=test_output,
            task_id="test-001"
        )
        print(f"\n✓ 测试成功！")
        print(f"  图片: {full_path}")
        print(f"  缩略图: {thumb_path}")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")

    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_qwen_api())
