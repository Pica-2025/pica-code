#!/bin/bash

echo "========================================="
echo "  Pica Frontend Server Startup"
echo "========================================="

cd src/frontend

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo ""
echo "启动前端开发服务器..."
echo "URL: http://localhost:5173"
echo ""

npm run dev
