#!/bin/bash
# stop_docker.sh - 停止 LLaMA-Factory Docker 容器

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "================================"
echo "停止 LLaMA-Factory Docker 容器"
echo "================================"

# 选择 compose 命令
choose_compose_cmd() {
    if docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
    else
        echo "";
    fi
}
COMPOSE_CMD=$(choose_compose_cmd)

if [ -f "$PROJECT_DIR/docker-compose.yml" ] && [ -n "$COMPOSE_CMD" ]; then
    echo "使用 $COMPOSE_CMD 停止服务 (compose down)..."
    $COMPOSE_CMD -f "$PROJECT_DIR/docker-compose.yml" down --remove-orphans || true
    echo "✓ compose 服务已停止 (若存在)"
else
    # 回退到基于容器名的停止
    if docker ps -a --format '{{.Names}}' | grep -q '^llama-factory$'; then
        echo "正在停止容器 llama-factory..."
        docker stop llama-factory || true
        docker rm llama-factory || true
        echo "✓ 容器已停止并移除"
    else
        echo "容器 llama-factory 未在运行"
    fi
fi

echo "================================"
