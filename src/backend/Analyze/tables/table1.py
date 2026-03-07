#!/usr/bin/env python3
"""
Table 1: Dimension Coverage Analysis
Extracted from: RQ1/rq1-2.py SECTION 3
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from color_config import COLORS, get_color, get_dimension_color, get_quality_color
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from datetime import datetime
import ast
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10

DIMENSIONS = ['SpatialComposition', 'Style', 'SubjectScene',
              'LightingColor', 'DetailTexture', 'Others']
DIMENSION_LABELS = {
    'SpatialComposition': 'SPA',
    'Style': 'STY',
    'SubjectScene': 'SUB',
    'LightingColor': 'LIG',
    'DetailTexture': 'DET',
    'Others': 'OTH'
}


def analyze_dimension_coverage(df, output_dir):
    """
    SECTION 3: DIMENSION COVERAGE ANALYSIS
    """
    print("=" * 80)
    print("SECTION 3: DIMENSION COVERAGE ANALYSIS ⭐⭐⭐⭐⭐")
    print("=" * 80)

    section3_dir = output_dir / "section03"
    section3_dir.mkdir(exist_ok=True)

    # Overall coverage statistics
    coverage_stats = {
        'Mean_Coverage': df['user_dimension_count'].mean(),
        'Median_Coverage': df['user_dimension_count'].median(),
        'Std_Coverage': df['user_dimension_count'].std(),
        'Min_Coverage': df['user_dimension_count'].min(),
        'Max_Coverage': df['user_dimension_count'].max(),
        'Coverage_Rate_%': df['user_dimension_count'].mean() / 6 * 100
    }

    print(f"\nOverall Coverage Statistics:")
    print(f"  Mean: {coverage_stats['Mean_Coverage']:.2f} / 6 dimensions ({coverage_stats['Coverage_Rate_%']:.1f}%)")
    print(f"  Median: {coverage_stats['Median_Coverage']:.0f} dimensions")
    print(f"  Range: {coverage_stats['Min_Coverage']:.0f} - {coverage_stats['Max_Coverage']:.0f} dimensions")

    # Dimension-level details
    dim_details = []
    for dim in DIMENSIONS:
        has_col = f'has_{dim.lower()}'
        class_col = f'classified_{dim.lower()}'

        sentences = df[class_col].apply(len)
        chars = df[class_col].apply(lambda x: sum(len(s) for s in x) if x else 0)

        dim_details.append({
            'Dimension': dim,
            'Inclusion_Rate_%': df[has_col].mean() * 100,
            'Avg_Sentences': sentences[sentences > 0].mean() if (sentences > 0).any() else 0,
            'Avg_Characters': chars[chars > 0].mean() if (chars > 0).any() else 0
        })

    dim_df = pd.DataFrame(dim_details).sort_values('Inclusion_Rate_%', ascending=False)
    dim_df.to_csv(section3_dir / 'dimension_details.csv', index=False)

    print("\nDimension Inclusion Rates:")
    for _, row in dim_df.iterrows():
        print(f"  {row['Dimension']:20s}: {row['Inclusion_Rate_%']:5.1f}%")

    print("\nGenerating figures...")

    # Figure 1: Coverage heatmap
    matrix = np.array([[1 if row[f'has_{d.lower()}'] else 0 for d in DIMENSIONS]
                       for _, row in df.iterrows()])
    sorted_idx = np.argsort(matrix.sum(axis=1))[::-1]

    fig, ax = plt.subplots(figsize=(10, 12))
    sns.heatmap(matrix[sorted_idx], cmap='RdYlGn', cbar_kws={'label': 'Present'},
                xticklabels=[DIMENSION_LABELS[d].replace('\n', ' ') for d in DIMENSIONS],
                yticklabels=False, ax=ax)
    ax.set_xlabel('Semantic Dimensions')
    ax.set_ylabel(f'First-Round Prompts (N={len(df)})')
    ax.set_title('Dimension Coverage Heatmap\n(Sorted by Total Coverage)')
    fig.savefig(section3_dir / 'fig1_coverage_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ fig1_coverage_heatmap.png")

    # Figure 2: Coverage distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    counts = df['user_dimension_count'].value_counts().sort_index()
    ax.bar(counts.index, counts.values, color=COLORS['primary'], alpha=0.7, edgecolor='black')
    ax.axvline(df['user_dimension_count'].mean(), color='red', linestyle='--', linewidth=2,
               label=f'Mean = {df["user_dimension_count"].mean():.2f}')
    ax.set_xlabel('Number of Dimensions Covered')
    ax.set_ylabel('Number of Prompts')
    ax.set_title('Distribution of Dimension Coverage')
    ax.set_xticks(range(0, 7))
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    for i, v in zip(counts.index, counts.values):
        ax.text(i, v+1, f'{v}\n({v/len(df)*100:.1f}%)', ha='center', va='bottom', fontsize=9)
    fig.savefig(section3_dir / 'fig2_coverage_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ fig2_coverage_distribution.png")

    # Figure 3: Dimension inclusion rates
    fig, ax = plt.subplots(figsize=(10, 6))
    dims_sorted = dim_df['Dimension'].tolist()
    rates_sorted = dim_df['Inclusion_Rate_%'].tolist()
    colors_bars = [COLORS['primary'] if r > 50 else COLORS['secondary'] for r in rates_sorted]
    ax.barh(range(len(dims_sorted)), rates_sorted, color=colors_bars, alpha=0.7, edgecolor='black')
    ax.set_yticks(range(len(dims_sorted)))
    ax.set_yticklabels([DIMENSION_LABELS[d].replace('\n', ' ') for d in dims_sorted])
    ax.set_xlabel('Inclusion Rate (%)')
    ax.set_title('Dimension Inclusion Rates in First-Round Prompts')
    ax.grid(axis='x', alpha=0.3)
    for i, rate in enumerate(rates_sorted):
        ax.text(rate+1, i, f'{rate:.1f}%', va='center', fontsize=9)
    fig.savefig(section3_dir / 'fig3_dimension_rates.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ fig3_dimension_rates.png")

    # Generate report
    report = f"""
