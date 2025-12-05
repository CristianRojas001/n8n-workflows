import markdown
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from bs4 import BeautifulSoup
import re

# Read the markdown file
md_file = r"d:\IT workspace\infosubvenciones-api\info\Propuesta Técnica_ Sistema Inteligente de Consulta de Subvenciones.md"
pdf_file = r"d:\IT workspace\infosubvenciones-api\info\Propuesta Técnica_ Sistema Inteligente de Consulta de Subvenciones.pdf"

with open(md_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert markdown to HTML
html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

# Parse HTML with BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Create PDF
doc = SimpleDocTemplate(pdf_file, pagesize=A4,
                        rightMargin=72, leftMargin=72,
                        topMargin=72, bottomMargin=18)

# Container for the 'Flowable' objects
elements = []

# Define styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Heading1Custom',
                          parent=styles['Heading1'],
                          fontSize=18,
                          textColor=colors.HexColor('#2c3e50'),
                          spaceAfter=12,
                          spaceBefore=12))

styles.add(ParagraphStyle(name='Heading2Custom',
                          parent=styles['Heading2'],
                          fontSize=14,
                          textColor=colors.HexColor('#34495e'),
                          spaceAfter=10,
                          spaceBefore=10))

styles.add(ParagraphStyle(name='Heading3Custom',
                          parent=styles['Heading3'],
                          fontSize=12,
                          textColor=colors.HexColor('#34495e'),
                          spaceAfter=8,
                          spaceBefore=8))

styles.add(ParagraphStyle(name='CodeBlock',
                          parent=styles['Code'],
                          fontSize=8,
                          leftIndent=20,
                          backgroundColor=colors.HexColor('#f4f4f4')))

# Process each element
for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'table', 'pre', 'hr']):
    if element.name == 'h1':
        elements.append(Paragraph(element.get_text(), styles['Heading1Custom']))
        elements.append(Spacer(1, 0.2*inch))
    elif element.name == 'h2':
        elements.append(Paragraph(element.get_text(), styles['Heading2Custom']))
        elements.append(Spacer(1, 0.15*inch))
    elif element.name == 'h3':
        elements.append(Paragraph(element.get_text(), styles['Heading3Custom']))
        elements.append(Spacer(1, 0.1*inch))
    elif element.name == 'h4':
        elements.append(Paragraph(element.get_text(), styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
    elif element.name == 'p':
        text = str(element).replace('<p>', '').replace('</p>', '')
        text = text.replace('<strong>', '<b>').replace('</strong>', '</b>')
        text = text.replace('<em>', '<i>').replace('</em>', '</i>')
        elements.append(Paragraph(text, styles['BodyText']))
        elements.append(Spacer(1, 0.1*inch))
    elif element.name in ['ul', 'ol']:
        for li in element.find_all('li', recursive=False):
            li_text = li.get_text()
            bullet = '•' if element.name == 'ul' else f"{element.find_all('li').index(li) + 1}."
            elements.append(Paragraph(f"{bullet} {li_text}", styles['BodyText']))
            elements.append(Spacer(1, 0.05*inch))
    elif element.name == 'table':
        # Extract table data
        rows = []
        for tr in element.find_all('tr'):
            cells = [td.get_text().strip() for td in tr.find_all(['th', 'td'])]
            rows.append(cells)

        if rows:
            # Create table
            t = Table(rows)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(t)
            elements.append(Spacer(1, 0.2*inch))
    elif element.name == 'pre':
        code_text = element.get_text()
        for line in code_text.split('\n'):
            if line.strip():
                elements.append(Paragraph(line, styles['CodeBlock']))
        elements.append(Spacer(1, 0.1*inch))
    elif element.name == 'hr':
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph('_' * 100, styles['BodyText']))
        elements.append(Spacer(1, 0.1*inch))

# Build PDF
try:
    doc.build(elements)
    print(f"PDF created successfully: {pdf_file}")
except Exception as e:
    print(f"Error creating PDF: {e}")
