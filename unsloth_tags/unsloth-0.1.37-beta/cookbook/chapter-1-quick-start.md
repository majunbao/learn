# Chapter 1: Quick Start & Architecture Overview

This chapter gets you fine-tuning in 5 minutes, then shows you the full architecture so you know where to dive deeper in later chapters.

## How to Read This Chapter

**Pass 1 — Build intuition (~15 min):** Read 1.1 → 1.2 → 1.3 in order. Skip source code walkthroughs. Focus on the minimal example and the architecture diagram.

**Pass 2 — Understand the flow (~20 min):** Read the 🔥 Source Code Walkthrough in 1.2 to see how the four steps connect internally.

**Pass 3 — Go deeper:** Pick your next chapter based on what interests you:
- Import patching & compatibility? → Chapter 2
- Model loading parameters & quantization? → Chapter 3
- Triton kernel internals? → Chapters 4-6
- Training system? → Chapter 9
- Data preparation? → Chapter 11
- Saving & export? → Chapter 12

---

## 1.1 The Simplest Fine-Tune

Four steps. That's all it takes:

```python
from unsloth import FastLanguageModel
from datasets import load_dataset

# Step 1: Load a model with 4-bit quantization
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.2-1B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,
)

# Step 2: Configure LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
)

# Step 3: Train
dataset = load_dataset("yahma/alpaca-cleaned", split="train")
from trl import SFTTrainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=2048,
)
trainer.train()

# Step 4: Save
model.save_pretrained("my_lora_model")
tokenizer.save_pretrained("my_lora_model")
```

Load → LoRA → Train → Save. But what actually happened? When you wrote `import unsloth`, the framework had already patched 20+ things in your runtime. When you called `from_pretrained()`, it auto-detected your GPU, resolved model names, and loaded with custom kernels. When you called `trainer.train()`, it used fused Triton kernels for the forward and backward pass.

## 1.2 The Four Steps Under the Hood

Before we read source code, let's build intuition with a picture:

```
  import unsloth
         │
         ▼
  ┌─ Step 0: Import-Time Patching ──────────────────────────┐
  │  (20+ patches fire before any model is loaded)          │
  │  • Fix trl/transformers/peft known bugs                 │
  │  • Disable broken causal_conv1d, vLLM                   │
  │  • Detect device (CUDA/ROCm/XPU/MPS)                    │
  │  → See Chapter 2 for full details                       │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  from_pretrained()
         │
         ▼
  ┌─ Step 1: Model Loading ─────────────────────────────────┐
  │  • Resolve model name via Mapper (4-bit → 16-bit)       │
  │  • Auto-detect model_type → dispatch to FastXxxModel    │
  │  • Load with BitsAndBytesConfig (4-bit NF4)             │
  │  • Patch attention, layernorm, MLP with Triton kernels  │
  │  • Apply gradient checkpointing ("unsloth" mode)        │
  │  • Fix RoPE inv_freq (transformers v5 bug)              │
  │  → See Chapter 3 for full details                       │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  get_peft_model()
         │
         ▼
  ┌─ Step 2: LoRA Configuration ────────────────────────────┐
  │  • Create LoraConfig with target_modules                │
  │  • Apply LoRA A, B matrices to each target layer        │
  │  • Freeze base weights (requires_grad=False)            │
  │  • Trainable params: ~0.5% of total (42M / 8B)         │
  │  → See Chapter 3 §3.4 for parameter deep dive           │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  trainer.train()
         │
         ▼
  ┌─ Step 3: Training with Fused Kernels ───────────────────┐
  │  Forward pass (per layer):                               │
  │  • Fused RMS LayerNorm (1 kernel vs 3 ops)              │
  │  • Fused RoPE (Q+K rotation, 1 kernel)                  │
  │  • Fused LoRA_MLP (dequant + LoRA + SwiGLU, 1 kernel)  │
  │  • Fused Cross-Entropy (no materialized logits)         │
  │  Backward pass:                                          │
  │  • Fused LoRA backward (analytical gradients)           │
  │  • Fused RMS LayerNorm backward                         │
  │  → See Chapters 4-6 for kernel source code              │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  save_pretrained() / save_pretrained_gguf()
         │
         ▼
  ┌─ Step 4: Saving & Export ───────────────────────────────┐
  │  • "lora": Save only adapters (~100MB)                  │
  │  • "merged_16bit": Merge LoRA + save full model (~16GB) │
  │  • GGUF: Merge → convert → quantize (q4_k_m, q8_0...)  │
  │  • Ollama: GGUF + auto-generated Modelfile              │
  │  • HF Hub: push_to_hub_merged / push_to_hub_gguf        │
  │  → See Chapter 12 for full details                      │
  └──────────────────────────────────────────────────────────┘
```

