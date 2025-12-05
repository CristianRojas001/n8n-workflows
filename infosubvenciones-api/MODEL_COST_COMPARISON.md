# Model Cost Comparison for 143,000 PDFs

## Quick Summary

| Model | Total Cost | Savings vs GPT-4o | Cost per PDF |
|-------|-----------|-------------------|--------------|
| **Gemini 2.5 Flash-Lite** | **$121.06** | **$5,654.21 (97.9%)** | **$0.00085** |
| GPT-4o-mini | $181.13 | $5,594.14 (96.9%) | $0.00127 |
| GPT-4o | $5,775.27 | - | $0.04039 |

## 🎯 Recommendation: Gemini 2.5 Flash-Lite

**Gemini 2.5 Flash-Lite is the most cost-effective option at $121.06 total**

### Why Gemini 2.5 Flash-Lite?

1. **Lowest cost**: $121.06 (vs $181 for GPT-4o-mini, $5,775 for GPT-4o)
2. **97.9% savings** compared to GPT-4o
3. **33% cheaper** than GPT-4o-mini
4. **Good quality**: Optimized for speed and cost-effectiveness
5. **Free tier available**: Up to 15 RPM free

## Detailed Breakdown

### Gemini 2.5 Flash-Lite
- **Input pricing**: $0.10 per 1M tokens
- **Output pricing**: $0.40 per 1M tokens
- **Summary generation**: $120.13
  - Input: 1.015B tokens × $0.10/1M = $101.54
  - Output: 46.5M tokens × $0.40/1M = $18.59
- **Embedding generation**: $0.93
- **Total**: **$121.06**

### GPT-4o-mini
- **Input pricing**: $0.15 per 1M tokens
- **Output pricing**: $0.60 per 1M tokens
- **Summary generation**: $180.20
  - Input: 1.015B tokens × $0.15/1M = $152.32
  - Output: 46.5M tokens × $0.60/1M = $27.89
- **Embedding generation**: $0.93
- **Total**: **$181.13**

### GPT-4o
- **Input pricing**: $5.00 per 1M tokens
- **Output pricing**: $15.00 per 1M tokens
- **Summary generation**: $5,774.34
  - Input: 1.015B tokens × $5.00/1M = $5,077.22
  - Output: 46.5M tokens × $15.00/1M = $697.13
- **Embedding generation**: $0.93
- **Total**: **$5,775.27**

## Token Requirements (All Models)

### Per PDF
- Summary input (PDF content): **7,101 tokens**
- Summary output (250 words): **325 tokens**
- Embedding input (summary): **325 tokens**
- **Total per PDF: 7,751 tokens**

### Total for 143,000 PDFs
- Summary input tokens: **1,015,443,000** (~1.02 billion)
- Summary output tokens: **46,475,000** (~46.5 million)
- Embedding input tokens: **46,475,000** (~46.5 million)
- **GRAND TOTAL: 1,108,393,000 tokens** (~1.11 billion)

## Additional Cost Optimization Options

### 1. Use Gemini 2.5 Flash-Lite Free Tier
- **Free tier**: Up to 500 RPD (requests per day)
- **Paid tier**: 1,500 RPD free, then $35/1,000 grounded prompts
- If you can process 500 PDFs/day, it would take 286 days but be completely free

### 2. Batch Processing (50% discount)
- Some providers offer batch API with 50% discount
- Estimated with batch: **~$60.53** for Gemini equivalent

### 3. Reduce Summary Length
- Current: 250 words → 325 tokens
- If you reduce to 150 words → 195 tokens
- Savings: ~20% on output tokens

### 4. Pre-filtering
- Skip processing duplicates or non-relevant PDFs
- Every 1% of PDFs skipped = ~$1.21 saved

## Implementation Considerations

### Gemini 2.5 Flash-Lite
- ✅ Lowest cost
- ✅ Good for high-volume processing
- ✅ Fast response times
- ⚠️ Quality may be slightly lower than GPT-4o for complex documents
- ⚠️ Need Google Cloud account

### GPT-4o-mini
- ✅ Good balance of cost and quality
- ✅ Easy to use (OpenAI API)
- ✅ Better than Gemini for complex reasoning
- ⚠️ 50% more expensive than Gemini Flash-Lite

### GPT-4o
- ✅ Highest quality summaries
- ✅ Best for complex documents
- ⚠️ 48x more expensive than Gemini
- ⚠️ 32x more expensive than GPT-4o-mini

## Final Recommendation

**Start with Gemini 2.5 Flash-Lite** for the bulk of your processing:
1. Test with 100-500 PDFs first to validate quality
2. Use the free tier if possible (500/day)
3. Switch to paid tier only if needed
4. Consider GPT-4o-mini as fallback for complex documents

**Expected total cost: $121.06** (or free if using free tier over time)

---

*Analysis based on 36 sample PDFs from `relevant_pdfs` directory*
*Prices as of January 2025*
