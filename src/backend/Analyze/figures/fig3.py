#!/usr/bin/env python3
"""
Fig 3 Analysis - First vs Last Round Dimension Coverage
Generated from: RQ2/rq2-2.py Section 3
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

COLORS.setdefault('base_stage', '#FAA26F')
COLORS.setdefault('agent_stage', '#65BDBA')
COLORS.setdefault('user', '#F97F5F')
COLORS.setdefault('gt', '#3C9BC9')
COLORS.setdefault('sand', '#FDCD94')
COLORS.setdefault('positive', '#B0D6A9')
COLORS.setdefault('negative', '#FC757B')
COLORS.setdefault('primary', '#3C9BC9')
COLORS.setdefault('secondary', '#FC757B')
COLORS.setdefault('tertiary', '#B0D6A9')
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

def analyze_dimension_coverage(first_rounds, last_rounds, output_dir):
    print("\n" + "=" * 80)
    print("SECTION 3: FIRST VS LAST ROUND DIMENSION COVERAGE")
    print("=" * 80)

    section3_dir = output_dir / "section03_dimension_coverage"
    section3_dir.mkdir(exist_ok=True)

    coverage_stats = []

    for dim in DIMENSIONS:
        dim_lower = dim.lower()
        has_col = f'has_{dim_lower}'

        if has_col not in first_rounds.columns:
            print(f"⚠️  Column {has_col} not found, skipping {dim}")
            continue

        first_has = first_rounds[has_col].sum()
        first_total = len(first_rounds)
        first_pct = first_has / first_total * 100

        last_has = last_rounds[has_col].sum()
        last_total = len(last_rounds)
        last_pct = last_has / last_total * 100

        change = last_has - first_has
        change_pct = last_pct - first_pct

        coverage_stats.append({
            'dimension': dim,
            'first_has': first_has,
            'first_total': first_total,
            'first_pct': first_pct,
            'last_has': last_has,
            'last_total': last_total,
            'last_pct': last_pct,
            'change': change,
            'change_pct': change_pct
        })

        print(f"\n{dim}:")
        print(f"  First: {first_has}/{first_total} ({first_pct:.1f}%)")
        print(f"  Last:  {last_has}/{last_total} ({last_pct:.1f}%)")
        print(f"  Change: {change:+d} ({change_pct:+.1f}%)")

    coverage_df = pd.DataFrame(coverage_stats)

    first_dim_cols = [f'has_{d.lower()}' for d in DIMENSIONS]

    for col in first_dim_cols:
        if col in first_rounds.columns:
            first_rounds[col] = first_rounds[col].astype(bool)
            last_rounds[col] = last_rounds[col].astype(bool)

    first_rounds['dim_count'] = first_rounds[first_dim_cols].sum(axis=1)
    last_rounds['dim_count'] = last_rounds[first_dim_cols].sum(axis=1)

    avg_first = first_rounds['dim_count'].mean()
    avg_last = last_rounds['dim_count'].mean()

    print(f"\nAverage Dimension Count:")
    print(f"  First: {avg_first:.2f} / 6")
    print(f"  Last:  {avg_last:.2f} / 6")
    print(f"  Change: {avg_last - avg_first:+.2f}")

    stats_path = section3_dir / 'dimension_coverage_stats.csv'
    coverage_df.to_csv(stats_path, index=False)
    print(f"\n✓ Saved: {stats_path.name}")

    fig, ax = plt.subplots(figsize=(10, 5))

    DIMS_NO_OTHERS = [d for d in DIMENSIONS if d != 'Others']
    coverage_no_others = coverage_df[coverage_df['dimension'].isin(DIMS_NO_OTHERS)]

    x = np.arange(len(DIMS_NO_OTHERS))
    width = 0.35

    first_pcts = [coverage_no_others[coverage_no_others['dimension']==d]['first_pct'].values[0]
                for d in DIMS_NO_OTHERS]
    last_pcts = [coverage_no_others[coverage_no_others['dimension']==d]['last_pct'].values[0]
                for d in DIMS_NO_OTHERS]

    ax.bar(x - width/2, first_pcts, width, label='First Round',
       color='#FAA26F', alpha=0.8, edgecolor='black')
    ax.bar(x + width/2, last_pcts, width, label='Final Round',
       color='#FAA26F', alpha=0.8, edgecolor='black', hatch='///')

    for i in range(len(DIMS_NO_OTHERS)):
        left_x = x[i] - width/2
        right_x = x[i] + width/2
        top = max(first_pcts[i], last_pcts[i]) + 2
        bracket_h = 2.5
        diff = last_pcts[i] - first_pcts[i]

        ax.plot([left_x, left_x, right_x, right_x],
                [top, top + bracket_h, top + bracket_h, top],
                color='black', linewidth=1.2, clip_on=False)

        label = f'+{diff:.1f}' if diff >= 0 else f'{diff:.1f}'
        ax.text((left_x + right_x) / 2, top + bracket_h + 0.8,
                label, ha='center', va='bottom', fontsize=18, fontweight='bold')

    ax.set_ylabel('Dimension-Level Hit Rate (%)', fontsize=21)
    ax.set_ylim(0, 125)
    ax.set_xticks(x)
    ax.set_xticklabels([DIMENSION_LABELS[d] for d in DIMS_NO_OTHERS],
                    rotation=0, ha='center', fontsize=20)
    ax.tick_params(axis='y', labelsize=20)
    ax.legend(fontsize=18, loc='upper right')
    ax.grid(alpha=0.3, axis='y')

    fig_path = section3_dir / 'fig1a_coverage_first_vs_last.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {fig_path.name}")

    fig, ax = plt.subplots(figsize=(10, 6))

    DIMS_NO_OTHERS_NO_SUBJECT = [d for d in DIMS_NO_OTHERS if d != 'SubjectScene']
    coverage_filtered = coverage_df[coverage_df['dimension'].isin(DIMS_NO_OTHERS_NO_SUBJECT)]

    x2 = np.arange(len(DIMS_NO_OTHERS_NO_SUBJECT))
    change_pcts = [coverage_filtered[coverage_filtered['dimension']==d]['change_pct'].values[0]
                for d in DIMS_NO_OTHERS_NO_SUBJECT]
    colors = [COLORS['positive'] if c > 0 else COLORS['negative'] for c in change_pcts]

    ax.bar(x2, change_pcts, color=colors, alpha=0.8, width=0.5)
    ax.axhline(0, color='gray', linestyle='-', linewidth=1)
    ax.set_ylabel('Coverage Change (%)', fontsize=22)
    ax.set_xticks(x2)
    ax.set_xticklabels([DIMENSION_LABELS[d] for d in DIMS_NO_OTHERS_NO_SUBJECT],
                        rotation=45, ha='right', fontsize=20)
    ax.tick_params(axis='y', labelsize=20)
    ax.grid(alpha=0.3, axis='y')

    fig_path = section3_dir / 'fig1b_coverage_change.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {fig_path.name}")
    
    fig, ax = plt.subplots(figsize=(8, 5))

    categories = ['First Round', 'Last Round']
    values = [avg_first, avg_last]
    colors_bar = [COLORS['primary'], COLORS['secondary']]

    bars = ax.bar(categories, values, color=colors_bar, alpha=0.8, width=0.5)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel('Average Dimension Count')
    ax.set_title('Average Number of Dimensions Covered')
    ax.set_ylim([0, 6])
    ax.axhline(6, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Maximum (6)')
    ax.grid(alpha=0.3, axis='y')
    ax.legend()

    plt.tight_layout()
    fig_path = section3_dir / 'fig2_avg_dimension_count.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {fig_path.name}")


if __name__ == "__main__":
    print("=" * 80)
    print("FIG 3 ANALYSIS - FIRST VS LAST ROUND DIMENSION COVERAGE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Setup paths - 从 Analyze/data/ 目录读取
    current_dir = Path(__file__).parent.parent  # Analyze/
    data_dir = current_dir / "data"
    output_dir = current_dir / "outputs" / "fig3"
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = data_dir / "ultimate_dataset.csv"
    
    if not dataset_path.exists():
        print(f"❌ ERROR: ultimate_dataset.csv not found")
        print(f"   Expected at: {dataset_path}")
        print("   Please run: python prepare_data.py")
        exit(1)
    
    print(f"✓ Input: {dataset_path.name}")
    print(f"✓ Output: outputs/\n")
    
    print("Loading data...")
    df = pd.read_csv(dataset_path)
    
    for dim in DIMENSIONS:
        dim_lower = dim.lower()
        bool_cols = [f'has_{dim_lower}', f'{dim_lower}_has_added', f'{dim_lower}_has_removed']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: True if (x == True or x == 1 or 
                                     (isinstance(x, str) and x.lower() == 'true'))
                    else False
                )
    
    print(f"✓ Loaded {len(df)} records\n")
    
    first_rounds = df[df['is_first_round'] == True].copy()
    last_rounds = df[df['is_last_round'] == True].copy()
    
    print(f"✓ First rounds: {len(first_rounds)}")
    print(f"✓ Last rounds: {len(last_rounds)}\n")
    
    analyze_dimension_coverage(first_rounds, last_rounds, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETED")
    print("=" * 80)
