#!/usr/bin/env python3
"""
Table 3: Coverage-Quality Relationship Analysis
Extracted from: RQ1/rq1-3.py SECTION 5
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from color_config import COLORS, get_color, get_dimension_color, get_quality_color
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr
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


def analyze_coverage_quality_relationship(df, output_dir):
    """
    SECTION 5: COVERAGE-QUALITY RELATIONSHIP
    """
    print("=" * 80)
    print("SECTION 5: COVERAGE-QUALITY RELATIONSHIP ⭐⭐⭐⭐⭐")
    print("=" * 80)
    
    section5_dir = output_dir / "section05"
    section5_dir.mkdir(exist_ok=True)
    
    # Compute correlations
    print("\nComputing correlations between coverage and quality...")
    
    corr_results = []
    for metric in QUALITY_METRICS:
        # Remove NaN values
        mask = df['user_dimension_count'].notna() & df[metric].notna()
        x = df.loc[mask, 'user_dimension_count']
        y = df.loc[mask, metric]
        
        if len(x) > 0:
            r_pearson, p_pearson = pearsonr(x, y)
            r_spearman, p_spearman = spearmanr(x, y)
            
            corr_results.append({
                'Quality_Metric': QUALITY_LABELS[metric],
                'Pearson_r': r_pearson,
                'Pearson_p': p_pearson,
                'Spearman_rho': r_spearman,
                'Spearman_p': p_spearman,
                'Significant': 'Yes' if p_pearson < 0.05 else 'No',
                'N': len(x)
            })
            
            sig = "**" if p_pearson < 0.05 else ""
            print(f"  {QUALITY_LABELS[metric]:20s}: r={r_pearson:+.3f} {sig}")
    
    corr_df = pd.DataFrame(corr_results)
    corr_df.to_csv(section5_dir / 'coverage_quality_correlations.csv', index=False)
    
    # Regression analysis
    print("\nPerforming regression analysis...")
    
    reg_results = []
    for metric in QUALITY_METRICS:
        mask = df['user_dimension_count'].notna() & df[metric].notna()
        X = df.loc[mask, 'user_dimension_count'].values.reshape(-1, 1)
        y = df.loc[mask, metric].values
        
        if len(X) > 0:
            reg = LinearRegression().fit(X, y)
            r_squared = reg.score(X, y)
            coefficient = reg.coef_[0]
            intercept = reg.intercept_
            
            reg_results.append({
                'Quality_Metric': QUALITY_LABELS[metric],
                'Coefficient': coefficient,
                'Intercept': intercept,
                'R_squared': r_squared,
                'Interpretation': f'+1 dimension → {coefficient:+.2f} points'
            })
    
    reg_df = pd.DataFrame(reg_results)
    reg_df.to_csv(section5_dir / 'regression_results.csv', index=False)
    
    # Figures
    print("\nGenerating figures...")
    
    # Fig 1: Correlation scatter plots (grid)
    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    axes = axes.flatten()
    
    for idx, metric in enumerate(QUALITY_METRICS):
        ax = axes[idx]
        mask = df['user_dimension_count'].notna() & df[metric].notna()
        x = df.loc[mask, 'user_dimension_count']
        y = df.loc[mask, metric]
        
        # Scatter
        ax.scatter(x, y, alpha=0.5, s=30, color=COLORS['primary'])
        
        # Regression line
        X = x.values.reshape(-1, 1)
        reg = LinearRegression().fit(X, y.values)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = reg.predict(x_line.reshape(-1, 1))
        ax.plot(x_line, y_line, 'r--', linewidth=2)
        
        # Stats
        r, p = pearsonr(x, y)
        ax.text(0.05, 0.95, f'r = {r:.3f}{"**" if p < 0.05 else ""}',
                transform=ax.transAxes, va='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_xlabel('Dimension Coverage')
        ax.set_ylabel(QUALITY_LABELS[metric])
        ax.set_title(QUALITY_LABELS[metric])
        ax.grid(alpha=0.3)
        ax.set_xticks(range(0, 7))
    
    # Hide extra subplots
    for idx in range(len(QUALITY_METRICS), len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    fig.savefig(section5_dir / 'fig1_coverage_vs_quality_scatter.png',
                dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ fig1_coverage_vs_quality_scatter.png")
    
    # Fig 2: Correlation heatmap
    fig, ax = plt.subplots(figsize=(10, 4))
    
    corr_matrix = corr_df[['Quality_Metric', 'Pearson_r']].set_index('Quality_Metric')
    corr_matrix = corr_matrix.T
    
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='RdYlGn',
                center=0, vmin=-1, vmax=1, cbar_kws={'label': 'Correlation'},
                ax=ax)
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('Coverage-Quality Correlations (Pearson r)')
    
    fig.savefig(section5_dir / 'fig2_correlation_heatmap.png',
                dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ fig2_correlation_heatmap.png")
    
    # Fig 3: Coefficient plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    reg_df_sorted = reg_df.sort_values('Coefficient', ascending=True)
    colors = [COLORS['positive'] if c > 0 else COLORS['negative']
              for c in reg_df_sorted['Coefficient']]
    
    ax.barh(range(len(reg_df_sorted)), reg_df_sorted['Coefficient'],
            color=colors, alpha=0.7, edgecolor='black')
    ax.set_yticks(range(len(reg_df_sorted)))
    ax.set_yticklabels(reg_df_sorted['Quality_Metric'])
    ax.set_xlabel('Coefficient (Quality Change per +1 Dimension)')
    ax.set_title('Impact of Dimension Coverage on Quality Metrics')
    ax.axvline(0, color='black', linestyle='-', linewidth=1)
    ax.grid(axis='x', alpha=0.3)
    
    for i, (_, row) in enumerate(reg_df_sorted.iterrows()):
        ax.text(row['Coefficient'], i, f'{row["Coefficient"]:+.2f}',
                va='center', ha='left' if row['Coefficient'] > 0 else 'right',
                fontsize=9)
    
    fig.savefig(section5_dir / 'fig3_regression_coefficients.png',
                dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ fig3_regression_coefficients.png")
    
    # Report
    report = f"""
