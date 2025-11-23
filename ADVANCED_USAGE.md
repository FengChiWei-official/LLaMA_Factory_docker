# LLaMA-Factory Docker 完整项目 - 高级使用指南

## 📦 项目文件清单

你现在拥有的完整项目包括：

### 📄 文档文件

| 文件 | 用途 | 首选读者 |
|------|------|---------|
| `README.md` | 项目概览 | 所有人 |
| `QUICKSTART.md` | 快速开始指南 | 新手 |
| `REQUIREMENTS.md` | 环境要求 | 系统管理员 |
| `TRAINING_CONFIG.md` | 训练配置参考 | 高级用户 |
| `TROUBLESHOOTING.md` | 故障排查 | 遇到问题时 |
| `ADVANCED_USAGE.md` | 本文件 | 进阶用户 |
| `docs/instruction.md` | 原始中文指南 | 参考资料 |

### 🔧 脚本文件

| 脚本 | 功能 |
|------|------|
| `scripts/setup_docker.sh` | 环境检查和初始化 |
| `scripts/start_docker.sh` | 启动容器 |
| `scripts/stop_docker.sh` | 停止容器 |
| `scripts/train_example.sh` | 显示训练示例信息 |

### 📋 配置文件

| 文件 | 功能 |
|------|------|
| `Dockerfile` | 自定义镜像构建配置 |
| `docker-compose.yml` | Docker Compose 编排配置 |
| `data/dataset_info.json` | 数据集注册配置 |
| `data/my_data.json` | 示例训练数据 (6条) |

### 📂 目录结构

```
.
├── output/          # 训练输出 (自动生成)
├── models/          # 模型缓存 (自动生成)
└── data/            # 数据集和配置 (重要)
```

---

## 🚀 高级启动方式

### 方式1：使用官方镜像 (推荐)

```bash
bash scripts/start_docker.sh
```

### 方式2：使用 Docker Compose

```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 停止
docker-compose down

# 查看日志
docker-compose logs -f
```

### 方式3：使用自定义 Dockerfile

```bash
# 构建自定义镜像
docker build -t llama-factory-custom:latest .

# 启动容器
docker run -d --gpus all \
    --name llama-factory \
    --shm-size 16g \
    -p 7860:7860 \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/output:/app/output \
    -e PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    llama-factory-custom:latest
```

---

## 🎯 多模型微调策略

### 场景1：快速原型验证

**目标**: 24小时内验证想法是否可行

**策略**:
```
模型: Qwen2.5-0.5B
数据: 100-500条示例
方式: LoRA
参数:
  - Batch Size: 8
  - Epochs: 1
  - Learning Rate: 5e-5
总耗时: 5-15 分钟
```

**步骤**:
1. 准备小规模数据集
2. 在 WebUI 选择 0.5B 模型
3. 设置上述参数
4. 观察 Loss 是否下降

---

### 场景2：生产级微调

**目标**: 训练高质量的可部署模型

**策略**:
```
模型: Qwen2.5-1.5B
数据: 5000-10000条精选数据
方式: LoRA
参数:
  - Batch Size: 4
  - Gradient Accumulation: 2
  - Epochs: 3
  - Learning Rate: 5e-5
  - Warmup Ratio: 0.1
总耗时: 2-4 小时
```

**步骤**:
1. 数据清洗和质量检查
2. 将数据分为 train/val (9:1)
3. 在 WebUI 配置参数
4. 监控 val loss 防止过拟合
5. 导出最佳 checkpoint

---

### 场景3：多模型对比实验

**目标**: 对比不同模型的微调效果

**步骤**:

```bash
# 实验1: 0.5B 模型
# WebUI 选择 Qwen2.5-0.5B
# 参数: Batch=8, Epochs=3
# 记录: Loss 曲线和最终精度

# 实验2: 1.5B 模型
# WebUI 选择 Qwen2.5-1.5B
# 参数: Batch=4, Epochs=3
# 记录: Loss 曲线和最终精度

# 实验3: 7B 模型 QLoRA
# WebUI 选择 Llama2-7B
# 方式: QLoRA
# 参数: Batch=1, Gradient Accumulation=4
# 记录: Loss 曲线和最终精度

# 比较结果
# 绘制不同模型的 Loss 曲线
# 评估训练速度、显存占用、最终性能
```

