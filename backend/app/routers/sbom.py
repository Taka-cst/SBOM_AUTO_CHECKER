from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SBOM, ScanResult
from app.services.sbom_parser import SBOMParser, SBOMParserException
from app.celery_worker import scan_sbom
import hashlib
import logging
from datetime import datetime
from uuid import UUID

router = APIRouter(prefix="/api/v1/sbom", tags=["SBOM"])
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_sbom_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    SBOMファイルをアップロードします
    """
    try:
        # ファイルサイズチェック (50MB)
        contents = await file.read()
        if len(contents) > 52428800:
            raise HTTPException(
                status_code=400,
                detail={"code": "FILE_TOO_LARGE", "message": "ファイルサイズが50MBを超えています"}
            )
        
        # ファイル形式チェック
        if not file.filename.endswith(('.json', '.xml')):
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_FILE_FORMAT", "message": "サポートされていないファイル形式です"}
            )
        
        # ファイルハッシュの計算
        file_hash = hashlib.sha256(contents).hexdigest()
        
        # 重複チェック
        existing = db.query(SBOM).filter(SBOM.file_hash == file_hash).first()
        if existing:
            logger.info(f"Duplicate SBOM detected: ID={existing.id}, filename={existing.filename}")
            
            # 最新のスキャン結果を取得
            latest_scan = db.query(ScanResult)\
                .filter(ScanResult.sbom_id == existing.id)\
                .order_by(ScanResult.scan_date.desc())\
                .first()
            
            # 再スキャンを実行
            scan_task = scan_sbom.delay(str(existing.id))  # UUIDを文字列として渡す
            logger.info(f"Rescan task started: task_id={scan_task.id}, sbom_id={existing.id}")
            
            # 既存のSBOM情報を返す
            response_data = {
                "sbom_id": str(existing.id),  # UUIDを文字列に変換
                "filename": existing.filename,
                "format": existing.format,
                "file_hash": existing.file_hash,
                "uploaded_at": existing.uploaded_at.isoformat(),
                "component_count": len(existing.content_json.get('components', [])),
                "scan_status": "rescanning",
                "scan_task_id": scan_task.id,
                "is_duplicate": True,
                "previous_scan": {
                    "scan_id": latest_scan.id,
                    "scan_date": latest_scan.scan_date.isoformat(),
                    "vulnerable_count": latest_scan.vulnerable_count,
                    "critical_count": latest_scan.critical_count,
                    "high_count": latest_scan.high_count,
                    "medium_count": latest_scan.medium_count,
                    "low_count": latest_scan.low_count
                } if latest_scan else None
            }
            
            return {
                "success": True,
                "data": response_data,
                "message": "このSBOMは既にアップロード済みです。最新のデータベースで再スキャンを開始しました。"
            }
        
        # SBOMファイルを解析
        try:
            parsed_data = SBOMParser.parse(contents, file.filename)
        except SBOMParserException as e:
            raise HTTPException(
                status_code=400,
                detail={"code": "PARSE_ERROR", "message": str(e)}
            )
        
        # データベースに保存
        sbom = SBOM(
            filename=file.filename,
            format=parsed_data['format'],
            file_hash=file_hash,
            content_json=parsed_data['raw_data'],
            uploaded_at=datetime.utcnow()
        )
        
        db.add(sbom)
        db.commit()
        db.refresh(sbom)
        
        logger.info(f"SBOM uploaded: ID={sbom.id}, filename={file.filename}")
        
        # 非同期でスキャンタスクを起動
        scan_task = scan_sbom.delay(str(sbom.id))  # UUIDを文字列として渡す
        
        logger.info(f"Scan task started: task_id={scan_task.id}, sbom_id={sbom.id}")
        
        # レスポンス
        response_data = {
            "sbom_id": str(sbom.id),  # UUIDを文字列に変換
            "filename": file.filename,
            "format": parsed_data['format'],
            "file_hash": file_hash,
            "uploaded_at": sbom.uploaded_at.isoformat(),
            "component_count": len(parsed_data.get('components', [])),
            "scan_status": "queued",
            "scan_task_id": scan_task.id,
            "is_duplicate": False
        }
        
        return {
            "success": True,
            "data": response_data,
            "message": "SBOMファイルが正常にアップロードされました。スキャンを開始しています。"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": "UPLOAD_FAILED", "message": str(e)}
        )


@router.get("")
async def get_sboms(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    SBOM一覧を取得します
    """
    try:
        offset = (page - 1) * limit
        
        # 総件数を取得
        total = db.query(SBOM).count()
        
        # データを取得
        sboms = db.query(SBOM).order_by(SBOM.uploaded_at.desc()).offset(offset).limit(limit).all()
        
        items = []
        for sbom in sboms:
            # 最新のスキャン結果を取得
            latest_scan = db.query(ScanResult).filter(
                ScanResult.sbom_id == sbom.id
            ).order_by(ScanResult.scan_date.desc()).first()
            
            items.append({
                "id": str(sbom.id),  # UUIDを文字列に変換
                "file_name": sbom.filename,
                "file_format": sbom.format,
                "uploaded_at": sbom.uploaded_at.isoformat(),
                "scan_status": latest_scan.status if latest_scan else "not_scanned",
                "vulnerable_count": latest_scan.vulnerable_count if latest_scan else 0
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
        logger.error(f"Failed to get SBOMs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sbom_id}")
async def get_sbom(
    sbom_id: str,  # UUIDを文字列として受け取る
    db: Session = Depends(get_db)
):
    """
    SBOM詳細を取得します
    """
    try:
        # UUIDに変換
        try:
            sbom_uuid = UUID(sbom_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid SBOM ID format")
        
        sbom = db.query(SBOM).filter(SBOM.id == sbom_uuid).first()
        
        if not sbom:
            raise HTTPException(status_code=404, detail="SBOM not found")
        
        # 最新のスキャン結果を取得
        latest_scan = db.query(ScanResult).filter(
            ScanResult.sbom_id == sbom_uuid
        ).order_by(ScanResult.scan_date.desc()).first()
        
        return {
            "success": True,
            "data": {
                "sbom_id": str(sbom.id),  # UUIDを文字列に変換
                "filename": sbom.filename,
                "format": sbom.format,
                "file_hash": sbom.file_hash,
                "uploaded_at": sbom.uploaded_at.isoformat(),
                "content": sbom.content_json,
                "latest_scan": {
                    "scan_id": latest_scan.id if latest_scan else None,
                    "status": latest_scan.status if latest_scan else "not_scanned",
                    "scan_date": latest_scan.scan_date.isoformat() if latest_scan else None,
                    "vulnerable_count": latest_scan.vulnerable_count if latest_scan else 0
                } if latest_scan else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get SBOM {sbom_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{sbom_id}")
async def delete_sbom(
    sbom_id: str,  # UUIDを文字列として受け取る
    db: Session = Depends(get_db)
):
    """
    SBOMを削除します
    """
    try:
        # UUIDに変換
        try:
            sbom_uuid = UUID(sbom_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid SBOM ID format")
        
        sbom = db.query(SBOM).filter(SBOM.id == sbom_uuid).first()
        
        if not sbom:
            raise HTTPException(status_code=404, detail="SBOM not found")
        
        # 関連するスキャン結果も削除
        db.query(ScanResult).filter(ScanResult.sbom_id == sbom_uuid).delete()
        
        # SBOMを削除
        db.delete(sbom)
        db.commit()
        
        logger.info(f"SBOM deleted: ID={sbom_id}")
        
        return {
            "success": True,
            "message": "SBOMが正常に削除されました"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete SBOM {sbom_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
