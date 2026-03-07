
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
GROUPS = ['base_first', 'base_last', 'agent_first', 'agent_last']
GROUP_LABELS = {
    'base_first': 'Base First',
    'base_last': 'Base Last',
    'agent_first': 'Agent First',
    'agent_last': 'Agent Last',
}

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from color_config import COLORS
except ImportError:
    COLORS = {}
COLOR_BASE = COLORS.get('base_stage', '#FAA26F')
COLOR_AGENT = COLORS.get('agent_stage', '#65BDBA')

# 使用本地 outputs 目录
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "fig6"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR = OUTPUT_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)
CACHE_PATH = OUTPUT_DIR / "semantic_mapping_raw.json"

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

def load_user_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    for dim in DIMENSIONS + ['others']:
        col = f'classified_{dim}'
        if col in df.columns:
            df[col] = df[col].apply(safe_eval_list)

    for col in ['is_first_round', 'is_last_round']:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: True if (x is True or x == 1 or
                                   (isinstance(x, str) and x.lower() == 'true'))
                else False
            )

    print(f"✅ {csv_path}: {len(df)} rows, {df['task_id'].nunique()} tasks")
    return df

def load_gt_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    for dim in DIMENSIONS + ['others']:
        col = f'gt_classified_{dim}'
        if col in df.columns:
            df[col] = df[col].apply(safe_eval_list)

    print(f"✅ {csv_path}: {len(df)} GT targets")
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
            print(f"    ⚠️ JSON parse error (attempt {attempt+1})")
        except Exception as e:
            wait = 2 ** attempt
            print(f"    ⚠️ API error: {e} (retry in {wait}s)")
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

def run_analysis(df_without, df_with, gt_df, client, model):
    cache = {}
    if CACHE_PATH.exists():
        with open(CACHE_PATH, 'r') as f:
            cache = json.load(f)
        print(f"  📦 Loaded cache: {len(cache)} entries")

    gt_lookup = {}
    for _, row in gt_df.iterrows():
        tidx = str(row['target_index'])
        gt_lookup[tidx] = {}
        for dim in DIMENSIONS:
            col = f'gt_classified_{dim}'
            gt_lookup[tidx][dim] = row[col] if isinstance(row[col], list) else []

    all_results = []
    stages = [
        ('base', df_without),
        ('agent', df_with),
    ]

    total_api_calls = 0

    for stage_name, df in stages:
        task_ids = df['task_id'].unique()
        print(f"\n  🔍 Processing {stage_name} stage: {len(task_ids)} tasks", flush=True)

        for i, task_id in enumerate(task_ids):
            task_data = df[df['task_id'] == task_id].sort_values('version_number')
            if len(task_data) == 0:
                continue

            tidx = str(task_data.iloc[0]['target_index'])
            if tidx not in gt_lookup:
                continue

            gt_dims = gt_lookup[tidx]

            first_row = task_data[task_data['is_first_round'] == True]
            last_row = task_data[task_data['is_last_round'] == True]

            for round_name, round_data in [('first', first_row), ('last', last_row)]:
                if len(round_data) == 0:
                    continue
                row = round_data.iloc[0]

                user_dims = {}
                for dim in DIMENSIONS:
                    col = f'classified_{dim}'
                    user_dims[dim] = row[col] if isinstance(row[col], list) else []

                cache_key = f"{stage_name}_{task_id}_{round_name}"
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

                group_key = f"{stage_name}_{round_name}"
                all_results.append({
                    'task_id': task_id,
                    'target_index': tidx,
                    'stage': stage_name,
                    'round': round_name,
                    'group': group_key,
                    'match_result': match_result,
                })

            print(f"\r    {i+1}/{len(task_ids)} tasks done (API calls: {total_api_calls})...", end='', flush=True)
        print()

    with open(CACHE_PATH, 'w') as f:
        json.dump(cache, f, ensure_ascii=False)
    print(f"\n  💾 Cache saved ({total_api_calls} total API calls)")

    return all_results

