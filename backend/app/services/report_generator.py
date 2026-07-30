import io
import uuid
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.spider import SpiderChart
from reportlab.graphics.charts.barcharts import HorizontalBarChart

from app.models.models import Task

class ReportGenerator:
    """Generates a highly detailed PDF Manuscript Proof Report using ReportLab."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def generate_pdf(self, task_id: uuid.UUID) -> bytes:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=50, leftMargin=50,
                                topMargin=50, bottomMargin=50)
                                
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            name='CoverTitle',
            parent=styles['Heading1'],
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor("#1e3a8a") 
        )
        
        subtitle_style = ParagraphStyle(
            name='CoverSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=40,
            textColor=colors.HexColor("#475569") 
        )
        
        heading1_style = ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading1'],
            fontSize=18,
            spaceBefore=25,
            spaceAfter=15,
            textColor=colors.HexColor("#0f172a"),
            borderPadding=8,
            backColor=colors.HexColor("#e2e8f0"),
            borderWidth=1,
            borderColor=colors.HexColor("#cbd5e1"),
            borderRadius=4
        )
        
        heading2_style = ParagraphStyle(
            name='SubHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor("#2563eb")
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
        elements.append(Spacer(1, 100))
        elements.append(Paragraph("JournaBuddy", title_style))
        elements.append(Paragraph("Manuscript Intelligence & Evaluation Certificate", title_style))
        
        elements.append(Spacer(1, 50))
        
        # Extract some overall stats for the cover
        agents = payload.get("agents", {})
        scores = []
        if agents:
            for k, v in agents.items():
                if isinstance(v, dict) and v.get("status") != "degraded":
                    for subk, subv in v.items():
                        if "score" in subk and isinstance(subv, (int, float)):
                            scores.append(subv)
                            
        overall_score = round(sum(scores)/len(scores), 1) if scores else "N/A"
        
        # Big Cover Box for Overall Score
        score_data = [[Paragraph(f"<font size=16><b>Overall AI Score</b></font><br/><font size=40 color='#059669'>{overall_score}</font><font size=20 color='#64748b'>/10</font>", ParagraphStyle('C', alignment=TA_CENTER))]]
        score_table = Table(score_data, colWidths=[300], rowHeights=[100])
        score_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 2, colors.HexColor("#34d399")),
            # Removed ROUNDEDCORNERS to ensure PDF compatibility
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 60))
        
        elements.append(Paragraph(f"<b>Original File:</b> {task.filename}", subtitle_style))
        elements.append(Paragraph(f"<b>Evaluation ID:</b> {task_id}", subtitle_style))
        date_str = datetime.datetime.now().strftime("%B %d, %Y - %H:%M UTC")
        elements.append(Paragraph(f"<b>Generated On:</b> {date_str}", subtitle_style))
        
        elements.append(PageBreak())
        
        # ==========================================
        # SECTION 1: LINGUISTIC & SYMBOLIC INTEGRITY
        # ==========================================
        elements.append(Paragraph("1. Linguistic & Symbolic Integrity", heading1_style))
        symbolic = payload.get("symbolic_check", {})
        
        if symbolic:
            elements.append(Paragraph("<b>Statistical Metrics:</b>", heading2_style))
            lexical_density = symbolic.get('lexical_density', 'N/A')
            shannon_entropy = symbolic.get('shannon_entropy', 'N/A')
            passive = symbolic.get('passive_voice_percent', 'N/A')
            
            metric_data = [
                ["Metric", "Score", "Target Range"],
                ["Lexical Density (TTR)", f"{lexical_density}%", "40% - 60%"],
                ["Shannon Entropy", f"{shannon_entropy} bits", "7.0 - 9.0 (High Info Density)"],
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
        
        if agents:
            # Gather scores for the radar chart
            axes = []
            values = []
            
            agent_map = {
                "language_compliance": ("Tone & Formality", "tone_score"),
                "research_rigor": ("Methodology Rigor", "methodology_score"),
                "reviewer_domain_specialist": ("Novelty", "novelty_score"),
                "reviewer_style_editor": ("Academic Style", "style_score"),
                "document_intelligence": ("Abstract Quality", "abstract_quality_score")
            }
            
            for k, v in agents.items():
                if isinstance(v, dict) and v.get("status") != "degraded" and k in agent_map:
                    label, score_key = agent_map[k]
                    if score_key in v and isinstance(v[score_key], (int, float)):
                        axes.append(label)
                        values.append(v[score_key])
                        
            if len(axes) >= 3:
                elements.append(Spacer(1, 10))
                d = Drawing(400, 250)
                spider = SpiderChart()
                spider.x = 100
                spider.y = 25
                spider.width = 200
                spider.height = 200
                spider.data = [values]
                spider.labels = axes
                spider.strands[0].fillColor = colors.HexColor("#8b5cf6")
                spider.strands[0].strokeColor = colors.HexColor("#7c3aed")
                spider.strands[0].strokeWidth = 2
                
                # Make the background web gray
                spider.spokes.strokeColor = colors.HexColor("#cbd5e1")
                spider.spokes.strokeWidth = 1
                
                # Setup min/max
                spider.spokes.labelRadius = 1.25
                for i in range(len(axes)):
                    spider.spokes[i].labelRadius = 1.15
                
                d.add(spider)
                elements.append(d)
                elements.append(Spacer(1, 20))
                
            for agent_name, result in agents.items():
                title = agent_name.replace('_', ' ').title()
                elements.append(Paragraph(title, heading2_style))
                
                if result.get("status") == "degraded":
                    elements.append(Paragraph("<i>Note: The LLM provider was unavailable. Results are degraded.</i>", body_style))
                    continue
                
                agent_content = []
                for key, val in result.items():
                    if key in ("status", "agent", "reason"):
                        continue
                    
                    clean_key = key.replace('_', ' ').title()
                    
                    if isinstance(val, list):
                        agent_content.append(Paragraph(f"<b>{clean_key}:</b>", body_style))
                        for item in val:
                            agent_content.append(Paragraph(f"• {str(item)}", bullet_style))
                    else:
                        agent_content.append(Paragraph(f"<b>{clean_key}:</b> {str(val)}", body_style))
                        
                # Wrap the agent feedback in a nice colored box
                agent_table = Table([[cell] for cell in agent_content], colWidths=[480])
                agent_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94a3b8")),
                    ('LEFTPADDING', (0,0), (-1,-1), 15),
                    ('RIGHTPADDING', (0,0), (-1,-1), 15),
                    ('TOPPADDING', (0,0), (-1,-1), 10),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ]))
                
                elements.append(agent_table)
                elements.append(Spacer(1, 15))
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
            # Draw Horizontal Bar Chart
            d = Drawing(400, 200)
            bc = HorizontalBarChart()
            bc.x = 50
            bc.y = 50
            bc.height = 125
            bc.width = 300
            
            # The data for the chart [ [val1, val2, val3] ]
            comp_vals = [float(j.get('compatibility_percent', 0)) for j in reversed(journals[:5])]
            labels = [j.get("title", "Unknown")[:30] + "..." for j in reversed(journals[:5])]
            
            bc.data = [comp_vals]
            bc.categoryAxis.categoryNames = labels
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = 100
            bc.valueAxis.valueStep = 20
            
            # Style it
            bc.bars[0].fillColor = colors.HexColor("#ec4899")
            bc.bars[0].strokeWidth = 0
            
            d.add(bc)
            elements.append(d)
            elements.append(Spacer(1, 20))
            
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
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#be185d")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 10),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#fdf2f8")),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#fbcfe8"))
            ]))
            elements.append(t3)
        else:
            elements.append(Paragraph("No journal matches found.", body_style))
            
        doc.build(elements)
        return buffer.getvalue()
