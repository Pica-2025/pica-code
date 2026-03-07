import numpy as np
import cv2
from pathlib import Path
from typing import Dict, Tuple
import json
import pickle

def load_linear_model():
    try:
        model_path = Path(__file__).parent / "simple_linear_model.pkl"
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        return model_data
    except FileNotFoundError:
        print("⚠️  警告: 找不到训练好的模型文件 simple_linear_model.pkl")
        print("   将使用默认权重")
        return None
    except Exception as e:
        print(f"⚠️  警告: 加载评分模型失败: {e}")
        return None

LINEAR_MODEL = load_linear_model()

DEFAULT_WEIGHTS = {
    'dino': 28.40,
    'hsv': 15.34,
    'structure': 5.07,
    'intercept': 44.66
}

def compute_dino_similarity(target_path: Path, generated_path: Path) -> float:
    try:
        from PIL import Image
        from auto_scorer_dino import calculate_dino_similarity

        target_img = Image.open(target_path).convert('RGB')
        generated_img = Image.open(generated_path).convert('RGB')

        similarity = calculate_dino_similarity(target_img, generated_img)

        return similarity

    except Exception as e:
        print(f"DINO相似度计算错误: {e}")
        import traceback
        traceback.print_exc()
        return 0.5

def compute_hsv_similarity(target_path: Path, generated_path: Path) -> float:
    try:
        target_img = cv2.imread(str(target_path))
        generated_img = cv2.imread(str(generated_path))

        if target_img is None or generated_img is None:
            return 0.0

        target_img = cv2.resize(target_img, (256, 256))
        generated_img = cv2.resize(generated_img, (256, 256))

        target_hsv = cv2.cvtColor(target_img, cv2.COLOR_BGR2HSV)
        generated_hsv = cv2.cvtColor(generated_img, cv2.COLOR_BGR2HSV)

        h_bins = 50
        s_bins = 60
        histSize = [h_bins, s_bins]
        h_ranges = [0, 180]
        s_ranges = [0, 256]
        ranges = h_ranges + s_ranges
        channels = [0, 1]

        target_hist = cv2.calcHist([target_hsv], channels, None, histSize, ranges, accumulate=False)
        generated_hist = cv2.calcHist([generated_hsv], channels, None, histSize, ranges, accumulate=False)

        cv2.normalize(target_hist, target_hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(generated_hist, generated_hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        similarity = cv2.compareHist(target_hist, generated_hist, cv2.HISTCMP_BHATTACHARYYA)

        similarity = 1.0 - similarity

        return max(0.0, min(1.0, similarity))

    except Exception as e:
        print(f"HSV相似度计算错误: {e}")
        return 0.5

def compute_structure_similarity(target_path: Path, generated_path: Path) -> float:
    try:
        from skimage.metrics import structural_similarity as ssim

        target_img = cv2.imread(str(target_path))
        generated_img = cv2.imread(str(generated_path))

        if target_img is None or generated_img is None:
            return 0.0

        target_img = cv2.resize(target_img, (256, 256))
        generated_img = cv2.resize(generated_img, (256, 256))

        target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
        generated_gray = cv2.cvtColor(generated_img, cv2.COLOR_BGR2GRAY)

        similarity, _ = ssim(target_gray, generated_gray, full=True)

        return max(0.0, min(1.0, similarity))

    except Exception as e:
        print(f"结构相似度计算错误: {e}")
        try:
            target_img = cv2.imread(str(target_path), cv2.IMREAD_GRAYSCALE)
            generated_img = cv2.imread(str(generated_path), cv2.IMREAD_GRAYSCALE)

            target_img = cv2.resize(target_img, (256, 256))
            generated_img = cv2.resize(generated_img, (256, 256))

            diff = np.abs(target_img.astype(float) - generated_img.astype(float))
            similarity = 1.0 - (diff.mean() / 255.0)

            return max(0.0, min(1.0, similarity))
        except:
            return 0.5

def predict_score_with_linear_model(dino: float, hsv: float, structure: float) -> float:
    if LINEAR_MODEL is not None:
        scaler = LINEAR_MODEL['scaler']
        model = LINEAR_MODEL['model']

        X = np.array([[dino, hsv, structure]])

        X_scaled = scaler.transform(X)

        score = model.predict(X_scaled)[0]

        score = np.clip(score, 0, 100)

        return float(score)
    else:
        score = (
            DEFAULT_WEIGHTS['dino'] * dino +
            DEFAULT_WEIGHTS['hsv'] * hsv +
            DEFAULT_WEIGHTS['structure'] * structure +
            DEFAULT_WEIGHTS['intercept']
        )

        score = np.clip(score, 0, 100)
        return float(score)

def compute_multi_dimensional_scores(
    target_path: Path,
    generated_path: Path,
    verbose: bool = False
) -> Dict[str, float]:
    if verbose:
        print(f"\n{'='*60}")
        print(f"[多维度相似度计算 - 线性回归模型]")
        print(f"  目标图: {target_path.name}")
        print(f"  生成图: {generated_path.name}")
        print(f"{'='*60}\n")

    dino_score = compute_dino_similarity(target_path, generated_path)
    hsv_score = compute_hsv_similarity(target_path, generated_path)
    structure_score = compute_structure_similarity(target_path, generated_path)

    if verbose:
        print(f"原始分数 (0-1 范围):")
        print(f"  DINOv2特征相似度: {dino_score:.4f}")
        print(f"  HSV颜色相似度:    {hsv_score:.4f}")
        print(f"  结构相似度:       {structure_score:.4f}")

    combined_score = predict_score_with_linear_model(dino_score, hsv_score, structure_score)

    if verbose:
        print(f"\n线性回归模型预测:")
        if LINEAR_MODEL is not None:
            print(f"  使用训练好的模型: simple_linear_model.pkl")
            print(f"  R² = {LINEAR_MODEL.get('r2_score', 'N/A')}")
            print(f"  Spearman ρ = {LINEAR_MODEL.get('spearman_rho', 'N/A')}")
        else:
            print(f"  使用默认权重（模型未加载）")
        print(f"  综合分数: {combined_score:.2f}/100")
        print(f"{'='*60}\n")

    return {
        "dino_score": round(dino_score, 4),
        "hsv_score": round(hsv_score, 4),
        "structure_score": round(structure_score, 4),
        "combined_score": round(combined_score, 2)
    }

def get_score_details_json(scores: Dict[str, float]) -> str:
    details = {
        "dimensions": {
            "dino": {
                "name": "DINOv2特征相似度",
                "score": scores["dino_score"],
                "weight": 27.52,
                "description": "基于深度学习特征的视觉相似度"
            },
            "hsv": {
                "name": "HSV颜色相似度",
                "score": scores["hsv_score"],
                "weight": 14.88,
                "description": "色调、饱和度、亮度的相似程度"
            },
            "structure": {
                "name": "结构相似度",
                "score": scores["structure_score"],
                "weight": 5.12,
                "description": "图像结构和纹理的相似程度"
            }
        },
        "combined_score": scores["combined_score"],
        "method": "simple_linear_regression",
        "model_info": {
            "type": "Linear Regression with MinMaxScaler",
            "r2_score": LINEAR_MODEL.get('r2_score') if LINEAR_MODEL else None,
            "spearman_rho": LINEAR_MODEL.get('spearman_rho') if LINEAR_MODEL else None
        }
    }
    return json.dumps(details, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("用法: python auto_scorer_multi.py <目标图路径> <生成图路径>")
        sys.exit(1)

    target = Path(sys.argv[1])
    generated = Path(sys.argv[2])

    if not target.exists():
        print(f"错误: 目标图不存在 - {target}")
        sys.exit(1)

    if not generated.exists():
        print(f"错误: 生成图不存在 - {generated}")
        sys.exit(1)

    scores = compute_multi_dimensional_scores(target, generated, verbose=True)

    print("\n详细信息JSON:")
    print(get_score_details_json(scores))
