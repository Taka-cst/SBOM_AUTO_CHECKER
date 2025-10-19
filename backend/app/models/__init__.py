from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.database import Base
import uuid


class SBOM(Base):
    """SBOMモデル"""
    __tablename__ = "sboms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String(255), nullable=False)
    format = Column(String(50), nullable=False)  # 'cyclonedx' or 'spdx'
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    content_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Vulnerability(Base):
    """脆弱性モデル"""
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String(50), unique=True, nullable=False, index=True)
    severity = Column(String(20))  # CRITICAL, HIGH, MEDIUM, LOW
    description = Column(Text)
    cvss_score = Column(DECIMAL(3, 1))
    cvss_vector = Column(String(100))
    published_date = Column(DateTime)
    modified_date = Column(DateTime, index=True)
    cpe_match = Column(JSONB)
    references = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScanResult(Base):
    """スキャン結果モデル"""
    __tablename__ = "scan_results"
    
    id = Column(Integer, primary_key=True, index=True)
    sbom_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    scan_date = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50))  # 'completed', 'in_progress', 'failed'
    total_components = Column(Integer, default=0)
    vulnerable_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    scan_duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScanVulnerability(Base):
    """スキャン脆弱性関連モデル"""
    __tablename__ = "scan_vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_result_id = Column(Integer, nullable=False, index=True)
    vulnerability_id = Column(Integer, nullable=False, index=True)
    component_name = Column(String(255), nullable=False)
    component_version = Column(String(100))
    matched_cpe = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
