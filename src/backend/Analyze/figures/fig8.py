#!/usr/bin/env python3
"""
Fig 8 Analysis - Descriptive Statistics (Section 2)
Generated from: RQ1/rq1-1.py Section 2
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from color_config import COLORS
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9

QUALITY_METRICS = [
    'ai_similarity_score', 'user_manual_score', 'average_star_score',
    'style_score', 'object_count_score', 'perspective_score',
    'depth_background_score'
]

QUALITY_LABELS = {
    'ai_similarity_score': 'AI Similarity',
    'user_manual_score': 'User Manual Score',
    'average_star_score': 'Average Star',
    'style_score': 'Style Quality',
    'object_count_score': 'Object Count',
    'perspective_score': 'Perspective',
    'depth_background_score': 'Depth & Background'
}

if __name__ == "__main__":
    print("=" * 80)
    print("FIG 8: DESCRIPTIVE STATISTICS ANALYSIS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Setup paths - 从 Analyze/data/ 目录读取
    current_dir = Path(__file__).parent.parent  # Analyze/
    data_dir = current_dir / "data"
    output_dir = current_dir / "outputs" / "fig8"
    section_dir = output_dir / "section02"
    section_dir.mkdir(parents=True, exist_ok=True)

    data_path = data_dir / "first_round_preprocessed.csv"

    if not data_path.exists():
        print(f"❌ ERROR: {data_path.name} not found")
        print(f"   Expected at: {data_path}")
        print("   Please run: python prepare_data.py")
        exit(1)

    print(f"✓ Loading preprocessed data: {data_path.name}\n")
    df_full = pd.read_csv(data_path)
    print(f"✓ Loaded {len(df_full):,} first-round prompts\n")

    time_threshold = df_full['prompt_time_seconds'].quantile(0.95)
    df_time = df_full[df_full['prompt_time_seconds'] <= time_threshold].copy()
    n_removed = len(df_full) - len(df_time)
    print(f"Time threshold (95th percentile): {time_threshold:.1f} seconds")
    print(f"Clean dataset: {len(df_time):,} records")
    print(f"Removed outliers: {n_removed}\n")

    print("=" * 80)
    print("SECTION 2: DESCRIPTIVE STATISTICS")
    print("=" * 80)

    print("\nComputing statistics...")

    stats_data = []

    stats_data.append({
        'Metric': 'Prompt Length (chars)',
        'Mean': df_full['prompt_length'].mean(),
        'Median': df_full['prompt_length'].median(),
        'Std': df_full['prompt_length'].std(),
        'Min': df_full['prompt_length'].min(),
        'Max': df_full['prompt_length'].max(),
        'Q25': df_full['prompt_length'].quantile(0.25),
        'Q75': df_full['prompt_length'].quantile(0.75)
    })

    stats_data.append({
        'Metric': 'Prompt Time (seconds, top 5% removed)',
        'Mean': df_time['prompt_time_seconds'].mean(),
        'Median': df_time['prompt_time_seconds'].median(),
        'Std': df_time['prompt_time_seconds'].std(),
        'Min': df_time['prompt_time_seconds'].min(),
        'Max': df_time['prompt_time_seconds'].max(),
        'Q25': df_time['prompt_time_seconds'].quantile(0.25),
        'Q75': df_time['prompt_time_seconds'].quantile(0.75)
    })

    for metric in QUALITY_METRICS:
        stats_data.append({
            'Metric': QUALITY_LABELS[metric],
            'Mean': df_full[metric].mean(),
            'Median': df_full[metric].median(),
            'Std': df_full[metric].std(),
            'Min': df_full[metric].min(),
            'Max': df_full[metric].max(),
            'Q25': df_full[metric].quantile(0.25),
            'Q75': df_full[metric].quantile(0.75)
        })

    stats_df = pd.DataFrame(stats_data)
    stats_path = section_dir / 'descriptive_statistics.csv'
    stats_df.to_csv(stats_path, index=False)
    print(f"  ✓ Saved: {stats_path.name}")

    print("\nGenerating figures...")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df_full['prompt_length'], bins=30, color=COLORS['primary'],
            alpha=0.7, edgecolor='black')
    mean_len = df_full['prompt_length'].mean()
    median_len = df_full['prompt_length'].median()
    ax.axvline(mean_len, color='red', linestyle='--',
               linewidth=2, label=f'Mean = {mean_len:.1f}')
    ax.axvline(median_len, color='orange', linestyle='--',
               linewidth=2, label=f'Median = {median_len:.1f}')
    ax.set_xlabel('Prompt Length (characters)')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of First-Round Prompt Length')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    fig_path = section_dir / 'fig1_length_distribution.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {fig_path.name}")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df_time['prompt_time_seconds'], bins=30, color=COLORS['secondary'],
            alpha=0.7, edgecolor='black')
    mean_time = df_time['prompt_time_seconds'].mean()
    median_time = df_time['prompt_time_seconds'].median()
    ax.axvline(mean_time, color='red', linestyle='--',
               linewidth=2, label=f'Mean = {mean_time:.1f}s')
    ax.axvline(median_time, color='orange', linestyle='--',
               linewidth=2, label=f'Median = {median_time:.1f}s')
    ax.set_xlabel('Prompt Time (seconds)')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of First-Round Prompt Time\n(Top 5% Outliers Removed)')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    fig_path = section_dir / 'fig2_time_distribution.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {fig_path.name}")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df_time['prompt_time_seconds'], df_time['prompt_length'],
               alpha=0.6, color=COLORS['tertiary'], s=50)

    mask = df_time['prompt_time_seconds'].notna() & df_time['prompt_length'].notna()
    X = df_time.loc[mask, 'prompt_time_seconds'].values.reshape(-1, 1)
    y = df_time.loc[mask, 'prompt_length'].values
    reg = LinearRegression().fit(X, y)
    x_line = np.linspace(X.min(), X.max(), 100)
    y_line = reg.predict(x_line.reshape(-1, 1))
    r_squared = reg.score(X, y)
    ax.plot(x_line, y_line, 'r--', linewidth=2, label=f'R² = {r_squared:.3f}')

    ax.set_xlabel('Prompt Time (seconds)')
    ax.set_ylabel('Prompt Length (characters)')
    ax.set_title('Relationship between Prompt Time and Length')
    ax.legend()
    ax.grid(alpha=0.3)
    fig_path = section_dir / 'fig3_length_vs_time.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {fig_path.name}")

    print("\nAnalyzing task sequence effects...")

    time_by_seq = df_time.groupby('task_sequence').agg({
        'prompt_time_seconds': ['mean', 'std', 'count']
    }).reset_index()
    time_by_seq.columns = ['task_sequence', 'time_mean', 'time_std', 'time_count']

    length_by_seq = df_full.groupby('task_sequence').agg({
        'prompt_length': ['mean', 'std', 'count']
    }).reset_index()
    length_by_seq.columns = ['task_sequence', 'length_mean', 'length_std', 'length_count']

    sequence_stats = time_by_seq.merge(length_by_seq, on='task_sequence')
    seq_stats_path = section_dir / 'task_sequence_statistics.csv'
    sequence_stats.to_csv(seq_stats_path, index=False)
    print(f"  ✓ Saved: {seq_stats_path.name}")

    seq_time_corr, seq_time_p = spearmanr(
        df_time['task_sequence'],
        df_time['prompt_time_seconds']
    )
    seq_length_corr, seq_length_p = spearmanr(
        df_full['task_sequence'],
        df_full['prompt_length']
    )

    print(f"\nCorrelation Results:")
    print(f"  Task Sequence × Time: ρ = {seq_time_corr:.3f}, p = {seq_time_p:.4f}")
    print(f"  Task Sequence × Length: ρ = {seq_length_corr:.3f}, p = {seq_length_p:.4f}")

    fig, ax = plt.subplots(figsize=(8, 6))
    sequence_stats['time_se'] = sequence_stats['time_std'] / np.sqrt(sequence_stats['time_count'])
    ax.errorbar(sequence_stats['task_sequence'],
                sequence_stats['time_mean'],
                yerr=sequence_stats['time_se'],
                fmt='o-', capsize=5, color=COLORS.get('sand', '#FDCD94'),
                linewidth=2.5, markersize=10, label='Mean ± SE')

    X_seq = sequence_stats['task_sequence'].values.reshape(-1, 1)
    y_time = sequence_stats['time_mean'].values
    reg_time = LinearRegression().fit(X_seq, y_time)
    y_pred = reg_time.predict(X_seq)
    slope_time = reg_time.coef_[0]

    ax.plot(X_seq, y_pred, color=COLORS.get('coral', '#FC757B'), linestyle='--',
        linewidth=3, alpha=0.8,
        label=f'Fitted Line (k={slope_time:.2f})')
    ax.set_xlabel('Task Sequence', fontsize=22)
    ax.set_ylabel('Prompt Time (seconds)', fontsize=22)
    ax.tick_params(axis='both', labelsize=20)
    ax.legend(fontsize=18)
    ax.grid(alpha=0.3)
    ax.set_xticks(range(1, 11))

    fig_path = section_dir / 'fig4a_task_sequence_time.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {fig_path.name}")

    fig, ax = plt.subplots(figsize=(8, 6))
    sequence_stats['length_se'] = sequence_stats['length_std'] / np.sqrt(sequence_stats['length_count'])
    ax.errorbar(sequence_stats['task_sequence'],
                sequence_stats['length_mean'],
                yerr=sequence_stats['length_se'],
                fmt='s-', capsize=5, color=COLORS.get('sand', '#FDCD94'),
                linewidth=2.5, markersize=10, label='Mean ± SE')

    y_length = sequence_stats['length_mean'].values
    reg_length = LinearRegression().fit(X_seq, y_length)
    y_pred = reg_length.predict(X_seq)
    slope_length = reg_length.coef_[0]

    ax.plot(X_seq, y_pred, color=COLORS.get('coral', '#FC757B'), linestyle='--',
        linewidth=3, alpha=0.8,
        label=f'Fitted Line (k={slope_length:.2f})')
    ax.set_xlabel('Task Sequence', fontsize=22)
    ax.set_ylabel('Prompt Length (characters)', fontsize=22)
    ax.tick_params(axis='both', labelsize=20)
    ax.legend(fontsize=18)
    ax.grid(alpha=0.3)
    ax.set_xticks(range(1, 11))
    ax.set_ylim(30, 175)
    fig_path = section_dir / 'fig4b_task_sequence_length.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {fig_path.name}")

    print("\n" + "=" * 80)
    print("✅ Analysis completed!")
    print(f"Output directory: {section_dir}")
    print("=" * 80)
