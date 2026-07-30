import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.models import Journal

async def seed_journals():
    async with AsyncSessionLocal() as db:
        # Create some dummy journals with mock 384-d embeddings
        journals = [
            Journal(
                issn="1234-5678",
                title="Journal of Academic Research",
                publisher="Science Group",
                is_doaj_indexed=True,
                trust_score=9.5,
                scope_embedding_json=[0.1] * 384
            ),
            Journal(
                issn="8765-4321",
                title="International Journal of Computing",
                publisher="Tech Press",
                is_doaj_indexed=True,
                trust_score=8.8,
                scope_embedding_json=[0.2] * 384
            ),
            Journal(
                issn="1111-2222",
                title="Medical Informatics Quarterly",
                publisher="Health Docs",
                is_doaj_indexed=False,
                trust_score=4.2,
                scope_embedding_json=[0.3] * 384
            )
        ]
        db.add_all(journals)
        await db.commit()
        print("Successfully seeded 3 mock journals into the database.")

if __name__ == "__main__":
    asyncio.run(seed_journals())
