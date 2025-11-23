# 训练配置参考

## 🎯 推荐的超参数配置

### 配置1：0.5B 小模型全量微调 (最稳定)

**硬件**: RTX 4060 (8GB)
**模型**: Qwen2.5-0.5B-Instruct
**方式**: LoRA

```
- Epochs: 3
- Batch Size: 8
- Gradient Accumulation: 1
- Learning Rate: 5e-5
- Warmup Ratio: 0.1
- Cutoff Length: 512
- Weight Decay: 0
```

**预期显存**: 3-4GB
**预期训练时间**: 30-60分钟 (取决于数据量)

---

### 配置2：1.5B 中等模型 LoRA (推荐)

**硬件**: RTX 4060 (8GB)
**模型**: Qwen2.5-1.5B-Instruct
**方式**: LoRA

```
- Epochs: 3
- Batch Size: 4
- Gradient Accumulation: 2
- Learning Rate: 5e-5
- Warmup Ratio: 0.1
- Cutoff Length: 512
- LoRA Rank: 8
- LoRA Alpha: 16
- LoRA Dropout: 0.05
```

**预期显存**: 5-6GB
**预期训练时间**: 1-2小时

---

### 配置3：7B 大模型 QLoRA 微调 (显存极限)

**硬件**: RTX 4060 (8GB)
**模型**: Llama2-7B 或 Qwen1.8B
**方式**: QLoRA (4-bit quantization)

```
- Epochs: 1-2
- Batch Size: 1
- Gradient Accumulation: 4
- Learning Rate: 1e-4
- Warmup Ratio: 0.03
- Cutoff Length: 256 (注意：长上下文会OOM)
- LoRA Rank: 8
- LoRA Alpha: 32
- LoRA Dropout: 0.05
- Quantization: 4bit
```

**预期显存**: 7-8GB (已接近满载)
**预期训练时间**: 2-3小时

---

### 配置4：DPO 偏好对齐 (仅用小模型)

**硬件**: RTX 4060 (8GB)
**模型**: Qwen2.5-0.5B-Instruct
**方式**: DPO (需要两个模型)

```
- Epochs: 2
- Batch Size: 4
- Gradient Accumulation: 2
- Learning Rate: 5e-6
- Cutoff Length: 512
- Temperature: 0.7
- Beta: 0.1
```

**预期显存**: 6-7GB (加载两个模型)
**预期训练时间**: 1-2小时

---

## 📊 对比表格

| 配置 | 模型 | 方式 | 显存 | 稳定性 | 推荐指数 |
|------|------|------|------|--------|---------|
| 1 | 0.5B | LoRA | 3-4GB | ⭐⭐⭐⭐⭐ | 🎓 学习用 |
| 2 | 1.5B | LoRA | 5-6GB | ⭐⭐⭐⭐ | ⭐ 最佳 |
| 3 | 7B | QLoRA | 7-8GB | ⭐⭐⭐ | 💪 挑战 |
| 4 | 0.5B | DPO | 6-7GB | ⭐⭐⭐ | 🧪 实验 |

---

## ⚡ 显存优化技巧

### 如果显存不足 (OOM):

1. **降低 Batch Size**
   ```
   8 → 4 → 2 → 1
   ```

2. **减小 Cutoff Length**
   ```
   512 → 256 → 128 (仅用于应急)
   ```

3. **增加 Gradient Accumulation**
   ```
   1 → 2 → 4 (补偿batch大小)
   ```

4. **启用 Gradient Checkpointing**
   ```
   在 WebUI 中勾选此选项
   可减少约30%显存占用
   ```

5. **降低精度**
   ```
   FP32 → FP16 (节省50%显存)
   FP16 → INT8 (需要特殊库支持)
   ```

### 如果训练太慢:

1. **提高 Batch Size** (在显存允许范围内)
2. **启用 Flash Attention** (如果支持)
3. **降低 Warmup Ratio**
4. **减少 Epochs** (仅在必要时)

---

## 📈 训练监控指标

| 指标 | 正常范围 | 说明 |
|------|---------|------|
| Loss | 逐步下降 | 应该稳定递减 |
| Learning Rate | 动态调整 | 需要预热和衰减 |
| GPU Util | 80-95% | 充分利用显卡 |
| Batch/s | 0.5-2 | 取决于模型和配置 |

---

## 🔧 常见配置问题

### Q: 应该选择多大的 Learning Rate?

**推荐值:**
- 全参数微调: 1e-4 ~ 5e-5
- LoRA: 5e-5 ~ 1e-4
- QLoRA: 1e-4 ~ 2e-4
- DPO: 1e-6 ~ 5e-6

### Q: LoRA Rank 应该设多大?

**推荐值:**
- 小模型 (< 3B): 8 ~ 16
- 中等模型 (3B ~ 13B): 8 ~ 32
- 大模型 (> 13B): 32 ~ 64

### Q: Epochs 应该是多少?

**推荐值:**
- 数据充足 (> 10k samples): 1 ~ 3
- 数据较少 (1k ~ 10k): 3 ~ 5
- 数据很少 (< 1k): 5 ~ 10 (注意过拟合)

---

## 💾 模型保存建议

**推荐方式:**
1. 训练完成后，使用 "导出" 功能
2. 选择 "Merged" 格式并保存
3. 保存到 `/app/output` (映射到宿主机 `./output`)

**文件结构:**
```
output/
├── model_merged/
│   ├── config.json
│   ├── pytorch_model.bin
│   ├── tokenizer.json
│   └── ...
├── lora_weights/
│   ├── adapter_config.json
│   ├── adapter_model.bin
│   └── ...
```

---

## 🎓 逐步优化建议

**第一周: 稳定性优先**
- 使用配置1 (0.5B)
- 小数据集测试 (100-1000条)
- 确保整个流程跑通

**第二周: 质量提升**
- 切换到配置2 (1.5B)
- 使用更大的数据集 (5000-10000条)
- 调整超参数

**第三周: 能力扩展**
- 尝试配置3 (7B QLoRA)
- 准备更高质量的数据
- 尝试多个 checkpoint 对比

**第四周: 进阶方法**
- 尝试配置4 (DPO)
- 实现多阶段训练
- 性能优化和模型合并

---

**最后更新**: 2025年11月
**基于**: LLaMA-Factory 官方文档
**硬件**: RTX 4060 (8GB VRAM)
