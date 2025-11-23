#!/bin/bash
# start_docker.sh - 启动 LLaMA-Factory Docker 容器

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${PROJECT_DIR}/data"
OUTPUT_DIR="${PROJECT_DIR}/output"
MODELS_DIR="${PROJECT_DIR}/models"

echo "================================"
echo "启动 LLaMA-Factory Docker 容器"
echo "================================"

# 检查必要的目录
if [ ! -d "$DATA_DIR" ]; then
    echo "创建 data 目录..."
    mkdir -p "$DATA_DIR"
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "创建 output 目录..."
    mkdir -p "$OUTPUT_DIR"
fi

if [ ! -d "$MODELS_DIR" ]; then
    echo "创建 models 目录..."
    mkdir -p "$MODELS_DIR"
fi

# 尝试登入
docker login
echo -e "\n使用官方 LLaMA-Factory 镜像..."

echo -e "\n启动容器..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" down
docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d

echo -e "\n================================"
echo "✓ 容器启动成功！"
echo "================================"
echo ""
echo "WebUI 访问地址: http://localhost:7860"
echo ""
echo "查看日志:"
echo "  docker logs -f llama-factory"
echo ""
echo "停止容器:"
echo "  bash scripts/stop_docker.sh"
echo ""
