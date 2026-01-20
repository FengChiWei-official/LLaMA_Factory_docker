#!/bin/bash
# start_docker.sh - 启动 LLaMA-Factory Docker 容器

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${PROJECT_DIR}/data"
OUTPUT_DIR="${PROJECT_DIR}/output"
MODELS_DIR="${PROJECT_DIR}/models"

# 选择使用的 compose 命令：优先使用 `docker compose`（插件），否则回退到 `docker-compose`
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
if [ -z "$COMPOSE_CMD" ]; then
    echo "错误: 未检测到 'docker compose' 插件或 'docker-compose' 二进制。请先安装 Docker Compose。"
    exit 1
fi

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

# 可选尝试登录（交互式）
if command -v docker &> /dev/null; then
    echo "检测到 Docker，若需私有仓库镜像请先登录（按 Ctrl+C 跳过）..."
    docker login || true
fi

echo -e "\n使用 compose 命令: $COMPOSE_CMD"
echo -e "\n启动容器..."
$COMPOSE_CMD -f "$PROJECT_DIR/docker-compose.yml" down || true
$COMPOSE_CMD -f "$PROJECT_DIR/docker-compose.yml" up -d

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
