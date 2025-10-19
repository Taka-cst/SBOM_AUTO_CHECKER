"""Trivy Scanner Service"""
import json
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TrivyService:
    """Trivyを使用した脆弱性スキャンサービス"""
    
    def __init__(self):
        self.trivy_cache_dir = os.getenv("TRIVY_CACHE_DIR", str(Path.home() / ".cache" / "trivy"))
        self.trivy_command = "trivy"
    
    def update_database(self) -> Dict[str, Any]:
        """
        Trivyの脆弱性データベースを更新
        
        Returns:
            更新結果の統計情報
        """
        logger.info("Starting Trivy database update...")
        
        try:
            # Trivy DBダウンロードコマンドを実行
            # 注: Trivy 0.67.2では、ダミースキャンでDBを更新する
            cmd = [
                self.trivy_command,
                "image",
                "--download-db-only",
                "--cache-dir", self.trivy_cache_dir,
                "alpine:latest"  # ダミーイメージ
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分タイムアウト
            )
            
            if result.returncode == 0:
                logger.info("Trivy database update completed successfully")
                logger.info(f"Output: {result.stdout}")
                
                return {
                    "status": "success",
                    "updated_at": datetime.utcnow().isoformat(),
                    "cache_dir": self.trivy_cache_dir,
                    "message": "Database updated successfully"
                }
            else:
                error_msg = f"Trivy DB update failed: {result.stderr}"
                logger.error(error_msg)
                return {
                    "status": "failed",
                    "error": error_msg,
                    "updated_at": datetime.utcnow().isoformat()
                }
                
        except subprocess.TimeoutExpired:
            error_msg = "Trivy DB update timed out"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "updated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = f"Trivy DB update error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "failed",
                "error": error_msg,
                "updated_at": datetime.utcnow().isoformat()
            }
    
    def scan_sbom(self, sbom_content: Dict[str, Any], sbom_format: str = "cyclonedx") -> Dict[str, Any]:
        """
        SBOMファイルをTrivyでスキャン
        
        Args:
            sbom_content: SBOMのJSON内容
            sbom_format: SBOMフォーマット ('cyclonedx' or 'spdx')
            
        Returns:
            スキャン結果
        """
        logger.info(f"Starting Trivy SBOM scan (format: {sbom_format})...")
        
        try:
            # 一時ファイルにSBOMを保存
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                json.dump(sbom_content, temp_file, indent=2)
                temp_path = temp_file.name
            
            try:
                # Trivyスキャンコマンドを実行
                cmd = [
                    self.trivy_command,
                    "sbom",
                    "--format", "json",
                    "--cache-dir", self.trivy_cache_dir,
                    "--severity", "UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL",
                    temp_path
                ]
                
                logger.info(f"Executing: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分タイムアウト
                )
                
                if result.returncode == 0 or result.returncode == 1:
                    # returncode 1 = 脆弱性が見つかった場合（正常）
                    logger.info("Trivy scan completed")
                    
                    # 結果をパース
                    scan_result = json.loads(result.stdout)
                    parsed_result = self._parse_trivy_result(scan_result)
                    
                    logger.info(f"Found {len(parsed_result['vulnerabilities'])} vulnerabilities")
                    return parsed_result
                else:
                    error_msg = f"Trivy scan failed: {result.stderr}"
                    logger.error(error_msg)
                    return {
                        "status": "failed",
                        "error": error_msg,
                        "vulnerabilities": [],
                        "severity_counts": {
                            "CRITICAL": 0,
                            "HIGH": 0,
                            "MEDIUM": 0,
                            "LOW": 0,
                            "UNKNOWN": 0
                        }
                    }
                    
            finally:
                # 一時ファイルを削除
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except subprocess.TimeoutExpired:
            error_msg = "Trivy scan timed out"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "vulnerabilities": [],
                "severity_counts": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
            }
        except Exception as e:
            error_msg = f"Trivy scan error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "failed",
                "error": error_msg,
                "vulnerabilities": [],
                "severity_counts": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
            }
    
    def _parse_trivy_result(self, trivy_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trivyのスキャン結果をパースして標準フォーマットに変換
        
        Args:
            trivy_result: Trivyの生JSON結果
            
        Returns:
            パース済みスキャン結果
        """
        vulnerabilities = []
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "UNKNOWN": 0
        }
        
        vulnerable_components = set()
        
        # Trivyの結果構造を解析
        results = trivy_result.get("Results", [])
        
        for result in results:
            target = result.get("Target", "unknown")
            vulns = result.get("Vulnerabilities", [])
            
            for vuln in vulns:
                cve_id = vuln.get("VulnerabilityID", "UNKNOWN")
                severity = vuln.get("Severity", "UNKNOWN")
                pkg_name = vuln.get("PkgName", "unknown")
                installed_version = vuln.get("InstalledVersion", "unknown")
                fixed_version = vuln.get("FixedVersion", "")
                title = vuln.get("Title", "")
                description = vuln.get("Description", "")
                
                # CVSS情報
                cvss_v3 = vuln.get("CVSS", {}).get("nvd", {}).get("V3Score", 0.0)
                cvss_vector = vuln.get("CVSS", {}).get("nvd", {}).get("V3Vector", "")
                
                # 参照情報
                references = vuln.get("References", [])
                
                vulnerability_data = {
                    "cve_id": cve_id,
                    "severity": severity,
                    "component_name": pkg_name,
                    "component_version": installed_version,
                    "fixed_version": fixed_version,
                    "title": title,
                    "description": description,
                    "cvss_score": cvss_v3,
                    "cvss_vector": cvss_vector,
                    "references": references,
                    "target": target,
                    "published_date": vuln.get("PublishedDate", ""),
                    "last_modified_date": vuln.get("LastModifiedDate", "")
                }
                
                vulnerabilities.append(vulnerability_data)
                
                # 統計情報を更新
                if severity in severity_counts:
                    severity_counts[severity] += 1
                else:
                    severity_counts["UNKNOWN"] += 1
                
                # 脆弱なコンポーネントを記録
                vulnerable_components.add(f"{pkg_name}@{installed_version}")
        
        return {
            "status": "success",
            "vulnerabilities": vulnerabilities,
            "severity_counts": severity_counts,
            "vulnerable_components_count": len(vulnerable_components),
            "total_vulnerabilities": len(vulnerabilities)
        }
    
    def check_trivy_installed(self) -> bool:
        """
        Trivyがインストールされているか確認
        
        Returns:
            インストールされている場合True
        """
        try:
            result = subprocess.run(
                [self.trivy_command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Trivy is installed: {result.stdout.strip()}")
                return True
            return False
        except Exception as e:
            logger.error(f"Trivy check failed: {str(e)}")
            return False


# シングルトンインスタンス
trivy_service = TrivyService()
