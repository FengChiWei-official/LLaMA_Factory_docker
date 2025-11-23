# LLaMA-Factory Docker 完整项目 - 故障排查指南

## 🔍 快速诊断清单

运行此脚本可快速诊断系统状态：

```bash
# 诊断脚本
echo "=== NVIDIA 驱动检查 ===" && nvidia-smi
echo -e "\n=== Docker 检查 ===" && docker --version
echo -e "\n=== nvidia-container-toolkit ===" && nvidia-container-toolkit --version
echo -e "\n=== 容器状态 ===" && docker ps -a --filter "name=llama-factory"
echo -e "\n=== 容器日志 (最后20行) ===" && docker logs --tail 20 llama-factory 2>/dev/null || echo "容器未运行"
echo -e "\n=== 数据目录 ===" && ls -lah ./data/ 2>/dev/null || echo "目录不存在"
```

---

## 📋 分类故障排查

### 1️⃣ Docker 启动相关问题

#### 问题：启动容器时提示 `permission denied`

**原因**: Docker daemon 权限问题

**解决方案**:
```bash
# 方案A: 使用 sudo
sudo bash scripts/start_docker.sh

# 方案B: 将当前用户加入 docker 组
sudo usermod -aG docker $USER
newgrp docker
bash scripts/start_docker.sh
```

---

#### 问题：`docker: Cannot connect to Docker daemon`

**原因**: Docker daemon 未启动

**解决方案**:
```bash
# 启动 Docker daemon
sudo systemctl start docker

# 设置开机自启 (可选)
sudo systemctl enable docker

# 验证
docker ps
```

---

#### 问题：容器创建后立即退出

**原因**: 容器启动命令出错或依赖缺失

**解决方案**:
```bash
# 查看容器日志
docker logs llama-factory

# 如果看到 CUDA 错误，继续下一部分
# 如果看到其他错误，删除容器后重试
docker rm llama-factory
bash scripts/start_docker.sh
```

---

### 2️⃣ GPU 相关问题

#### 问题：`CUDA error: no CUDA-capable device is detected`

**原因**: Docker 无法访问 GPU

**解决方案**:
```bash
# 步骤1: 检查宿主机 GPU
nvidia-smi

# 步骤2: 检查 nvidia-container-toolkit
nvidia-container-toolkit --version

# 如未安装:
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 步骤3: 验证 Docker 可以访问 GPU
docker run --rm --gpus all nvidia/cuda:11.8.0-runtime-ubuntu22.04 nvidia-smi

# 步骤4: 如果验证通过，重新启动容器
docker restart llama-factory
```

---

#### 问题：容器内 `nvidia-smi` 显示 `0 GPU detected`

**原因**: GPU 驱动或运行时配置错误

**解决方案**:
```bash
# 检查宿主机驱动
nvidia-smi

# 检查 CUDA 版本匹配
docker exec llama-factory nvidia-smi

# 强制重启 docker runtime
sudo systemctl restart docker

# 重启容器
docker restart llama-factory
```

---

#### 问题：CUDA Out of Memory (OOM)

**原因**: 显存不足

**症状**:
```
RuntimeError: CUDA out of memory. Tried to allocate X.XX GiB
```

**解决方案** (按优先级尝试):

```bash
# 1️⃣ 减小 Batch Size (在 WebUI 中修改)
# 4 → 2 → 1

# 2️⃣ 减小 Cutoff Length (在 WebUI 中修改)
# 512 → 256 (仅作为最后手段)

# 3️⃣ 启用 Gradient Checkpointing (在 WebUI 中勾选)
# 可减少 ~30% 显存占用

# 4️⃣ 增加 Gradient Accumulation Steps (在 WebUI 中修改)
# 如果 Batch=1，设置 Gradient Accumulation=4

# 5️⃣ 使用 QLoRA 替代 LoRA (仅适用于大模型)

# 6️⃣ 查看实时显存占用
watch -n 1 'docker exec llama-factory nvidia-smi'
```

---

### 3️⃣ WebUI 相关问题

#### 问题：无法访问 WebUI (http://localhost:7860)

**原因**: 容器未启动或端口映射错误