SECTION 3:  DIMENSION COVERAGE ANALYSIS REPORT
{'=' * 80}

Overall Coverage Statistics:
  Mean dimensions covered: {coverage_stats['Mean_Coverage']:.2f} / 6 ({coverage_stats['Coverage_Rate_%']:.1f}%)
  Median: {coverage_stats['Median_Coverage']:.0f} dimensions
  Standard deviation: {coverage_stats['Std_Coverage']:.2f}
  Range: {coverage_stats['Min_Coverage']:.0f} - {coverage_stats['Max_Coverage']:.0f} dimensions

Coverage Distribution:
"""

    for idx, count in counts.items():
        pct = count / len(df) * 100
        report += f"  {idx} dimensions: {count:3d} prompts ({pct:5.1f}%)\n"

    report += f"\n{'=' * 80}\n"
    report += "Dimension-Specific Inclusion Rates:\n"
    report += f"{'=' * 80}\n\n"

    for _, row in dim_df.iterrows():
        report += f"{row['Dimension']}:\n"
        report += f"  Inclusion rate:     {row['Inclusion_Rate_%']:.1f}%\n"
        report += f"  Avg sentences:      {row['Avg_Sentences']:.1f}\n"
        report += f"  Avg characters:     {row['Avg_Characters']:.0f}\n\n"

    with open(section3_dir / 'coverage_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("  ✓ coverage_report.txt")

    print(f"\n✓ Section 3 completed: {section3_dir.name}/")
    return dim_df, coverage_stats


if __name__ == "__main__":
    print("=" * 80)
    print("TABLE 1: DIMENSION COVERAGE ANALYSIS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Setup paths - 从 Analyze/data/ 目录读取
    current_dir = Path(__file__).parent.parent  # Analyze/
    data_dir = current_dir / "data"
    output_dir = current_dir / "outputs" / "table1"
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / "first_round_preprocessed.csv"

    if not data_path.exists():
        print(f"❌ ERROR: {data_path.name} not found")
        print(f"   Expected location: {data_path}")
        print("   Please run: python prepare_data.py")
        sys.exit(1)

    print(f"✓ Loading preprocessed data: {data_path.name}")
    df = pd.read_csv(data_path)
    
    # Parse list columns
    def safe_eval_list(x):
        if pd.isna(x) or x == '':
            return []
        if isinstance(x, list):
            return x
        try:
            result = ast.literal_eval(x)
            return result if isinstance(result, list) else []
        except:
            return []
    
    for dim in DIMENSIONS:
        col = f'classified_{dim.lower()}'
        if col in df.columns:
            df[col] = df[col].apply(safe_eval_list)

    print(f"✓ Loaded {len(df):,} first-round prompts\n")

    # Run analysis
    dim_df, coverage_stats = analyze_dimension_coverage(df, output_dir)

    print("\n" + "=" * 80)
    print("✅ TABLE 1 GENERATION COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