def aggregate_results(all_results: list) -> dict:
    agg = {g: {d: {'total': 0, 'matched': 0, 'n_tasks': 0} for d in DIMENSIONS} for g in GROUPS}

    for entry in all_results:
        group = entry['group']
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
    width = 0.18

    base_first = [agg['base_first'][d]['hit_rate'] for d in DIMENSIONS]
    base_last = [agg['base_last'][d]['hit_rate'] for d in DIMENSIONS]
    agent_first = [agg['agent_first'][d]['hit_rate'] for d in DIMENSIONS]
    agent_last = [agg['agent_last'][d]['hit_rate'] for d in DIMENSIONS]

    ax.bar(x - 1.5*width, base_first, width, label='Base First',
           color=COLOR_BASE, alpha=0.8, edgecolor='black')
    ax.bar(x - 0.5*width, base_last, width, label='Base Final',
           color=COLOR_BASE, alpha=0.8, edgecolor='black', hatch='///')
    ax.bar(x + 0.5*width, agent_first, width, label='Agent First',
           color=COLOR_AGENT, alpha=0.8, edgecolor='black')
    ax.bar(x + 1.5*width, agent_last, width, label='Agent Final',
           color=COLOR_AGENT, alpha=0.8, edgecolor='black', hatch='///')

    bracket_h = 1.0
    text_offset = 0.3
    tier_gap = 4.0

    for i in range(len(DIMENSIONS)):
        left_x1 = x[i] - 1.5*width
        right_x1 = x[i] - 0.5*width
        top1 = max(base_first[i], base_last[i]) + 1.0
        diff1 = base_last[i] - base_first[i]

        ax.plot([left_x1, left_x1, right_x1, right_x1],
                [top1, top1 + bracket_h, top1 + bracket_h, top1],
                color='black', linewidth=1.0, clip_on=False)
        label1 = f'+{diff1:.1f}' if diff1 >= 0 else f'{diff1:.1f}'
        ax.text((left_x1 + right_x1) / 2, top1 + bracket_h + text_offset,
                label1, ha='center', va='bottom', fontsize=18, fontweight='bold')

        left_x2 = x[i] + 0.5*width
        right_x2 = x[i] + 1.5*width
        top2 = max(agent_first[i], agent_last[i]) + 1.0
        diff2 = agent_last[i] - agent_first[i]

        ax.plot([left_x2, left_x2, right_x2, right_x2],
                [top2, top2 + bracket_h, top2 + bracket_h, top2],
                color='black', linewidth=1.0, clip_on=False)
        label2 = f'+{diff2:.1f}' if diff2 >= 0 else f'{diff2:.1f}'
        ax.text((left_x2 + right_x2) / 2, top2 + bracket_h + text_offset,
                label2, ha='center', va='bottom', fontsize=18, fontweight='bold')

    ax.set_ylabel('Keyword-Level Hit Rate (%)', fontsize=22)
    ax.set_xticks(x)
    ax.set_xticklabels([DIMENSION_LABELS[d] for d in DIMENSIONS],
                        rotation=0, ha='center', fontsize=26)
    ax.tick_params(axis='y', labelsize=22)
    ax.legend(fontsize=22, loc='upper right')
    ax.grid(alpha=0.3, axis='y')
    all_rates = base_first + base_last + agent_first + agent_last
    ax.set_ylim(0, 40)
    plt.tight_layout()

    fig_path = output_dir / 'semantic_hit_rate.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {fig_path.name}")

