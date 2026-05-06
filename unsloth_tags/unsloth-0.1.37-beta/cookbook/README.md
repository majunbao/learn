# Unsloth - Source Code Analysis & Cookbook

## 📖 Table of Contents

| Chapter | Title | Topic | Key Source Files | Status |
|---------|-------|-------|------------------|--------|
| 1 | Quick Start & Architecture Overview | 5 分钟跑通微调 + 全系统架构图 | `__init__.py`, `models/loader.py` | ✅ Complete |
| 2 | Import-Time Patching & Compatibility | `import unsloth` 背后的 20+ 补丁与设备检测 | `import_fixes.py`, `device_type.py` | ✅ Complete |
| 3 | Model Loading Deep Dive | `from_pretrained()` 全流程：量化、分发、Mapper、RoPE 修复 | `models/loader.py`, `models/mapper.py`, `models/loader_utils.py` | ✅ Complete |
| 4 | Triton Kernels — Loss & Normalization | 融合交叉熵、RMS LayerNorm、标准 LayerNorm | `kernels/cross_entropy_loss.py`, `kernels/rms_layernorm.py`, `kernels/layernorm.py` | 📝 Planned |
| 5 | Triton Kernels — Attention & Position Encoding | RoPE、Flex Attention、Softcapping | `kernels/rope_embedding.py`, `kernels/flex_attention.py`, `utils/attention_dispatch.py` | 📝 Planned |
| 6 | Triton Kernels — LoRA Fusion & Activation | 融合 LoRA 前向/反向、SwiGLU/GeGLU、快速反量化 | `kernels/fast_lora.py`, `kernels/swiglu.py`, `kernels/geglu.py`, `kernels/utils.py` | 📝 Planned |
| 7 | Model Architecture Support | Llama/Mistral/Gemma/Qwen/Granite 的 FastModel 实现 | `models/llama.py`, `models/mistral.py`, `models/gemma.py`, `models/gemma2.py`, `models/qwen2.py`, `models/qwen3.py` | 📝 Planned |
| 8 | Vision Language Models & Specialized Architectures | VLM 加载、MoE (Qwen3-MoE/GLM4)、Sentence Transformer | `models/vision.py`, `models/qwen3_moe.py`, `models/glm4_moe.py`, `models/sentence_transformer.py`, `kernels/moe/` | 📝 Planned |
| 9 | Training System | UnslothTrainer、Q-GaLore、Embedding LR、Auto Packing、梯度检查点 | `trainer.py`, `optimizers/q_galore_adamw.py`, `utils/packing.py` | 📝 Planned |
| 10 | RL & Preference Training | GRPO/PPO/DPO/KTO 的 Unsloth 补丁与 vLLM 集成 | `models/rl.py`, `models/rl_replacements.py`, `models/dpo.py` | 📝 Planned |
| 11 | Data Preparation | Chat 模板、RawTextDataLoader、SyntheticDataKit、train_on_responses_only | `chat_templates.py`, `dataprep/raw_text.py`, `dataprep/synthetic.py`, `ollama_template_mappers.py` | 📝 Planned |
| 12 | Saving & Export | LoRA 合并、GGUF 转换、Ollama 导出、HF Hub 推送 | `save.py`, `tokenizer_utils.py` | 📝 Planned |
| 13 | Model Registry & FP8 Quantization | 模型注册表、名称映射、FP8 在线/离线量化 | `registry/registry.py`, `registry/_*.py`, `kernels/fp8.py`, `models/loader_utils.py` | 📝 Planned |
| 14 | CLI & Studio Integration | unsloth-cli 命令行工具与 Unsloth Studio 后端 | `unsloth_cli/`, `studio/backend/` | 📝 Planned |
| A | Appendix | API 速查表、故障排查、版本兼容矩阵 | — | 📝 Planned |

## 📁 Files

