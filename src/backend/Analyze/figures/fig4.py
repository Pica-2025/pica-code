
import pandas as pd
import numpy as np
import ast
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

MODEL = os.environ.get('SEMANTIC_MODEL', 'gpt-5.2')

DIMENSIONS = ['spatialcomposition', 'style', 'subjectscene',
              'lightingcolor', 'detailtexture']
DIMENSION_LABELS = {
    'spatialcomposition': 'SPA',
    'style': 'STY',
    'subjectscene': 'SUB',
    'lightingcolor': 'LIG',
    'detailtexture': 'DET',
}
GROUPS = ['first', 'second', 'last']
GROUP_LABELS = {
    'first': 'First Round',
    'second': 'Second Round',
    'last': 'Last Round',
}

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from color_config import COLORS
except ImportError:
    COLORS = {}
COLOR_BASE = COLORS.get('base_stage', '#FAA26F')

# 使用本地 outputs 目录
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "fig4"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR = OUTPUT_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)
CACHE_PATH = OUTPUT_DIR / "semantic_mapping_rq2_raw.json"

plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

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

def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    for dim in DIMENSIONS + ['others']:
        col = f'classified_{dim}'
        if col in df.columns:
            df[col] = df[col].apply(safe_eval_list)

    for dim in DIMENSIONS + ['others']:
        col = f'gt_classified_{dim}'
        if col in df.columns:
            df[col] = df[col].apply(safe_eval_list)

    for col in ['is_first_round', 'is_last_round']:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: True if (x is True or x == 1 or
                                   (isinstance(x, str) and x.lower() == 'true'))
                else False
            )

    print(f"✅ {csv_path}: {len(df)} rows, {df['task_id'].nunique()} tasks", flush=True)
    return df

def build_matching_prompt(gt_dims: dict, user_dims: dict) -> str:
    lines = []
    lines.append("You are evaluating how well a user's text-to-image prompt covers the concepts "
                 "described in a ground truth reference, dimension by dimension.")
    lines.append("")
    lines.append("For each dimension below, I provide a list of Ground Truth (GT) concept sentences "
                 "and a list of User prompt sentences. For each GT sentence, determine if the User's "
                 "sentences contain a semantically equivalent or closely matching concept.")
    lines.append("")
    lines.append("Rules:")
    lines.append("- A match means the user expressed the SAME or VERY SIMILAR concept, "
                 "even if using different words or phrasing.")
    lines.append("- Partial overlap counts as a match if the core meaning is preserved.")
    lines.append("- If the user list is empty, all GT sentences are unmatched (0).")
    lines.append("")

    has_any_gt = False
    for dim in DIMENSIONS:
        gt_list = gt_dims.get(dim, [])
        user_list = user_dims.get(dim, [])
        if not gt_list:
            continue
        has_any_gt = True
        lines.append(f"## {dim} ({len(gt_list)} GT sentences)")
        lines.append(f"GT: {json.dumps(gt_list, ensure_ascii=False)}")
        lines.append(f"User: {json.dumps(user_list, ensure_ascii=False)}")
        lines.append("")

    if not has_any_gt:
        return None

    lines.append("Return ONLY a JSON object. For each dimension that appears above, "
                 "provide an array of 1 (matched) or 0 (not matched) corresponding to each GT sentence.")
    lines.append('Example: {"spatialcomposition": [1, 0, 1], "style": [1]}')
    lines.append("Do NOT include dimensions that were not listed above.")

    return "\n".join(lines)

