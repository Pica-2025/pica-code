# Pica: Interactive Image Generation System

> **Note**: This repository is submitted for anonymous peer review. Author information has been removed.

## Overview

Pica is a web-based system for studying human-AI collaborative image generation. It enables users to iteratively refine AI-generated images through natural language prompts, supporting comparative studies between different image generation models. It's an abbreviation for the great artist Pablo Picasso.

## Features

- **Dual-Model Support**: Integrates multiple image generation APIs (Qwen-Image, Gemini)
- **Interactive Refinement**: Users can iteratively improve generated images through prompt modifications
- **Multi-Dimensional Rating**: Evaluates generated images across multiple dimensions (style, object count, perspective, depth/background)
- **Automatic Scoring**: ML-based automatic scoring system using image similarity metrics
- **Data Export**: Comprehensive data export for research analysis

## Project Structure

```
AnonymousPica/
├── src/
│   ├── backend/          # FastAPI backend
│   └── frontend/         # React frontend
├── scripts/              # Utility scripts
│   ├── init_db.py        # Initialize database
│   ├── build_manifest.py # Generate image manifest
│   ├── start_backend.sh  # Start backend server
│   └── start_frontend.sh # Start frontend server
├── data/                 # Data directory
│   ├── targets/          # Target images
│   ├── generations/      # Generated images (runtime)
│   ├── revisions/        # Revised images (runtime)
│   └── manifests/        # Image manifests
├── figs/                 # Figures for documentation
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── LICENSE               # MIT License
└── README.md             # This file
```

## System Requirements

- **Python**: 3.10 or higher
- **Node.js**: 18 or higher
- **Operating System**: macOS, Linux, or Windows
- **Memory**: 8GB RAM recommended
- **Storage**: 10GB+ for image data

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AnonymousPica
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and fill in your API keys:
# - DASHSCOPE_API_KEY: For Qwen-Image API
# - GEMINI_API_KEY: For Google Gemini API
```

### 4. Prepare Data

Place target images in `data/targets/` directory (see `data/README.md` for details).

### 5. Initialize Database

```bash
python scripts/init_db.py
```

### 6. Generate Image Manifest

```bash
python scripts/build_manifest.py
```

### 7. Install Frontend Dependencies

```bash
cd src/frontend
npm install
cd ../..
```

## Usage

### Start Backend Server

```bash
bash scripts/start_backend.sh
# Backend will be available at http://localhost:8000
# API documentation: http://localhost:8000/docs
```

### Start Frontend Server

```bash
bash scripts/start_frontend.sh
# Frontend will be available at http://localhost:5173
```

### Default Accounts

- **Admin**: `admin` / `admin123`
- **Tester**: `test001` / `password123` (test001 ~ test010)

## API Keys

This system requires API keys from the following services:

- **Alibaba Cloud DashScope**: For Qwen-Image API ([Get API Key](https://help.aliyun.com/zh/model-studio/get-api-key))
- **Google AI**: For Gemini API ([Get API Key](https://ai.google.dev/))

Configure these in `.env` file before running.

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **PyJWT**: JWT-based authentication
- **Pillow & OpenCV**: Image processing
- **Scikit-learn**: Automatic scoring models

### Frontend
- **React**: UI framework
- **Ant Design**: UI component library
- **Axios**: HTTP client
- **Vite**: Build tool

## Data Privacy

**This repository does NOT include:**
- User study data
- Database files
- User account information
- Analysis outputs with personally identifiable information

These items are excluded via `.gitignore` to protect participant privacy.

## Citation

If you use this code in your research, please cite:

```
[Citation information will be added after peer review]
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This research uses APIs from:
- Alibaba Cloud DashScope (Qwen-Image)
- Google AI (Gemini)

---

**For Reviewers**: This is an anonymized version for peer review. Full acknowledgments and author information will be added in the camera-ready version.
