
import random
from typing import List
from pathlib import Path
from sqlalchemy.orm import Session

from config import (
    TASKS_PER_SESSION,
    QWEN_TASKS_COUNT,
    GEMINI_TASKS_COUNT,
    QWEN_TARGET_RANGE,
    GEMINI_TARGET_RANGE,
    TARGETS_DIR
)
from models import Task
from crud import create_task
from manifest_loader import load_manifest

def assign_tasks_to_session(db: Session, session_id: str) -> List[Task]:
    manifest = load_manifest()

    if len(manifest) < QWEN_TARGET_RANGE[1]:
        raise ValueError(
            f"Qwen图片数量不足，需要至少 {QWEN_TARGET_RANGE[1]} 张，"
            f"当前只有 {len(manifest)} 张"
        )

    if len(manifest) < GEMINI_TARGET_RANGE[1]:
        raise ValueError(
            f"Gemini图片数量不足，需要至少 {GEMINI_TARGET_RANGE[1]} 张，"
            f"当前只有 {len(manifest)} 张"
        )

    qwen_images = []
    gemini_images = []

    for img_info in manifest:
        img_index = int(img_info.get("index", 0))

        if QWEN_TARGET_RANGE[0] <= img_index <= QWEN_TARGET_RANGE[1]:
            qwen_images.append(img_info)
        elif GEMINI_TARGET_RANGE[0] <= img_index <= GEMINI_TARGET_RANGE[1]:
            gemini_images.append(img_info)

    print(f"  Qwen图片池: {len(qwen_images)} 张 (index {QWEN_TARGET_RANGE[0]}-{QWEN_TARGET_RANGE[1]})")
    print(f"  Gemini图片池: {len(gemini_images)} 张 (index {GEMINI_TARGET_RANGE[0]}-{GEMINI_TARGET_RANGE[1]})")

    if len(qwen_images) < QWEN_TASKS_COUNT:
        raise ValueError(
            f"Qwen图片数量不足，需要 {QWEN_TASKS_COUNT} 张，"
            f"当前只有 {len(qwen_images)} 张"
        )

    selected_qwen = random.sample(qwen_images, QWEN_TASKS_COUNT)

    selected_prompt_ids = set()
    for img in selected_qwen:
        if 'prompt_id' in img:
            selected_prompt_ids.add(int(img['prompt_id']))
        else:
            img_index = int(img.get("index", 0))
            prompt_id = ((img_index - 1) % 30) + 1
            selected_prompt_ids.add(prompt_id)

    print(f"  已选Qwen图片的prompt_id: {sorted(selected_prompt_ids)}")

    available_gemini = []
    for img in gemini_images:
        if 'prompt_id' in img:
            prompt_id = int(img['prompt_id'])
        else:
            img_index = int(img.get("index", 0))
            prompt_id = ((img_index - 1) % 30) + 1

        if prompt_id not in selected_prompt_ids:
            available_gemini.append(img)

    print(f"  可用Gemini图片: {len(available_gemini)} 张（已排除 {QWEN_TASKS_COUNT} 个重复prompt）")

    if len(available_gemini) < GEMINI_TASKS_COUNT:
        raise ValueError(
            f"可用Gemini图片不足，需要 {GEMINI_TASKS_COUNT} 张，"
            f"当前只有 {len(available_gemini)} 张（排除重复后）"
        )

    selected_gemini = random.sample(available_gemini, GEMINI_TASKS_COUNT)

    all_selected = []

    for img_info in selected_qwen:
        all_selected.append({
            'model_type': 'qwen',
            'img_info': img_info
        })

    for img_info in selected_gemini:
        all_selected.append({
            'model_type': 'gemini',
            'img_info': img_info
        })

    random.shuffle(all_selected)

    tasks = []
    for round_num, item in enumerate(all_selected, start=1):
        model_type = item['model_type']
        img_info = item['img_info']

        original_index = int(img_info.get("index", round_num))

        task = create_task(
            db=db,
            session_id=session_id,
            round_number=round_num,
            target_index=original_index,
            target_filename=img_info["filename"],
            target_sha256=img_info.get("sha256", ""),
            ground_truth=img_info.get("ground_truth", ""),
            difficulty=img_info.get("difficulty", "medium"),
            model_type=model_type
        )
        tasks.append(task)

        print(f"    Round {round_num}: {img_info['filename']} ({model_type})")

    print(f"✓ 已为会话 {session_id} 分配 {len(tasks)} 个任务")
    print(f"  - Qwen任务: {sum(1 for t in tasks if t.model_type == 'qwen')}")
    print(f"  - Gemini任务: {sum(1 for t in tasks if t.model_type == 'gemini')}")

    return tasks