def call_gpt(prompt: str, client, model: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_completion_tokens=1000,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content.strip()
            result = json.loads(text)
            return result
        except json.JSONDecodeError:
            try:
                start = text.index('{')
                end = text.rindex('}') + 1
                result = json.loads(text[start:end])
                return result
            except:
                pass
            print(f"    ⚠️ JSON parse error (attempt {attempt+1})", flush=True)
        except Exception as e:
            wait = 2 ** attempt
            print(f"    ⚠️ API error: {e} (retry in {wait}s)", flush=True)
            time.sleep(wait)
    return {}

def match_single(gt_dims: dict, user_dims: dict, client, model: str) -> dict:
    result = {}
    for dim in DIMENSIONS:
        gt_list = gt_dims.get(dim, [])
        result[dim] = {
            'total': len(gt_list),
            'matched': 0,
            'details': [0] * len(gt_list)
        }

    prompt = build_matching_prompt(gt_dims, user_dims)
    if prompt is None:
        return result

    gpt_result = call_gpt(prompt, client, model)

    for dim in DIMENSIONS:
        gt_list = gt_dims.get(dim, [])
        if not gt_list:
            continue
        matches = gpt_result.get(dim, [])
        if isinstance(matches, list) and len(matches) == len(gt_list):
            matches = [1 if m else 0 for m in matches]
        else:
            matches = [0] * len(gt_list)
        result[dim]['details'] = matches
        result[dim]['matched'] = sum(matches)

    return result

def run_analysis(df, client, model):
    cache = {}
    if CACHE_PATH.exists():
        with open(CACHE_PATH, 'r') as f:
            cache = json.load(f)
        print(f"  📦 Loaded cache: {len(cache)} entries", flush=True)

    all_results = []
    total_api_calls = 0
    task_ids = df['task_id'].unique()

    print(f"\n  🔍 Processing {len(task_ids)} tasks (first + second + last rounds)", flush=True)

    for i, task_id in enumerate(task_ids):
        task_data = df[df['task_id'] == task_id].sort_values('version_number')
        if len(task_data) == 0:
            continue

        first_row = task_data[task_data['is_first_round'] == True]
        last_row = task_data[task_data['is_last_round'] == True]
        second_row = task_data[task_data['version_number'] == 2]

        for round_name, round_data in [('first', first_row), ('second', second_row), ('last', last_row)]:
            if len(round_data) == 0:
                continue
            row = round_data.iloc[0]

            gt_dims = {}
            for dim in DIMENSIONS:
                col = f'gt_classified_{dim}'
                gt_dims[dim] = row[col] if isinstance(row[col], list) else []

            user_dims = {}
            for dim in DIMENSIONS:
                col = f'classified_{dim}'
                user_dims[dim] = row[col] if isinstance(row[col], list) else []

            cache_key = f"base_{task_id}_{round_name}"
            if cache_key in cache:
                match_result = cache[cache_key]
            else:
                match_result = match_single(gt_dims, user_dims, client, model)
                cache[cache_key] = match_result
                total_api_calls += 1

                if total_api_calls % 20 == 0:
                    with open(CACHE_PATH, 'w') as f:
                        json.dump(cache, f, ensure_ascii=False)
                    print(f"\n    💾 Cache saved ({total_api_calls} API calls)", flush=True)

            tidx = str(row.get('target_index', ''))
            all_results.append({
                'task_id': task_id,
                'target_index': tidx,
                'round': round_name,
                'match_result': match_result,
            })

        print(f"\r    {i+1}/{len(task_ids)} tasks done (API calls: {total_api_calls})...", end='', flush=True)

    print()

    with open(CACHE_PATH, 'w') as f:
        json.dump(cache, f, ensure_ascii=False)
    print(f"\n  💾 Cache saved ({total_api_calls} total API calls)", flush=True)

    return all_results

def aggregate_results(all_results: list) -> dict:
    agg = {g: {d: {'total': 0, 'matched': 0, 'n_tasks': 0} for d in DIMENSIONS} for g in GROUPS}

    for entry in all_results:
        group = entry['round']
        if group not in agg:
            continue
        mr = entry['match_result']
        for dim in DIMENSIONS:
            dim_result = mr.get(dim, {})
            total = dim_result.get('total', 0)
            matched = dim_result.get('matched', 0)
            if total > 0:
                agg[group][dim]['total'] += total
                agg[group][dim]['matched'] += matched
                agg[group][dim]['n_tasks'] += 1

    for g in GROUPS:
        for d in DIMENSIONS:
            total = agg[g][d]['total']
            matched = agg[g][d]['matched']
            agg[g][d]['hit_rate'] = (matched / total * 100) if total > 0 else 0

    return agg

def create_figure(agg: dict, output_dir: Path):
    fig, ax = plt.subplots(figsize=(10, 5))

    x = np.arange(len(DIMENSIONS))
    width = 0.22

    first_rates = [agg['first'][d]['hit_rate'] for d in DIMENSIONS]
    second_rates = [agg['second'][d]['hit_rate'] for d in DIMENSIONS]
    last_rates = [agg['last'][d]['hit_rate'] for d in DIMENSIONS]

    ax.bar(x - width, first_rates, width, label='First Round',
           color=COLOR_BASE, alpha=0.5, edgecolor='black')
    ax.bar(x, second_rates, width, label='Second Round',
           color=COLOR_BASE, alpha=0.75, edgecolor='black', hatch='...')
    ax.bar(x + width, last_rates, width, label='Final Round',
           color=COLOR_BASE, alpha=1.0, edgecolor='black', hatch='///')

    bracket_h = 1.2
    text_offset = 0.3
    tier_gap = 4.5

    for i in range(len(DIMENSIONS)):
        left_x = x[i] - width
        right_x = x[i]
        top1 = max(first_rates[i], second_rates[i]) + 1.0
        diff1 = second_rates[i] - first_rates[i]

        ax.plot([left_x, left_x, right_x, right_x],
                [top1, top1 + bracket_h, top1 + bracket_h, top1],
                color='black', linewidth=1.0, clip_on=False)
        label1 = f'+{diff1:.1f}' if diff1 >= 0 else f'{diff1:.1f}'
        ax.text((left_x + right_x) / 2, top1 + bracket_h + text_offset,
                label1, ha='center', va='bottom', fontsize=18, fontweight='bold')

        left_x2 = x[i]
        right_x2 = x[i] + width
        top2 = max(first_rates[i], second_rates[i], last_rates[i]) + tier_gap
        diff2 = last_rates[i] - second_rates[i]

        ax.plot([left_x2, left_x2, right_x2, right_x2],
                [top2, top2 + bracket_h, top2 + bracket_h, top2],
                color='black', linewidth=1.0, clip_on=False)
        label2 = f'+{diff2:.1f}' if diff2 >= 0 else f'{diff2:.1f}'
        ax.text((left_x2 + right_x2) / 2, top2 + bracket_h + text_offset,
                label2, ha='center', va='bottom', fontsize=18, fontweight='bold')

    ax.set_ylabel('Keyword-Level Hit Rate (%)', fontsize=23)
    ax.set_xticks(x)
    ax.set_xticklabels([DIMENSION_LABELS[d] for d in DIMENSIONS],
                        rotation=0, ha='center', fontsize=24)
    ax.tick_params(axis='y', labelsize=22)
    ax.legend(fontsize=20, loc='upper right')
    ax.grid(alpha=0.3, axis='y')
    all_rates = first_rates + second_rates + last_rates
    ax.set_ylim(0, max(max(all_rates) * 1.5, 35))
    plt.tight_layout()

    fig_path = output_dir / 'semantic_hit_rate_rq2.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {fig_path.name}", flush=True)

def generate_report(agg: dict, all_results: list, output_dir: Path):

    rows = []
    for dim in DIMENSIONS:
        row = {'Dimension': dim}
        for g in GROUPS:
            row[f'{GROUP_LABELS[g]}_HitRate_%'] = round(agg[g][dim]['hit_rate'], 1)
            row[f'{GROUP_LABELS[g]}_Matched'] = agg[g][dim]['matched']
            row[f'{GROUP_LABELS[g]}_Total'] = agg[g][dim]['total']
            row[f'{GROUP_LABELS[g]}_Tasks'] = agg[g][dim]['n_tasks']
        row['Improvement_pp'] = round(agg['last'][dim]['hit_rate'] - agg['first'][dim]['hit_rate'], 1)
        rows.append(row)

    csv_path = output_dir / 'semantic_mapping_rq2_stats.csv'
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    print(f"  ✓ {csv_path.name}", flush=True)

    first_overall = _calc_overall(agg, 'first')
    second_overall = _calc_overall(agg, 'second')
    last_overall = _calc_overall(agg, 'last')

    report = []
    report.append("=" * 80)
    report.append("RQ2 SEMANTIC MAPPING: BASE STAGE FIRST / SECOND / LAST ROUND")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Model: {MODEL}")
    report.append(f"Total task-round evaluations: {len(all_results)}")
    report.append("")

    report.append("=" * 80)
    report.append("SEMANTIC HIT RATE BY DIMENSION")
    report.append("=" * 80)
    report.append("")
    header = f"{'Dimension':20s} | {'First':>10s} | {'Second':>10s} | {'Last':>10s} | {'1st→Last':>10s}"
    report.append(header)
    report.append(f"{'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")

    for dim in DIMENSIONS:
        fr = agg['first'][dim]['hit_rate']
        sr = agg['second'][dim]['hit_rate']
        lr = agg['last'][dim]['hit_rate']
        imp = lr - fr
        report.append(f"{dim:20s} | {fr:9.1f}% | {sr:9.1f}% | {lr:9.1f}% | {imp:+9.1f}pp")

    report.append(f"{'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
    imp_overall = last_overall - first_overall
    report.append(f"{'OVERALL':20s} | {first_overall:9.1f}% | {second_overall:9.1f}% | {last_overall:9.1f}% | {imp_overall:+9.1f}pp")
    report.append("")

    report.append("=" * 80)
    report.append("SAMPLE COUNTS (GT sentences evaluated)")
    report.append("=" * 80)
    report.append("")
    header = f"{'Dimension':20s} | {'1st Total':>10s} | {'2nd Total':>10s} | {'Last Total':>10s}"
    report.append(header)
    report.append(f"{'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
    for dim in DIMENSIONS:
        ft = agg['first'][dim]['total']
        st = agg['second'][dim]['total']
        lt = agg['last'][dim]['total']
        report.append(f"{dim:20s} | {ft:>10d} | {st:>10d} | {lt:>10d}")
    report.append("")

    report.append("=" * 80)
    report.append("KEY FINDINGS")
    report.append("=" * 80)
    report.append("")

    report.append(f"1. Iteration Effect (First → Second → Last Round):")
    report.append(f"   Overall: {first_overall:.1f}% → {second_overall:.1f}% → {last_overall:.1f}%")
    early_gain = second_overall - first_overall
    late_gain = last_overall - second_overall
    report.append(f"   Early gain (1st→2nd): {early_gain:+.1f}pp")
    report.append(f"   Later gain (2nd→last): {late_gain:+.1f}pp")
    if early_gain > late_gain + 2:
        report.append(f"   → Most improvement happens in the FIRST iteration")
    elif late_gain > early_gain + 2:
        report.append(f"   → Most improvement happens in LATER iterations")
    else:
        report.append(f"   → Improvement is GRADUAL across iterations")
    report.append("")

    dim_imp = [(d, agg['last'][d]['hit_rate'] - agg['first'][d]['hit_rate']) for d in DIMENSIONS]
    dim_imp.sort(key=lambda x: x[1], reverse=True)
    report.append(f"2. Dimension Improvement Ranking (1st → 2nd → last):")
    for rank, (dim, imp) in enumerate(dim_imp, 1):
        fr = agg['first'][dim]['hit_rate']
        sr = agg['second'][dim]['hit_rate']
        lr = agg['last'][dim]['hit_rate']
        report.append(f"   {rank}. {dim:20s}: {fr:.1f}% → {sr:.1f}% → {lr:.1f}% (total {imp:+.1f}pp)")
    report.append("")

    report.append(f"3. Most Improved:  {dim_imp[0][0]} ({dim_imp[0][1]:+.1f}pp)")
    report.append(f"   Least Improved: {dim_imp[-1][0]} ({dim_imp[-1][1]:+.1f}pp)")
    report.append("")

    dim_last = [(d, agg['last'][d]['hit_rate']) for d in DIMENSIONS]
    dim_last.sort(key=lambda x: x[1])
    report.append(f"4. Remaining Gaps (Last Round, lowest → highest):")
    for dim, rate in dim_last:
        marker = "⚠️" if rate < 40 else ""
        report.append(f"   {dim:20s}: {rate:.1f}% {marker}")
    report.append("")

    report.append(f"5. Iteration Effectiveness:")
    improved = [d for d, imp in dim_imp if imp > 3]
    stable = [d for d, imp in dim_imp if abs(imp) <= 3]
    if improved:
        report.append(f"   Clearly improved (>3pp): {', '.join(improved)}")
    if stable:
        report.append(f"   Stable (±3pp):           {', '.join(stable)}")
    report.append("")

    report.append("=" * 80)

    report_path = output_dir / 'semantic_mapping_rq2_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    print(f"  ✓ {report_path.name}", flush=True)

def _calc_overall(agg: dict, group: str) -> float:
    total_matched = sum(agg[group][d]['matched'] for d in DIMENSIONS)
    total_gt = sum(agg[group][d]['total'] for d in DIMENSIONS)
    return (total_matched / total_gt * 100) if total_gt > 0 else 0

def main():
    print("=" * 80)
    print("RQ2 SEMANTIC MAPPING: BASE STAGE FIRST / SECOND / LAST ROUND")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Model: {MODEL}\n")

    if len(sys.argv) < 2:
        print("Usage: python semantic_mapping_rq2.py <ultiwithout.csv>")
        sys.exit(1)

    try:
        from openai import OpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("❌ ERROR: Set OPENAI_API_KEY environment variable")
            sys.exit(1)
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized\n")
    except ImportError:
        print("❌ ERROR: pip install openai")
        sys.exit(1)

    print("📂 Loading data...")
    df = load_data(sys.argv[1])

    print("\n🔍 Running semantic matching (first, second & last round vs GT)...")
    all_results = run_analysis(df, client, MODEL)

    print("\n📊 Aggregating results...")
    agg = aggregate_results(all_results)

    print("\n🎨 Creating visualization...")
    create_figure(agg, FIGURES_DIR)

    print("\n📝 Generating report...")
    generate_report(agg, all_results, OUTPUT_DIR)

    print(f"\n✅ COMPLETE")
    print(f"  Output: {OUTPUT_DIR}/")
    print(f"  Figure: {FIGURES_DIR}/semantic_hit_rate_rq2.png")
    print(f"  Report: {OUTPUT_DIR}/semantic_mapping_rq2_report.txt")
    print(f"  Stats:  {OUTPUT_DIR}/semantic_mapping_rq2_stats.csv")
    print(f"  Cache:  {CACHE_PATH} (delete to re-run all)")
    print("=" * 80)

if __name__ == '__main__':
    main()