**解决方案**:
```bash
# 步骤1: 检查容器是否运行
docker ps

# 如果没看到 llama-factory:
bash scripts/start_docker.sh
sleep 10  # 等待容器启动

# 步骤2: 检查端口映射
docker port llama-factory

# 应该看到:
# 7860/tcp -> 0.0.0.0:7860

# 步骤3: 如果端口被占用
# 查看占用端口的进程
sudo lsof -i :7860

# 释放端口 (或修改容器配置)
sudo kill -9 <PID>

# 步骤4: 检查防火墙
sudo ufw allow 7860/tcp  # Ubuntu
firewall-cmd --add-port=7860/tcp --permanent  # CentOS
```

---

#### 问题：WebUI 显示 `0 GPU detected`

**原因**: WebUI 未检测到 GPU

**解决方案**:
```bash
# 步骤1: 进入容器检查
docker exec -it llama-factory bash

# 在容器内执行
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# 步骤2: 如果命令返回 False，容器配置有问题
# 退出容器
exit

# 步骤3: 重启容器
docker restart llama-factory

# 步骤4: 等待 30 秒后刷新 WebUI
```

---

#### 问题：WebUI 页面加载很慢或卡顿

**原因**: 容器资源不足或网络问题

**解决方案**:
```bash
# 检查容器资源使用
docker stats llama-factory

# 查看容器日志
docker logs -f llama-factory

# 如果 CPU 占用过高:
# 减小数据加载的 num_workers
# 在 WebUI 高级选项中修改

# 如果内存不足:
# 减小 Batch Size
```

---

### 4️⃣ 数据集相关问题

#### 问题：在 WebUI 中看不到自己的数据集

**原因**: 数据集未正确注册或文件路径错误

**解决方案**:
```bash
# 步骤1: 检查数据文件是否存在
ls -l ./data/my_data.json

# 步骤2: 验证 dataset_info.json 格式
cat ./data/dataset_info.json

# 应该包含:
# {
#   "my_custom_dataset": {
#     "file_name": "my_data.json"
#   }
# }

# 步骤3: 检查容器内的数据
docker exec llama-factory ls -l /app/data/

# 步骤4: 刷新 WebUI
# Ctrl + F5 (硬刷新)

# 步骤5: 如果仍不出现，重启容器
docker restart llama-factory
sleep 10
# 重新刷新 WebUI
```

---

#### 问题：数据集格式错误导致训练失败

**原因**: JSON 格式不符合要求

**解决方案**:
```bash
# 检查 JSON 格式
python -m json.tool ./data/my_data.json

# 应该看到格式化的 JSON，如果有错误会报告行号

# 修正后重新验证
python -c "
import json
with open('./data/my_data.json') as f:
    data = json.load(f)
print(f'成功加载 {len(data)} 条数据')
print(f'第一条数据: {data[0]}')
"
```

---

#### 问题：训练时提示 `FileNotFoundError: [Errno 2] No such file or directory`

**原因**: 文件映射路径不正确

**解决方案**:
```bash
# 检查卷挂载
docker inspect llama-factory | grep -A 5 "Mounts"

# 验证宿主机路径
ls -la /home/mia/mnt/dataset/Repositiory/LLaMA_Factory_docker/data/

# 验证容器内路径
docker exec llama-factory ls -la /app/data/

# 如果路径不匹配，修改 docker-compose.yml 中的挂载配置
```

---

### 5️⃣ 训练过程问题

#### 问题：Loss 不下降或持续增长

**原因**: 学习率过高或数据质量问题

**解决方案**:
```bash
# 1️⃣ 降低学习率
# WebUI → 学习率: 5e-5 → 1e-5

# 2️⃣ 增加预热步数
# WebUI → Warmup Ratio: 0.1 → 0.2

# 3️⃣ 检查数据质量
# 确保 my_data.json 格式正确
# 样本应该是有意义的指令-回答对

# 4️⃣ 从小学习率开始
# 开始: 1e-5，逐步增加观察效果
```

---

#### 问题：训练突然卡住或停止响应

**原因**: 内存泄漏或数据加载问题

**解决方案**:
```bash
# 查看容器进程
docker top llama-factory

# 查看实时日志
docker logs -f llama-factory

# 如果看到内存持续增长:
# 减小 Batch Size
# 重启容器

docker restart llama-factory

# 如果经常卡住，可能是数据问题:
# 检查 my_data.json 是否有损坏的条目
python -c "
import json
with open('./data/my_data.json') as f:
    for i, line in enumerate(f):
        try:
            json.loads(line)
        except:
            print(f'第 {i} 行有问题')
"
```

