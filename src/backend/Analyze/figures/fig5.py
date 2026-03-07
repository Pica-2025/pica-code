
import pandas as pd
import numpy as np
import ast
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

DIMENSIONS = ['spatialcomposition', 'style', 'subjectscene',
              'lightingcolor', 'detailtexture']

DIMENSION_LABELS = {
    'spatialcomposition': 'SPA',
    'style': 'STY',
    'subjectscene': 'SUB',
    'lightingcolor': 'LIG',
    'detailtexture': 'DET',
}

# 使用 Analyze/outputs 目录
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "fig5"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR = OUTPUT_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

def load_dataset(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    all_dims = DIMENSIONS + ['others']
    for dim in all_dims:
        col = f'classified_{dim}'
        if col in df.columns:
            df[col] = df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else []))

    print(f"✅ {csv_path}: {len(df)} rows, {df['task_id'].nunique()} tasks")
    return df

def analyze_dimension_presence(df_without: pd.DataFrame, df_with: pd.DataFrame) -> dict:
    results = {}

    results['avg_dims_by_version'] = {'without': {}, 'with': {}}

    for df_key, df in [('without', df_without), ('with', df_with)]:
        for v in range(1, 9):
            v_data = df[df['version_number'] == v]
            if len(v_data) > 0:
                dim_counts = []
                for idx, row in v_data.iterrows():
                    count = sum(1 for dim in DIMENSIONS if len(row.get(f'classified_{dim}', [])) > 0)
                    dim_counts.append(count)
                results['avg_dims_by_version'][df_key][v] = np.mean(dim_counts)

    results['final_dim_chars'] = {'without': {}, 'with': {}}

    for df_key, df in [('without', df_without), ('with', df_with)]:
        for dim in DIMENSIONS:
            char_counts = []
            for task_id in df['task_id'].unique():
                task_data = df[df['task_id'] == task_id].sort_values('version_number')
                final_row = task_data.iloc[-1]
                sentences = final_row.get(f'classified_{dim}', [])
                char_count = sum(len(str(s)) for s in sentences)
                char_counts.append(char_count)

            results['final_dim_chars'][df_key][dim] = np.mean(char_counts) if char_counts else 0

    results['final_dim_presence'] = {'without': {}, 'with': {}}

    for df_key, df in [('without', df_without), ('with', df_with)]:
        for dim in DIMENSIONS:
            presence_count = 0
            total = 0
            for task_id in df['task_id'].unique():
                task_data = df[df['task_id'] == task_id].sort_values('version_number')
                total += 1
                final_row = task_data.iloc[-1]
                if len(final_row.get(f'classified_{dim}', [])) > 0:
                    presence_count += 1

            results['final_dim_presence'][df_key][dim] = (presence_count / total * 100) if total > 0 else 0

    results['v1_to_final_change'] = {'without': [], 'with': []}
    results['final_avg_dims'] = {'without': 0, 'with': 0}

    for df_key, df in [('without', df_without), ('with', df_with)]:
        changes = []
        final_dims = []

        for task_id in df['task_id'].unique():
            task_data = df[df['task_id'] == task_id].sort_values('version_number')

            if len(task_data) > 0:
                first_row = task_data.iloc[0]
                v1_count = sum(1 for dim in DIMENSIONS if len(first_row.get(f'classified_{dim}', [])) > 0)

                final_row = task_data.iloc[-1]
                final_count = sum(1 for dim in DIMENSIONS if len(final_row.get(f'classified_{dim}', [])) > 0)

                changes.append(final_count - v1_count)
                final_dims.append(final_count)

        results['v1_to_final_change'][df_key] = changes
        results['final_avg_dims'][df_key] = np.mean(final_dims) if final_dims else 0

    return results

