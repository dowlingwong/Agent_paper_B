---
language:
- en
- multilingual
license: apache-2.0
base_model: Qwen/Qwen3.6-27B
tags:
- qwen3.6
- reasoning
- distillation
- claude-opus
- gguf
- llama-cpp
- ollama
- fine-tuned
pipeline_tag: text-generation
datasets:
- nohurry/Opus-4.6-Reasoning-3000x-filtered
- Roman1111111/claude-opus-4.6-10000x
- Jackrong/Qwen3.5-reasoning-700x
---

# Qwen3.6-27B — Claude Opus Reasoning Distilled · GGUF

<p align="center">
  <img src="https://img.shields.io/badge/Base%20Model-Qwen3.6--27B-blue?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Format-GGUF-red?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Distilled%20From-Claude%204.6%20Opus-purple?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-Apache%202.0-green?style=for-the-badge"/>
</p>

> GGUF quantized versions of [rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled](https://huggingface.co/rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled) for use with **llama.cpp, Ollama, LM Studio, and any GGUF-compatible runtime**.

> 🙏 This model was trained following the methodology by [Jackrong](https://huggingface.co/Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled), adapted for Qwen3.6-27B.

---

## 🎯 What Is This?

Qwen3.6-27B fine-tuned on ~14k Claude 4.6 Opus reasoning traces. The model adopts a structured, efficient thinking style — concise on simple tasks, deep on hard ones — while fully preserving the base model's exceptional coding and math capabilities.

**Key improvement over base Qwen3.6-27B:** reduced verbose reasoning loops, replaced with Claude-style structured step-by-step decomposition.

**Base model benchmark:**

![Benchmark Results](qwen3.6_27b_score.png)

---

## 📦 Available Quantizations

Choose based on your available VRAM/RAM:

| File | Size | Min VRAM | Quality | Recommended For |
|---|---|---|---|---|
| `Q2_K` | ~10GB | 12GB | ⭐⭐ | Very limited hardware |
| `Q3_K_M` | ~13GB | 16GB | ⭐⭐⭐ | Budget setups |
| `Q4_K_S` | ~16GB | 20GB | ⭐⭐⭐⭐ | Good balance |
| `Q4_K_M` | 16.5GB | 20GB | ⭐⭐⭐⭐ ✅ **Best choice** | Most users |
| `Q5_K_S` | ~19GB | 24GB | ⭐⭐⭐⭐⭐ | High quality |
| `Q5_K_M` | ~20GB | 24GB | ⭐⭐⭐⭐⭐ | High quality |
| `Q6_K` | ~23GB | 28GB | ⭐⭐⭐⭐⭐ | Near-lossless |
| `Q8_0` | 28.6GB | 36GB | ⭐⭐⭐⭐⭐ | Maximum quality |

> **Q4_K_M is recommended** for most users — best quality-to-size ratio, runs on a 24GB GPU with headroom.

---

## 🚀 Quick Start

### llama.cpp

```bash
# Download
huggingface-cli download rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled-GGUF \
  --include "*Q4_K_M*" --local-dir ./model

# Run CLI
./llama-cli \
  -m ./model/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled-Q4_K_M.gguf \
  --temp 0.6 \
  --top-p 0.95 \
  --top-k 20 \
  --presence-penalty 1.5 \
  --ctx-size 8192 \
  -p "Implement a red-black tree in Python with insert and delete."

# Run as server (OpenAI-compatible API)
./llama-server \
  -m ./model/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled-Q4_K_M.gguf \
  --temp 0.6 \
  --top-p 0.95 \
  --top-k 20 \
  --ctx-size 8192 \
  --port 8080
```

### Ollama

```bash
# Create Modelfile
cat > Modelfile << 'EOF'
FROM rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled-GGUF:Q4_K_M
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER num_ctx 8192
EOF

ollama create qwen36-opus -f Modelfile
ollama run qwen36-opus
```

### LM Studio

Search for `rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled-GGUF` in the model browser and download your preferred quantization.

### OpenAI-compatible API (llama-server)

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8080/v1", api_key="none")

response = client.chat.completions.create(
    model="qwen3.6-27b-opus",
    messages=[{"role": "user", "content": "Write a merge sort implementation in Python."}],
    max_tokens=4096,
    temperature=0.6,
    top_p=0.95,
)
print(response.choices[0].message.content)
```

---

## ⚙️ Recommended Sampling Parameters

| Mode | temperature | top_p | top_k | presence_penalty |
|---|---|---|---|---|
| Thinking (general) | 1.0 | 0.95 | 20 | 0.0 |
| Thinking (coding) | 0.6 | 0.95 | 20 | 0.0 |
| Non-thinking | 0.7 | 0.80 | 20 | 1.5 |

---

## 🧠 Example Output Style

The model always reasons before answering:

```
<think>
Let me analyze this request carefully:

1. Identify the core objective...
2. Break the task into subcomponents...
3. Evaluate constraints and edge cases...
4. Formulate a step-by-step solution...
</think>

[Final Answer]
```

---

## 📊 Base Model Performance

| Benchmark | **Qwen3.6-27B** | Claude 4.5 Opus | Qwen3.5-397B |
|---|---|---|---|
| SWE-bench Verified | **77.2** | 80.9 | 76.2 |
| SWE-bench Pro | **53.5** | 57.1 | 50.9 |
| Terminal-Bench 2.0 | **59.3** | 59.3 | 52.5 |
| AIME 2026 | **94.1** | 95.1 | 93.3 |
| GPQA Diamond | **87.8** | 87.0 | 88.4 |
| MMLU-Pro | **86.2** | 89.5 | 87.8 |

*Source: [Qwen3.6-27B official release](https://qwen.ai/blog?id=qwen3.6-27b)*

---

## 📖 Citation

```bibtex
@misc{rico03-qwen36-opus-reasoning,
  title  = {Qwen3.6-27B Claude Opus Reasoning Distilled},
  author = {rico03},
  year   = {2026},
  url    = {https://huggingface.co/rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled}
}
```

---

## 🙏 Acknowledgements

- [Jackrong](https://huggingface.co/Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled) — pipeline guide
- [Unsloth](https://github.com/unslothai/unsloth) — GGUF export tooling
- [Qwen Team](https://github.com/QwenLM) — Apache 2.0 base model

---

*Released for research and personal use.*