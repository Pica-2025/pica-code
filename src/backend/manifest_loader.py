import csv
from pathlib import Path
from typing import List, Dict, Optional

from config import MANIFEST_PATH

def load_manifest() -> List[Dict[str, str]]:
    images = []

    if not MANIFEST_PATH.exists():
        print(f"⚠️ 警告：清单文件不存在 {MANIFEST_PATH}")
        return images

    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            images.append(row)

    print(f"✓ 已加载 {len(images)} 张图片的清单")
    return images

def get_image_by_filename(filename: str) -> Optional[Dict[str, str]]:
    manifest = load_manifest()
    for img in manifest:
        if img["filename"] == filename:
            return img
    return None

def get_image_by_index(index: int) -> Optional[Dict[str, str]]:
    manifest = load_manifest()
    if 0 <= index < len(manifest):
        return manifest[index]
    return None

def get_total_count() -> int:
    return len(load_manifest())

def load_targets_manifest():
    import pandas as pd

    images = load_manifest()
    if not images:
        return pd.DataFrame(columns=['index', 'filename', 'ground_truth', 'difficulty'])

    df = pd.DataFrame(images)

    if 'index' not in df.columns:
        df['index'] = range(1, len(df) + 1)

    if 'ground_truth' not in df.columns:
        df['ground_truth'] = ''

    if 'difficulty' not in df.columns:
        df['difficulty'] = ''

    return df
