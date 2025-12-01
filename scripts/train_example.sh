#!/bin/bash
# train_example.sh - 训练示例脚本

set -e

# 支持 --cpu （使用 CPU compose 文件）
CPU_MODE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --cpu)
            CPU_MODE=1
            shift
            ;;
        *)
            echo "✗ 未知参数: $1"
            echo "用法: bash scripts/train_example.sh [--cpu]"
            exit 1
            ;;
    esac
done

echo "================================"
echo "LLaMA-Factory 训练示例"
echo "================================"

# 检查容器是否在运行
if ! docker ps --format '{{.Names}}' | grep -q '^llama-factory$'; then
    echo "✗ 容器 llama-factory 未在运行"
    echo "请先执行: bash scripts/start_docker.sh [--cpu]"
    exit 1
fi

echo -e "\n[1/3] 等待容器就绪..."
sleep 5

echo -e "\n[2/3] 检查WebUI..."
if [ "$CPU_MODE" -eq 1 ]; then
    echo "⚠ 当前为 CPU 模式 (compose: docker-compose-cpu.yml)"
fi
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
