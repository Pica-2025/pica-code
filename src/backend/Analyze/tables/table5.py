
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from color_config import COLORS
except ImportError:
    COLORS = {'base_stage': '#FAA26F', 'agent_stage': '#65BDBA'}

COLOR_WITHOUT = COLORS.get('base_stage', '#FAA26F')
COLOR_WITH = COLORS.get('agent_stage', '#65BDBA')

OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "table5"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR = OUTPUT_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

def load_dataset(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    for col in ['is_first_round', 'is_last_round', 'is_final', 'generation_type']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.strip('"').str.strip("'")

    numeric_cols = ['ai_similarity_score', 'user_manual_score', 'prompt_time_seconds',
                    'prompt_length', 'version_number', 'user_difficulty_rating']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    print(f"✅ {csv_path}: {len(df)} rows, {df['task_id'].nunique()} tasks")
    return df

def analyze_data(df_without: pd.DataFrame, df_with: pd.DataFrame) -> dict:
    results = {}

    results['ai_change'] = {
        'without_max_minus_first': [],
        'without_final_minus_first': [],
        'with_max_minus_first': [],
        'with_final_minus_first': []
    }

    for df_key, df in [('without', df_without), ('with', df_with)]:
        for task_id in df['task_id'].unique():
            task_data = df[df['task_id'] == task_id].sort_values('version_number')

            if len(task_data) >= 1:
                first_score = task_data.iloc[0]['ai_similarity_score']
                max_score = task_data['ai_similarity_score'].max()
                final_score = task_data.iloc[-1]['ai_similarity_score']

                results['ai_change'][f'{df_key}_max_minus_first'].append(max_score - first_score)
                results['ai_change'][f'{df_key}_final_minus_first'].append(final_score - first_score)

    results['ai_change']['without_max_mean'] = np.mean(results['ai_change']['without_max_minus_first'])
    results['ai_change']['without_final_mean'] = np.mean(results['ai_change']['without_final_minus_first'])
    results['ai_change']['with_max_mean'] = np.mean(results['ai_change']['with_max_minus_first'])
    results['ai_change']['with_final_mean'] = np.mean(results['ai_change']['with_final_minus_first'])

    results['prompt_length'] = {
        'without_mean': df_without['prompt_length'].mean(),
        'with_mean': df_with['prompt_length'].mean(),
        'without_change': 0,
        'with_change': 0
    }

    for df_key, df in [('without', df_without), ('with', df_with)]:
        changes = []
        for task_id in df['task_id'].unique():
            task_data = df[df['task_id'] == task_id].sort_values('version_number')

            if len(task_data) >= 2:
                for i in range(1, len(task_data)):
                    change = task_data.iloc[i]['prompt_length'] - task_data.iloc[i-1]['prompt_length']
                    changes.append(change)
        results['prompt_length'][f'{df_key}_change'] = np.mean(changes) if changes else 0

    threshold_without = np.percentile(df_without['prompt_time_seconds'].dropna(), 95)
    threshold_with = np.percentile(df_with['prompt_time_seconds'].dropna(), 95)

    without_time_filtered = df_without[df_without['prompt_time_seconds'] <= threshold_without]
    with_time_filtered = df_with[df_with['prompt_time_seconds'] <= threshold_with]

    results['input_time'] = {
        'without': without_time_filtered['prompt_time_seconds'].mean(),
        'with': with_time_filtered['prompt_time_seconds'].mean()
    }

    results['difficulty'] = {'without': {}, 'with': {}}
    for difficulty in ['Easy', 'Medium', 'Hard']:
        if difficulty == 'Easy':
            without_diff = df_without[df_without['user_difficulty_rating'] <= 3]
            with_diff = df_with[df_with['user_difficulty_rating'] <= 3]
        elif difficulty == 'Medium':
            without_diff = df_without[(df_without['user_difficulty_rating'] > 3) & (df_without['user_difficulty_rating'] <= 6)]
            with_diff = df_with[(df_with['user_difficulty_rating'] > 3) & (df_with['user_difficulty_rating'] <= 6)]
        else:
            without_diff = df_without[df_without['user_difficulty_rating'] > 6]
            with_diff = df_with[df_with['user_difficulty_rating'] > 6]

        results['difficulty']['without'][difficulty] = without_diff['ai_similarity_score'].mean() if len(without_diff) > 0 else 0
        results['difficulty']['with'][difficulty] = with_diff['ai_similarity_score'].mean() if len(with_diff) > 0 else 0

    results['rounds_dist'] = {'without': {}, 'with': {}}
    for df_key, df in [('without', df_without), ('with', df_with)]:
        round_counts = df.groupby('task_id')['version_number'].max()
        total = len(round_counts)
        for r in range(1, 9):
            count = (round_counts == r).sum()
            results['rounds_dist'][df_key][r] = (count / total * 100) if total > 0 else 0

    results['avg_rounds'] = {}
    for df_key, df in [('without', df_without), ('with', df_with)]:
        round_counts = df.groupby('task_id')['version_number'].max()
        results['avg_rounds'][df_key] = round_counts.mean()

    results['total_time'] = {'without': [], 'with': []}
    for df_key, df, df_filtered in [('without', df_without, without_time_filtered),
                                      ('with', df_with, with_time_filtered)]:
        for task_id in df['task_id'].unique():
            task_data = df_filtered[df_filtered['task_id'] == task_id]
            if len(task_data) > 0:
                task_time = task_data['prompt_time_seconds'].sum()
                results['total_time'][df_key].append(task_time)

    results['total_time']['without_mean'] = np.mean(results['total_time']['without'])
    results['total_time']['with_mean'] = np.mean(results['total_time']['with'])

    results['final_prompt_length'] = {'without': [], 'with': []}
    for df_key, df in [('without', df_without), ('with', df_with)]:
        for task_id in df['task_id'].unique():
            task_data = df[df['task_id'] == task_id].sort_values('version_number')
            final_length = task_data.iloc[-1]['prompt_length']
            results['final_prompt_length'][df_key].append(final_length)

    results['final_prompt_length']['without_mean'] = np.mean(results['final_prompt_length']['without'])
    results['final_prompt_length']['with_mean'] = np.mean(results['final_prompt_length']['with'])

    results['completion_50'] = {'without': 0, 'with': 0}
    results['completion_90'] = {'without': 0, 'with': 0}
    results['median_rounds'] = {'without': 0, 'with': 0}
    results['avg_rounds_multi'] = {'without': 0, 'with': 0}

    for df_key, df in [('without', df_without), ('with', df_with)]:
        round_counts = df.groupby('task_id')['version_number'].max()
        total = len(round_counts)

        results['median_rounds'][df_key] = round_counts.median()

        multi_round_tasks = round_counts[round_counts > 1]
        results['avg_rounds_multi'][df_key] = multi_round_tasks.mean() if len(multi_round_tasks) > 0 else 0

        cumulative = 0
        for r in range(1, 9):
            count = (round_counts == r).sum()
            cumulative += count
            pct = cumulative / total * 100

            if pct >= 50 and results['completion_50'][df_key] == 0:
                results['completion_50'][df_key] = r
            if pct >= 90 and results['completion_90'][df_key] == 0:
                results['completion_90'][df_key] = r
                break

    return results

def create_plots(results: dict, output_dir: Path):

    def apply_format(ax, ylabel, show_legend=False):
        ax.set_title('')
        ax.set_xlabel('')
        ax.set_ylabel(ylabel, fontsize=26)
        ax.tick_params(axis='both', labelsize=24)
        if show_legend:
            ax.legend(fontsize=18, loc='upper right')
        ax.grid(alpha=0.3, axis='y')

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(2)
    width = 0.35

    max_changes = [results['ai_change']['without_max_mean'], results['ai_change']['with_max_mean']]
    final_changes = [results['ai_change']['without_final_mean'], results['ai_change']['with_final_mean']]

    ax.bar(x[0] - width/2, max_changes[0], width, label='Base Stage', alpha=0.7, color=COLOR_WITHOUT,edgecolor='black')
    ax.bar(x[0] + width/2, max_changes[1], width, label='Agent Stage', alpha=0.7, color=COLOR_WITH,edgecolor='black')
    ax.bar(x[1] - width/2, final_changes[0], width, alpha=0.7, color=COLOR_WITHOUT,edgecolor='black')
    ax.bar(x[1] + width/2, final_changes[1], width, alpha=0.7, color=COLOR_WITH,edgecolor='black')

    ax.set_xticks(x)
    ax.set_xticklabels(['Max - First', 'Final - First'], fontsize=22)
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_ylim(top=max(max_changes + final_changes) * 1.2)
    apply_format(ax, 'AI Score Change', show_legend=True)
    plt.tight_layout()
    plt.savefig(output_dir / '1_ai_score_change.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 1. AI Score Change Comparison")

    fig, ax = plt.subplots(figsize=(8, 6))
    categories = ['Without_Agent', 'With_Agent']
    times = [results['input_time']['without'], results['input_time']['with']]
    bars = ax.bar(categories, times, alpha=0.7, color=[COLOR_WITHOUT, COLOR_WITH])
    apply_format(ax, 'Time (seconds)')
    plt.tight_layout()
    plt.savefig(output_dir / '2_avg_input_time.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 2. Average Input Time")

    fig, ax = plt.subplots(figsize=(8, 6))
    avg_rounds = [results['avg_rounds']['without'], results['avg_rounds']['with']]
    ax.bar(categories, avg_rounds, alpha=0.7, color=[COLOR_WITHOUT, COLOR_WITH])
    apply_format(ax, 'Average Rounds')
    plt.tight_layout()
    plt.savefig(output_dir / '3_avg_completion_rounds.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 3. Average Completion Rounds")

    fig, ax = plt.subplots(figsize=(8, 6))
    total_times = [results['total_time']['without_mean'], results['total_time']['with_mean']]
    ax.bar(categories, total_times, alpha=0.7, color=[COLOR_WITHOUT, COLOR_WITH])
    apply_format(ax, 'Total Time (seconds)')
    plt.tight_layout()
    plt.savefig(output_dir / '4_total_time_spent.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 4. Total Time Spent")

    fig, ax = plt.subplots(figsize=(8, 6))
    final_lengths = [results['final_prompt_length']['without_mean'], results['final_prompt_length']['with_mean']]
    ax.bar(categories, final_lengths, alpha=0.7, color=[COLOR_WITHOUT, COLOR_WITH])
    apply_format(ax, 'Average Prompt Length (characters)')
    plt.tight_layout()
    plt.savefig(output_dir / '5_final_prompt_length.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 5. Final Prompt Length")

    fig, ax = plt.subplots(figsize=(8, 6))
    avg_changes = [results['prompt_length']['without_change'], results['prompt_length']['with_change']]
    ax.bar(categories, avg_changes, alpha=0.7, color=[COLOR_WITHOUT, COLOR_WITH])
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    apply_format(ax, 'Average Length Change (characters/round)')
    plt.tight_layout()
    plt.savefig(output_dir / '6_avg_prompt_change.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 6. Average Prompt Length Change")

    fig, ax = plt.subplots(figsize=(8, 6))
    multi_vals = [results['avg_rounds_multi']['without'], results['avg_rounds_multi']['with']]
    ax.bar(categories, multi_vals, alpha=0.7, color=[COLOR_WITHOUT, COLOR_WITH])
    for i, v in enumerate(multi_vals):
        ax.text(i, v + 0.05, f'{v:.2f}', ha='center', fontsize=20, fontweight='bold')
    apply_format(ax, 'Average Rounds')
    plt.tight_layout()
    plt.savefig(output_dir / '7_avg_rounds_multi.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 7. Average Rounds (Multi-Round Tasks)")

def generate_report(results: dict, output_path: Path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("AB Test Comparison Report: With_Agent vs Without_Agent\n")
        f.write("="*80 + "\n\n")

        f.write("【AI Score Change】\n")
        f.write(f"  Without_Agent (Max - First):   {results['ai_change']['without_max_mean']:+.2f}\n")
        f.write(f"  Without_Agent (Final - First): {results['ai_change']['without_final_mean']:+.2f}\n")
        f.write(f"  With_Agent (Max - First):      {results['ai_change']['with_max_mean']:+.2f}\n")
        f.write(f"  With_Agent (Final - First):    {results['ai_change']['with_final_mean']:+.2f}\n\n")

        f.write("【Prompt Length】\n")
        f.write(f"  Without_Agent Average: {results['prompt_length']['without_mean']:.1f} chars\n")
        f.write(f"  With_Agent Average:    {results['prompt_length']['with_mean']:.1f} chars\n")
        f.write(f"  Without_Agent Change:  {results['prompt_length']['without_change']:+.1f} chars/round\n")
        f.write(f"  With_Agent Change:     {results['prompt_length']['with_change']:+.1f} chars/round\n\n")

        f.write("【Input Time (top 5% outliers removed)】\n")
        f.write(f"  Without_Agent per Version: {results['input_time']['without']:.1f} sec\n")
        f.write(f"  With_Agent per Version:    {results['input_time']['with']:.1f} sec\n")
        f.write(f"  Difference:                {results['input_time']['with'] - results['input_time']['without']:+.1f} sec\n\n")

        f.write("【AI Score by Difficulty】\n")
        for diff in ['Easy', 'Medium', 'Hard']:
            f.write(f"  {diff:8s} - Without: {results['difficulty']['without'][diff]:.2f}, ")
            f.write(f"With: {results['difficulty']['with'][diff]:.2f}\n")
        f.write("\n")

        f.write("【Completion Rounds】\n")
        f.write(f"  Without_Agent Average: {results['avg_rounds']['without']:.2f} rounds\n")
        f.write(f"  With_Agent Average:    {results['avg_rounds']['with']:.2f} rounds\n")
        f.write(f"  Difference:            {results['avg_rounds']['with'] - results['avg_rounds']['without']:+.2f}\n\n")

        f.write("【Total Time Spent (top 5% outliers removed)】\n")
        f.write(f"  Without_Agent: {results['total_time']['without_mean']:.1f} sec/task\n")
        f.write(f"  With_Agent:    {results['total_time']['with_mean']:.1f} sec/task\n")
        f.write(f"  Difference:    {results['total_time']['with_mean'] - results['total_time']['without_mean']:+.1f} sec\n\n")

        f.write("【Round Distribution】\n")
        f.write("  Rounds | Without | With\n")
        f.write("  -------+---------+------\n")
        for r in range(1, 9):
            f.write(f"    {r}    |  {results['rounds_dist']['without'][r]:5.1f}% | {results['rounds_dist']['with'][r]:5.1f}%\n")

        f.write("\n【Final Prompt Length】\n")
        f.write(f"  Without_Agent: {results['final_prompt_length']['without_mean']:.1f} chars\n")
        f.write(f"  With_Agent:    {results['final_prompt_length']['with_mean']:.1f} chars\n")
        f.write(f"  Difference:    {results['final_prompt_length']['with_mean'] - results['final_prompt_length']['without_mean']:+.1f} chars\n")

        f.write("\n【Completion Milestones】\n")
        f.write(f"  50% completed by:\n")
        f.write(f"    Without_Agent: {results['completion_50']['without']} rounds\n")
        f.write(f"    With_Agent:    {results['completion_50']['with']} rounds\n")
        f.write(f"  90% completed by:\n")
        f.write(f"    Without_Agent: {results['completion_90']['without']} rounds\n")
        f.write(f"    With_Agent:    {results['completion_90']['with']} rounds\n")

        f.write("\n【Median Completion Rounds】\n")
        f.write(f"  Without_Agent: {results['median_rounds']['without']:.1f} rounds\n")
        f.write(f"  With_Agent:    {results['median_rounds']['with']:.1f} rounds\n")
        f.write(f"  Difference:    {results['median_rounds']['with'] - results['median_rounds']['without']:+.1f} rounds\n")

        f.write("\n【Average Rounds for Multi-Round Tasks】\n")
        f.write(f"  Without_Agent: {results['avg_rounds_multi']['without']:.2f} rounds\n")
        f.write(f"  With_Agent:    {results['avg_rounds_multi']['with']:.2f} rounds\n")
        f.write(f"  Difference:    {results['avg_rounds_multi']['with'] - results['avg_rounds_multi']['without']:+.2f} rounds\n")

        f.write("\n" + "="*80 + "\n")

    print(f"  ✓ Report: {output_path}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python compare.py <without_agent.csv> <with_agent.csv>")
        sys.exit(1)
def main():
    # 可以从命令行参数读取，或使用本地 data/ 目录的默认文件
    if len(sys.argv) >= 3:
        csv_without = sys.argv[1]
        csv_with = sys.argv[2]
        print("使用命令行参数提供的数据文件")
    else:
        # 使用 Analyze/data/ 目录的默认文件
        data_dir = Path(__file__).parent.parent / "data"  # Analyze/data/
        csv_without = str(data_dir / "ultiwithout.csv")
        csv_with = str(data_dir / "ultiwith.csv")
        print("使用 Analyze/data/ 目录的数据文件")
        
        if not Path(csv_without).exists() or not Path(csv_with).exists():
            print(f"❌ ERROR: 数据文件不存在")
            print(f"   Expected: {csv_without}")
            print(f"   Expected: {csv_with}")
            print(f"   请运行: python prepare_data.py")
            print(f"   或提供命令行参数: python table5.py <without.csv> <with.csv>")
            sys.exit(1)

    print("\n📂 Loading data...")
    df_without = load_dataset(csv_without)
    df_with = load_dataset(csv_with)

    print("\n📊 Analyzing...")
    results = analyze_data(df_without, df_with)

    print("\n🎨 Creating visualizations...")
    create_plots(results, FIGURES_DIR)

    print("\n📝 Generating report...")
    report_path = OUTPUT_DIR / "comparison_report.txt"
    generate_report(results, report_path)

    print(f"\n✅ Complete!")
    print(f"  Figures: {FIGURES_DIR}/")
    print(f"  Report:  {report_path}\n")

if __name__ == '__main__':
    main()