The key insight: **each step is optimized at a different level**. Import patching fixes bugs before they happen. Model loading auto-selects the best quantization and patches slow operations with fast kernels. Training replaces every PyTorch operation in the critical path with a fused Triton kernel. Saving provides one-click export to every major deployment format.

## 1.3 Full Architecture Overview

Here's how all Unsloth components connect:

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                        User Code                                    │
  │  from unsloth import FastLanguageModel                              │
  │  model, tokenizer = FastLanguageModel.from_pretrained(...)          │
  │  model = FastLanguageModel.get_peft_model(...)                      │
  │  trainer = UnslothTrainer(...)                                      │
  │  trainer.train()                                                    │
  │  model.save_pretrained_gguf(...)                                    │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
  │  unsloth/     │    │  unsloth/kernels │    │  unsloth/save    │
  │  __init__.py  │    │                  │    │                  │
  │  (Patching)   │    │  cross_entropy   │    │  _merge_lora()   │
  │               │    │  rms_layernorm   │    │  unsloth_save()  │
  │  import_fixes │    │  rope_embedding  │    │  save_to_gguf()  │
  │  device_type  │    │  fast_lora       │    │  ollama_export   │
  │  trl/peft/    │    │  swiglu/geglu    │    │  HF Hub push     │
  │  transformers │    │  flex_attention  │    └──────────────────┘
  │  patches      │    │  fp8             │              Ch.12
  │               │    │  moe/            │
  │     Ch.2      │    │  utils.py        │
  └──────┬───────┘    └────────┬─────────┘
         │                     │
         │              Ch.4-6
         │                     │
         ▼                     ▼
  ┌──────────────┐    ┌──────────────────┐
  │  unsloth/     │    │  unsloth/models  │
  │  trainer.py   │    │                  │
  │               │    │  loader.py       │ ← from_pretrained dispatcher
  │  Unsloth      │    │  llama.py        │ ← FastLlamaModel
  │  Trainer      │    │  mistral.py      │ ← FastMistralModel
  │  Unsloth      │    │  gemma.py/2.py   │ ← FastGemmaModel/2
  │  Training     │    │  qwen2/3.py      │ ← FastQwen2/3Model
  │  Arguments    │    │  vision.py       │ ← FastBaseModel (VLMs)
  │  Q-GaLore     │    │  mapper.py       │ ← Model name redirection
  │  Auto Packing │    │  _utils.py       │ ← Shared model utilities
  │               │    │  rl.py           │ ← RL training patches
  │    Ch.9       │    │  dpo.py          │ ← DPO/KTO patches
  └──────┬───────┘    └────────┬─────────┘
         │                     │
         │              Ch.3,7,8,10
         │                     │
         └──────────┬──────────┘
                    ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                    External Dependencies                      │
  │  transformers  │  peft  │  trl  │  bitsandbytes  │  triton  │
  │  (patched)     │(patched│(patched│  (patched)     │(kernels) │
  └──────────────────────────────────────────────────────────────┘
                    │
                    ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                     unsloth_zoo                               │
  │  Shared utilities: device_type, loss_utils, gradient_ckpt,   │
  │  peft_utils, vision_utils, compiler, training_utils,         │
  │  hf_utils, vllm_utils, llama_cpp, dataset_utils              │
  └──────────────────────────────────────────────────────────────┘
```

### Module → Chapter Mapping

| Module | Purpose | Chapter |
|--------|---------|---------|
| `unsloth/__init__.py` | Import-time patching, env setup | Chapter 2 |
| `unsloth/import_fixes.py` | 20+ compatibility patches | Chapter 2 |
| `unsloth/device_type.py` | GPU detection (CUDA/ROCm/XPU/MPS) | Chapter 2 |
| `unsloth/models/loader.py` | `from_pretrained()` dispatcher | Chapter 3 |
| `unsloth/models/mapper.py` | Model name redirection (4-bit↔16-bit) | Chapter 3, 13 |
| `unsloth/models/llama.py` | FastLlamaModel implementation | Chapter 7 |
| `unsloth/models/vision.py` | VLM loading (FastBaseModel) | Chapter 8 |
| `unsloth/kernels/cross_entropy_loss.py` | Fused cross-entropy kernel | Chapter 4 |
| `unsloth/kernels/rms_layernorm.py` | Fused RMS layernorm kernel | Chapter 4 |
| `unsloth/kernels/rope_embedding.py` | Fused RoPE kernel | Chapter 5 |
| `unsloth/kernels/flex_attention.py` | Flex Attention + softcapping | Chapter 5 |
| `unsloth/kernels/fast_lora.py` | Fused LoRA_MLP forward/backward | Chapter 6 |
| `unsloth/kernels/swiglu.py` | Fused SwiGLU activation | Chapter 6 |
| `unsloth/kernels/geglu.py` | Fused GeGLU activation | Chapter 6 |
| `unsloth/kernels/fp8.py` | FP8 quantization patches | Chapter 13 |
| `unsloth/kernels/moe/` | MoE grouped GEMM kernels | Chapter 8 |
| `unsloth/trainer.py` | UnslothTrainer, Q-GaLore, packing | Chapter 9 |
| `unsloth/optimizers/` | Q-GaLore AdamW optimizer | Chapter 9 |
| `unsloth/models/rl.py` | RL training patches | Chapter 10 |
| `unsloth/chat_templates.py` | 7 chat template formats | Chapter 11 |
| `unsloth/dataprep/` | RawTextDataLoader, SyntheticDataKit | Chapter 11 |
| `unsloth/save.py` | LoRA merge, GGUF, Ollama, HF Hub | Chapter 12 |
| `unsloth/registry/` | Model registry, ModelInfo, QuantType | Chapter 13 |
| `unsloth_cli/` | CLI commands (train/export/infer) | Chapter 14 |

### Key Design Principle

The architecture reveals Unsloth's core design: **it's a thin but deep optimization layer**. It doesn't replace `transformers`, `peft`, or `trl` — it sits on top and replaces only the performance-critical parts with custom Triton kernels. Everything else (tokenization, model definition, training loop, LoRA application) is delegated to the original libraries, just with patches applied at import time.

```
  Your code
      │
      ▼
  ┌─ Unsloth optimizations ──────────────────────────┐
  │  • Triton kernels replace slow PyTorch ops        │
  │  • Import patches fix bugs before they happen     │
  │  • Smart gradient checkpointing saves VRAM        │
  │  • Auto packing/padding-free eliminates waste     │
  └───────────────────────────────────────────────────┘
      │
      ▼
  ┌─ Original libraries (patched) ────────────────────┐
  │  • transformers: model definition, tokenization    │
  │  • peft: LoRA application, adapter management      │
  │  • trl: SFTTrainer, training loop                  │
  │  • bitsandbytes: 4-bit quantization                │
  └───────────────────────────────────────────────────┘
```

## 1.4 A Complete End-to-End Example

Here's a complete fine-tuning script that uses every major Unsloth feature:

```python
import unsloth
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template, train_on_responses_only
from unsloth import UnslothTrainer, UnslothTrainingArguments
from datasets import load_dataset
import torch

# ── Step 1: Load model with 4-bit quantization ──
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.1-8B-Instruct-unsloth-bnb-4bit",
    max_seq_length=4096,
    load_in_4bit=True,
    dtype=None,
    use_gradient_checkpointing="unsloth",
)

# ── Step 2: Configure LoRA ──
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    use_rslora=False,
    loftq_config=None,
)