def create_visualizations(results: dict, output_dir: Path):

    fig, ax = plt.subplots(figsize=(12, 5))
    versions = list(range(1, 9))
    without_dims = [results['avg_dims_by_version']['without'].get(v, 0) for v in versions]
    with_dims = [results['avg_dims_by_version']['with'].get(v, 0) for v in versions]

    ax.plot(versions, without_dims, 'o-', label='Without_Agent', linewidth=2,
            markersize=8, color=COLOR_WITHOUT)
    ax.plot(versions, with_dims, 's-', label='With_Agent', linewidth=2,
            markersize=8, color=COLOR_WITH)

    ax.set_title('')
    ax.set_xlabel('')
    ax.set_ylabel('Average Number of Dimensions', fontsize=22)
    ax.tick_params(axis='both', labelsize=20)
    ax.legend(fontsize=18, loc='upper right')
    ax.grid(alpha=0.3, axis='y')
    ax.set_xticks(versions)
    plt.tight_layout()
    plt.savefig(output_dir / 'semantic_dims_by_version.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Dimensions by version")

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(DIMENSIONS))
    width = 0.35

    without_presence = [results['final_dim_presence']['without'][dim] for dim in DIMENSIONS]
    with_presence = [results['final_dim_presence']['with'][dim] for dim in DIMENSIONS]

    ax.bar(x - width/2, without_presence, width, label='Base Stage',
           alpha=0.7, color=COLOR_WITHOUT, edgecolor='black')
    ax.bar(x + width/2, with_presence, width, label='Agent Stage',
           alpha=0.7, color=COLOR_WITH, edgecolor='black')

    for i in range(len(DIMENSIONS)):
        left_x = x[i] - width/2
        right_x = x[i] + width/2
        top = max(without_presence[i], with_presence[i]) + 1.5
        bracket_h = 2.0
        diff = with_presence[i] - without_presence[i]

        ax.plot([left_x, left_x, right_x, right_x],
                [top, top + bracket_h, top + bracket_h, top],
                color='black', linewidth=1.2, clip_on=False)

        label = f'+{diff:.1f}%' if diff >= 0 else f'{diff:.1f}%'
        ax.text((left_x + right_x) / 2, top + bracket_h + 0.5,
                label, ha='center', va='bottom', fontsize=18, fontweight='bold')

    ax.set_title('')
    ax.set_xlabel('')
    ax.set_ylabel('Dimension-Level Hit Rate (%)', fontsize=22)
    ax.set_xticks(x)
    ax.set_xticklabels([DIMENSION_LABELS[d] for d in DIMENSIONS], fontsize=26)
    ax.tick_params(axis='y', labelsize=26)
    ax.legend(fontsize=22, loc='upper right')
    ax.grid(alpha=0.3, axis='y')
    ax.set_ylim([0, 145])
    plt.tight_layout()
    plt.savefig(output_dir / 'semantic_final_presence.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Final dimension presence")

def generate_report(results: dict, output_path: Path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Semantic Dimension Analysis Report\n")
        f.write("="*80 + "\n\n")

        f.write("【Average Dimensions by Version】\n\n")

        f.write("Version | Without_Agent | With_Agent | Difference\n")
        f.write("--------+---------------+------------+-----------\n")
        for v in range(1, 9):
            without = results['avg_dims_by_version']['without'].get(v, 0)
            with_v = results['avg_dims_by_version']['with'].get(v, 0)
            diff = with_v - without
            f.write(f"  v{v}    |     {without:.2f}      |   {with_v:.2f}   | {diff:+.2f}\n")

        without_avg = np.mean([results['avg_dims_by_version']['without'].get(v, 0) for v in range(1, 9)])
        with_avg = np.mean([results['avg_dims_by_version']['with'].get(v, 0) for v in range(1, 9)])

        f.write(f"\nOverall Average:\n")
        f.write(f"  Without_Agent: {without_avg:.2f} dimensions per version\n")
        f.write(f"  With_Agent:    {with_avg:.2f} dimensions per version\n")
        f.write(f"  Difference:    {with_avg - without_avg:+.2f}\n")

        without_trend = results['avg_dims_by_version']['without'].get(8, 0) - results['avg_dims_by_version']['without'].get(1, 0)
        with_trend = results['avg_dims_by_version']['with'].get(8, 0) - results['avg_dims_by_version']['with'].get(1, 0)

        f.write(f"\nTrend from v1 to v8:\n")
        f.write(f"  Without_Agent: {without_trend:+.2f} dimensions\n")
        f.write(f"  With_Agent:    {with_trend:+.2f} dimensions\n")

        f.write("\n")

        f.write("【Final Version: Character Count by Dimension】\n\n")

        f.write("Dimension            | Without_Agent | With_Agent | Difference | % Change\n")
        f.write("---------------------+---------------+------------+------------+---------\n")

        total_without = 0
        total_with = 0

        for dim in DIMENSIONS:
            without = results['final_dim_chars']['without'][dim]
            with_v = results['final_dim_chars']['with'][dim]
            diff = with_v - without
            pct_change = (diff / without * 100) if without > 0 else 0

            total_without += without
            total_with += with_v

            f.write(f"{dim:20s} | {without:13.1f} | {with_v:10.1f} | {diff:+10.1f} | {pct_change:+6.1f}%\n")

        f.write("---------------------+---------------+------------+------------+---------\n")
        f.write(f"{'TOTAL':20s} | {total_without:13.1f} | {total_with:10.1f} | {total_with - total_without:+10.1f} | {((total_with - total_without) / total_without * 100):+6.1f}%\n")

        dim_changes = [(dim, results['final_dim_chars']['with'][dim] - results['final_dim_chars']['without'][dim])
                       for dim in DIMENSIONS]
        dim_changes.sort(key=lambda x: x[1], reverse=True)

        f.write(f"\nTop 3 Dimensions with Largest Character Increase:\n")
        for i, (dim, change) in enumerate(dim_changes[:3], 1):
            f.write(f"  {i}. {dim}: +{change:.1f} characters\n")

        f.write("\n")

        f.write("【Final Version: Dimension Presence Rate】\n\n")

        f.write("Dimension            | Without_Agent | With_Agent | Difference\n")
        f.write("---------------------+---------------+------------+-----------\n")

        for dim in DIMENSIONS:
            without = results['final_dim_presence']['without'][dim]
            with_v = results['final_dim_presence']['with'][dim]
            diff = with_v - without
            f.write(f"{dim:20s} | {without:12.1f}% | {with_v:9.1f}% | {diff:+6.1f}%\n")

        without_high_coverage = sum(1 for dim in DIMENSIONS if results['final_dim_presence']['without'][dim] >= 80)
        with_high_coverage = sum(1 for dim in DIMENSIONS if results['final_dim_presence']['with'][dim] >= 80)

        f.write(f"\nDimensions with ≥80% presence rate:\n")
        f.write(f"  Base Stage: {without_high_coverage}/{len(DIMENSIONS)} dimensions\n")
        f.write(f"  Agent Stage:    {with_high_coverage}/{len(DIMENSIONS)} dimensions\n")

        without_min_dim = min(DIMENSIONS, key=lambda d: results['final_dim_presence']['without'][d])
        with_min_dim = min(DIMENSIONS, key=lambda d: results['final_dim_presence']['with'][d])

        f.write(f"\nLowest presence dimension:\n")
        f.write(f"  Base Stage: {without_min_dim} ({results['final_dim_presence']['without'][without_min_dim]:.1f}%)\n")
        f.write(f"  Agent Stage:    {with_min_dim} ({results['final_dim_presence']['with'][with_min_dim]:.1f}%)\n")

        f.write("\n")

        f.write("【First Version to Final Version: Dimension Change】\n\n")

        without_changes = results['v1_to_final_change']['without']
        with_changes = results['v1_to_final_change']['with']

        without_avg_change = np.mean(without_changes) if without_changes else 0
        with_avg_change = np.mean(with_changes) if with_changes else 0

        f.write(f"Average dimension increase from v1 to final:\n")
        f.write(f"  Without_Agent: {without_avg_change:+.2f} dimensions per task\n")
        f.write(f"  With_Agent:    {with_avg_change:+.2f} dimensions per task\n")
        f.write(f"  Difference:    {with_avg_change - without_avg_change:+.2f}\n\n")

        without_positive = sum(1 for x in without_changes if x > 0)
        without_zero = sum(1 for x in without_changes if x == 0)
        without_negative = sum(1 for x in without_changes if x < 0)

        with_positive = sum(1 for x in with_changes if x > 0)
        with_zero = sum(1 for x in with_changes if x == 0)
        with_negative = sum(1 for x in with_changes if x < 0)

        without_total = len(without_changes)
        with_total = len(with_changes)

        f.write("Distribution of dimension changes:\n")
        f.write("                 | Increased | No Change | Decreased\n")
        f.write("-----------------+-----------+-----------+----------\n")
        f.write(f"Without_Agent    | {without_positive:4d} ({without_positive/without_total*100:5.1f}%) | "
                f"{without_zero:4d} ({without_zero/without_total*100:5.1f}%) | "
                f"{without_negative:4d} ({without_negative/without_total*100:5.1f}%)\n")
        f.write(f"With_Agent       | {with_positive:4d} ({with_positive/with_total*100:5.1f}%) | "
                f"{with_zero:4d} ({with_zero/with_total*100:5.1f}%) | "
                f"{with_negative:4d} ({with_negative/with_total*100:5.1f}%)\n")

        f.write("\n")

        f.write("【Final Version: Average Number of Dimensions】\n\n")

        without_final_avg = results['final_avg_dims']['without']
        with_final_avg = results['final_avg_dims']['with']

        f.write(f"Average dimensions in final version:\n")
        f.write(f"  Without_Agent: {without_final_avg:.2f} dimensions\n")
        f.write(f"  With_Agent:    {with_final_avg:.2f} dimensions\n")
        f.write(f"  Difference:    {with_final_avg - without_final_avg:+.2f}\n")

        f.write("\n" + "="*80 + "\n")

        f.write("\n【KEY INSIGHTS】\n\n")

        f.write("1. Final Version Dimension Count:\n")
        f.write(f"   With_Agent final prompts average {with_final_avg:.2f} dimensions,\n")
        f.write(f"   compared to {without_final_avg:.2f} in Without_Agent ({with_final_avg - without_final_avg:+.2f} difference).\n\n")

        f.write("2. Dimension Growth During Iteration:\n")
        without_avg_change = np.mean(without_changes) if without_changes else 0
        with_avg_change = np.mean(with_changes) if with_changes else 0
        f.write(f"   From v1 to final, Without_Agent adds {without_avg_change:+.2f} dimensions on average,\n")
        f.write(f"   while With_Agent adds {with_avg_change:+.2f} dimensions.\n\n")

        f.write("3. Content Detail:\n")
        total_without = sum(results['final_dim_chars']['without'][dim] for dim in DIMENSIONS)
        total_with = sum(results['final_dim_chars']['with'][dim] for dim in DIMENSIONS)
        pct_increase = ((total_with - total_without) / total_without * 100) if total_without > 0 else 0
        f.write(f"   With_Agent prompts contain {pct_increase:+.1f}% more characters in total,\n")
        f.write(f"   indicating more detailed descriptions ({total_with:.0f} vs {total_without:.0f} chars).\n\n")

        f.write("4. Coverage Improvement:\n")
        if with_high_coverage > without_high_coverage:
            f.write(f"   With_Agent achieves high coverage (≥80%) in {with_high_coverage} dimensions\n")
            f.write(f"   compared to {without_high_coverage} dimensions in Without_Agent.\n\n")
        else:
            f.write(f"   Both groups show similar coverage patterns ({with_high_coverage} vs {without_high_coverage} dimensions ≥80%).\n\n")

        f.write("="*80 + "\n")

    print(f"  ✓ Report: {output_path}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python analyze_semantic.py <without_agent.csv> <with_agent.csv>")
        sys.exit(1)

    csv_without = sys.argv[1]
    csv_with = sys.argv[2]

    print("\n📂 Loading data...")
    df_without = load_dataset(csv_without)
    df_with = load_dataset(csv_with)

    print("\n📊 Analyzing dimensions...")
    results = analyze_dimension_presence(df_without, df_with)

    print("\n🎨 Creating visualizations...")
    create_visualizations(results, FIGURES_DIR)

    print("\n📝 Generating report...")
    report_path = OUTPUT_DIR / "semantic_analysis_report.txt"
    generate_report(results, report_path)

    print(f"\n✅ Complete!")
    print(f"  Figures: {FIGURES_DIR}/")
    print(f"  Report:  {report_path}\n")

if __name__ == '__main__':
    main()
