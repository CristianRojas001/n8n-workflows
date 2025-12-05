# Models Cost Comparison
## Processing 143,000 PDFs - Complete Pricing Breakdown

**Analysis Date**: January 24, 2025
**Sample Size**: 1,009 PDFs analyzed
**Average Tokens per PDF**: 8,852 tokens
**Summary Length**: 250 words (325 tokens)

---

## Quick Summary

| Rank | Model + Embedding | Total Cost | Cost/PDF | Summary Cost | Embedding Cost | Savings vs GPT-4o |
|------|------------------|------------|----------|--------------|----------------|-------------------|
| 🥇 **#1** | **Gemini Flash-Lite + OpenAI (1536d)** | **$146.09** | **$0.00102** | $145.16 | $0.93 | **97.9%** |
| 🥇 **#1** | **Gemini Flash-Lite + OpenAI (256d)** | **$146.09** | **$0.00102** | $145.16 | $0.93 | **97.9%** |
| 🥈 #2 | Gemini Flash-Lite + Gemini Embed | $152.13 | $0.00106 | $145.16 | $6.97 | 97.8% |
| 🥉 #3 | GPT-4o-mini + OpenAI (1536d) | $218.67 | $0.00153 | $217.74 | $0.93 | 96.9% |
| 🥉 #3 | GPT-4o-mini + OpenAI (256d) | $218.67 | $0.00153 | $217.74 | $0.93 | 96.9% |
| 4️⃣ | GPT-4o + OpenAI Embed | $7,026.53 | $0.04913 | $7,025.60 | $0.93 | - |

---

## Token Requirements

### Per PDF Average:
```
├── PDF Input (for summarization):    8,852 tokens
├── Summary Output (250 words):         325 tokens
├── Embedding Input (from summary):     325 tokens
└── TOTAL PER PDF:                    9,502 tokens
```

### Total for 143,000 PDFs:
```
├── Summary Input Tokens:    1,265,693,000  (1.27 billion)
├── Summary Output Tokens:      46,475,000  (46.5 million)
├── Embedding Input Tokens:     46,475,000  (46.5 million)
└── GRAND TOTAL:             1,358,643,000  (1.36 billion tokens)
```

---

## Detailed Cost Breakdown

### 1. Gemini 2.5 Flash-Lite + OpenAI text-embedding-3-small (1536d)

#### Pricing:
- **Summary Input**: $0.10 per 1M tokens
- **Summary Output**: $0.40 per 1M tokens
- **Embedding**: $0.02 per 1M tokens
- **Embedding Dimensions**: 1536

#### Calculation:
```
Summary Generation:
  Input:  1,265,693,000 ÷ 1,000,000 × $0.10 = $126.57
  Output:    46,475,000 ÷ 1,000,000 × $0.40 = $18.59
  Subtotal:                                    $145.16

Embedding Generation:
  Input:     46,475,000 ÷ 1,000,000 × $0.02 = $0.93

TOTAL COST:                                    $146.09
```

#### Best For:
- ✅ Lowest cost option
- ✅ Excellent summary quality
- ✅ Full-dimension embeddings (max precision)
- ✅ Production-ready rate limits

---

### 2. Gemini 2.5 Flash-Lite + OpenAI text-embedding-3-small (256d)

#### Pricing:
- **Summary Input**: $0.10 per 1M tokens
- **Summary Output**: $0.40 per 1M tokens
- **Embedding**: $0.02 per 1M tokens (same as 1536d)
- **Embedding Dimensions**: 256

#### Calculation:
```
Summary Generation:                            $145.16  (same)
Embedding Generation:                          $0.93    (same)
TOTAL COST:                                    $146.09
```

#### Best For:
- ✅ Same cost as 1536d option
- ✅ **6x smaller vectors** (1 KB vs 6 KB per embedding)
- ✅ **Faster search** performance
- ✅ **Lower storage costs** (143 MB vs 858 MB total)
- ✅ Ideal for large-scale deployments

#### Important Note:
**OpenAI charges the SAME price ($0.02/1M) regardless of dimensions!**
The dimension parameter only affects the vector size returned, not the API cost.

---

### 3. Gemini 2.5 Flash-Lite + Google Gemini Embedding

#### Pricing:
- **Summary Input**: $0.10 per 1M tokens
- **Summary Output**: $0.40 per 1M tokens
- **Embedding**: $0.15 per 1M tokens
- **Embedding Dimensions**: 768

#### Calculation:
```
Summary Generation:                            $145.16

Embedding Generation:
  Input:     46,475,000 ÷ 1,000,000 × $0.15 = $6.97

TOTAL COST:                                    $152.13
```

#### Best For:
- ✅ Single vendor (Google) - simpler billing
- ✅ 768 dimensions (middle ground)
- ⚠️ $6 more expensive than OpenAI embeddings

---

### 4. GPT-4o-mini + OpenAI text-embedding-3-small (1536d)

#### Pricing:
- **Summary Input**: $0.15 per 1M tokens
- **Summary Output**: $0.60 per 1M tokens
- **Embedding**: $0.02 per 1M tokens
- **Embedding Dimensions**: 1536