# ── Step 3: Apply chat template ──
tokenizer = get_chat_template(tokenizer, chat_template="llama3")

# ── Step 4: Prepare dataset ──
def formatting_prompts_func(examples):
    convos = examples["conversations"]
    texts = [
        tokenizer.apply_chat_template(
            convo, tokenize=False, add_generation_prompt=False
        )
        for convo in convos
    ]
    return {"text": texts}

dataset = load_dataset("openchat/openchat_sharegpt4_dataset", split="train")
dataset = dataset.map(formatting_prompts_func, batched=True)

# ── Step 5: Train ──
trainer = UnslothTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=4096,
    args=UnslothTrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=100,
        learning_rate=2e-4,
        embedding_learning_rate=5e-5,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        output_dir="outputs",
        seed=3407,
        report_to="none",
    ),
)

trainer = train_on_responses_only(
    trainer,
    instruction_part="<|start_header_id|>user<|end_header_id|>\n\n",
    response_part="<|start_header_id|>assistant<|end_header_id|>\n\n",
)
trainer.train()

# ── Step 6: Save in multiple formats ──
model.save_pretrained("my_lora_model")
tokenizer.save_pretrained("my_lora_model")

model.save_pretrained_merged("my_merged_model", tokenizer, save_method="merged_16bit")

