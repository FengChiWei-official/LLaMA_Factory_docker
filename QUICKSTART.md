# LLaMA-Factory Docker 完整项目 - 快速启动指南

## 📋 项目概述

这是一个完整的 **LLaMA-Factory + Docker + RTX 4060** 集成项目，可以帮助你在有限的显存条件下进行大模型微调。

- **目标硬件**: RTX 4060 (8GB VRAM)
- **框架**: LLaMA-Factory
- **容器**: Docker + nvidia-docker
- **支持的微调方法**: LoRA、QLoRA、SFT、DPO

## 🚀 快速开始 (5分钟)

### 第一步：环境检查

```bash
# 检查NVIDIA驱动
nvidia-smi

# 检查nvidia-container-toolkit
nvidia-container-toolkit --version

# 如果未安装，执行环境设置脚本
bash scripts/setup_docker.sh
```

### 第二步：启动Docker容器

```bash
# 方法1：使用启动脚本
bash scripts/start_docker.sh

# 方法2：使用Docker Compose
docker-compose up -d
```

### 第三步：访问WebUI

打开浏览器访问: **http://localhost:7860**

## 📂 项目结构详解

```
LLaMA_Factory_docker/
├── docs/
│   └── instruction.md              # 详细的配置和使用说明书
│
├── data/
│   ├── my_data.json               # 示例训练数据集 (6个例子)
│   └── dataset_info.json          # 数据集配置文件
│
├── output/                        # 训练输出目录
│   └── (自动生成的模型文件)
│
├── models/                        # 模型缓存目录
│   └── (自动下载的预训练模型)
│
├── scripts/
│   ├── setup_docker.sh            # ✓ 环境检查脚本
│   ├── start_docker.sh            # ✓ 启动容器脚本
│   ├── stop_docker.sh             # ✓ 停止容器脚本
│   └── train_example.sh           # ℹ️ 训练示例信息
│
├── Dockerfile                     # Docker镜像定制 (可选)
├── docker-compose.yml            # Docker Compose配置
├── README.md                      # 项目说明文档
└── QUICKSTART.md                 # 本文件
```

## 🎯 完整使用流程

### 步骤1: 准备数据

在 `data/my_data.json` 中添加你的训练数据，格式如下：

```json
[
  {
    "instruction": "问题/指令",
    "input": "补充信息（可选）",
    "output": "期望的回答"
  },
  ...
]
```

**已包含的示例数据**:
- Docker 使用教程
- GPU加速训练说明
- RTX 4060 显卡建议
- LLaMA-Factory 启动方法
- CUDA显存不足解决方案
- 数据准备步骤

### 步骤2: 注册数据集

数据已在 `data/dataset_info.json` 中注册：

```json
{
  "my_custom_dataset": {
    "file_name": "my_data.json"
  }
}
```

### 步骤3: WebUI 配置和训练

1. **访问**: http://localhost:7860
2. **选择模型**: Qwen2.5-0.5B-Instruct (初学者推荐)
3. **选择方式**: 
   - 左侧菜单 → "监督微调"
   - 微调方式: LoRA
4. **选择数据**:
   - 数据集: my_custom_dataset
5. **设置参数**:
   ```
   Epochs: 3
   Batch Size: 4
   Gradient Accumulation Steps: 4
   Learning Rate: 5e-5
   Cutoff Length: 512
   ```
6. **点击"开始训练"** 并监控Loss曲线

### 步骤4: 模型导出

训练完成后：
1. 切换到 "导出" 标签
2. 选择你训练的模型
3. 导出格式: LoRA 或 Merged
4. 输出路径: `/app/output` (宿主机: `./output`)

## ⚙️ 常用命令

```bash
# 查看容器状态
docker ps

# 查看实时日志
docker logs -f llama-factory

# 进入容器交互式终端
docker exec -it llama-factory bash

# 停止容器
bash scripts/stop_docker.sh

# 删除容器和镜像
docker stop llama-factory
docker rm llama-factory
docker rmi hiyouga/llama-factory:latest

# 检查GPU状态
docker exec llama-factory nvidia-smi
```

## 🔧 RTX 4060 优化建议

| 任务 | 推荐配置 |
|------|--------|
| **学习和测试** | Qwen2.5-0.5B + LoRA, Batch=4 |
| **小规模微调** | Qwen2.5-1.5B + LoRA, Batch=2 |
| **7B模型微调** | QLoRA (4-bit), Batch=1, Gradient Accumulation=4 |
| **8B模型微调** | QLoRA (4-bit), Batch=1, Cutoff Length=512 |

