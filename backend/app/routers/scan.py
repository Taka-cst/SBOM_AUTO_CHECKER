"""Scan Result Router"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ScanResult, ScanVulnerability, Vulnerability
from app.services.report_service import report_service
import logging
from uuid import UUID

router = APIRouter(prefix="/api/v1/scan", tags=["Scan"])
logger = logging.getLogger(__name__)


@router.get("/{sbom_id}/result")
async def get_scan_result(
    sbom_id: str,  # UUIDを文字列として受け取る
    db: Session = Depends(get_db)
):
    """
    指定されたSBOMの最新スキャン結果を取得
    """
    try:
        # UUIDに変換
        try:
            sbom_uuid = UUID(sbom_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid SBOM ID format")
        
        # 最新のスキャン結果を取得
        scan_result = db.query(ScanResult).filter(
            ScanResult.sbom_id == sbom_uuid
        ).order_by(ScanResult.scan_date.desc()).first()
        
        if not scan_result:
            raise HTTPException(status_code=404, detail="Scan result not found")
        
        # スキャンで検出された脆弱性の詳細を取得
        scan_vulnerabilities = db.query(ScanVulnerability, Vulnerability).join(
            Vulnerability,
            ScanVulnerability.vulnerability_id == Vulnerability.id
        ).filter(
            ScanVulnerability.scan_result_id == scan_result.id
        ).all()
        
        vulnerabilities = []
        for scan_vuln, vuln in scan_vulnerabilities:
            vulnerabilities.append({
                "cve_id": vuln.cve_id,
                "severity": vuln.severity,
                "cvss_score": float(vuln.cvss_score) if vuln.cvss_score else None,
                "cvss_vector": vuln.cvss_vector,
                "description": vuln.description,
                "component_name": scan_vuln.component_name,
                "component_version": scan_vuln.component_version,
                "published_date": vuln.published_date.isoformat() if vuln.published_date else None,
                "references": vuln.references
            })
        
        return {
            "success": True,
            "data": {
                "scan_id": scan_result.id,
                "sbom_id": str(scan_result.sbom_id),  # UUIDを文字列に変換
                "scan_date": scan_result.scan_date.isoformat(),
                "status": scan_result.status,
                "total_components": scan_result.total_components,
                "vulnerable_count": scan_result.vulnerable_count,
                "severity_counts": {
                    "critical": scan_result.critical_count,
                    "high": scan_result.high_count,
                    "medium": scan_result.medium_count,
                    "low": scan_result.low_count
                },
                "scan_duration_seconds": scan_result.scan_duration_seconds,
                "vulnerabilities": vulnerabilities
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan result for SBOM {sbom_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_scan_history(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    スキャン履歴を取得
    """
    try:
        offset = (page - 1) * limit
        
        # 総件数
        total = db.query(ScanResult).count()
        
        # スキャン結果を取得
        scan_results = db.query(ScanResult).order_by(
            ScanResult.scan_date.desc()
        ).offset(offset).limit(limit).all()
        
        items = []
        for scan in scan_results:
            items.append({
                "scan_id": scan.id,
                "sbom_id": scan.sbom_id,
                "scan_date": scan.scan_date.isoformat(),
                "status": scan.status,
                "total_components": scan.total_components,
                "vulnerable_count": scan.vulnerable_count,
                "severity_counts": {
                    "critical": scan.critical_count,
                    "high": scan.high_count,
                    "medium": scan.medium_count,
                    "low": scan.low_count
                }
            })
        
        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "current_page": page,
                    "total_pages": (total + limit - 1) // limit,
                    "total_items": total,
                    "items_per_page": limit
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get scan history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{sbom_id}/rescan")
async def rescan_sbom(
    sbom_id: str,  # UUIDを文字列として受け取る
    db: Session = Depends(get_db)
):
    """
    SBOMを再スキャン
    """
    try:
        from app.celery_worker import scan_sbom
        from app.models import SBOM
        
        # UUIDに変換
        try:
            sbom_uuid = UUID(sbom_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid SBOM ID format")
        
        # SBOMの存在確認
        sbom = db.query(SBOM).filter(SBOM.id == sbom_uuid).first()
        if not sbom:
            raise HTTPException(status_code=404, detail="SBOM not found")
        
        # スキャンタスクを起動 (文字列UUIDを渡す)
        scan_task = scan_sbom.delay(sbom_id)
        
        logger.info(f"Rescan task started: task_id={scan_task.id}, sbom_id={sbom_id}")
        
        return {
            "success": True,
            "data": {
                "sbom_id": sbom_id,
                "scan_task_id": scan_task.id,
                "status": "queued"
            },
            "message": "再スキャンを開始しました"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rescan SBOM {sbom_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sbom_id}/export")
async def export_scan_report(
    sbom_id: str,  # UUIDを文字列として受け取る
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """
    スキャン結果をエクスポート
    
    Args:
        sbom_id: SBOM ID (UUID)
        format: エクスポート形式 (json or csv)
    """
    try:
        # UUIDに変換
        try:
            sbom_uuid = UUID(sbom_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid SBOM ID format")
        
        # 最新のスキャン結果を取得
        scan_result = db.query(ScanResult).filter(
            ScanResult.sbom_id == sbom_uuid
        ).order_by(ScanResult.scan_date.desc()).first()
        
        if not scan_result:
            raise HTTPException(status_code=404, detail="Scan result not found")
        
        # スキャンで検出された脆弱性の詳細を取得
        scan_vulnerabilities = db.query(ScanVulnerability, Vulnerability).join(
            Vulnerability,
            ScanVulnerability.vulnerability_id == Vulnerability.id
        ).filter(
            ScanVulnerability.scan_result_id == scan_result.id
        ).all()
        
        vulnerabilities = []
        for scan_vuln, vuln in scan_vulnerabilities:
            vulnerabilities.append({
                "cve_id": vuln.cve_id,
                "severity": vuln.severity,
                "cvss_score": float(vuln.cvss_score) if vuln.cvss_score else None,
                "cvss_vector": vuln.cvss_vector,
                "description": vuln.description,
                "component_name": scan_vuln.component_name,
                "component_version": scan_vuln.component_version,
                "published_date": vuln.published_date.isoformat() if vuln.published_date else None,
                "references": vuln.references
            })
        
        scan_data = {
            "scan_id": scan_result.id,
            "sbom_id": str(scan_result.sbom_id),  # UUIDを文字列に変換
            "scan_date": scan_result.scan_date.isoformat(),
            "status": scan_result.status,
            "total_components": scan_result.total_components,
            "vulnerable_count": scan_result.vulnerable_count,
            "severity_counts": {
                "critical": scan_result.critical_count,
                "high": scan_result.high_count,
                "medium": scan_result.medium_count,
                "low": scan_result.low_count
            },
            "scan_duration_seconds": scan_result.scan_duration_seconds,
            "vulnerabilities": vulnerabilities
        }
        
        # レポート生成
        if format == "json":
            content = report_service.generate_json_report(scan_data)
            media_type = "application/json"
            filename = f"scan_report_{sbom_id}.json"
        else:  # csv
            content = report_service.generate_csv_report(scan_data)
            media_type = "text/csv"
            filename = f"scan_report_{sbom_id}.csv"
        
        logger.info(f"Report exported: SBOM ID={sbom_id}, format={format}")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export report for SBOM {sbom_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sbom_id}/summary")
async def get_scan_summary(
    sbom_id: str,  # UUIDを文字列として受け取る
    db: Session = Depends(get_db)
):
    """
    スキャン結果のサマリーを取得
    """
    try:
        # UUIDに変換
        try:
            sbom_uuid = UUID(sbom_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid SBOM ID format")
        
        # 最新のスキャン結果を取得
        scan_result = db.query(ScanResult).filter(
            ScanResult.sbom_id == sbom_uuid
        ).order_by(ScanResult.scan_date.desc()).first()
        
        if not scan_result:
            raise HTTPException(status_code=404, detail="Scan result not found")
        
        scan_data = {
            "scan_id": scan_result.id,
            "sbom_id": str(scan_result.sbom_id),  # UUIDを文字列に変換
            "scan_date": scan_result.scan_date.isoformat(),
            "total_components": scan_result.total_components,
            "vulnerable_count": scan_result.vulnerable_count,
            "severity_counts": {
                "critical": scan_result.critical_count,
                "high": scan_result.high_count,
                "medium": scan_result.medium_count,
                "low": scan_result.low_count
            }
        }
        
        summary = report_service.generate_summary_report(scan_data)
        
        return {
            "success": True,
            "data": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get summary for SBOM {sbom_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