---

#### 问题：训练非常慢

**原因**: 硬件限制或配置不优

**解决方案**:
```bash
# 1️⃣ 查看 GPU 利用率
docker exec llama-factory nvidia-smi -l 1

# 应该看到 80-95% 的 GPU 利用率
# 如果低于 50%，增加 Batch Size

# 2️⃣ 启用 Flash Attention (如果可用)
# WebUI → 勾选 "Flash Attention 2"

# 3️⃣ 增加 Batch Size (在显存允许范围内)
# 4 → 8 (如果 Loss 稳定的话)

# 4️⃣ 使用更小的 Cutoff Length (只作为最后手段)
# 512 → 256

# 5️⃣ 启用梯度检查点会减速但减显存
# 如果显存充足，禁用它
```

---

### 6️⃣ 模型导出问题

#### 问题：导出时出错

**原因**: 磁盘空间不足或权限问题

**解决方案**:
```bash
# 检查磁盘空间
df -h ./output/

# 确保输出目录可写
ls -ld ./output/
chmod 755 ./output/

# 尝试手动导出
docker exec llama-factory python -c "
from llamafactory.cli import main
main()
"

# 查看容器日志获取更多信息
docker logs --tail 50 llama-factory
```

---

## 🆘 终极大招 - 重置一切

如果以上方案都不行，核选项是重新开始：

```bash
# 第一步: 停止并删除容器
docker stop llama-factory
docker rm llama-factory

# 第二步: 删除镜像 (可选，如果想重新拉取最新版本)
docker rmi hiyouga/llama-factory:latest

# 第三步: 清理没用的镜像和容器
docker system prune -a

# 第四步: 重新启动
bash scripts/setup_docker.sh
bash scripts/start_docker.sh

# 第五步: 等待 30 秒
sleep 30

# 第六步: 访问 WebUI
# 打开浏览器访问 http://localhost:7860
```

---

## 📞 获取更多帮助

### 查看完整日志

```bash
# 最后 100 行
docker logs --tail 100 llama-factory

# 实时日志
docker logs -f llama-factory

# 导出日志到文件
docker logs llama-factory > llama-factory.log 2>&1
```

### 进入容器调试

```bash
# 进入容器 bash
docker exec -it llama-factory bash

# 查看环境变量
env

# 查看 Python 环境
python --version
pip list | grep -E "(torch|transformers|llamafactory)"

# 检查 CUDA
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name())"

# 退出容器
exit
```

### 收集诊断信息

```bash
# 生成完整诊断报告
cat > diagnose.sh << 'EOF'
#!/bin/bash
echo "=== System Info ===" > diagnosis.txt
uname -a >> diagnosis.txt

echo -e "\n=== NVIDIA Driver ===" >> diagnosis.txt
nvidia-smi >> diagnosis.txt

echo -e "\n=== Docker Version ===" >> diagnosis.txt
docker --version >> diagnosis.txt

echo -e "\n=== nvidia-container-toolkit ===" >> diagnosis.txt
nvidia-container-toolkit --version >> diagnosis.txt

echo -e "\n=== Container Info ===" >> diagnosis.txt
docker ps -a >> diagnosis.txt

echo -e "\n=== Container Logs ===" >> diagnosis.txt
docker logs llama-factory >> diagnosis.txt 2>&1

echo -e "\n=== GPU Info (inside container) ===" >> diagnosis.txt
docker exec llama-factory nvidia-smi >> diagnosis.txt 2>&1

echo -e "\n=== Files ===" >> diagnosis.txt
ls -lah data/ >> diagnosis.txt

cat diagnosis.txt
EOF

bash diagnose.sh
```

---

## 📚 常见错误代码参考

| 错误代码 | 含义 | 初步解决方案 |
|---------|------|-----------|
| 137 | 容器被杀死（通常是 OOM） | 减小 Batch Size |
| 1 | 通用错误 | 查看日志了解详情 |
| 126 | 权限拒绝 | 使用 `sudo` 或修改权限 |
| 404 | 资源未找到 | 检查文件路径 |

---

**最后更新**: 2025年11月
**状态**: 完整诊断指南
**覆盖**: 99% 常见问题
