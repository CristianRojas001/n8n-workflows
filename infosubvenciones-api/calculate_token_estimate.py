"""
Token estimation script for PDF processing pipeline.

This script calculates:
1. Average token count from sample PDFs
2. Estimated tokens for generating 250-word summaries
3. Estimated tokens for embedding generation
4. Total cost projection for processing 143,000 PDFs
"""

import os
import json
import tiktoken
from pathlib import Path
from typing import List, Dict, Tuple
import PyPDF2
from statistics import mean, median, stdev
import pandas as pd
from datetime import datetime

# Initialize tokenizer (using GPT-4 encoding as standard)
encoding = tiktoken.get_encoding("cl100k_base")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text content from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def count_tokens(text: str) -> int:
    """Count tokens in a text string."""
    return len(encoding.encode(text))

def analyze_pdfs(pdf_directory: str, sample_size: int = None) -> Dict:
    """
    Analyze PDFs in directory and calculate token statistics.

    Args:
        pdf_directory: Path to directory containing PDFs
        sample_size: Number of PDFs to sample (None = all PDFs)

    Returns:
        Dictionary with statistics
    """
    pdf_files = list(Path(pdf_directory).glob("*.pdf"))

    if sample_size and sample_size < len(pdf_files):
        import random
        pdf_files = random.sample(pdf_files, sample_size)

    print(f"Analyzing {len(pdf_files)} PDFs...")

    token_counts = []
    char_counts = []
    page_counts = []

    for i, pdf_path in enumerate(pdf_files, 1):
        if i % 10 == 0:
            print(f"  Processed {i}/{len(pdf_files)} PDFs...")

        text = extract_text_from_pdf(str(pdf_path))
        tokens = count_tokens(text)

        # Get page count
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pages = len(pdf_reader.pages)
        except:
            pages = 0

        token_counts.append(tokens)
        char_counts.append(len(text))
        page_counts.append(pages)

    # Calculate statistics
    stats = {
        'total_pdfs_analyzed': len(pdf_files),
        'token_stats': {
            'mean': mean(token_counts),
            'median': median(token_counts),
            'min': min(token_counts),
            'max': max(token_counts),
            'stdev': stdev(token_counts) if len(token_counts) > 1 else 0
        },
        'char_stats': {
            'mean': mean(char_counts),
            'median': median(char_counts),
        },
        'page_stats': {
            'mean': mean(page_counts),
            'median': median(page_counts),
        },
        'individual_counts': token_counts
    }

    return stats

def estimate_summary_tokens(input_tokens: int, output_words: int = 250) -> Dict:
    """
    Estimate tokens needed for summary generation.

    Args:
        input_tokens: Average input tokens per PDF
        output_words: Target summary length in words

    Returns:
        Dictionary with token estimates
    """
    # Rough estimate: 1 word ≈ 1.3 tokens for English
    output_tokens = int(output_words * 1.3)

    return {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_per_pdf': input_tokens + output_tokens
    }

def estimate_embedding_tokens(summary_words: int = 250) -> int:
    """
    Estimate tokens for embedding generation.

    Args:
        summary_words: Summary length in words

    Returns:
        Estimated token count
    """
    # Embeddings use input tokens only
    return int(summary_words * 1.3)