model.save_pretrained_gguf("my_gguf_model", tokenizer, quantization_method="q4_k_m")

model.push_to_hub_merged("username/my-model", tokenizer, save_method="merged_16bit")
model.push_to_hub_gguf("username/my-model", tokenizer, quantization_method="q4_k_m")
```

### What Happens When You Run This

| Step | What Happens Internally | VRAM Impact |
|------|------------------------|-------------|
| `import unsloth` | ~20 patches applied to trl/transformers/peft/torch | 0 GB |
| `from_pretrained()` | Load 4-bit model, patch attention/layernorm/MLP/RoPE, fix tokenizer | ~5 GB |
| `get_peft_model()` | Add LoRA adapters (A, B matrices) to target modules | +0.5 GB |
| `get_chat_template()` | Replace tokenizer's chat template | 0 GB |
| `UnslothTrainer()` | Auto-detect padding-free / packing, configure optimizer | 0 GB |
| `trainer.train()` | Forward: fused LoRA_MLP + RMS layernorm + RoPE; Backward: fused LoRA backward + cross_entropy | ~8 GB peak |
| `save_pretrained()` | Save LoRA adapters (A, B, scaling) | 0 GB |
| `save_pretrained_merged()` | Merge LoRA: dequantize W + add s*A@B → save full model | ~16 GB temp |
| `save_pretrained_gguf()` | Merge → convert to GGUF → quantize with llama.cpp | Disk I/O |

### Post-Training Inspection

```python
# Check trainable vs total parameters
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"Trainable: {trainable:,} / {total:,} = {100*trainable/total:.2f}%")
# → Trainable: 41,943,936 / 8,030,261,248 = 0.52%

# Check LoRA config
print(model.peft_config)
# → {'default': LoraConfig(r=16, lora_alpha=16, target_modules=['q_proj', ...])}

# Check training loss curve
import pandas as pd
log_df = pd.DataFrame(trainer.state.log_history)
print(log_df[["step", "loss", "learning_rate"]].tail(10))
```

## 1.5 What's Next?

Now that you've seen the full picture, here's where to go deeper:

| Want to Understand... | Go To |
|----------------------|-------|
| Why `import unsloth` must come first | Chapter 2 |
| How `from_pretrained()` auto-selects quantization and dispatches to the right model class | Chapter 3 |
| How Triton kernels replace PyTorch operations to achieve 2x speedup | Chapters 4, 5, 6 |
| How each model architecture (Llama, Gemma, Qwen) is optimized differently | Chapter 7 |
| How to fine-tune vision models or MoE models | Chapter 8 |
| How UnslothTrainer, Q-GaLore, and auto packing work | Chapter 9 |
| How to do RL/PPO/DPO training with Unsloth | Chapter 10 |
| How to prepare data (chat templates, synthetic data, raw text) | Chapter 11 |
| How saving, GGUF export, and Ollama integration work | Chapter 12 |
| How the model registry and FP8 quantization work | Chapter 13 |
| How to use the CLI and Studio | Chapter 14 |