def get_target_image_path(filename: str) -> Path:
    return TARGETS_DIR / filename

def get_target_image_url(filename: str) -> str:
    return f"/data/targets/{filename}"

if __name__ == "__main__":
    print("=" * 60)
    print("双模型任务分配逻辑测试")
    print("=" * 60)

    print("\n【测试1：加载manifest】")
    try:
        from manifest_loader import load_manifest, get_total_count

        manifest = load_manifest()
        total = get_total_count()
        print(f"✓ 加载成功，共 {total} 张图片")

        qwen_count = sum(1 for img in manifest
                        if QWEN_TARGET_RANGE[0] <= int(img.get('index', 0)) <= QWEN_TARGET_RANGE[1])
        gemini_count = sum(1 for img in manifest
                          if GEMINI_TARGET_RANGE[0] <= int(img.get('index', 0)) <= GEMINI_TARGET_RANGE[1])

        print(f"  - Qwen图片 ({QWEN_TARGET_RANGE[0]}-{QWEN_TARGET_RANGE[1]}): {qwen_count} 张")
        print(f"  - Gemini图片 ({GEMINI_TARGET_RANGE[0]}-{GEMINI_TARGET_RANGE[1]}): {gemini_count} 张")

    except Exception as e:
        print(f"✗ 加载失败: {e}")

    print(f"\n【测试2：模拟分配任务】")
    print(f"每个session分配 {TASKS_PER_SESSION} 个任务：")
    print(f"  - Qwen: {QWEN_TASKS_COUNT} 个")
    print(f"  - Gemini: {GEMINI_TASKS_COUNT} 个")
    print()

    try:
        qwen_pool = [img for img in manifest
                     if QWEN_TARGET_RANGE[0] <= int(img.get('index', 0)) <= QWEN_TARGET_RANGE[1]]
        gemini_pool = [img for img in manifest
                       if GEMINI_TARGET_RANGE[0] <= int(img.get('index', 0)) <= GEMINI_TARGET_RANGE[1]]

        selected_qwen = random.sample(qwen_pool, QWEN_TASKS_COUNT)

        selected_prompt_ids = set()
        for img in selected_qwen:
            if 'prompt_id' in img:
                selected_prompt_ids.add(img['prompt_id'])
            else:
                img_index = int(img.get("index", 0))
                prompt_id = ((img_index - 1) % 30) + 1
                selected_prompt_ids.add(prompt_id)

        print(f"✓ 已选Qwen图片:")
        for i, img in enumerate(selected_qwen, 1):
            idx = int(img.get('index', 0))
            pid = ((idx - 1) % 30) + 1 if 'prompt_id' not in img else img['prompt_id']
            print(f"  {i}. {img['filename']} (index={idx}, prompt_id={pid})")

        print(f"\n✓ 已选prompt_id: {sorted(selected_prompt_ids)}")

        available_gemini = []
        for img in gemini_pool:
            if 'prompt_id' in img:
                prompt_id = img['prompt_id']
            else:
                img_index = int(img.get("index", 0))
                prompt_id = ((img_index - 1) % 30) + 1

            if prompt_id not in selected_prompt_ids:
                available_gemini.append(img)

        print(f"\n✓ 可用Gemini图片: {len(available_gemini)} 张")

        selected_gemini = random.sample(available_gemini, GEMINI_TASKS_COUNT)

        print(f"\n✓ 已选Gemini图片:")
        for i, img in enumerate(selected_gemini, 1):
            idx = int(img.get('index', 0))
            pid = ((idx - 1) % 30) + 1 if 'prompt_id' not in img else img['prompt_id']
            print(f"  {i}. {img['filename']} (index={idx}, prompt_id={pid})")

        gemini_prompt_ids = set()
        for img in selected_gemini:
            if 'prompt_id' in img:
                pid = img['prompt_id']
            else:
                idx = int(img.get("index", 0))
                pid = ((idx - 1) % 30) + 1
            gemini_prompt_ids.add(pid)

        overlap = selected_prompt_ids & gemini_prompt_ids
        if overlap:
            print(f"\n❌ 错误：发现重复的prompt_id: {overlap}")
        else:
            print(f"\n✅ 验证通过：Qwen和Gemini没有重复的prompt")

    except Exception as e:
        print(f"✗ 模拟失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
