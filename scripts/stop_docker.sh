#!/bin/bash
# stop_docker.sh - 停止 LLaMA-Factory Docker 容器

echo "================================"
echo "停止 LLaMA-Factory Docker 容器"
echo "================================"

if docker ps -a --format '{{.Names}}' | grep -q '^llama-factory$'; then
    echo "正在停止容器..."
    docker stop llama-factory
    echo "✓ 容器已停止"
else
    echo "容器 llama-factory 未在运行"
fi

echo "================================"
