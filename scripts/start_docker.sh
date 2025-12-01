#!/bin/bash
# start_docker.sh - 启动 LLaMA-Factory Docker 容器

set -e

# 解析参数（支持 --cpu 跳过/使用 CPU compose 文件）
CPU_MODE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --cpu)
            CPU_MODE=1
            shift
            ;;
        *)
            echo "✗ 未知参数: $1"
            echo "用法: bash scripts/start_docker.sh [--cpu]"
            exit 1
            ;;
    esac
done

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
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
if [ "$CPU_MODE" -eq 1 ]; then
    COMPOSE_FILE="$PROJECT_DIR/docker-compose-cpu.yml"
    echo "⚠ 使用 CPU 模式 (compose: docker-compose-cpu.yml)"
fi

docker-compose -f "$COMPOSE_FILE" down
docker-compose -f "$COMPOSE_FILE" up -d

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
echo "  bash scripts/stop_docker.sh [--cpu]"
echo ""
