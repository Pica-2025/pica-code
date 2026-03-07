#!/usr/bin/env python3
"""
最简单的线性回归方案：
1. 标准化三个维度
2. 线性回归
3. 更新数据库
2dc4be22-e04d-4f56-bd04-d01dd1e58335

47f9b6ce-8612-4653-aeb0-d4491399d179

9e93614a-d00a-4c01-ae3e-f0794c1a7714
用法：
python simple_linear_regression.py --mode train     # 训练
python simple_linear_regression.py --mode test      # 测试
python simple_linear_regression.py --mode update    # 更新数据库
"""

import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from database import get_db
from models import ImageVersion, Task
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import cross_val_score
from scipy.stats import spearmanr
import pickle
from datetime import datetime


def load_data(session_ids=None):
    """加载数据"""
    db = next(get_db())
    
    try:
        query = db.query(ImageVersion).filter(
            ImageVersion.dino_score.isnot(None),
            ImageVersion.hsv_score.isnot(None),
            ImageVersion.structure_score.isnot(None),
            ImageVersion.user_manual_score.isnot(None)
        )
        
        if session_ids:
            query = query.join(Task, ImageVersion.task_id == Task.task_id).filter(
                Task.session_id.in_(session_ids)
            )
        
        versions = query.all()
        
        X = np.column_stack([
            [v.dino_score for v in versions],
            [v.hsv_score for v in versions],
            [v.structure_score for v in versions]
        ])
        y = np.array([v.user_manual_score for v in versions])
        
        return X, y, versions
    finally:
        db.close()


