#!/usr/bin/env python3
"""
Target & Model Comparison Analysis
Compares performance with and without agent intervention
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "compara"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_dataset(csv_path: str) -> pd.DataFrame:
    """Load and preprocess dataset"""
    df = pd.read_csv(csv_path)
    
    for col in ['model_type', 'target_filename', 'generation_type']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.strip('"').str.strip("'")
    
    numeric_cols = ['ai_similarity_score', 'version_number', 'target_index']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print(f"✅ {csv_path}: {len(df)} rows, {df['target_filename'].nunique()} tasks")
    return df

def analyze_by_target(df_without: pd.DataFrame, df_with: pd.DataFrame) -> pd.DataFrame:
    """Analyze performance by target image"""
    results = []
    
    all_targets = set(df_without['target_filename'].unique()) | set(df_with['target_filename'].unique())
    
    for target in sorted(all_targets):
        target_without = df_without[df_without['target_filename'] == target]
        target_with = df_with[df_with['target_filename'] == target]
        
        without_first = without_final = np.nan
        if len(target_without) > 0:
            first_data = target_without[target_without['version_number'] == 1]
            if len(first_data) > 0:
                without_first = first_data['ai_similarity_score'].mean()
            
            final_data = []
            for task_id in target_without['task_id'].unique():
                task = target_without[target_without['task_id'] == task_id].sort_values('version_number')
                if len(task) > 0:
                    final_data.append(task.iloc[-1]['ai_similarity_score'])
            without_final = np.mean(final_data) if final_data else np.nan
        
        with_first = with_final = np.nan
        if len(target_with) > 0:
            first_data = target_with[target_with['version_number'] == 1]
            if len(first_data) > 0:
                with_first = first_data['ai_similarity_score'].mean()
            
            final_data = []
            for task_id in target_with['task_id'].unique():
                task = target_with[target_with['task_id'] == task_id].sort_values('version_number')
                if len(task) > 0:
                    final_data.append(task.iloc[-1]['ai_similarity_score'])
            with_final = np.mean(final_data) if final_data else np.nan
        
        results.append({
            'target': target,
            'without_first': without_first,
            'without_final': without_final,
            'without_improvement': without_final - without_first if not np.isnan(without_first) and not np.isnan(without_final) else np.nan,
            'with_first': with_first,
            'with_final': with_final,
            'with_improvement': with_final - with_first if not np.isnan(with_first) and not np.isnan(with_final) else np.nan
        })
    
    return pd.DataFrame(results)

def analyze_by_model(df_without: pd.DataFrame, df_with: pd.DataFrame) -> pd.DataFrame:
    """Analyze performance by model type"""
    results = []
    
    all_models = set(df_without['model_type'].unique()) | set(df_with['model_type'].unique())
    
    for model in sorted(all_models):
        model_without = df_without[df_without['model_type'] == model]
        model_with = df_with[df_with['model_type'] == model]
        
        without_first = without_final = np.nan
        if len(model_without) > 0:
            first_data = model_without[model_without['version_number'] == 1]
            without_first = first_data['ai_similarity_score'].mean() if len(first_data) > 0 else np.nan
            
            final_data = []
            for task_id in model_without['task_id'].unique():
                task = model_without[model_without['task_id'] == task_id].sort_values('version_number')
                if len(task) > 0:
                    final_data.append(task.iloc[-1]['ai_similarity_score'])
            without_final = np.mean(final_data) if final_data else np.nan
        
        with_first = with_final = np.nan
        if len(model_with) > 0:
            first_data = model_with[model_with['version_number'] == 1]
            with_first = first_data['ai_similarity_score'].mean() if len(first_data) > 0 else np.nan
            
            final_data = []
            for task_id in model_with['task_id'].unique():
                task = model_with[model_with['task_id'] == task_id].sort_values('version_number')
                if len(task) > 0:
                    final_data.append(task.iloc[-1]['ai_similarity_score'])
            with_final = np.mean(final_data) if final_data else np.nan
        
        results.append({
            'model': model,
            'without_first': without_first,
            'without_final': without_final,
            'without_improvement': without_final - without_first if not np.isnan(without_first) and not np.isnan(without_final) else np.nan,
            'with_first': with_first,
            'with_final': with_final,
            'with_improvement': with_final - with_first if not np.isnan(with_first) and not np.isnan(with_final) else np.nan
        })
    
    return pd.DataFrame(results)

def generate_report(target_results: pd.DataFrame, model_results: pd.DataFrame, output_path: Path):
    """Generate comprehensive text report"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("TARGET & MODEL COMPARISON ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("MODEL ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        
        for _, row in model_results.iterrows():
            f.write(f"Model: {row['model']}\n")
            f.write(f"  Without Agent:\n")
            f.write(f"    First Round AI Score:  {row['without_first']:6.2f}\n")
            f.write(f"    Final Round AI Score:  {row['without_final']:6.2f}\n")
            f.write(f"    Improvement:           {row['without_improvement']:+6.2f}\n")
            f.write(f"  With Agent:\n")
            f.write(f"    First Round AI Score:  {row['with_first']:6.2f}\n")
            f.write(f"    Final Round AI Score:  {row['with_final']:6.2f}\n")
            f.write(f"    Improvement:           {row['with_improvement']:+6.2f}\n")
            f.write(f"  Agent Benefit:\n")
            f.write(f"    Improvement Difference: {row['with_improvement'] - row['without_improvement']:+6.2f}\n")
            f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("TARGET ANALYSIS SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        valid_targets = target_results.dropna(subset=['without_improvement', 'with_improvement']).copy()
        
        if len(valid_targets) > 0:
            f.write(f"Total Targets Analyzed: {len(valid_targets)}\n\n")
            
            f.write("Overall Statistics:\n")
            f.write(f"  Without Agent - Mean Improvement: {valid_targets['without_improvement'].mean():6.2f}\n")
            f.write(f"  With Agent    - Mean Improvement: {valid_targets['with_improvement'].mean():6.2f}\n")
            f.write(f"  Agent Benefit (Difference):       {(valid_targets['with_improvement'] - valid_targets['without_improvement']).mean():+6.2f}\n\n")
            
            valid_targets['improvement_diff'] = valid_targets['with_improvement'] - valid_targets['without_improvement']
            
            f.write("\n" + "-" * 80 + "\n")
            f.write("TOP 10 TARGETS: Most Benefit from Agent\n")
            f.write("-" * 80 + "\n\n")
            
            top10 = valid_targets.nlargest(10, 'improvement_diff')
            for i, (_, row) in enumerate(top10.iterrows(), 1):
                f.write(f"{i:2d}. {row['target']}\n")
                f.write(f"    Without Agent: {row['without_improvement']:+6.2f}\n")
                f.write(f"    With Agent:    {row['with_improvement']:+6.2f}\n")
                f.write(f"    Difference:    {row['improvement_diff']:+6.2f}\n\n")
            
            f.write("\n" + "-" * 80 + "\n")
            f.write("BOTTOM 10 TARGETS: Least Benefit from Agent\n")
            f.write("-" * 80 + "\n\n")
            
            bottom10 = valid_targets.nsmallest(10, 'improvement_diff')
            for i, (_, row) in enumerate(bottom10.iterrows(), 1):
                f.write(f"{i:2d}. {row['target']}\n")
                f.write(f"    Without Agent: {row['without_improvement']:+6.2f}\n")
                f.write(f"    With Agent:    {row['with_improvement']:+6.2f}\n")
                f.write(f"    Difference:    {row['improvement_diff']:+6.2f}\n\n")
            
            f.write("\n" + "-" * 80 + "\n")
            f.write("DISTRIBUTION STATISTICS\n")
            f.write("-" * 80 + "\n\n")
            
            f.write(f"Improvement Difference (With - Without):\n")
            f.write(f"  Mean:   {valid_targets['improvement_diff'].mean():+6.2f}\n")
            f.write(f"  Median: {valid_targets['improvement_diff'].median():+6.2f}\n")
            f.write(f"  Std:    {valid_targets['improvement_diff'].std():6.2f}\n")
            f.write(f"  Min:    {valid_targets['improvement_diff'].min():+6.2f}\n")
            f.write(f"  Max:    {valid_targets['improvement_diff'].max():+6.2f}\n\n")
            
            positive = (valid_targets['improvement_diff'] > 0).sum()
            negative = (valid_targets['improvement_diff'] < 0).sum()
            neutral = (valid_targets['improvement_diff'] == 0).sum()
            
            f.write(f"Target Distribution:\n")
            f.write(f"  Agent Helped:  {positive:3d} targets ({positive/len(valid_targets)*100:5.1f}%)\n")
            f.write(f"  Agent Hurt:    {negative:3d} targets ({negative/len(valid_targets)*100:5.1f}%)\n")
            f.write(f"  No Difference: {neutral:3d} targets ({neutral/len(valid_targets)*100:5.1f}%)\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")

def main():
    print("=" * 80)
    print("TARGET & MODEL COMPARISON ANALYSIS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    DATA_DIR = Path(__file__).parent.parent / "data"
    
    csv_without = DATA_DIR / "ultiwithout.csv"
    csv_with = DATA_DIR / "ultiwith.csv"
    
    if not csv_without.exists():
        print(f"❌ Error: {csv_without} not found!")
        print("Please run: python prepare_data.py")
        sys.exit(1)
    
    if not csv_with.exists():
        print(f"❌ Error: {csv_with} not found!")
        print("Please run: python prepare_data.py")
        sys.exit(1)
    
    print("📂 Loading data...")
    df_without = load_dataset(str(csv_without))
    df_with = load_dataset(str(csv_with))
    
    print("\n📊 Analyzing by target...")
    target_results = analyze_by_target(df_without, df_with)
    target_path = OUTPUT_DIR / "target_analysis.csv"
    target_results.to_csv(target_path, index=False)
    print(f"  ✓ Saved: target_analysis.csv")
    
    print("\n📊 Analyzing by model...")
    model_results = analyze_by_model(df_without, df_with)
    model_path = OUTPUT_DIR / "model_analysis.csv"
    model_results.to_csv(model_path, index=False)
    print(f"  ✓ Saved: model_analysis.csv")
    
    print("\n📝 Generating report...")
    report_path = OUTPUT_DIR / "comparison_report.txt"
    generate_report(target_results, model_results, report_path)
    print(f"  ✓ Saved: comparison_report.txt")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"  - target_analysis.csv")
    print(f"  - model_analysis.csv")
    print(f"  - comparison_report.txt")
    print()

if __name__ == '__main__':
    main()