#### Calculation:
```
Summary Generation:
  Input:  1,265,693,000 ÷ 1,000,000 × $0.15 = $189.85
  Output:    46,475,000 ÷ 1,000,000 × $0.60 = $27.89
  Subtotal:                                    $217.74

Embedding Generation:                          $0.93

TOTAL COST:                                    $218.67
```

#### Best For:
- ✅ Single vendor (OpenAI)
- ✅ Better quality for complex documents vs Gemini
- ⚠️ 50% more expensive than Gemini Flash-Lite

---

### 5. GPT-4o-mini + OpenAI text-embedding-3-small (256d)

#### Pricing & Calculation:
```
Summary Generation:                            $217.74  (same)
Embedding Generation:                          $0.93    (same)
TOTAL COST:                                    $218.67
```

Same cost as 1536d option, but with smaller vectors for faster search.

---

### 6. GPT-4o + OpenAI text-embedding-3-small

#### Pricing:
- **Summary Input**: $5.00 per 1M tokens
- **Summary Output**: $15.00 per 1M tokens
- **Embedding**: $0.02 per 1M tokens
- **Embedding Dimensions**: 1536

#### Calculation:
```
Summary Generation:
  Input:  1,265,693,000 ÷ 1,000,000 × $5.00  = $6,328.47
  Output:    46,475,000 ÷ 1,000,000 × $15.00 = $697.13
  Subtotal:                                     $7,025.60

Embedding Generation:                           $0.93

TOTAL COST:                                     $7,026.53
```

#### Best For:
- ✅ Maximum quality summaries
- ✅ Complex technical documents
- ⚠️ **48x more expensive** than Gemini Flash-Lite

---

## Embedding Dimensions Comparison

### OpenAI text-embedding-3-small

| Dimensions | API Cost | Vector Size | Storage (143K) | Search Speed | Best Use Case |
|------------|----------|-------------|----------------|--------------|---------------|
| **1536** | $0.02/1M | 6 KB/vector | 858 MB | Standard | Maximum precision, default |
| **512** | $0.02/1M | 2 KB/vector | 286 MB | Fast | Balanced quality/speed |
| **256** | $0.02/1M | 1 KB/vector | 143 MB | Fastest | Large-scale, speed-critical |

**Key Insight**: All dimensions cost the **same $0.02 per 1M tokens** from the API!
Only difference is storage space and search performance.

### Google Gemini Embedding

| Model | Dimensions | API Cost | Vector Size |
|-------|------------|----------|-------------|
| gemini-embedding-001 | 768 | $0.15/1M | 3 KB/vector |

---

## Cost Savings Analysis

### vs GPT-4o (Baseline):

| Option | Cost | Savings | Savings % |
|--------|------|---------|-----------|
| Gemini + OpenAI (any dim) | $146.09 | $6,880.44 | **97.9%** |
| Gemini + Gemini Embed | $152.13 | $6,874.40 | **97.8%** |
| GPT-4o-mini + OpenAI | $218.67 | $6,807.86 | **96.9%** |

---

## Recommendations

### 🥇 **Best Overall: Gemini Flash-Lite + OpenAI (256d)**
**Total Cost**: $146.09
```
✅ Lowest cost
✅ Excellent quality
✅ 6x smaller storage
✅ Faster search
✅ Same API cost as 1536d
```

### 🥈 **Best for Quality: GPT-4o-mini + OpenAI (256d)**
**Total Cost**: $218.67 (+$73)
```
✅ Better for complex documents
✅ Single vendor (OpenAI)
✅ Still 97% cheaper than GPT-4o
```

### 🥉 **Best for Google Ecosystem: Gemini Flash-Lite + Gemini Embed**
**Total Cost**: $152.13 (+$6)
```
✅ Single vendor (Google)
✅ Simpler billing
✅ 768d vectors (middle ground)
```

---

## Important Notes

### ⚠️ Cost Variance
- Standard deviation: 10,442 tokens
- Expected range: **$124 - $168** (±15%)
- Large PDFs may exceed average

### ✅ Excluded from Analysis
- **Free tiers**: Unsuitable for 143,000 PDFs
  - Gemini free: 500 RPD = 286 days to complete
  - Not production-ready

### 💡 Optimization Tips
1. Start with 256d embeddings (same cost, better performance)
2. Test with 1,000 PDFs before full-scale processing
3. Consider batch processing for 50% API discount
4. Monitor actual costs vs estimates

---

## Calculation Methodology

### Step 1: PDF Analysis
- Analyzed 1,009 PDFs using PyPDF2
- Counted tokens using tiktoken (cl100k_base)
- Calculated mean: 8,852 tokens/PDF

### Step 2: Scaling
- Multiplied by 143,000 PDFs
- Added summary output (325 tokens)
- Added embedding input (325 tokens)

### Step 3: Cost Calculation
- Divided by 1,000,000 for per-token rate
- Applied model-specific pricing
- Summed all components

### ✅ All Calculations Verified
Every number has been double-checked and verified in [CALCULATION_VERIFICATION.md](CALCULATION_VERIFICATION.md)

---

**Last Updated**: January 24, 2025
**Based on**: 1,009 PDF sample analysis
**Pricing**: January 2025 rates
