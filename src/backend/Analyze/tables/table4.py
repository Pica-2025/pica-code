#!/usr/bin/env python3
"""
Table 4: Dimension Addition Effects
Extracted from: RQ2/rq2-2.py SECTION 5 + RQ2/rq2-3.py SECTION 8
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from color_config import COLORS, DIMENSION_COLORS, get_dimension_color
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10

DIMENSIONS = ['SpatialComposition', 'Style', 'SubjectScene',
              'LightingColor', 'DetailTexture', 'Others']


def analyze_dimension_addition_effects(all_versions, output_dir):
    """
    SECTION 5: AI SCORE CHANGE WHEN DIMENSIONS ARE ADDED
    (From RQ2/rq2-2.py)
    """
    print("\n" + "=" * 80)
    print("SECTION 5: AI SCORE CHANGE WHEN DIMENSIONS ARE ADDED")
    print("=" * 80)
    
    section5_dir = output_dir / "section05_dimension_addition_effects"
    section5_dir.mkdir(exist_ok=True)
    
    # Analyze each dimension
    addition_results = []
    
    for dim in DIMENSIONS:
        dim_lower = dim.lower()
        has_added_col = f'{dim_lower}_has_added'
        
        if has_added_col not in all_versions.columns:
            print(f"⚠️  Column {has_added_col} not found, skipping {dim}")
            continue
        
        # Filter versions where content was added to this dimension
        added = all_versions[all_versions[has_added_col] == True].copy()
        
        if len(added) == 0:
            print(f"⚠️  No additions found for {dim}")
            continue
        
        # Calculate AI score change statistics
        score_changes = added['ai_similarity_score_change'].dropna()
        
        if len(score_changes) < 5:
            print(f"⚠️  Insufficient data for {dim} ({len(score_changes)} records)")
            continue
        
        mean_change = score_changes.mean()
        median_change = score_changes.median()
        positive_count = (score_changes > 0).sum()
        negative_count = (score_changes < 0).sum()
        no_change_count = (score_changes == 0).sum()
        
        positive_pct = positive_count / len(score_changes) * 100
        
        addition_results.append({
            'dimension': dim,
            'n_additions': len(added),
            'mean_score_change': mean_change,
            'median_score_change': median_change,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'no_change_count': no_change_count,
            'positive_pct': positive_pct
        })
        
        print(f"\n{dim}:")
        print(f"  N additions: {len(added)}")
        print(f"  Mean AI score change: {mean_change:+.2f}")
        print(f"  Median AI score change: {median_change:+.1f}")
        print(f"  Positive: {positive_count} ({positive_pct:.1f}%)")
        print(f"  Negative: {negative_count}")
        print(f"  No change: {no_change_count}")
    
    results_df = pd.DataFrame(addition_results)
    
    # Save statistics
    stats_path = section5_dir / 'dimension_addition_effects_stats.csv'
    results_df.to_csv(stats_path, index=False)
    print(f"\n✓ Saved: {stats_path.name}")
    
    return results_df


def analyze_dimension_from_zero_to_one(all_versions, output_dir):
    """
    SECTION 8: SCORE PERFORMANCE WHEN DIMENSIONS GO FROM 0 TO 1
    (From RQ2/rq2-3.py)
    """
    print("\n" + "=" * 80)
    print("SECTION 8: SCORE PERFORMANCE WHEN DIMENSIONS GO FROM 0 TO 1")
    print("=" * 80)
    
    section8_dir = output_dir / "section08_dimension_zero_to_one"
    section8_dir.mkdir(exist_ok=True)
    
    # Analyze each dimension
    dimension_results = []
    
    for dim in DIMENSIONS:
        dim_lower = dim.lower()
        has_col = f'has_{dim_lower}'
        
        if has_col not in all_versions.columns:
            print(f"⚠️  Column {has_col} not found, skipping {dim}")
            continue
        
        # Find cases where dimension went from False to True
        zero_to_one_cases = []
        
        for task_id in all_versions['task_id'].unique():
            task_data = all_versions[all_versions['task_id'] == task_id].sort_values('version_number')
            
            if len(task_data) < 2:
                continue
            
            # Find first version where dimension became True
            for i in range(1, len(task_data)):
                prev_row = task_data.iloc[i-1]
                curr_row = task_data.iloc[i]
                
                # Check if dimension went from False to True
                prev_has = prev_row[has_col]
                curr_has = curr_row[has_col]
                
                if prev_has == False and curr_has == True:
                    # This is a 0→1 transition
                    zero_to_one_cases.append({
                        'task_id': task_id,
                        'version': curr_row['version_number'],
                        'ai_score': curr_row['ai_similarity_score'],
                        'ai_score_change': curr_row['ai_similarity_score_change'],
                        'user_score': curr_row['user_manual_score'],
                        'user_score_change': curr_row['user_manual_score_change']
                    })
                    break  # Only count first transition
        
        if len(zero_to_one_cases) == 0:
            print(f"⚠️  No 0→1 transitions found for {dim}")
            continue
        
        zero_to_one_df = pd.DataFrame(zero_to_one_cases)
        
        # Calculate statistics
        ai_scores = zero_to_one_df['ai_score'].dropna()
        ai_changes = zero_to_one_df['ai_score_change'].dropna()
        user_scores = zero_to_one_df['user_score'].dropna()
        
        mean_ai_score = ai_scores.mean()
        mean_ai_change = ai_changes.mean()
        mean_user_score = user_scores.mean()
        
        # Count positive/negative changes
        positive_count = (ai_changes > 0).sum()
        negative_count = (ai_changes < 0).sum()
        zero_count = (ai_changes == 0).sum()
        
        positive_pct = positive_count / len(ai_changes) * 100 if len(ai_changes) > 0 else 0
        
        dimension_results.append({
            'dimension': dim,
            'n_transitions': len(zero_to_one_cases),
            'mean_ai_score': mean_ai_score,
            'mean_ai_change': mean_ai_change,
            'mean_user_score': mean_user_score,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'zero_count': zero_count,
            'positive_pct': positive_pct
        })
        
        print(f"\n{dim}:")
        print(f"  N transitions (0→1): {len(zero_to_one_cases)}")
        print(f"  Mean AI score after adding: {mean_ai_score:.2f}")
        print(f"  Mean AI score change: {mean_ai_change:+.2f}")
        print(f"  Positive changes: {positive_count} ({positive_pct:.1f}%)")
        print(f"  Negative changes: {negative_count}")
    
    results_df = pd.DataFrame(dimension_results)
    
    # Save statistics
    stats_path = section8_dir / 'zero_to_one_stats.csv'
    results_df.to_csv(stats_path, index=False)
    print(f"\n✓ Saved: {stats_path.name}")
    
    return results_df


if __name__ == "__main__":
    print("=" * 80)
    print("TABLE 4: DIMENSION ADDITION EFFECTS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Setup paths - 从 Analyze/data/ 目录读取
    current_dir = Path(__file__).parent.parent  # Analyze/
    data_dir = current_dir / "data"
    output_dir = current_dir / "outputs" / "table4"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    all_versions_path = data_dir / "ultimate_dataset.csv"
    
    if not all_versions_path.exists():
        print(f"❌ ERROR: {all_versions_path.name} not found")
        print(f"   Expected location: {all_versions_path}")
        print("   Please run: python prepare_data.py")
        sys.exit(1)

    print(f"✓ Loading all versions data: {all_versions_path.name}")
    all_versions = pd.read_csv(all_versions_path)
    print(f"✓ Loaded {len(all_versions):,} version records\n")

    # Run SECTION 5 analysis
    addition_results = analyze_dimension_addition_effects(all_versions, output_dir)
    
    # Run SECTION 8 analysis
    transition_results = analyze_dimension_from_zero_to_one(all_versions, output_dir)

    print("\n" + "=" * 80)
    print("✅ TABLE 4 GENERATION COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

