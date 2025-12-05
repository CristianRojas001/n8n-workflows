import markdown
from weasyprint import HTML, CSS
from pathlib import Path

# Read the markdown file
md_file = r"d:\IT workspace\infosubvenciones-api\info\Propuesta Técnica_ Sistema Inteligente de Consulta de Subvenciones.md"
pdf_file = r"d:\IT workspace\infosubvenciones-api\info\Propuesta Técnica_ Sistema Inteligente de Consulta de Subvenciones.pdf"

with open(md_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert markdown to HTML
html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'nl2br'])

# Create a complete HTML document with styling
html_document = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @page {{
            size: A4;
            margin: 2.5cm;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 11pt;
        }}
        h1 {{
            font-size: 24pt;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 20px;
        }}
        h2 {{
            font-size: 18pt;
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 18px;
        }}
        h3 {{
            font-size: 14pt;
            color: #34495e;
            margin-top: 14px;
        }}
        h4 {{
            font-size: 12pt;
            color: #34495e;
            margin-top: 12px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            font-size: 10pt;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 10px;
            text-align: left;
            border: 1px solid #2980b9;
        }}
        td {{
            padding: 8px;
            border: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 12px;
            border-left: 4px solid #3498db;
            overflow-x: auto;
            font-size: 9pt;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 20px 0;
        }}
        strong {{
            color: #2c3e50;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 15px 0;
            padding-left: 15px;
            color: #555;
            font-style: italic;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

# Convert HTML to PDF
HTML(string=html_document).write_pdf(pdf_file)
print(f"PDF created successfully: {pdf_file}")