---

## 💾 数据管理最佳实践

### 数据集版本控制

创建多个版本的数据集用于实验：

```bash
# 目录结构
data/
├── dataset_info.json
├── my_data_v1.json      # 版本1: 原始数据
├── my_data_v2.json      # 版本2: 去重后
├── my_data_v3.json      # 版本3: 加入质量评分
├── my_data_test.json    # 测试集
└── my_data_val.json     # 验证集
```

修改 `dataset_info.json`：

```json
{
  "my_dataset_v1": {
    "file_name": "my_data_v1.json"
  },
  "my_dataset_v2": {
    "file_name": "my_data_v2.json"
  },
  "my_dataset_v3": {
    "file_name": "my_data_v3.json"
  }
}
```

### 数据质量评估脚本

```python
# analyze_data.py
import json
from collections import Counter

def analyze_dataset(file_path):
    with open(file_path) as f:
        data = json.load(f)
    
    print(f"总数据条数: {len(data)}")
    
    # 统计字段
    if isinstance(data[0], dict):
        keys = set()
        for item in data:
            keys.update(item.keys())
        print(f"包含字段: {keys}")
        
        # 检查空值
        for key in keys:
            empty_count = sum(1 for item in data if not item.get(key))
            print(f"  {key}: {empty_count} 条为空")
        
        # 长度统计
        lengths = []
        for item in data:
            for value in item.values():
                if isinstance(value, str):
                    lengths.append(len(value))
        
        if lengths:
            print(f"文本长度: 平均 {sum(lengths)/len(lengths):.0f}, 最大 {max(lengths)}")

# 使用
analyze_dataset('data/my_data.json')
```

---

## 🔄 多阶段训练

### 第一阶段：基础能力

```
模型: 0.5B
任务: 基础指令理解
数据: 500 条基础数据
方式: LoRA
参数: Batch=8, Epochs=3, LR=5e-5
输出: checkpoint_1
```

### 第二阶段：领域微调

```
初始权重: checkpoint_1
任务: 领域特定任务
数据: 1000 条领域数据
方式: LoRA
参数: Batch=4, Epochs=2, LR=1e-5 (降低学习率)
输出: checkpoint_2
```

### 第三阶段：偏好学习

```
模型: checkpoint_2
任务: 质量改进
方式: DPO
数据: 500 条 (chosen/rejected 对)
参数: Batch=4, Epochs=2, LR=5e-6
输出: final_model
```

---

## 🧪 实验追踪

### 创建实验日志

```bash
# experiments/
├── exp_001_baseline/
│   ├── config.json        # 超参数
│   ├── metrics.json       # 性能指标
│   ├── loss.csv           # Loss 曲线
│   └── model/             # 模型权重
│
├── exp_002_with_warmup/
│   ├── config.json
│   ├── metrics.json
│   ├── loss.csv
│   └── model/
│
└── README.md              # 实验记录
```

### 记录模板

```json
{
  "experiment_id": "exp_001",
  "date": "2025-11-22",
  "model": "Qwen2.5-1.5B",
  "dataset": "my_data_v2",
  "hyperparameters": {
    "batch_size": 4,
    "learning_rate": 5e-5,
    "epochs": 3,
    "warmup_ratio": 0.1
  },
  "results": {
    "final_train_loss": 0.45,
    "final_eval_loss": 0.52,
    "training_time": "2.5h",
    "gpu_memory_used": "6.2GB"
  },
  "notes": "这个配置表现很好，推荐使用"
}
```

---

## 📊 性能优化技巧

### GPU 显存优化

```bash
# 1. 启用 Gradient Checkpointing
#    可减少 30% 显存占用
#    缺点: 训练速度降低 ~10%

# 2. 使用 FlashAttention-2
#    可减少 20% 显存占用
#    加速 30-50%

# 3. 启用 Flash Attention 2 + Gradient Checkpointing
#    综合效果最好

# 4. 对于 QLoRA:
#    - 使用 8-bit Adam 而不是标准 Adam
#    - 启用 CPU Offloading (牺牲速度换显存)
```

### 训练速度优化

