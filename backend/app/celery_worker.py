from celery import Celery
from celery.schedules import crontab
from app.config import settings
from app.database import SessionLocal
from app.services.trivy_service import trivy_service
from app.models import SBOM, ScanResult, Vulnerability, ScanVulnerability
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Celeryアプリケーションの作成
celery_app = Celery(
    "sbom_scanner",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery設定
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1時間
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery Beat スケジュール設定
celery_app.conf.beat_schedule = {
    'update-trivy-database-every-12-hours': {
        'task': 'app.celery_worker.update_trivy_db',
        'schedule': crontab(hour='*/12', minute=0),  # 12時間ごと
    },
}


@celery_app.task(name='app.celery_worker.update_trivy_db')
def update_trivy_db():
    """
    Trivy脆弱性データベースを更新するタスク
    12時間ごとに実行される
    """
    logger.info("Starting Trivy database update task...")
    
    try:
        # Trivyのインストール確認
        if not trivy_service.check_trivy_installed():
            error_msg = "Trivy is not installed"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Trivy DBを更新
        stats = trivy_service.update_database()
        
        logger.info(f"Trivy DB update completed: {stats}")
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Trivy DB update failed: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name='app.celery_worker.scan_sbom', bind=True)
def scan_sbom(self, sbom_id: str):  # UUIDを文字列として受け取る
    """
    SBOMに対してTrivyスキャンを実行するタスク
    
    Args:
        sbom_id: スキャン対象のSBOM ID (UUID文字列)
    """
    from uuid import UUID
    
    logger.info(f"Starting Trivy SBOM scan task for SBOM ID: {sbom_id}")
    db = SessionLocal()
    
    try:
        # UUIDに変換
        try:
            sbom_uuid = UUID(sbom_id)
        except ValueError:
            logger.error(f"Invalid SBOM ID format: {sbom_id}")
            return {
                "status": "failed",
                "error": "Invalid SBOM ID format"
            }
        
        # SBOMを取得
        sbom = db.query(SBOM).filter(SBOM.id == sbom_uuid).first()
        if not sbom:
            logger.error(f"SBOM not found: ID={sbom_id}")
            return {
                "status": "failed",
                "error": "SBOM not found"
            }
        
        # スキャン開始時刻
        start_time = time.time()
        
        logger.info(f"Scanning SBOM: {sbom.filename} (format: {sbom.format})")
        
        # Trivyでスキャン実行
        scan_results = trivy_service.scan_sbom(
            sbom_content=sbom.content_json,
            sbom_format=sbom.format
        )
        
        if scan_results.get("status") != "success":
            raise Exception(scan_results.get("error", "Trivy scan failed"))
        
        # スキャン所要時間を計算
        scan_duration = int(time.time() - start_time)
        
        # コンポーネント数を計算(フォーマットに応じて異なるキーを使用)
        if sbom.format.lower() == 'cyclonedx':
            total_components = len(sbom.content_json.get('components', []))
        elif sbom.format.lower() == 'spdx':
            total_components = len(sbom.content_json.get('packages', []))
        else:
            # 両方試す
            components = sbom.content_json.get('components', [])
            packages = sbom.content_json.get('packages', [])
            total_components = len(components) if components else len(packages)
        
        logger.info(f"Total components in SBOM: {total_components}")
        
        # スキャン結果をデータベースに保存
        scan_result = ScanResult(
            sbom_id=sbom_uuid,  # UUIDを使用
            scan_date=datetime.utcnow(),
            status='completed',
            total_components=total_components,
            vulnerable_count=scan_results['vulnerable_components_count'],
            critical_count=scan_results['severity_counts'].get('CRITICAL', 0),
            high_count=scan_results['severity_counts'].get('HIGH', 0),
            medium_count=scan_results['severity_counts'].get('MEDIUM', 0),
            low_count=scan_results['severity_counts'].get('LOW', 0),
            scan_duration_seconds=scan_duration
        )
        
        db.add(scan_result)
        db.flush()  # IDを取得
        
        # 脆弱性の詳細を保存
        for vuln_data in scan_results['vulnerabilities']:
            # Vulnerabilityテーブルに保存または取得
            vulnerability = db.query(Vulnerability).filter(
                Vulnerability.cve_id == vuln_data['cve_id']
            ).first()
            
            if not vulnerability:
                vulnerability = Vulnerability(
                    cve_id=vuln_data['cve_id'],
                    severity=vuln_data['severity'],
                    description=vuln_data.get('description', ''),
                    cvss_score=vuln_data.get('cvss_score', 0.0),
                    cvss_vector=vuln_data.get('cvss_vector', ''),
                    published_date=datetime.fromisoformat(vuln_data['published_date'].replace('Z', '+00:00')) if vuln_data.get('published_date') else None,
                    modified_date=datetime.fromisoformat(vuln_data['last_modified_date'].replace('Z', '+00:00')) if vuln_data.get('last_modified_date') else None,
                    references={'urls': vuln_data.get('references', [])}
                )
                db.add(vulnerability)
                db.flush()
            
            # ScanVulnerabilityに関連付け
            scan_vuln = ScanVulnerability(
                scan_result_id=scan_result.id,
                vulnerability_id=vulnerability.id,
                component_name=vuln_data['component_name'],
                component_version=vuln_data['component_version'],
                matched_cpe=vuln_data.get('target', '')
            )
            db.add(scan_vuln)
        
        db.commit()
        
        logger.info(f"Trivy scan completed for SBOM ID: {sbom_id}, Result ID: {scan_result.id}")
        logger.info(f"Found {len(scan_results['vulnerabilities'])} vulnerabilities")
        
        return {
            "status": "success",
            "sbom_id": sbom_id,
            "scan_result_id": scan_result.id,
            "total_components": total_components,
            "vulnerable_count": scan_results['vulnerable_components_count'],
            "total_vulnerabilities": scan_results['total_vulnerabilities'],
            "severity_counts": scan_results['severity_counts'],
            "scan_duration_seconds": scan_duration
        }
        
    except Exception as e:
        logger.error(f"Trivy scan failed for SBOM ID {sbom_id}: {str(e)}", exc_info=True)
        
        # 失敗したスキャン結果を記録
        try:
            failed_scan = ScanResult(
                sbom_id=sbom_id,
                scan_date=datetime.utcnow(),
                status='failed',
                total_components=0,
                vulnerable_count=0
            )
            db.add(failed_scan)
            db.commit()
        except:
            db.rollback()
        
        return {
            "status": "failed",
            "error": str(e),
            "sbom_id": sbom_id
        }
        
    finally:
        db.close()


if __name__ == '__main__':
    celery_app.start()