## ⚠️ 常见问题解决

### Q1: CUDA Out of Memory

**症状**: `CUDA out of memory` 错误

**解决方案**:
1. 减小 `Batch Size` (4 → 2 → 1)
2. 减小 `Cutoff Length` (512 → 256)
3. 启用 Gradient Checkpointing
4. 使用更小的模型或QLoRA量化

```bash
# 查看显存占用
docker exec llama-factory nvidia-smi
```

### Q2: 找不到数据集

**症状**: WebUI 中看不到 `my_custom_dataset`

**解决方案**:
1. 确认 `data/my_data.json` 存在
2. 确认 `data/dataset_info.json` 中已配置
3. 刷新 WebUI 页面 (Ctrl+F5)
4. 重启容器:
   ```bash
   docker restart llama-factory
   ```

### Q3: Docker 无法访问GPU

**症状**: 显示 `0 GPU detected`

**解决方案**:
```bash
# 检查nvidia-container-toolkit
nvidia-container-toolkit --version

# 如未安装，执行
bash scripts/setup_docker.sh
```

### Q4: WebUI 无响应

**症状**: 访问 http://localhost:7860 无反应

**解决方案**:
```bash
# 查看容器是否运行
docker ps

# 查看日志
docker logs -f llama-factory

# 重启容器
docker restart llama-factory

# 等待30秒后重新访问
```

## 📊 监控和调试

### 实时监控

```bash
# 监控GPU使用
watch -n 1 'docker exec llama-factory nvidia-smi'

# 查看容器资源
docker stats llama-factory

# 监控训练日志
docker logs -f --tail 50 llama-factory
```

### 进阶调试

```bash
# 进入容器查看文件
docker exec -it llama-factory bash
ls -la /app/data
cat /app/data/dataset_info.json

# 检查显卡驱动
docker exec llama-factory nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
```

## 🎓 建议学习路径

1. **第1天**: 使用示例数据跑通流程
   ```bash
   bash scripts/train_example.sh
   ```

2. **第2天**: 用自己的小数据集训练 0.5B 模型

3. **第3天**: 尝试 1.5B 模型或 LoRA 微调

4. **第4天**: 体验 QLoRA 进行 7B 模型微调

5. **第5天**: 尝试 DPO 或其他高级方法 (使用小模型)

## 📝 数据集准备完全指南

### Alpaca 格式 (推荐)

```json
[
  {
    "instruction": "问题/指令",
    "input": "可选的补充信息",
    "output": "期望的回答"
  }
]
```

### ShareGPT 格式 (适合多轮对话)

```json
[
  {
    "conversations": [
      {
        "from": "user",
        "value": "用户输入"
      },
      {
        "from": "assistant",
        "value": "助手回答"
      }
    ]
  }
]
```

## 🔐 性能优化技巧

| 技巧 | 作用 | 推荐 |
|------|------|------|
| **Gradient Checkpointing** | 降低显存占用 | ✓ 对4060必要 |
| **fp16 精度** | 加速训练 | ✓ 推荐使用 |
| **Gradient Accumulation** | 模拟更大batch | ✓ 设置为4-8 |
| **LoRA** | 参数高效微调 | ✓ 优先使用 |
| **QLoRA** | 4-bit量化微调 | ✓ 用于7B+模型 |

## 📚 相关资源

- [LLaMA-Factory 官方仓库](https://github.com/hiyouga/LLaMA-Factory)
- [Docker 官方文档](https://docs.docker.com/)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)
- [RTX 4060 性能指南](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4060/)

## 🎉 成功标志

当你看到以下信息，说明项目配置成功：

```
✓ WebUI 已就绪
✓ 所有依赖检查通过
✓ Docker 容器运行正常
✓ 可以访问 http://localhost:7860
✓ 能在数据集列表中看到 my_custom_dataset
```

## 📞 故障排查清单

- [ ] `nvidia-smi` 能正常显示GPU
- [ ] `docker ps` 显示 `llama-factory` 容器在运行
- [ ] `docker logs llama-factory` 无错误
- [ ] 能访问 http://localhost:7860
- [ ] WebUI 显示可用的GPU
- [ ] 数据集下拉框包含 `my_custom_dataset`
- [ ] 能选择模型并开始训练

## ✨ 开始你的微调之旅！

```bash
# 一键启动！
bash scripts/start_docker.sh
# 然后访问 http://localhost:7860
```

---

**最后更新**: 2025年
**作者**: LLaMA-Factory Docker Project
**许可证**: MIT
