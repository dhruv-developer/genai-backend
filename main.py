from fastapi import FastAPI
from routers import ingest, entity, features, rules, score, alerts, monitoring

app = FastAPI(title="Grant Risk API")

app.include_router(ingest.router)
app.include_router(entity.router)
app.include_router(features.router)
app.include_router(rules.router)
app.include_router(score.router)
app.include_router(alerts.router)
app.include_router(monitoring.router)
