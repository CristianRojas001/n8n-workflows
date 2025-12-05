import json
import pandas as pd
from calculate_token_estimate import export_to_excel

# Load the results
with open('token_estimation_results.json', 'r') as f:
    results = json.load(f)

# Export to Excel
excel_file = "token_estimation_results_NEW.xlsx"
export_to_excel(
    results['sample_analysis'],
    results['projections'],
    results['config']['total_pdfs'],
    results['config']['summary_words'],
    excel_file
)

print(f"Excel file created successfully: {excel_file}")
