# 数据准备说明

## 目录结构

数据文件应放置在 `data/` 目录下，具体结构如下：

```
data/
├── targets/          # 目标图片（必需）
│   ├── tgt_0001.jpg
│   ├── tgt_0002.jpg
│   └── ...
├── manifests/        # 自动生成的清单文件
│   └── targets_manifest.csv
├── generations/      # AI 生成的图片（运行时生成）
├── revisions/        # 用户修改后的图片（运行时生成）
├── thumbs/          # 缩略图（运行时生成）
├── logs/            # 日志文件（运行时生成）
├── exports/         # 导出数据（运行时生成）
└── temp/            # 临时文件（运行时生成）
```

## 准备数据

### 方式 1: 使用已有的目标图片

如果你已经有目标图片，请：

1. 将图片放置到 `data/targets/` 目录
2. 建议命名格式：`tgt_0001.jpg`, `tgt_0002.jpg`, ...
3. 支持的格式：`.jpg`, `.jpeg`, `.png`

### 方式 2: 从外部下载

如果图片托管在外部，请参考论文或代码仓库说明获取下载链接。

## 生成清单文件

准备好目标图片后，运行以下命令生成清单文件：

```bash
python scripts/build_manifest.py
```

这将自动扫描 `data/targets/` 目录并生成 `data/manifests/targets_manifest.csv`。

## 数据说明

### 目标图片（Target Images）

- **数量**: 建议 30-60 张
- **尺寸**: 建议 1024x1024 或更大
- **格式**: JPG 或 PNG
- **内容**: 根据研究需求选择不同风格和复杂度的图片

### 清单文件字段

`targets_manifest.csv` 包含以下字段：

- `index`: 图片序号
- `filename`: 文件名
- `rel_path`: 相对路径
- `abs_path`: 绝对路径
- `bytes`: 文件大小（字节）
- `width`: 图片宽度
- `height`: 图片高度
- `sha256`: 文件哈希值
- `mtime`: 修改时间
- `difficulty`: 难度等级（easy/medium/hard）
- `prompt_id`: 提示词 ID
- `ground_truth`: 参考描述

## 隐私说明

**请勿在公开仓库中包含：**
- 用户研究的原始数据
- 数据库文件（`database.db`）
- 用户信息文件（`users.csv` 等）
- 包含个人信息的日志文件

这些文件已被 `.gitignore` 排除。
