from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.scanner import ScanResultItem, ScannerNLQueryRequest
from app.services.scanner_service import ScannerService

router = APIRouter(prefix="/scanner", tags=["Market Scanner"])


@router.get("/presets")
async def get_scanner_presets():
    return ScannerService.get_presets()


@router.post("/run", response_model=List[ScanResultItem])
async def run_scanner(rules: List[Dict[str, Any]]):
    return await ScannerService.run_scan(rules)


@router.post("/nl-query")
async def translate_nl_scanner(req: ScannerNLQueryRequest):
    return await ScannerService.translate_natural_language_query(req.query)
