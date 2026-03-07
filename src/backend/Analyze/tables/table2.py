#!/usr/bin/env python3
"""
Table 2: Dimension Impact Analysis
Extracted from: RQ1/rq1-3.py SECTION 6
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from color_config import COLORS, get_color, get_dimension_color, get_quality_color
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr, ttest_ind
from sklearn.linear_model import LinearRegression
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10

DIMENSIONS = ['SpatialComposition', 'Style', 'SubjectScene',
              'LightingColor', 'DetailTexture', 'Others']

QUALITY_METRICS = [
    'ai_similarity_score', 'user_manual_score', 'average_star_score',
    'style_score', 'object_count_score', 'perspective_score',
    'depth_background_score'
]

QUALITY_LABELS = {
    'ai_similarity_score': 'AI Similarity',
    'user_manual_score': 'User Manual',
    'average_star_score': 'Average Star',
    'style_score': 'Style',
    'object_count_score': 'Object Count',
    'perspective_score': 'Perspective',
    'depth_background_score': 'Depth & BG'
}


def analyze_dimension_impact(df, output_dir):
    """
    SECTION 6: DIMENSION IMPACT ANALYSIS
    """
    print("=" * 80)
    print("SECTION 6: DIMENSION IMPACT ANALYSIS ⭐⭐⭐⭐⭐")
    print("=" * 80)

    section6_dir = output_dir / "section06"
    section6_dir.mkdir(exist_ok=True)

    print("\nPerforming t-tests for dimension presence vs quality...")

    # T-test for each dimension × quality metric
    impact_results = []
    universal_dims = []  # Record 100% presence dimensions

    for dim in DIMENSIONS:
        has_col = f'has_{dim.lower()}'
        
        # Check if 100% present
        presence_rate = df[has_col].mean()
        
        for metric in QUALITY_METRICS:
            # Split into has/doesn't have
            has_dim = df[df[has_col] == True][metric].dropna()
            no_dim = df[df[has_col] == False][metric].dropna()
            
            if len(no_dim) == 0:  # 100% present case
                if metric == QUALITY_METRICS[0]:  # Record only once
                    universal_dims.append({
                        'Dimension': dim,
                        'Presence_Rate': presence_rate * 100,
                        'Metrics': {}
                    })
                
                # Record average for this metric
                universal_dims[-1]['Metrics'][metric] = has_dim.mean()
                
                # Don't add to impact_results since we can't calculate diff
                continue
                
            if len(has_dim) > 0 and len(no_dim) > 0:
                # T-test
                t_stat, p_val = ttest_ind(has_dim, no_dim)
                mean_diff = has_dim.mean() - no_dim.mean()
                
                impact_results.append({
                    'Dimension': dim,
                    'Quality_Metric': QUALITY_LABELS[metric],
                    'Has_Mean': has_dim.mean(),
                    'No_Mean': no_dim.mean(),
                    'Difference': mean_diff,
                    't_statistic': t_stat,
                    'p_value': p_val,
                    'Significant': 'Yes' if p_val < 0.05 else 'No',
                    'N_Has': len(has_dim),
                    'N_No': len(no_dim)
                })

    impact_df = pd.DataFrame(impact_results)
    impact_df.to_csv(section6_dir / 'dimension_impact_details.csv', index=False)

    # Save 100% presence dimensions
    if universal_dims:
        universal_df = pd.DataFrame([
            {
                'Dimension': d['Dimension'],
                'Presence_Rate_%': d['Presence_Rate'],
                **{QUALITY_LABELS[m]: v for m, v in d['Metrics'].items()}
            }
            for d in universal_dims
        ])
        universal_df.to_csv(section6_dir / 'universal_dimensions.csv', index=False)
        print(f"\n✓ Found {len(universal_dims)} dimension(s) with 100% presence:")
        for d in universal_dims:
            print(f"  - {d['Dimension']}: {d['Presence_Rate']:.1f}%")

    # Print summary
    print("\nSignificant impacts (p < 0.05):")
    sig_impacts = impact_df[impact_df['Significant'] == 'Yes'].sort_values(
        'Difference', ascending=False, key=abs
    )

    for _, row in sig_impacts.head(10).iterrows():
        print(f"  {row['Dimension']:20s} → {row['Quality_Metric']:15s}: "
              f"{row['Difference']:+.2f} points **")

    if len(sig_impacts) == 0:
        print("  (No significant impacts found)")

    # Generate report
    report = f"""
