from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SBOMBase(BaseModel):
    """SBOM基本スキーマ"""
    filename: str
    format: str


class SBOMCreate(SBOMBase):
    """SBOM作成スキーマ"""
    file_hash: str
    content_json: Dict[str, Any]


class SBOMResponse(SBOMBase):
    """SBOMレスポンススキーマ"""
    id: int
    uploaded_at: datetime
    file_hash: str
    component_count: int = 0
    
    class Config:
        from_attributes = True


class VulnerabilityBase(BaseModel):
    """脆弱性基本スキーマ"""
    cve_id: str
    severity: Optional[str] = None
    description: Optional[str] = None
    cvss_score: Optional[float] = None


class VulnerabilityResponse(VulnerabilityBase):
    """脆弱性レスポンススキーマ"""
    id: int
    cvss_vector: Optional[str] = None
    published_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    references: Optional[List[str]] = []
    
    class Config:
        from_attributes = True


class ScanResultBase(BaseModel):
    """スキャン結果基本スキーマ"""
    sbom_id: int
    status: str


class ScanResultResponse(ScanResultBase):
    """スキャン結果レスポンススキーマ"""
    id: int
    scan_date: datetime
    total_components: int
    vulnerable_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    scan_duration_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True


class ScanVulnerabilityDetail(BaseModel):
    """スキャン脆弱性詳細"""
    cve_id: str
    component_name: str
    component_version: Optional[str] = None
    severity: str
    cvss_score: Optional[float] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None
    references: Optional[List[str]] = []


class ApiResponse(BaseModel):
    """API共通レスポンス"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[Dict[str, Any]] = None


class PaginationMeta(BaseModel):
    """ページネーションメタ情報"""
    current_page: int
    total_pages: int
    total_items: int
    items_per_page: int


class PaginatedResponse(BaseModel):
    """ページネーション付きレスポンス"""
    items: List[Any]
    pagination: PaginationMeta
