import logging
from fastapi import FastAPI
from routers import alerts, features, ingest, entity, monitoring, rules, score, health
from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(title="AML Service")
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # or ["*"] for quick testing (not for prod)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],   # include OPTIONS
    allow_headers=["*"],             # allow Authorization, Content-Type, etc.
    expose_headers=["*"],
)

app.include_router(health.router, prefix="")
app.include_router(ingest.router, prefix="")
app.include_router(features.router, prefix="")
app.include_router(rules.router, prefix="")
app.include_router(score.router, prefix="")
app.include_router(alerts.router, prefix="")
app.include_router(entity.router, prefix="")
app.include_router(monitoring.router, prefix="")

@app.get("/summary")
async def get_summary():

    return {
        "summary": {
            "totalTransactions": 146,
            "highRisk": 9,
            "mediumRisk": 28,
            "lowRisk": 109,
            "avgScore": 0.34,
        },
        "news": [
            {
                "title": "Suspicious transaction detected for NGO",
                "href": "#",
                "source": "Alert System",
                "date": "2025-09-20",
            },
            {
                "title": "Circular fund flow detected for Company",
                "href": "#",
                "source": "Alert System",
                "date": "2025-09-19",
            },
        ],
    }


@app.get("/reports")
async def get_reports():

    return [
        {
            "id": "TXN-2025-001",
            "date": "2025-09-19",
            "counterparty": "NGO",
            "amount": 1250000,
            "risk_score": 0.87,
            "level": "High",
        },
        {
            "id": "TXN-2025-002",
            "date": "2025-09-18",
            "counterparty": "Company",
            "amount": 810000,
            "risk_score": 0.42,
            "level": "Medium",
        },
    ]