SECTION 6: DIMENSION IMPACT ANALYSIS REPORT
{'=' * 80}

Research Question:
  Which dimensions most impact image generation quality?

Method:
  Independent samples t-test for each dimension × quality metric
  Comparison: Has dimension vs Doesn't have dimension

Dataset:
  N = {len(df):,} first-round prompts
  Total tests: {len(impact_df)} (testable combinations)

"""

    # Add 100% presence dimensions section
    if universal_dims:
        report += f"""{'=' * 80}
Universal Dimensions (100% Presence - No Comparison Possible):
{'=' * 80}
"""
        for dim_info in universal_dims:
            report += f"\n{dim_info['Dimension']}:\n"
            report += f"  Presence rate: {dim_info['Presence_Rate']:.1f}%\n"
            report += f"  All prompts include this dimension\n"
            report += f"  Quality metrics (mean scores):\n"
            for metric, value in dim_info['Metrics'].items():
                report += f"    {QUALITY_LABELS[metric]:20s}: {value:.2f}\n"

    report += f"""
{'=' * 80}
Comparative Analysis Results:
{'=' * 80}
  Significant impacts (p < 0.05): {len(sig_impacts)} / {len(impact_df)}

Top 10 Strongest Impacts:
"""

    for i, (_, row) in enumerate(sig_impacts.head(10).iterrows(), 1):
        report += f"\n{i}. {row['Dimension']} → {row['Quality_Metric']}\n"
        report += f"   Difference: {row['Difference']:+.2f} points\n"
        report += f"   Has: {row['Has_Mean']:.2f}  No: {row['No_Mean']:.2f}\n"
        report += f"   t = {row['t_statistic']:.3f}, p = {row['p_value']:.4f}\n"

    # Per-dimension summary
    report += f"\n{'=' * 80}\n"
    report += f"Per-Dimension Summary:\n"
    report += f"{'=' * 80}\n"

    # Report universal dimensions first
    universal_dim_names = [d['Dimension'] for d in universal_dims]
    for dim in universal_dim_names:
        report += f"\n{dim}:\n"
        report += f"  Status: Universal (100% presence)\n"
        report += f"  No comparative analysis possible\n"
        dim_data = next(d for d in universal_dims if d['Dimension'] == dim)
        avg_score = np.mean(list(dim_data['Metrics'].values()))
        report += f"  Average quality score: {avg_score:.2f}\n"

    # Report other dimensions
    for dim in DIMENSIONS:
        if dim in universal_dim_names:
            continue
            
        dim_impacts = impact_df[impact_df['Dimension'] == dim]
        sig_count = (dim_impacts['Significant'] == 'Yes').sum()
        avg_impact = dim_impacts['Difference'].mean()
        
        report += f"\n{dim}:\n"
        report += f"  Significant impacts: {sig_count} / {len(dim_impacts)}\n"
        report += f"  Average impact: {avg_impact:+.2f} points\n"
        
        if sig_count > 0:
            strongest = dim_impacts.loc[dim_impacts['Difference'].abs().idxmax()]
            report += f"  Strongest: {strongest['Quality_Metric']} ({strongest['Difference']:+.2f})\n"

    report += f"\n{'=' * 80}\n"

    with open(section6_dir / 'dimension_impact_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("  ✓ dimension_impact_report.txt")

    print(f"\n✓ Section 6 completed: {section6_dir.name}/")
    return impact_df, universal_dims


if __name__ == "__main__":
    print("=" * 80)
    print("TABLE 2: DIMENSION IMPACT ANALYSIS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Setup paths - 从 Analyze/data/ 目录读取
    current_dir = Path(__file__).parent.parent  # Analyze/
    data_dir = current_dir / "data"
    output_dir = current_dir / "outputs" / "table2"
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / "first_round_preprocessed.csv"

    if not data_path.exists():
        print(f"❌ ERROR: {data_path.name} not found")
        print(f"   Expected location: {data_path}")
        print("   Please run: python prepare_data.py")
        sys.exit(1)

    print(f"✓ Loading preprocessed data: {data_path.name}")
    df = pd.read_csv(data_path)
    print(f"✓ Loaded {len(df):,} first-round prompts\n")

    # Run analysis
    impact_df, universal_dims = analyze_dimension_impact(df, output_dir)

    print("\n" + "=" * 80)
    print("✅ TABLE 2 GENERATION COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

