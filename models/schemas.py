from pydantic import BaseModel
from typing import List, Dict, Any

class IngestRequest(BaseModel):
    data_type: str
    records: List[Dict[str, Any]]

class ResolveRequest(BaseModel):
    party_ids: List[str]