def calculate_total_costs(
    avg_tokens_per_pdf: int,
    total_pdfs: int = 143000,
    summary_words: int = 250
) -> Dict:
    """
    Calculate total token requirements for the full pipeline.

    Pipeline steps:
    1. Read PDF and generate summary (input + output tokens)
    2. Generate embedding from summary (input tokens only)

    Args:
        avg_tokens_per_pdf: Average tokens per PDF
        total_pdfs: Total number of PDFs to process
        summary_words: Target summary length

    Returns:
        Dictionary with cost breakdown for multiple models
    """
    # Step 1: Summary generation
    summary_est = estimate_summary_tokens(avg_tokens_per_pdf, summary_words)

    # Step 2: Embedding generation (using summary)
    embedding_tokens = estimate_embedding_tokens(summary_words)

    # Total tokens per PDF
    tokens_per_pdf = {
        'summary_input': summary_est['input_tokens'],
        'summary_output': summary_est['output_tokens'],
        'embedding_input': embedding_tokens,
        'total': summary_est['total_per_pdf'] + embedding_tokens
    }

    # Scale to full dataset
    total_tokens = {
        'summary_input_tokens': tokens_per_pdf['summary_input'] * total_pdfs,
        'summary_output_tokens': tokens_per_pdf['summary_output'] * total_pdfs,
        'embedding_input_tokens': tokens_per_pdf['embedding_input'] * total_pdfs,
        'total_tokens': tokens_per_pdf['total'] * total_pdfs
    }

    # Pricing for multiple models (as of 2025)
    # NOTE: Free tiers excluded - unsuitable for processing 143,000 PDFs at scale
    models = {
        'gpt4o': {
            'input_per_1m': 5.0,
            'output_per_1m': 15.0,
            'embedding_per_1m': 0.02,  # text-embedding-3-small
            'embedding_name': 'text-embedding-3-small',
            'embedding_dimensions': 1536,
            'name': 'GPT-4o + OpenAI Embed'
        },
        'gpt4o_mini': {
            'input_per_1m': 0.15,
            'output_per_1m': 0.60,
            'embedding_per_1m': 0.02,  # text-embedding-3-small (1536d)
            'embedding_name': 'text-embedding-3-small (1536d)',
            'embedding_dimensions': 1536,
            'name': 'GPT-4o-mini + OpenAI Embed (1536d)'
        },
        'gpt4o_mini_256d': {
            'input_per_1m': 0.15,
            'output_per_1m': 0.60,
            'embedding_per_1m': 0.02,  # Same cost, just returns fewer dimensions
            'embedding_name': 'text-embedding-3-small (256d)',
            'embedding_dimensions': 256,
            'name': 'GPT-4o-mini + OpenAI Embed (256d)',
            'note': 'Same API cost as 1536d, but smaller vectors (better for storage/search speed)'
        },
        'gemini_flash_lite_openai': {
            'input_per_1m': 0.10,
            'output_per_1m': 0.40,
            'embedding_per_1m': 0.02,  # text-embedding-3-small
            'embedding_name': 'text-embedding-3-small (1536d)',
            'embedding_dimensions': 1536,
            'name': 'Gemini Flash-Lite + OpenAI Embed (1536d)'
        },
        'gemini_flash_lite_openai_256d': {
            'input_per_1m': 0.10,
            'output_per_1m': 0.40,
            'embedding_per_1m': 0.02,  # Same cost
            'embedding_name': 'text-embedding-3-small (256d)',
            'embedding_dimensions': 256,
            'name': 'Gemini Flash-Lite + OpenAI Embed (256d)'
        },
        'gemini_flash_lite_gemini': {
            'input_per_1m': 0.10,
            'output_per_1m': 0.40,
            'embedding_per_1m': 0.15,  # gemini-embedding-001 paid tier
            'embedding_name': 'gemini-embedding-001',
            'embedding_dimensions': 768,
            'name': 'Gemini Flash-Lite + Gemini Embed'
        }
    }

    # Calculate costs for each model
    model_costs = {}
    for model_key, pricing in models.items():
        cost = {
            'summary_generation': (
                (total_tokens['summary_input_tokens'] / 1_000_000 * pricing['input_per_1m']) +
                (total_tokens['summary_output_tokens'] / 1_000_000 * pricing['output_per_1m'])
            ),
            'embedding_generation': (
                total_tokens['embedding_input_tokens'] / 1_000_000 * pricing['embedding_per_1m']
            )
        }
        cost['total'] = cost['summary_generation'] + cost['embedding_generation']
        model_costs[model_key] = {
            'name': pricing['name'],
            'costs': cost,
            'pricing': {k: v for k, v in pricing.items() if k not in ['name']},
            'embedding_info': {
                'model': pricing.get('embedding_name', 'N/A'),
                'dimensions': pricing.get('embedding_dimensions', 'N/A')
            }
        }

    return {
        'tokens_per_pdf': tokens_per_pdf,
        'total_tokens': total_tokens,
        'model_costs': model_costs,
        'total_pdfs': total_pdfs
    }

