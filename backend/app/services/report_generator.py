import io
import uuid
import datetime
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

from app.models.models import Task

class ReportGenerator:
    """Generates a highly detailed PDF Manuscript Proof Report using ReportLab."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def generate_pdf(self, task_id: uuid.UUID) -> bytes:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=50)
                                
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            name='CoverTitle',
            parent=styles['Heading1'],
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor("#1e3a8a") # Tailwind blue-900
        )
        
        subtitle_style = ParagraphStyle(
            name='CoverSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=40,
            textColor=colors.HexColor("#475569") # Tailwind slate-600
        )
        
        heading1_style = ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading1'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#0f172a"),
            borderPadding=5,
            backColor=colors.HexColor("#e2e8f0")
        )
        
        heading2_style = ParagraphStyle(
            name='SubHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=5,
            textColor=colors.HexColor("#3b82f6")
        )
        
        body_style = ParagraphStyle(
            name='BodyText',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )
        
        bullet_style = ParagraphStyle(
            name='BulletText',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            leftIndent=20,
            firstLineIndent=-10,
            spaceAfter=5
        )

        elements = []
        payload = task.dashboard_payload or {}
        
        # ==========================================
        # COVER PAGE
        # ==========================================
        elements.append(Spacer(1, 150))
        elements.append(Paragraph("JournaBuddy", title_style))
        elements.append(Paragraph("Manuscript Intelligence & Evaluation Certificate", title_style))
        
        elements.append(Spacer(1, 50))
        elements.append(Paragraph(f"<b>Original File:</b> {task.original_filename}", subtitle_style))
        elements.append(Paragraph(f"<b>Evaluation ID:</b> {task_id}", subtitle_style))
        
        date_str = datetime.datetime.now().strftime("%B %d, %Y - %H:%M UTC")
        elements.append(Paragraph(f"<b>Generated On:</b> {date_str}", subtitle_style))
        
        elements.append(Spacer(1, 100))
        elements.append(Paragraph("This document serves as an automated proof of review, encompassing symbolic, statistical, and AI-driven semantic analysis.", body_style))
        elements.append(PageBreak())
        
        # ==========================================
        # SECTION 1: LINGUISTIC & SYMBOLIC INTEGRITY
        # ==========================================
        elements.append(Paragraph("1. Linguistic & Symbolic Integrity", heading1_style))
        symbolic = payload.get("symbolic_check", {})
        
        if symbolic:
            elements.append(Paragraph("<b>Statistical Metrics:</b>", heading2_style))
            flesch = symbolic.get('flesch_reading_ease', 'N/A')
            flesch_grade = symbolic.get('flesch_kincaid_grade', 'N/A')
            passive = symbolic.get('passive_voice_percent', 'N/A')
            
            metric_data = [
                ["Metric", "Score", "Target Range"],
                ["Flesch Reading Ease", str(flesch), "30 - 50 (Academic)"],
                ["Flesch-Kincaid Grade", str(flesch_grade), "12 - 16"],
                ["Passive Voice Density", f"{passive}%", "< 25%"]
            ]
            
            t = Table(metric_data, colWidths=[200, 100, 150])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 10),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1"))
            ]))
            elements.append(t)
            elements.append(Spacer(1, 15))
            
            issues = symbolic.get("issues", [])
            elements.append(Paragraph("<b>Critical Rule Violations:</b>", heading2_style))
            if issues:
                for issue in issues:
                    elements.append(Paragraph(f"• {issue}", bullet_style))
            else:
                elements.append(Paragraph("No critical formatting or symbolic rule violations detected.", body_style))
        else:
            elements.append(Paragraph("No linguistic data available for this manuscript.", body_style))
            
        elements.append(Spacer(1, 20))
        
        # ==========================================
        # SECTION 2: REFERENCE VERIFICATION
        # ==========================================
        elements.append(Paragraph("2. Reference & Citation Verification", heading1_style))
        references = payload.get("reference_enrichment", [])
        
        if references:
            elements.append(Paragraph("The following Digital Object Identifiers (DOIs) were extracted and validated against Crossref and OpenAlex.", body_style))
            
            ref_data = [["DOI", "Title (Truncated)", "Valid?", "Citations"]]
            for ref in references:
                doi = ref.get("crossref", {}).get("doi", "N/A")
                title = ref.get("crossref", {}).get("title", "Unknown")[:40] + "..."
                is_valid = "Yes" if ref.get("crossref", {}).get("is_valid") else "No"
                citations = str(ref.get("openalex", {}).get("citation_count", 0))
                ref_data.append([doi, title, is_valid, citations])
                
            t2 = Table(ref_data, colWidths=[120, 220, 50, 60])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#059669")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#ecfdf5")),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#a7f3d0"))
            ]))
            elements.append(t2)
        else:
            elements.append(Paragraph("No extractable DOIs were found in the text.", body_style))

        elements.append(PageBreak())

        # ==========================================
        # SECTION 3: AI PEER REVIEW BOARD
        # ==========================================
        elements.append(Paragraph("3. AI Peer Reviewer Feedback", heading1_style))
        elements.append(Paragraph("This section contains qualitative analysis generated by specialized Large Language Model personas.", body_style))
        
        agents = payload.get("agents", {})
        if agents:
            for agent_name, result in agents.items():
                title = agent_name.replace('_', ' ').title()
                elements.append(Paragraph(title, heading2_style))
                
                if result.get("status") == "degraded":
                    elements.append(Paragraph("<i>Note: The LLM provider was unavailable. Results are degraded.</i>", body_style))
                    continue
                
                for key, val in result.items():
                    if key == "status":
                        continue
                    
                    clean_key = key.replace('_', ' ').title()
                    
                    if isinstance(val, list):
                        elements.append(Paragraph(f"<b>{clean_key}:</b>", body_style))
                        for item in val:
                            elements.append(Paragraph(f"• {str(item)}", bullet_style))
                    else:
                        elements.append(Paragraph(f"<b>{clean_key}:</b> {str(val)}", body_style))
                        
                elements.append(Spacer(1, 10))
        else:
            elements.append(Paragraph("No AI review data available.", body_style))

        elements.append(PageBreak())
        
        # ==========================================
        # SECTION 4: TARGET JOURNALS
        # ==========================================
        elements.append(Paragraph("4. Target Journal Scope Match", heading1_style))
        elements.append(Paragraph("Journals are ranked by semantic cosine distance between the manuscript's embeddings and the journal's published aims and scope.", body_style))
        
        journals = payload.get("journal_matches", [])
        if journals:
            j_data = [["Journal Title", "Compatibility", "Acceptance Likelihood", "Trust Score"]]
            for j in journals:
                j_data.append([
                    j.get("title", "Unknown")[:45] + "...", 
                    f"{j.get('compatibility_percent', 0)}%", 
                    f"{j.get('acceptance_likelihood_percent', 0)}%",
                    str(j.get('trust_score', 'N/A'))
                ])
                
            t3 = Table(j_data, colWidths=[220, 80, 100, 60])
            t3.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#7c3aed")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 10),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f5f3ff")),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#ddd6fe"))
            ]))
            elements.append(t3)
        else:
            elements.append(Paragraph("No journal matches found.", body_style))
            
        doc.build(elements)
        return buffer.getvalue()
