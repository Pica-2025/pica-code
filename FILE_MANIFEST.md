# 完整文件转移清单

## ✅ 已转移的文件

### 后端核心模块 (15 个文件)

1. **配置与数据库**
   - `config.py` - 系统配置（已匿名化：硬编码路径改为相对路径，API Keys 改为环境变量）
   - `database.py` - 数据库连接
   - `models.py` - 数据模型定义

2. **认证与授权**
   - `auth.py` - JWT 认证
   - `schemas.py` - Pydantic 数据验证模式

3. **业务逻辑**
   - `crud.py` - 数据库操作
   - `tasks.py` - 任务分配逻辑
   - `manifest_loader.py` - 目标图片清单加载

4. **AI 图像生成**
   - `qwen_client.py` - 阿里云通义千问 API 客户端
   - `gemini_client.py` - Google Gemini API 客户端

5. **自动评分系统**
   - `auto_scorer_multi.py` - 多维度自动评分（DINO + HSV + Structure）
   - `auto_scorer_dino.py` - DINO v2 图像相似度计算
   - `simple_linear_model.pkl` - 训练好的线性回归模型
   - `polynomial_model_degree3_alpha0.1.pkl` - 多项式回归模型

6. **API 路由**
   - `main.py` - FastAPI 主应用
   - `admin_data_routes.py` - 管理员数据查看路由

7. **Wise 智能助手**
   - `wise_tasks.py` - Wise 后台任务处理

### Wise 模块 (wise/ 目录，2 个文件)

- `wise_client_v3.py` - Wise API 客户端
- `wise_knowledge_v3.py` - Wise 知识库
- `__init__.py` - 模块初始化文件

### 研究分析模块 (Analyze/ 目录，51+ 个文件)

**研究问题分析 (RQ1-RQ4)**
- `RQ1/` - 研究问题 1 相关分析脚本
- `RQ2/` - 研究问题 2 相关分析脚本
- `RQ4/` - 研究问题 4 相关分析脚本

**核心分析脚本**
- `difficulty_analysis.py` - 难度分析
- `duration_analysis.py` - 时长分析
- `prompt_length_analysis.py` - 提示词长度分析
- `round_score_analysis.py` - 轮次得分分析
- `user_model_analysis.py` - 用户模型分析
- `version_analysis.py` - 版本迭代分析
- `agent_comparison.py` - 智能体对比分析
- `stratified_analysis.py` - 分层分析
- `export_complete_dataset.py` - 完整数据集导出
- `research_analysis_main.py` - 研究分析主程序
- `compareRQ4.py` - RQ4 对比分析
- `analyze_semanticRQ4.py` - RQ4 语义分析

**辅助文件**
- `color_config.py` - 可视化颜色配置
- `tsne_analysis/` - t-SNE 降维分析

### 前端代码 (src/frontend/)

**React 应用**
- `src/` - React 源代码目录 (11 个 JS/JSX 文件)
- `index.html` - HTML 入口
- `package.json` - NPM 依赖配置
- `vite.config.js` - Vite 构建配置

### 运行脚本 (scripts/ 目录，4 个文件)

- `init_db.py` - 数据库初始化脚本（已更新路径）
- `build_manifest.py` - 图片清单生成脚本（已更新路径）
- `start_backend.sh` - 后端启动脚本
- `start_frontend.sh` - 前端启动脚本

### 数据文件 (data/ 目录)

- `targets/` - 60 张目标图片（已复制）
- `manifests/` - 清单文件目录（运行时生成）
- `README.md` - 数据准备说明

### 配置文件

- `requirements.txt` - Python 依赖列表（完整版，包含所有必需包）
- `.env.example` - 环境变量模板（已移除真实 API Keys）
- `.gitignore` - Git 忽略规则（排除敏感文件）
- `LICENSE` - MIT 许可证（匿名版）

### 文档文件

- `README.md` - 项目说明（英文学术格式）
- `PROJECT_SUMMARY.md` - 项目总结
- `ANONYMIZATION_CHECKLIST.md` - 匿名化检查清单
- `DEPENDENCIES.md` - 依赖说明文档（已在原始项目中）

## ❌ 已排除的文件（敏感数据）

### 用户数据
- `database.db` - 用户研究数据库
- `users.csv`, `users_admin.csv`, `users_users.csv` - 用户账户信息
- `username&password.csv` - 用户名密码文件

### 生成数据（运行时数据）
- `data/generations/` - AI 生成的图片
- `data/revisions/` - 用户修改的图片
- `data/thumbs/` - 缩略图
- `data/exports/` - 导出的用户数据

### 分析输出（包含用户信息）
- `backend/DataAnalysis/analysis_output/` - 分析结果输出
- `*.xlsx`, `*.csv` - 分析数据文件（在 Analyze/ 中的部分 CSV 已包含作为示例）

### 其他排除
- `wiseold/` - 旧版本 Wise（已废弃）
- `__pycache__/` - Python 缓存
- `.DS_Store` - macOS 系统文件
- `node_modules/` - NPM 依赖（需重新安装）

## 🔍 目录结构对比

### 原始项目 (Pica/)
```
Pica/
├── backend/
│   ├── api/                 # 后端核心代码
│   │   ├── *.py
│   │   ├── wise/
│   │   ├── Analyze/
│   │   └── wise_useragent_test/
│   └── DataAnalysis/        # 数据分析（另一套脚本）
├── data/                    # 数据目录
├── frontend/                # 前端代码
└── scripts/                 # 脚本
```

### 匿名项目 (AnonymousPica/)
```
AnonymousPica/
├── src/
│   ├── backend/             # 后端所有代码
│   │   ├── *.py            # 核心模块
│   │   ├── wise/           # Wise 模块
│   │   ├── Analyze/        # 研究分析脚本
│   │   └── wise_useragent_test/
│   └── frontend/            # 前端代码
├── scripts/                 # 运行脚本
├── data/                    # 数据目录
├── figs/                    # 图片（预留）
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## 📋 转移总结

### 文件统计
- **总文件数**: 约 100+ 个
- **Python 文件**: 68 个
- **JavaScript/JSX 文件**: 11 个
- **目标图片**: 60 个
- **脚本文件**: 4 个
- **配置文件**: 4 个
- **文档文件**: 5 个

### 匿名化处理
✅ 硬编码路径改为相对路径  
✅ API Keys 改为环境变量  
✅ 移除所有用户数据  
✅ 移除数据库文件  
✅ 排除运行时生成数据  
✅ .gitignore 配置完善  

### 完整性验证
✅ 所有核心功能文件已复制  
✅ 所有依赖模块已包含  
✅ Wise 智能助手完整转移  
✅ 研究分析脚本完整转移  
✅ 前端代码完整转移  
✅ 运行脚本已更新路径  

## ✅ 可以投稿

AnonymousPica 项目已完整准备好，所有必需文件已转移，敏感信息已移除，可用于学术投稿！