def export_to_excel(stats: Dict, projections: Dict, total_pdfs: int, summary_words: int, filename: str):
    """
    Export results to Excel with multiple sheets.

    Args:
        stats: PDF analysis statistics
        projections: Token and cost projections
        total_pdfs: Total number of PDFs
        summary_words: Summary length in words
        filename: Output Excel filename
    """
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Sheet 1: Summary
        summary_data = {
            'Metric': [
                'Total PDFs to Process',
                'Summary Length (words)',
                'Sample Size Analyzed',
                'Avg Tokens per PDF',
                'Median Tokens per PDF',
                'Min Tokens',
                'Max Tokens',
                'Std Deviation',
                'Avg Pages per PDF'
            ],
            'Value': [
                f"{total_pdfs:,}",
                f"{summary_words}",
                f"{stats['total_pdfs_analyzed']}",
                f"{stats['token_stats']['mean']:.0f}",
                f"{stats['token_stats']['median']:.0f}",
                f"{stats['token_stats']['min']:.0f}",
                f"{stats['token_stats']['max']:.0f}",
                f"{stats['token_stats']['stdev']:.0f}",
                f"{stats['page_stats']['mean']:.1f}"
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)

        # Sheet 2: Token Breakdown per PDF
        tokens_per_pdf = projections['tokens_per_pdf']
        token_data = {
            'Component': [
                'Summary Input (PDF Content)',
                'Summary Output (250 words)',
                'Embedding Input (Summary)',
                'Total per PDF'
            ],
            'Tokens': [
                tokens_per_pdf['summary_input'],
                tokens_per_pdf['summary_output'],
                tokens_per_pdf['embedding_input'],
                tokens_per_pdf['total']
            ]
        }
        df_tokens = pd.DataFrame(token_data)
        df_tokens.to_excel(writer, sheet_name='Tokens per PDF', index=False)

        # Sheet 3: Total Token Requirements
        total_tokens = projections['total_tokens']
        total_token_data = {
            'Component': [
                'Summary Input Tokens',
                'Summary Output Tokens',
                'Embedding Input Tokens',
                'GRAND TOTAL'
            ],
            'Total Tokens': [
                total_tokens['summary_input_tokens'],
                total_tokens['summary_output_tokens'],
                total_tokens['embedding_input_tokens'],
                total_tokens['total_tokens']
            ],
            'Formatted': [
                f"{total_tokens['summary_input_tokens']:,}",
                f"{total_tokens['summary_output_tokens']:,}",
                f"{total_tokens['embedding_input_tokens']:,}",
                f"{total_tokens['total_tokens']:,}"
            ]
        }
        df_total_tokens = pd.DataFrame(total_token_data)
        df_total_tokens.to_excel(writer, sheet_name='Total Tokens', index=False)

        # Sheet 4: Cost Comparison by Model
        cost_comparison = []
        for model_key, model_data in projections['model_costs'].items():
            cost_comparison.append({
                'Model': model_data['name'],
                'Summary Cost': f"${model_data['costs']['summary_generation']:,.2f}",
                'Embedding Cost': f"${model_data['costs']['embedding_generation']:,.2f}",
                'TOTAL COST': f"${model_data['costs']['total']:,.2f}",
                'Embedding Model': model_data['embedding_info']['model'],
                'Embedding Dims': model_data['embedding_info']['dimensions'],
                'Total Cost (numeric)': model_data['costs']['total']
            })
        df_costs = pd.DataFrame(cost_comparison)
        df_costs = df_costs.sort_values('Total Cost (numeric)')
        df_costs = df_costs.drop('Total Cost (numeric)', axis=1)
        df_costs.to_excel(writer, sheet_name='Cost Comparison', index=False)

        # Sheet 5: Detailed Cost Breakdown
        detailed_costs = []
        for model_key, model_data in projections['model_costs'].items():
            detailed_costs.append({
                'Model': model_data['name'],
                'Component': 'Summary Generation',
                'Cost (USD)': model_data['costs']['summary_generation']
            })
            detailed_costs.append({
                'Model': model_data['name'],
                'Component': 'Embedding Generation',
                'Cost (USD)': model_data['costs']['embedding_generation']
            })
            detailed_costs.append({
                'Model': model_data['name'],
                'Component': 'TOTAL',
                'Cost (USD)': model_data['costs']['total']
            })
        df_detailed = pd.DataFrame(detailed_costs)
        pivot_table = df_detailed.pivot(index='Component', columns='Model', values='Cost (USD)')
        pivot_table.to_excel(writer, sheet_name='Detailed Breakdown')

        # Sheet 6: Cost Savings Analysis
        gpt4o_cost = projections['model_costs']['gpt4o']['costs']['total']
        savings_data = []
        for model_key, model_data in projections['model_costs'].items():
            if model_key != 'gpt4o':
                cost = model_data['costs']['total']
                savings = gpt4o_cost - cost
                savings_pct = (savings / gpt4o_cost) * 100
                savings_data.append({
                    'Alternative Model': model_data['name'],
                    'Cost': f"${cost:,.2f}",
                    'Savings vs GPT-4o': f"${savings:,.2f}",
                    'Savings Percentage': f"{savings_pct:.1f}%"
                })
        if savings_data:
            df_savings = pd.DataFrame(savings_data)
            df_savings.to_excel(writer, sheet_name='Savings Analysis', index=False)

    print(f"\nExcel file created with {6 if savings_data else 5} sheets:")
    print("  1. Summary - Overall metrics")
    print("  2. Tokens per PDF - Token breakdown")
    print("  3. Total Tokens - Total requirements")
    print("  4. Cost Comparison - Model costs")
    print("  5. Detailed Breakdown - Cost matrix")
    print("  6. Savings Analysis - Cost savings vs GPT-4o")

def main():
    """Main execution function."""
    # Configuration
    PDF_DIRECTORY = r"D:\IT workspace\infosubvenciones-api\relevant_pdfs"
    SAMPLE_SIZE = None  # Set to None to analyze all PDFs, or a number for sampling
    TOTAL_PDFS = 143000
    SUMMARY_WORDS = 250

    print("=" * 70)
    print("PDF TOKEN ESTIMATION TOOL")
    print("=" * 70)
    print()

    # Analyze sample PDFs
    print(f"Step 1: Analyzing PDFs in {PDF_DIRECTORY}")
    print("-" * 70)
    stats = analyze_pdfs(PDF_DIRECTORY, SAMPLE_SIZE)

    print()
    print("PDF ANALYSIS RESULTS:")
    print(f"  Total PDFs analyzed: {stats['total_pdfs_analyzed']}")
    print(f"  Average tokens per PDF: {stats['token_stats']['mean']:.0f}")
    print(f"  Median tokens per PDF: {stats['token_stats']['median']:.0f}")
    print(f"  Min tokens: {stats['token_stats']['min']:.0f}")
    print(f"  Max tokens: {stats['token_stats']['max']:.0f}")
    print(f"  Standard deviation: {stats['token_stats']['stdev']:.0f}")
    print(f"  Average pages: {stats['page_stats']['mean']:.1f}")
    print()

    # Calculate projections
    print(f"Step 2: Calculating projections for {TOTAL_PDFS:,} PDFs")
    print("-" * 70)
    avg_tokens = int(stats['token_stats']['mean'])
    projections = calculate_total_costs(avg_tokens, TOTAL_PDFS, SUMMARY_WORDS)

    print()
    print("TOKENS PER PDF BREAKDOWN:")
    print(f"  Summary input (PDF content): {projections['tokens_per_pdf']['summary_input']:,} tokens")
    print(f"  Summary output ({SUMMARY_WORDS} words): {projections['tokens_per_pdf']['summary_output']:,} tokens")
    print(f"  Embedding input (summary): {projections['tokens_per_pdf']['embedding_input']:,} tokens")
    print(f"  TOTAL per PDF: {projections['tokens_per_pdf']['total']:,} tokens")
    print()

    print("TOTAL TOKEN REQUIREMENTS FOR 143,000 PDFs:")
    print(f"  Summary input tokens: {projections['total_tokens']['summary_input_tokens']:,}")
    print(f"  Summary output tokens: {projections['total_tokens']['summary_output_tokens']:,}")
    print(f"  Embedding input tokens: {projections['total_tokens']['embedding_input_tokens']:,}")
    print(f"  GRAND TOTAL: {projections['total_tokens']['total_tokens']:,} tokens")
    print()

    print("ESTIMATED COSTS BY MODEL (USD):")
    print("=" * 70)
    for model_key, model_data in projections['model_costs'].items():
        print(f"\n{model_data['name']}:")
        print(f"  Summary generation: ${model_data['costs']['summary_generation']:,.2f}")
        print(f"  Embedding generation: ${model_data['costs']['embedding_generation']:,.2f}")
        print(f"  TOTAL COST: ${model_data['costs']['total']:,.2f}")
        print(f"  Embedding: {model_data['embedding_info']['model']} ({model_data['embedding_info']['dimensions']}d)")
    print()

    # Save results to JSON
    output_file = "token_estimation_results.json"
    results = {
        'sample_analysis': stats,
        'projections': projections,
        'config': {
            'pdf_directory': PDF_DIRECTORY,
            'sample_size': SAMPLE_SIZE,
            'total_pdfs': TOTAL_PDFS,
            'summary_words': SUMMARY_WORDS
        },
        'generated_at': datetime.now().isoformat()
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_file}")

    # Export to Excel
    excel_file = "token_estimation_results.xlsx"
    export_to_excel(stats, projections, TOTAL_PDFS, SUMMARY_WORDS, excel_file)
    print(f"Excel report saved to: {excel_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
