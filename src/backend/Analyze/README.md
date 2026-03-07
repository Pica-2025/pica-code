# Analysis Scripts for Paper Tables and Figures

This directory contains independent analysis scripts that generate all tables and figures used in the paper.

## Directory Structure

```
Analyze/
├── prepare_data.py          # Data preparation script
├── data/                    # Cleaned data files (generated)
├── tables/                  # Table generation scripts
│   ├── table1.py           # Table 1: Dimension Coverage
│   ├── table2.py           # Table 2: Dimension Impact
│   ├── table3.py           # Table 3: Coverage-Quality Relationship
│   ├── table4.py           # Table 4: Dimension Addition Effects
│   ├── table5.py           # Table 5: RQ4 Comparison
│   └── table_compara.py    # Target & Model Comparison Analysis
├── figures/                 # Figure generation scripts
│   ├── fig3.py             # Figure 3: First vs Last Round Coverage
│   ├── fig4.py             # Figure 4: Semantic Analysis
│   ├── fig5.py             # Figure 5: Semantic Mapping
│   ├── fig6.py             # Figure 6: Extended Analysis
│   └── fig8.py             # Figure 8: Descriptive Statistics
└── outputs/                 # Generated outputs (organized by script)
    ├── table1/
    ├── table2/
    ├── fig3/
    ├── compara/
    └── ...
```

## Requirements

- **Conda Environment**: `pica`
  - Contains: pandas, numpy, matplotlib, scipy, scikit-learn, seaborn
- **Database**: `database.db` (in parent directory: backend/)
- **Python**: 3.13+

## Quick Start

### 1. Prepare Data (Required - First Time Only)

```bash
cd Analyze
conda run -n pica python prepare_data.py
```

This will:
- Extract data from database and create 4 CSV files in `data/`
- Clean sensitive fields (user_manual_score and rating scores → 0)
- Output files:
  - `first_round_preprocessed.csv` (617 KB)
  - `ultimate_dataset.csv` (2400 KB)
  - `ultiwith.csv` (1763 KB)
  - `ultiwithout.csv` (1716 KB)

### 2. Generate Tables

```bash
cd tables

# Table 1: Dimension Coverage (Section 3)
conda run -n pica python table1.py

# Table 2: Dimension Impact (Section 6)
conda run -n pica python table2.py

# Table 3: Coverage-Quality Relationship (Section 7)
conda run -n pica python table3.py

# Table 4: Dimension Addition Effects (RQ2 Sections 5 + 8)
conda run -n pica python table4.py

# Table 5: RQ4 Comparison Analysis
conda run -n pica python table5.py

# Target & Model Comparison Analysis (supplementary)
conda run -n pica python table_compara.py
```

### 3. Generate Figures

```bash
cd figures

# Figure 3: First vs Last Round Coverage
conda run -n pica python fig3.py

# Figure 8: Descriptive Statistics  
conda run -n pica python fig8.py

# Figures 4, 5, 6 (require command-line arguments)
conda run -n pica python fig4.py [args]
conda run -n pica python fig5.py [args]
conda run -n pica python fig6.py [args]
```

## Output Organization

All outputs are saved in `Analyze/outputs/` organized by script name:

```
outputs/
├── table1/
│   └── section03/
│       ├── fig1_coverage_heatmap.png
│       ├── fig2_coverage_distribution.png
│       ├── fig3_dimension_rates.png
│       └── coverage_report.txt
├── table2/
│   └── section06/
│       └── dimension_impact_report.txt
├── compara/
│   ├── target_analysis.csv
│   ├── model_analysis.csv
│   └── comparison_report.txt
├── fig3/
│   └── section03_dimension_coverage/
│       ├── fig1a_coverage_first_vs_last.png
│       ├── fig1b_coverage_change.png
│       └── fig2_avg_dimension_count.png
└── ...
```

## Data Files

All data files are in `Analyze/data/` with **anonymized and cleaned** content:

1. **first_round_preprocessed.csv** (617 KB)
   - 150 first-round prompts with dimension analysis
   - Used by: table1.py, table2.py, table3.py, fig8.py

2. **ultimate_dataset.csv** (2400 KB)
   - 508 total records (first + last rounds)
   - Used by: table4.py, fig3.py

3. **ultiwith.csv** (1763 KB)
   - Data with agent intervention
   - Used by: table5.py, table_compara.py

4. **ultiwithout.csv** (1716 KB)
   - Data without agent intervention
   - Used by: table5.py, table_compara.py

**All sensitive fields zeroed:**
- `user_manual_score`
- `style_score`
- `object_count_score`
- `perspective_score`
- `depth_background_score`

## Anonymization

This codebase has been fully anonymized:

✅ **Code**: All comments removed (511 KB from 85 files)  
✅ **Database**: 90 users anonymized (test001 → Participant001)  
✅ **CSV Files**: 2000+ phone numbers → Participant IDs  
✅ **Scores**: All sensitive rating fields → 0  

## Paper Mapping

| Script | Paper Element | Description |
|--------|--------------|-------------|
| table1.py | Table 1 | Dimension Coverage Analysis (RQ1) |
| table2.py | Table 2 | Dimension Impact on Quality (RQ1) |
| table3.py | Table 3 | Coverage-Quality Relationship (RQ1) |
| table4.py | Table 4 | Dimension Addition Effects (RQ2) |
| table5.py | Table 5 | Agent Intervention Comparison (RQ4) |
| table_compara.py | Supplementary | Target & Model Comparison Analysis |
| fig3.py | Figure 3 | First vs Last Round Coverage |
| fig4.py | Figure 4 | Semantic Analysis |
| fig5.py | Figure 5 | Semantic Mapping |
| fig6.py | Figure 6 | Extended Analysis |
| fig8.py | Figure 8 | Descriptive Statistics |

## Notes

- All scripts are **completely independent** and can run in any order (after prepare_data.py)
- Scripts automatically create output directories
- If data files are missing, scripts will show error: "Please run: python prepare_data.py"
- All paths use relative navigation from script locations
- No external dependencies on deleted RQ1/RQ2/RQ4 folders

## Workflow Summary

```
1. conda run -n pica python prepare_data.py   # Once, to create data/
2. cd tables && conda run -n pica python table1.py  # Run any script
3. Check outputs in ../outputs/table1/            # View results
```

---

**Environment**: Conda environment `pica` (Python 3.13+)  
**Last Updated**: 2026-03-07
