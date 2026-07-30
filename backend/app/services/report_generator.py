import io
import uuid
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.models.models import Task

class ReportGenerator:
    """Generates a PDF Manuscript Proof Report using ReportLab."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def generate_pdf(self, task_id: uuid.UUID) -> bytes:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
                                
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CenterTitle', alignment=1, fontSize=18, spaceAfter=20))
        styles.add(ParagraphStyle(name='Heading2', fontSize=14, spaceAfter=10, textColor=colors.HexColor("#2c3e50")))
        
        elements = []
        
        # Title
        elements.append(Paragraph("JournaBuddy Manuscript Evaluation Certificate", styles['CenterTitle']))
        elements.append(Paragraph(f"Task ID: {task_id}", styles['Normal']))
        elements.append(Paragraph(f"Filename: {task.original_filename}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        payload = task.dashboard_payload or {}
        
        # 1. Symbolic Checks
        elements.append(Paragraph("1. Symbolic Rule Checks", styles['Heading2']))
        symbolic = payload.get("symbolic_check", {})
        if symbolic:
            elements.append(Paragraph(f"Flesch-Kincaid Grade: {symbolic.get('flesch_kincaid_grade', 'N/A')}", styles['Normal']))
            elements.append(Paragraph(f"Passive Voice: {symbolic.get('passive_voice_percent', 'N/A')}%", styles['Normal']))
            issues = symbolic.get("issues", [])
            if issues:
                elements.append(Paragraph("Issues Detected:", styles['Normal']))
                for issue in issues:
                    elements.append(Paragraph(f"• {issue}", styles['Normal']))
        else:
            elements.append(Paragraph("No symbolic data available.", styles['Normal']))
        elements.append(Spacer(1, 15))
        
        # 2. AI Peer Reviewers
        elements.append(Paragraph("2. AI Peer Reviewer Feedback", styles['Heading2']))
        agents = payload.get("agents", {})
        if agents:
            for agent_name, result in agents.items():
                elements.append(Paragraph(f"<b>{agent_name.replace('_', ' ').title()}</b>", styles['Normal']))
                # Dump a few key metrics
                for k, v in result.items():
                    if k not in ["status"]:
                        val_str = str(v)[:100] + ("..." if len(str(v)) > 100 else "")
                        elements.append(Paragraph(f"{k}: {val_str}", styles['Normal']))
                elements.append(Spacer(1, 10))
        else:
            elements.append(Paragraph("No AI review data available.", styles['Normal']))
        elements.append(Spacer(1, 15))
            
        # 3. Journal Matcher
        elements.append(Paragraph("3. Target Journal Scope Match", styles['Heading2']))
        journals = payload.get("journal_matches", [])
        if journals:
            data = [["Journal Title", "Compatibility", "Acceptance Likelihood"]]
            for j in journals:
                data.append([
                    j.get("title", "Unknown")[:40], 
                    f"{j.get('compatibility_percent', 0)}%", 
                    f"{j.get('acceptance_likelihood_percent', 0)}%"
                ])
                
            t = Table(data, colWidths=[250, 100, 120])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("No journal matches found.", styles['Normal']))
            
        doc.build(elements)
        return buffer.getvalue()
