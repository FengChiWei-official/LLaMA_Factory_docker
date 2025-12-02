#!/bin/bash
# train_example.sh - 训练示例脚本

set -e

echo "================================"
echo "LLaMA-Factory 训练示例"
echo "================================"

# 检查容器是否在运行
if ! docker ps --format '{{.Names}}' | grep -q '^llama-factory$'; then
    # 如果未通过 docker ps 找到，尝试用 docker compose 查询（如果可用）
    if docker compose version >/dev/null 2>&1 && [ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/docker-compose.yml" ]; then
        if docker compose -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/docker-compose.yml" ps --services --filter "status=running" | grep -q '^llama-factory$'; then
            echo "✓ llama-factory 服务正在运行 (via docker compose)"
        else
            echo "✗ 容器/服务 llama-factory 未在运行"
            echo "请先执行: bash scripts/start_docker.sh"
            exit 1
        fi
    else
        echo "✗ 容器 llama-factory 未在运行"
        echo "请先执行: bash scripts/start_docker.sh"
        exit 1
    fi
fi

echo -e "\n[1/3] 等待容器就绪..."
sleep 5

echo -e "\n[2/3] 检查WebUI..."
if curl -s http://localhost:7860 > /dev/null; then
    echo "✓ WebUI 已就绪"
else
    echo "⚠ WebUI 可能还在初始化，请稍后..."
fi

echo -e "\n[3/3] 训练信息"
echo "================================"
echo "模型推荐: Qwen2.5-0.5B-Instruct"
echo "微调方式: LoRA"
echo "数据集: my_custom_dataset"
echo "Batch Size: 4"
echo "Epochs: 3"
echo "Learning Rate: 5e-5"
echo "================================"

echo -e "\n请访问 http://localhost:7860 在WebUI中进行训练配置"
echo ""
echo "查看容器日志:"
echo "  docker logs -f llama-factory"
echo ""
echo "进入容器终端:"
echo "  docker exec -it llama-factory bash"
echo ""