SECTION 5: COVERAGE-QUALITY RELATIONSHIP REPORT
{'=' * 80}

Research Question:
  Does dimension coverage correlate with image generation quality?

Dataset:
  N = {len(df):,} first-round prompts

Correlation Analysis:
{'=' * 80}
"""
    
    for _, row in corr_df.iterrows():
        report += f"\n{row['Quality_Metric']}:\n"
        report += f"  Pearson r:  {row['Pearson_r']:+.3f}  (p = {row['Pearson_p']:.4f})\n"
        report += f"  Spearman ρ: {row['Spearman_rho']:+.3f}  (p = {row['Spearman_p']:.4f})\n"
        report += f"  Significant: {row['Significant']}\n"
    
    report += f"\nRegression Analysis:\n"
    report += f"{'=' * 80}\n"
    report += f"Impact of +1 dimension on quality:\n\n"
    
    for _, row in reg_df.iterrows():
        report += f"{row['Quality_Metric']:20s}: {row['Coefficient']:+.2f} points (R² = {row['R_squared']:.3f})\n"
    
    # Key findings
    report += f"\n{'=' * 80}\n"
    report += f"Key Findings:\n"
    report += f"{'=' * 80}\n"
    
    sig_corrs = corr_df[corr_df['Significant'] == 'Yes']
    if len(sig_corrs) > 0:
        report += f"\n✓ {len(sig_corrs)}/{len(corr_df)} quality metrics show significant correlation\n"
        
        strongest = corr_df.loc[corr_df['Pearson_r'].abs().idxmax()]
        report += f"\n✓ Strongest correlation: {strongest['Quality_Metric']}\n"
        report += f"  r = {strongest['Pearson_r']:.3f}, p = {strongest['Pearson_p']:.4e}\n"
        
        best_reg = reg_df.loc[reg_df['R_squared'].idxmax()]
        report += f"\n✓ Best predictive model: {best_reg['Quality_Metric']}\n"
        report += f"  {best_reg['Interpretation']}\n"
        report += f"  R² = {best_reg['R_squared']:.3f}\n"
    else:
        report += f"\n⚠️  No significant correlations found\n"
    
    report += f"\n{'=' * 80}\n"
    
    with open(section5_dir / 'coverage_quality_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("  ✓ coverage_quality_report.txt")
    
    print(f"\n✓ Section 5 completed: {section5_dir.name}/")
    return corr_df, reg_df


if __name__ == "__main__":
    print("=" * 80)
    print("TABLE 3: COVERAGE-QUALITY RELATIONSHIP ANALYSIS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Setup paths - 从 Analyze/data/ 目录读取
    current_dir = Path(__file__).parent.parent  # Analyze/
    data_dir = current_dir / "data"
    output_dir = current_dir / "outputs" / "table3"
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / "first_round_preprocessed.csv"

    if not data_path.exists():
        print(f"❌ ERROR: {data_path.name} not found")
        print(f"   Expected location: {data_path}")
        print("   Please run RQ1/rq1-1.py first!")
        sys.exit(1)

    print(f"✓ Loading preprocessed data: {data_path.name}")
    df = pd.read_csv(data_path)
    print(f"✓ Loaded {len(df):,} first-round prompts\n")

    # Run analysis
    corr_df, reg_df = analyze_coverage_quality_relationship(df, output_dir)

    print("\n" + "=" * 80)
    print("✅ TABLE 3 GENERATION COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

