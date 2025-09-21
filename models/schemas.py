# from pydantic import BaseModel
# from typing import List, Dict, Any

# class IngestRequest(BaseModel):
#     data_type: str
#     records: List[Dict[str, Any]]

# class ResolveRequest(BaseModel):
#     party_ids: List[str]

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class IngestRequest(BaseModel):
    data_type: str = Field(..., description="Collection name, e.g., 'transactions', 'entities'")
    records: List[Dict[str, Any]]

class FeatureRequest(BaseModel):
    theta_micro: float = 0.005
    windows: List[int] = [7, 30, 90]


class ResolveRequest(BaseModel):
    party_ids: List[str]


class FeatureComputeRequest(BaseModel):
    theta_micro: float = 0.005
    windows: List[int] = [7, 30, 90]


class TriageRequest(BaseModel):
    disposition: str
    analyst_notes: Optional[str] = None
