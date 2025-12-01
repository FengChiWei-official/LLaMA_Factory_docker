#!/bin/bash
# stop_docker.sh - 停止 LLaMA-Factory Docker 容器

CPU_MODE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --cpu)
            CPU_MODE=1
            shift
            ;;
        *)
            echo "✗ 未知参数: $1"
            echo "用法: bash scripts/stop_docker.sh [--cpu]"
            exit 1
            ;;
    esac
done

echo "================================"
echo "停止 LLaMA-Factory Docker 容器"
echo "================================"

COMPOSE_FILE="docker-compose.yml"
if [ "$CPU_MODE" -eq 1 ]; then
    COMPOSE_FILE="docker-compose-cpu.yml"
    echo "⚠ 使用 CPU 模式 (compose: docker-compose-cpu.yml)"
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if docker ps -a --format '{{.Names}}' | grep -q '^llama-factory$'; then
    echo "正在停止容器 (compose: $COMPOSE_FILE)..."
    docker-compose -f "$PROJECT_DIR/$COMPOSE_FILE" down
    echo "✓ 容器已停止并从 compose 中移除"
else
    echo "容器 llama-factory 未在运行"
fi

echo "================================"
