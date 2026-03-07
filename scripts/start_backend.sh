#!/bin/bash

echo "========================================="
echo "  Pica Backend Server Startup"
echo "========================================="

if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 文件不存在"
    echo "请复制 .env.example 并配置："
    echo "  cp .env.example .env"
    echo "  # 然后编辑 .env 文件填入 API 密钥"
    exit 1
fi

if [ ! -f "src/backend/database.db" ]; then
    echo "⚠️  数据库不存在，正在初始化..."
    python scripts/init_db.py
fi

if [ ! -f "data/manifests/targets_manifest.csv" ]; then
    echo "⚠️  清单文件不存在，正在生成..."
    python scripts/build_manifest.py
fi

echo ""
echo "启动后端服务器..."
echo "URL: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo ""

cd src/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