def train_model(X, y):
    """训练模型"""
    
    print("="*80)
    print("训练线性回归模型")
    print("="*80)
    print()
    
    print(f"训练数据: {len(y)} 条")
    print()
    
    # 步骤1: 标准化
    print("步骤1: MinMax标准化")
    print("-" * 60)
    
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"原始范围:")
    print(f"  DINO:      [{X[:, 0].min():.3f}, {X[:, 0].max():.3f}]")
    print(f"  HSV:       [{X[:, 1].min():.3f}, {X[:, 1].max():.3f}]")
    print(f"  Structure: [{X[:, 2].min():.3f}, {X[:, 2].max():.3f}]")
    print()
    
    print(f"标准化后: 全部 [0.000, 1.000]")
    print()
    
    # 步骤2: 线性回归
    print("步骤2: 线性回归")
    print("-" * 60)
    
    model = LinearRegression()
    model.fit(X_scaled, y)
    
    print(f"拟合方程:")
    print(f"  用户评分 = {model.coef_[0]:.4f} × scaled_DINO")
    print(f"           + {model.coef_[1]:.4f} × scaled_HSV")
    print(f"           + {model.coef_[2]:.4f} × scaled_Structure")
    print(f"           + {model.intercept_:.4f}")
    print()
    
    # 相对权重
    total_abs = abs(model.coef_[0]) + abs(model.coef_[1]) + abs(model.coef_[2])
    print(f"相对权重:")
    print(f"  DINO:      {abs(model.coef_[0])/total_abs*100:>5.1f}%")
    print(f"  HSV:       {abs(model.coef_[1])/total_abs*100:>5.1f}%")
    print(f"  Structure: {abs(model.coef_[2])/total_abs*100:>5.1f}%")
    print()
    
    # 步骤3: 评估
    print("步骤3: 模型评估")
    print("-" * 60)
    
    y_pred = model.predict(X_scaled)
    
    r2 = r2_score(y, y_pred)
    rho, p = spearmanr(y, y_pred)
    
    print(f"训练集性能:")
    print(f"  R²:         {r2:.4f}")
    print(f"  Spearman ρ: {rho:.4f} (p={p:.2e})")
    print()
    
    # 交叉验证
    cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='r2')
    print(f"交叉验证 (5折):")
    print(f"  平均R²:     {cv_scores.mean():.4f}")
    print(f"  标准差:     {cv_scores.std():.4f}")
    print()
    
    overfit = r2 - cv_scores.mean()
    print(f"过拟合分析:")
    print(f"  训练R² - 交叉验证R² = {overfit:.4f}")
    if overfit < 0.1:
        print(f"  ✅ 优秀，几乎不过拟合")
    elif overfit < 0.3:
        print(f"  ✅ 良好")
    else:
        print(f"  ⚠️  需要注意")
    print()
    
    return {
        'scaler': scaler,
        'model': model,
        'metrics': {
            'r2': r2,
            'spearman_rho': rho,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
    }


def save_model(result, filepath='simple_linear_model.pkl'):
    """保存模型"""
    
    print("="*80)
    print("保存模型")
    print("="*80)
    print()
    
    with open(filepath, 'wb') as f:
        pickle.dump(result, f)
    
    print(f"✅ 模型已保存: {filepath}")
    print()
    print("模型包含:")
    print("  - MinMaxScaler (标准化器)")
    print("  - LinearRegression (线性回归)")
    print("  - 性能指标")
    print()


def load_model(filepath='simple_linear_model.pkl'):
    """加载模型"""
    
    with open(filepath, 'rb') as f:
        result = pickle.load(f)
    
    return result


def predict_score(model_data, dino, hsv, structure, scale_to_01=False):
    """
    预测单个样本
    
    Args:
        scale_to_01: 如果True，返回0-1；如果False，返回0-100
    """
    
    # 标准化
    X = np.array([[dino, hsv, structure]])
    X_scaled = model_data['scaler'].transform(X)
    
    # 预测
    score = model_data['model'].predict(X_scaled)[0]
    
    # Clip到[0, 100]
    score = np.clip(score, 0, 100)
    
    # 如果需要缩放到0-1
    if scale_to_01:
        score = score / 100.0
    
    return score


def test_model(model_data):
    """测试模型"""
    
    print("="*80)
    print("测试模型预测")
    print("="*80)
    print()
    
    test_cases = [
        {'name': '低质量', 'dino': 0.70, 'hsv': 0.20, 'structure': 0.05},
        {'name': '中等质量', 'dino': 0.85, 'hsv': 0.45, 'structure': 0.15},
        {'name': '高质量', 'dino': 0.92, 'hsv': 0.68, 'structure': 0.32},
    ]
    
    print(f"{'场景':<15} {'DINO':<8} {'HSV':<8} {'Structure':<12} {'预测(0-100)':<15} {'预测(0-1)'}")
    print("-" * 75)
    
    for case in test_cases:
        score_100 = predict_score(
            model_data,
            case['dino'],
            case['hsv'],
            case['structure'],
            scale_to_01=False
        )
        score_01 = predict_score(
            model_data,
            case['dino'],
            case['hsv'],
            case['structure'],
            scale_to_01=True
        )
        print(f"{case['name']:<15} {case['dino']:<8.3f} {case['hsv']:<8.3f} "
              f"{case['structure']:<12.3f} {score_100:>10.1f}%      {score_01:>10.3f}")
    
    print()
    print("💡 数据库将存储0-1范围的值")
    print()


def update_database(model_data, sessions=None, dry_run=True):
    """更新数据库"""
    
    print("="*80)
    if dry_run:
        print("模拟运行（Dry Run）")
    else:
        print("更新数据库")
    print("="*80)
    print()
    
    db = next(get_db())
    
    try:
        # 查询要更新的数据
        query = db.query(ImageVersion).filter(
            ImageVersion.dino_score.isnot(None),
            ImageVersion.hsv_score.isnot(None),
            ImageVersion.structure_score.isnot(None)
        )
        
        if sessions:
            query = query.join(Task, ImageVersion.task_id == Task.task_id).filter(
                Task.session_id.in_(sessions)
            )
        
        versions = query.all()
        
        print(f"将更新 {len(versions)} 条记录")
        print()
        
        if not dry_run:
            # 备份
            backup_file = f"ai_scores_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(backup_file, 'w') as f:
                f.write("version_id,old_score\n")
                for v in versions:
                    f.write(f"{v.version_id},{v.ai_similarity_score}\n")
            print(f"✅ 已备份到: {backup_file}")
            print()
        
        # 计算新分数
        new_scores_100 = []  # 0-100 for display
        new_scores_01 = []   # 0-1 for database
        old_scores = []
        
        for v in versions:
            # 计算0-100的分数（用于显示）
            score_100 = predict_score(
                model_data,
                v.dino_score,
                v.hsv_score,
                v.structure_score,
                scale_to_01=False
            )
            
            # 计算0-1的分数（用于数据库）
            score_01 = score_100 / 100.0
            
            new_scores_100.append(score_100)
            new_scores_01.append(score_01)
            old_scores.append(v.ai_similarity_score if v.ai_similarity_score else 0)
        
        new_scores_100 = np.array(new_scores_100)
        new_scores_01 = np.array(new_scores_01)
        old_scores = np.array(old_scores)
        
        # 统计（显示0-100）
        print("新评分统计 (0-100显示):")
        print(f"  范围:     [{new_scores_100.min():.1f}, {new_scores_100.max():.1f}]")
        print(f"  均值:     {new_scores_100.mean():.1f}")
        print(f"  中位数:   {np.median(new_scores_100):.1f}")
        print()
        
        print("新评分统计 (0-1存储):")
        print(f"  范围:     [{new_scores_01.min():.3f}, {new_scores_01.max():.3f}]")
        print(f"  均值:     {new_scores_01.mean():.3f}")
        print(f"  中位数:   {np.median(new_scores_01):.3f}")
        print()
        
        if not dry_run:
            print("评分分布 (0-100显示):")
            bins = [0, 20, 40, 60, 80, 100]
            labels = ['Terrible', 'Bad', 'OK', 'Fine', 'Great']
            for i in range(len(bins)-1):
                count = ((new_scores_100 >= bins[i]) & (new_scores_100 < bins[i+1])).sum()
                if i == len(bins)-2:
                    count = ((new_scores_100 >= bins[i]) & (new_scores_100 <= bins[i+1])).sum()
                pct = count / len(new_scores_100) * 100
                print(f"  {labels[i]:<10} [{bins[i]:>3}-{bins[i+1]:>3}): {count:>4} ({pct:>5.1f}%)")
            print()
        
        # 变化最大的前10条（对比旧的0-1值）
        changes = new_scores_01 - old_scores
        top_indices = np.argsort(np.abs(changes))[-10:][::-1]
        
        print("变化最大的前10条记录 (0-1存储):")
        print(f"{'版本ID':<12} {'旧分数(0-1)':<15} {'新分数(0-1)':<15} {'变化':<10} {'新分数(0-100)'}")
        print("-" * 70)
        for idx in top_indices:
            v = versions[idx]
            print(f"{v.version_id:<12} {old_scores[idx]:<15.3f} "
                  f"{new_scores_01[idx]:<15.3f} {changes[idx]:>+9.3f}  {new_scores_100[idx]:>6.1f}%")
        print()
        
        if dry_run:
            print("⚠️  这是模拟运行，数据库未修改")
            print("   使用 --mode update 真正更新数据库")
        else:
            # 确认
            print("⚠️  即将更新数据库！")
            confirm = input("输入 'YES' 确认更新: ")
            
            if confirm == 'YES':
                # 存储0-1的值到数据库
                for v, new_score in zip(versions, new_scores_01):
                    v.ai_similarity_score = float(new_score)  # 0-1范围
                
                db.commit()
                print()
                print(f"✅ 成功更新 {len(versions)} 条记录！")
                print(f"   (数据库存储0-1范围，前端显示时需要×100)")
                
                # 保存更新报告
                report_file = f"score_update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                with open(report_file, 'w') as f:
                    f.write("version_id,old_score_01,new_score_01,change_01,new_score_100\n")
                    for v, old, new_01, new_100 in zip(versions, old_scores, new_scores_01, new_scores_100):
                        f.write(f"{v.version_id},{old:.4f},{new_01:.4f},{new_01-old:.4f},{new_100:.2f}\n")
                print(f"✅ 更新报告已保存: {report_file}")
            else:
                print("❌ 取消更新")
        
        print()
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="简单线性回归")
    parser.add_argument('--mode', type=str, required=True,
                       choices=['train', 'test', 'dry-run', 'update'],
                       help='运行模式')
    parser.add_argument('--sessions', type=str, default=None,
                       help='用于训练的sessions (逗号分隔)')
    parser.add_argument('--model', type=str, default='simple_linear_model.pkl',
                       help='模型文件路径')
    
    args = parser.parse_args()
    
    # 处理sessions
    session_ids = None
    if args.sessions:
        session_ids = [s.strip() for s in args.sessions.split(',')]
    
    if args.mode == 'train':
        # 训练模式
        print("📊 加载训练数据...")
        X, y, _ = load_data(session_ids=session_ids)
        
        # 训练
        result = train_model(X, y)
        
        # 保存
        save_model(result, args.model)
        
        # 测试
        test_model(result)
        
    elif args.mode == 'test':
        # 测试模式
        print("📊 加载模型...")
        result = load_model(args.model)
        
        print(f"模型性能:")
        print(f"  R²:         {result['metrics']['r2']:.4f}")
        print(f"  Spearman ρ: {result['metrics']['spearman_rho']:.4f}")
        print()
        
        test_model(result)
        
    elif args.mode == 'dry-run':
        # 模拟运行
        print("📊 加载模型...")
        result = load_model(args.model)
        
        update_database(result, sessions=session_ids, dry_run=True)
        
    elif args.mode == 'update':
        # 真正更新
        print("📊 加载模型...")
        result = load_model(args.model)
        
        update_database(result, sessions=session_ids, dry_run=False)