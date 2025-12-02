# LLaMA-Factory Docker 完整项目

这是一个基于 Docker + RTX 4060 + LLaMA-Factory 的完整项目实现。

## 项目结构

```
LLaMA_Factory_docker/
├── docs/
│   └── instruction.md          # 详细的使用说明书
├── data/
│   ├── my_data.json            # 自定义训练数据集
│   └── dataset_info.json       # 数据集配置
├── output/                     # 训练输出文件夹
├── models/                     # 模型存储文件夹
├── scripts/
│   ├── setup_docker.sh         # Docker 环境初始化脚本
│   ├── start_docker.sh         # 启动Docker容器脚本
│   ├── stop_docker.sh          # 停止Docker容器脚本
│   └── train_example.sh        # 训练示例脚本
├── Dockerfile                  # 自定义Dockerfile (可选)
├── docker-compose.yml          # Docker Compose配置
└── README.md                   # 项目说明文档
```

## 快速开始

### 1. 环境检查

```bash
# 检查NVIDIA驱动
nvidia-smi

# 检查nvidia-container-toolkit
nvidia-container-toolkit --version
```

### 2. 启动项目

```bash
# 执行启动脚本
bash scripts/start_docker.sh

# 或使用Docker Compose
docker-compose up -d
```

### 3. 访问WebUI

在浏览器中打开 `http://localhost:7860`

## 主要功能

✅ Docker容器化部署  
✅ GPU支持 (nvidia-docker)  
✅ 自定义数据集集成  
✅ 多种微调方法 (SFT/LoRA/QLoRA/DPO)  
✅ RTX 4060 显卡优化  
✅ 自动化脚本  

## 文件说明

| 文件 | 说明 |
|------|------|
| `my_data.json` | 示例训练数据集，包含6个示例 |
| `dataset_info.json` | 数据集配置文件，注册自定义数据集 |
| `docker-compose.yml` | 完整的Docker Compose配置 |
| `scripts/setup_docker.sh` | 环境检查和初始化 |
| `scripts/start_docker.sh` | 启动Docker容器 |
| `scripts/stop_docker.sh` | 停止Docker容器 |

## 支持的模型

- Qwen2.5-0.5B (推荐初学者)
- Qwen2.5-1.5B
- Llama2-7B (QLoRA)
- Llama2-8B (QLoRA)

## 常见问题

### Q: CUDA Out of Memory
A: 减小Batch Size 或使用QLoRA量化方法

### Q: 找不到数据集
A: 确认已修改dataset_info.json并刷新WebUI

### Q: Docker无法调用GPU
A: 检查是否安装了nvidia-container-toolkit

## 脚本使用：无需手动设置 PYTHONPATH

项目中包含一个用于批量检测/转换文件编码的脚本：`scripts/convert_encoding_cli.py`。
为了方便在仓库根目录直接运行，脚本在启动时会把项目根加入 `sys.path`，因此你可以直接运行：

```bash
# dry-run（只检测并打印，不修改文件）
python3 scripts/convert_encoding_cli.py --root medical_ds/samples --target utf-8 --dry-run

# 真正执行并在修改前创建备份
python3 scripts/convert_encoding_cli.py --root medical_ds/samples --target utf-8 --backup
```

如果你更喜欢通过 Makefile 来调用（更简洁），仓库根还包含一个 `Makefile`（见下），可直接运行对应目标。

Makefile 示例（可传参）:

```bash
# 默认使用仓库中的 medical_ds/samples
make convert-dry

# 指定自定义目录或文件，例如直接传入 medical_ds
make convert-dry ROOT=medical_ds TARGET=utf-8

# 真正执行并创建备份
make convert-run ROOT=medical_ds TARGET=utf-8
```

## 许可证

MIT License