def generate_report(agg: dict, all_results: list, output_dir: Path):

    rows = []
    for dim in DIMENSIONS:
        row = {'Dimension': dim}
        for g in GROUPS:
            row[f'{GROUP_LABELS[g]}_HitRate_%'] = round(agg[g][dim]['hit_rate'], 1)
            row[f'{GROUP_LABELS[g]}_Matched'] = agg[g][dim]['matched']
            row[f'{GROUP_LABELS[g]}_Total'] = agg[g][dim]['total']
            row[f'{GROUP_LABELS[g]}_Tasks'] = agg[g][dim]['n_tasks']
        rows.append(row)

    csv_path = output_dir / 'semantic_mapping_stats.csv'
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    print(f"  ✓ {csv_path.name}")

    report = []
    report.append("=" * 80)
    report.append("SEMANTIC MAPPING ANALYSIS: USER PROMPTS VS GROUND TRUTH")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Model: {MODEL}")
    report.append(f"Total task-round evaluations: {len(all_results)}")
    report.append("")

    report.append("【Semantic Hit Rate by Dimension (%)】")
    report.append("")
    header = f"{'Dimension':20s} | {'Base 1st':>10s} | {'Base Lst':>10s} | {'Agt 1st':>10s} | {'Agt Lst':>10s}"
    report.append(header)
    report.append(f"{'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")

    for dim in DIMENSIONS:
        bf = agg['base_first'][dim]['hit_rate']
        bl = agg['base_last'][dim]['hit_rate']
        af = agg['agent_first'][dim]['hit_rate']
        al = agg['agent_last'][dim]['hit_rate']
        report.append(f"{dim:20s} | {bf:9.1f}% | {bl:9.1f}% | {af:9.1f}% | {al:9.1f}%")

    report.append(f"{'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
    for g in GROUPS:
        total_matched = sum(agg[g][d]['matched'] for d in DIMENSIONS)
        total_gt = sum(agg[g][d]['total'] for d in DIMENSIONS)
        overall = (total_matched / total_gt * 100) if total_gt > 0 else 0
        if g == 'base_first':
            bf_overall = overall
        elif g == 'base_last':
            bl_overall = overall
        elif g == 'agent_first':
            af_overall = overall
        else:
            al_overall = overall
    report.append(f"{'OVERALL':20s} | {bf_overall:9.1f}% | {bl_overall:9.1f}% | {af_overall:9.1f}% | {al_overall:9.1f}%")
    report.append("")

    report.append("【Sample Counts (GT sentences evaluated)】")
    report.append("")
    header = f"{'Dimension':20s} | {'Base 1st':>10s} | {'Base Lst':>10s} | {'Agt 1st':>10s} | {'Agt Lst':>10s}"
    report.append(header)
    report.append(f"{'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
    for dim in DIMENSIONS:
        vals = [str(agg[g][dim]['total']) for g in GROUPS]
        report.append(f"{dim:20s} | {vals[0]:>10s} | {vals[1]:>10s} | {vals[2]:>10s} | {vals[3]:>10s}")
    report.append("")

    report.append("=" * 80)
    report.append("KEY FINDINGS")
    report.append("=" * 80)
    report.append("")

    base_improve = bl_overall - bf_overall
    agent_improve = al_overall - af_overall
    report.append(f"1. Iteration Effect (First → Last Round):")
    report.append(f"   Base Stage:  {bf_overall:.1f}% → {bl_overall:.1f}% ({base_improve:+.1f}pp)")
    report.append(f"   Agent Stage: {af_overall:.1f}% → {al_overall:.1f}% ({agent_improve:+.1f}pp)")
    if agent_improve > base_improve + 2:
        report.append(f"   → Agent Stage shows GREATER improvement through iteration")
    elif base_improve > agent_improve + 2:
        report.append(f"   → Base Stage shows GREATER improvement through iteration")
    else:
        report.append(f"   → Both stages show SIMILAR improvement through iteration")
    report.append("")

    report.append(f"2. Agent vs Base (Final Round):")
    report.append(f"   Base Last:  {bl_overall:.1f}%")
    report.append(f"   Agent Last: {al_overall:.1f}%")
    diff = al_overall - bl_overall
    if diff > 2:
        report.append(f"   → Agent Stage final prompts are CLOSER to GT ({diff:+.1f}pp)")
    elif diff < -2:
        report.append(f"   → Base Stage final prompts are CLOSER to GT ({-diff:+.1f}pp)")
    else:
        report.append(f"   → Both stages reach SIMILAR proximity to GT")
    report.append("")

    report.append(f"3. Per-Dimension Agent Advantage (Last Round):")
    for dim in DIMENSIONS:
        bl = agg['base_last'][dim]['hit_rate']
        al = agg['agent_last'][dim]['hit_rate']
        diff = al - bl
        marker = "↑" if diff > 2 else "↓" if diff < -2 else "≈"
        report.append(f"   {dim:20s}: Base {bl:5.1f}% vs Agent {al:5.1f}% ({diff:+.1f}pp {marker})")
    report.append("")

    report.append(f"4. Most/Least Covered Dimensions (Agent Last):")
    agent_last_rates = [(d, agg['agent_last'][d]['hit_rate']) for d in DIMENSIONS]
    agent_last_rates.sort(key=lambda x: x[1], reverse=True)
    report.append(f"   Best:  {agent_last_rates[0][0]} ({agent_last_rates[0][1]:.1f}%)")
    report.append(f"   Worst: {agent_last_rates[-1][0]} ({agent_last_rates[-1][1]:.1f}%)")
    report.append("")

    report.append("=" * 80)

    report_path = output_dir / 'semantic_mapping_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    print(f"  ✓ {report_path.name}")

def main():
    print("=" * 80)
    print("SEMANTIC MAPPING ANALYSIS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Model: {MODEL}\n")

    if len(sys.argv) < 4:
        print("Usage: python semantic_mapping.py <ultiwithout.csv> <ultiwith.csv> <ground_truth_analysis.csv>")
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
    df_without = load_user_data(sys.argv[1])
    df_with = load_user_data(sys.argv[2])
    gt_df = load_gt_data(sys.argv[3])

    print("\n🔍 Running semantic matching...")
    all_results = run_analysis(df_without, df_with, gt_df, client, MODEL)

    print("\n📊 Aggregating results...")
    agg = aggregate_results(all_results)

    print("\n🎨 Creating visualizations...")
    create_figure(agg, FIGURES_DIR)

    print("\n📝 Generating report...")
    generate_report(agg, all_results, OUTPUT_DIR)

    print(f"\n✅ COMPLETE")
    print(f"  Output: {OUTPUT_DIR}/")
    print(f"  Figure: {FIGURES_DIR}/semantic_hit_rate.png")
    print(f"  Report: {OUTPUT_DIR}/semantic_mapping_report.txt")
    print(f"  Stats:  {OUTPUT_DIR}/semantic_mapping_stats.csv")
    print(f"  Cache:  {CACHE_PATH} (delete to re-run all)")
    print("=" * 80)

if __name__ == '__main__':
    main()
