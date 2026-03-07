
import torch
import numpy as np
from PIL import Image
from typing import Union
from pathlib import Path

_dino_model = None
_dino_processor = None
_device = None

def init_dino_model():
    global _dino_model, _dino_processor, _device

    if _dino_model is not None:
        return

    print("正在加载 DINO v2 模型...")

    try:
        import transformers, inspect
        print(f"  transformers 版本: {transformers.__version__}")
        print(f"  transformers 路径: {inspect.getfile(transformers)}")

        try:
            from transformers import AutoImageProcessor, AutoModel
            print("  使用 AutoImageProcessor")
        except ImportError:
            print("  ⚠️ 找不到 AutoImageProcessor，尝试使用 AutoFeatureExtractor 作为替代")
            from transformers import AutoFeatureExtractor as AutoImageProcessor, AutoModel

        _device = "cpu"
        print(f"  使用设备: {_device} (避免 GPU 显存冲突)")

        model_name = "facebook/dinov2-small"

        _dino_processor = AutoImageProcessor.from_pretrained(model_name)
        _dino_model = AutoModel.from_pretrained(model_name).to(_device)
        print()
        print("  ✓ DINO v2 模型加载完成")

    except Exception as e:
        import traceback
        print(f"  ❌ DINO v2 模型加载失败: {e}")
        traceback.print_exc()
        raise

def calculate_dino_similarity(image1: Image.Image, image2: Image.Image) -> float:
    init_dino_model()

    try:
        inputs1 = _dino_processor(images=image1, return_tensors="pt").to(_device)
        inputs2 = _dino_processor(images=image2, return_tensors="pt").to(_device)

        with torch.no_grad():
            outputs1 = _dino_model(**inputs1)
            outputs2 = _dino_model(**inputs2)

            features1 = outputs1.last_hidden_state[:, 0]
            features2 = outputs2.last_hidden_state[:, 0]

            features1 = features1 / features1.norm(dim=-1, keepdim=True)
            features2 = features2 / features2.norm(dim=-1, keepdim=True)

            similarity = (features1 * features2).sum().item()

        similarity = (similarity + 1) / 2

        return max(0.0, min(1.0, similarity))

    except Exception as e:
        print(f"  ⚠️ DINO 计算失败: {e}")
        return 0.5

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        img1 = Image.open(sys.argv[1]).convert('RGB')
        img2 = Image.open(sys.argv[2]).convert('RGB')

        score = calculate_dino_similarity(img1, img2)
        print(f"DINO v2 相似度: {score:.3f}")
    else:
        print("用法: python auto_scorer_dino.py <图片1> <图片2>")
