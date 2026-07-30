import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.report_generator import ReportGenerator

router = APIRouter()

@router.get("/report/{task_id}")
async def get_report(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Generate and return a PDF certificate evaluating the manuscript.
    """
    try:
        generator = ReportGenerator(db)
        pdf_bytes = await generator.generate_pdf(task_id)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=JournaBuddy_Report_{task_id}.pdf"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