- [README.md](README.md) - This file (目录 & 阅读指南)
- [chapter-1-quick-start.md](chapter-1-quick-start.md) - 快速上手 & 架构概览
- [chapter-2-import-patching.md](chapter-2-import-patching.md) - 导入时补丁与兼容性
- [chapter-3-model-loading.md](chapter-3-model-loading.md) - 模型加载深度剖析
- [chapter-4-kernels-loss-norm.md](chapter-4-kernels-loss-norm.md) - 内核：损失函数与归一化
- [chapter-5-kernels-attention-rope.md](chapter-5-kernels-attention-rope.md) - 内核：注意力与位置编码
- [chapter-6-kernels-lora-activation.md](chapter-6-kernels-lora-activation.md) - 内核：LoRA 融合与激活函数
- [chapter-7-model-architectures.md](chapter-7-model-architectures.md) - 模型架构支持
- [chapter-8-vision-moe-specialized.md](chapter-8-vision-moe-specialized.md) - 视觉模型、MoE 与特殊架构
- [chapter-9-training-system.md](chapter-9-training-system.md) - 训练系统
- [chapter-10-rl-preference.md](chapter-10-rl-preference.md) - 强化学习与偏好训练
- [chapter-11-data-preparation.md](chapter-11-data-preparation.md) - 数据准备
- [chapter-12-saving-export.md](chapter-12-saving-export.md) - 保存与导出
- [chapter-13-registry-fp8.md](chapter-13-registry-fp8.md) - 模型注册表与 FP8 量化
- [chapter-14-cli-studio.md](chapter-14-cli-studio.md) - CLI 与 Studio 集成
- [appendix.md](appendix.md) - 附录

## About This Book

This cookbook takes you deep into the source code of Unsloth — the framework that makes LLM fine-tuning 2x faster and uses 70% less memory. You'll not only learn how to *use* Unsloth but also understand *why* it's designed the way it is and *how* it works under the hood — from the custom Triton kernels that replace slow PyTorch operations, to the import-time patching system that modifies transformers/PEFT/TRL before they load.

## How to Read This Book

### 学习路线建议

**路线 A — 快速上手（只需跑通微调）：**
Chapter 1 → Chapter 3 (仅参数表) → Chapter 11 → Chapter 9 (仅示例) → Chapter 12

**路线 B — 深入理解加速原理：**
Chapter 1 → Chapter 2 → Chapter 4 → Chapter 5 → Chapter 6 → Chapter 3

**路线 C — 完整掌握全部源码：**
按 1-14 顺序阅读，每章包含 🔥 源码剖析

**路线 D — 贡献者入门：**
Chapter 1 → Chapter 2 → Chapter 7 → Chapter 13 → 对应你要修改的章节

### 阅读三遍法

**Pass 1 — 建立直觉：** 每章先读流程图、参数表、示例代码，跳过 🔥 源码剖析

**Pass 2 — 深入源码：** 回来读每章的 🔥 源码剖析（此时已理解大方向，代码容易读）

**Pass 3 — 查漏补缺：** 根据需要选读深潜子节

## Philosophy

- **Source Code First** - 每个解释都直接关联到 `unsloth/` 中的实际源码
- **Practical Examples** - 通过运行学习，不只是阅读
- **From Import to Export** - 全生命周期覆盖：`import unsloth` → load → LoRA → train → save → GGUF
- **Visual Learning** - ASCII 流程图和架构图解释复杂系统

## Who Should Read This?

- 想深入理解 Unsloth 如何实现加速的开发者
- 在消费级 GPU 上微调 LLM 并需要优化显存的工程师
- 对 Triton 内核、LoRA 融合、导入时补丁工作原理感兴趣的人
- 想在贡献代码前理解代码库的贡献者

## Chapter Summaries

### Chapter 1: Quick Start & Architecture Overview
5 分钟跑通一次完整的 LoRA 微调，然后通过全系统架构图理解 Unsloth 的模块组成和数据流。涵盖 `FastLanguageModel.from_pretrained()`、`get_peft_model()`、`UnslothTrainer` 的最小用法。

### Chapter 2: Import-Time Patching & Compatibility
当你写下 `import unsloth` 时，框架在后台执行了 20+ 个补丁：禁用有 bug 的 causal_conv1d、修复 vLLM 版本冲突、配置 AMD GPU 路径、修补 trl/transformers/peft 的已知问题。本章逐个分析每个补丁的原因和效果，并解释设备检测系统（CUDA/ROCm/XPU/MPS）。