```bash
# 1. 增加 Batch Size (在显存允许范围内)
#    4 → 8 可加速约 1.5x

# 2. 启用 Flash Attention 2
#    可加速 30-50%

# 3. 启用 Mixed Precision (FP16)
#    自动启用，加速 20-40%

# 4. 降低 Evaluation 频率
#    比如从每 100 步改为每 500 步

# 5. 增加 Number of Workers for Data Loading
#    需要调整 config.json
```

---

## 🔗 模型合并和部署

### 步骤1：导出 LoRA 权重

```bash
# 在 WebUI 的 "导出" 标签中
# 1. 选择训练好的模型
# 2. 导出格式: LoRA 权重
# 3. 输出位置: /app/output
```

### 步骤2：合并权重

```bash
# 进入容器
docker exec -it llama-factory bash

# 合并权重
python src/train.py \
    --export_model \
    --export_dir ./merged_model \
    --model_name_or_path Qwen/Qwen2.5-1.5B-Instruct \
    --adapter_name_or_path ./lora_weights
```

### 步骤3：模型量化 (可选)

```bash
# 使用 GPTQ 量化
python -m llamafactory.cli export \
    --model_name_or_path ./merged_model \
    --export_dir ./quantized_model \
    --quantization_bit 4
```

### 步骤4：模型部署

部署到 Ollama：
```bash
# 1. 将模型复制到 Ollama 目录
cp -r ./merged_model ~/.ollama/models/

# 2. 创建 Modelfile
cat > Modelfile << EOF
FROM ./merged_model
EOF

# 3. 创建模型
ollama create my-model -f Modelfile

# 4. 运行模型
ollama run my-model "你好"
```

---

## 🐛 调试和性能分析

### 启用详细日志

```bash
# 设置日志级别
docker exec llama-factory bash -c "
export TRANSFORMERS_VERBOSITY=debug
export TF_CPP_MIN_LOG_LEVEL=0
python -m llamafactory.webui
"
```

### 性能剖析

```python
# profile_training.py
import cProfile
import pstats
from io import StringIO

# 运行性能剖析
pr = cProfile.Profile()
pr.enable()

# ... 训练代码 ...

pr.disable()
s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(20)  # 打印前20个耗时函数
print(s.getvalue())
```

---

## 🔐 安全性最佳实践

### 保护数据隐私

```bash
# 1. 使用环境变量而不是硬编码敏感信息
docker run -d --gpus all \
    -e HF_TOKEN=your_token_here \
    hiyouga/llama-factory:latest

# 2. 限制容器网络访问
docker network create restricted
docker run --network restricted ...

# 3. 定期删除中间产物
docker exec llama-factory rm -rf /tmp/*
```

### 模型版本控制

```bash
# 使用 Git LFS 管理大文件
git lfs install
git lfs track "*.bin" "*.safetensors"

# 记录模型版本
echo "model_v1.bin (SHA256: xxx)" > models/manifest.txt
```

---

## 📈 监控和告警

### 实时监控脚本

```bash
#!/bin/bash
# monitor.sh

while true; do
    echo "=== $(date) ==="
    docker stats llama-factory --no-stream
    
    echo ""
    docker exec llama-factory nvidia-smi \
        --query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total \
        --format=csv
    
    sleep 10
done
```

### 异常告警

```python
# alert.py
import subprocess
import time
import json

def get_gpu_memory():
    result = subprocess.run([
        'docker', 'exec', 'llama-factory', 'nvidia-smi',
        '--query-gpu=memory.used,memory.total',
        '--format=csv,noheader'
    ], capture_output=True, text=True)
    used, total = map(int, result.stdout.split(','))
    return used / total * 100

# 告警阈值
MEMORY_THRESHOLD = 95

while True:
    mem_usage = get_gpu_memory()
    if mem_usage > MEMORY_THRESHOLD:
        print(f"⚠️ WARNING: GPU memory at {mem_usage:.1f}%")
        # 发送告警 (邮件/Slack/钉钉)
    time.sleep(60)
```

---

## 🎓 学习资源

### 官方文档
- [LLaMA-Factory GitHub](https://github.com/hiyouga/LLaMA-Factory)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [LoRA 论文](https://arxiv.org/abs/2106.09685)

### 教程和示例
- LLaMA-Factory 官方教程
- PEFT (Parameter-Efficient Fine-Tuning) 库文档
- QLoRA 实践指南

---

**最后更新**: 2025年11月
**难度**: 中级到高级
**先决条件**: 完成 QUICKSTART 指南