### Chapter 3: Model Loading Deep Dive
`from_pretrained()` 是 Unsloth 的核心入口。本章深入每个参数（量化模式、设备映射、FP8、vLLM 推理）、模型名称解析（Mapper 系统）、架构分发（Llama→FastLlamaModel）、以及 Transformers v5 的 RoPE inv_freq 修复。

### Chapter 4: Triton Kernels — Loss & Normalization
Unsloth 速度的核心来源。本章剖析融合交叉熵损失（避免物化 logits 张量）、RMS LayerNorm（单次 kernel pass）、标准 LayerNorm 的 Triton 实现，并解释 `tl.constexpr`、数值稳定的 logsumexp、rsqrt 缓存等关键技术。

### Chapter 5: Triton Kernels — Attention & Position Encoding
RoPE 融合内核（支持打包索引、前向/反向）、Flex Attention 与 Softcapping（Gemma 2 的注意力机制）、注意力后端分发系统（SDPA/Flash/xformers/Flex Attention 四选一）。

### Chapter 6: Triton Kernels — LoRA Fusion & Activation
`LoRA_MLP` 自定义 autograd 函数如何融合 dequantize + LoRA matmul + SwiGLU/GeGLU 激活，实现前向和反向各只需一次 kernel launch。还覆盖 `fast_dequantize` 4-bit 反量化和 `matmul_lora` 融合计算。

### Chapter 7: Model Architecture Support
Unsloth 如何为不同架构（Llama、Mistral、Gemma/2、Qwen2/3、Granite、Cohere）实现各自的 FastModel。每种架构的注意力修补、MLP 替换、推理加速路径有何不同。

### Chapter 8: Vision Language Models & Specialized Architectures
VLM 加载流程（`FastBaseModel`、`AutoModelForVision2Seq`）、MoE 架构支持（Qwen3-MoE 的 grouped GEMM、GLM4 的 sigmoid router + shared expert）、Sentence Transformer 的 Embedding 模型微调与导出。

### Chapter 9: Training System
`UnslothTrainer` 与 `UnslothTrainingArguments` 的完整剖析：Q-GaLore 优化器（低秩投影 + INT8 权重量化）、独立的 embedding learning rate、自动 padding-free 检测、sample packing、梯度检查点策略（`unsloth` vs `unsloth_smart`）、`unsloth_train()` 版本兼容处理。

### Chapter 10: RL & Preference Training
Unsloth 对 GRPO/PPO 等 RL 训练和 DPO/KTO 偏好训练的补丁。vLLM 集成（在线采样）、`RL_REPLACEMENTS` 替换机制、`torch.compile` 优化选项、`GuidedDecodingParams` 兼容层。

### Chapter 11: Data Preparation
7 种 chat template 的对比与使用、`get_chat_template()` / `apply_chat_template()`、ShareGPT 格式标准化、`train_on_responses_only()` 损失掩码、`RawTextDataLoader` 原始文本加载、`SyntheticDataKit` 合成 QA 数据生成。

### Chapter 12: Saving & Export
LoRA 适配器保存、合并到 16-bit 模型（`_merge_lora()` 源码剖析：反量化 + `addmm_` + 无穷检查）、GGUF 转换 4 步流程（合并→转换→量化→Sentencepiece 保留）、18 种量化选项对比、Ollama Modelfile 自动生成、HF Hub 推送。

### Chapter 13: Model Registry & FP8 Quantization
`MODEL_REGISTRY` 全局注册表、`ModelInfo` / `ModelMeta` 数据类、`QuantType` 枚举、`_register_models()` 批量注册、名称 Mapper 三级映射（4-bit↔16-bit↔原始）。FP8 量化：`FP8Linear`/`FbgemmFP8Linear` 的 forward 补丁、row-wise vs block-wise 量化、离线量化工具 `_offline_quantize_to_fp8()`。

### Chapter 14: CLI & Studio Integration
`unsloth-cli` 命令行工具（train/export/inference/studio 子命令）、YAML/JSON 配置文件、Unsloth Studio 后端架构（FastAPI 路由、训练 Worker、推理 Worker、数据配方系统）。

### Appendix: API Quick Reference
`FastLanguageModel.from_pretrained()` 参数速查、`get_peft_model()` 参数速查、GGUF 量化方法速查、Chat 模板速查、故障排查指南、版本兼容矩阵（transformers/peft/trl/unsloth_zoo 最低版本要求）。
