"""NVD API Service - CVE データ取得と脆弱性DB更新"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from app.models import Vulnerability
from app.config import settings

logger = logging.getLogger(__name__)


class NVDService:
    """NVD API連携サービス"""
    
    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'NVD_API_KEY', None)
        self.headers = {}
        if self.api_key:
            self.headers['apiKey'] = self.api_key
            self.rate_limit_delay = 0.6  # APIキーあり: 100リクエスト/分
        else:
            self.rate_limit_delay = 6.0  # APIキーなし: 10リクエスト/分
    
    def fetch_recent_cves(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        最近のCVEデータを取得
        
        Args:
            days: 過去何日分のデータを取得するか
            
        Returns:
            CVEデータのリスト
        """
        logger.info(f"Fetching CVEs from last {days} days...")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        all_cves = []
        start_index = 0
        results_per_page = 2000  # NVD APIの最大値
        
        while True:
            try:
                params = {
                    'pubStartDate': start_date.strftime('%Y-%m-%dT00:00:00.000'),
                    'pubEndDate': end_date.strftime('%Y-%m-%dT23:59:59.999'),
                    'startIndex': start_index,
                    'resultsPerPage': results_per_page
                }
                
                logger.info(f"Requesting CVEs from index {start_index}...")
                response = requests.get(
                    self.BASE_URL,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                vulnerabilities = data.get('vulnerabilities', [])
                
                if not vulnerabilities:
                    break
                
                all_cves.extend(vulnerabilities)
                logger.info(f"Retrieved {len(vulnerabilities)} CVEs")
                
                # 次のページがあるか確認
                total_results = data.get('totalResults', 0)
                if start_index + results_per_page >= total_results:
                    break
                
                start_index += results_per_page
                
                # レート制限対策
                time.sleep(self.rate_limit_delay)
                
            except requests.RequestException as e:
                logger.error(f"Failed to fetch CVEs: {str(e)}")
                break
        
        logger.info(f"Total CVEs fetched: {len(all_cves)}")
        return all_cves
    
    def fetch_cve_by_id(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        特定のCVEデータを取得
        
        Args:
            cve_id: CVE ID (例: CVE-2023-12345)
            
        Returns:
            CVEデータ、取得失敗時はNone
        """
        try:
            params = {'cveId': cve_id}
            response = requests.get(
                self.BASE_URL,
                headers=self.headers,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            vulnerabilities = data.get('vulnerabilities', [])
            
            if vulnerabilities:
                return vulnerabilities[0]
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch CVE {cve_id}: {str(e)}")
            return None
    
    def save_vulnerability_to_db(self, db: Session, cve_data: Dict[str, Any]) -> Optional[Vulnerability]:
        """
        CVEデータをデータベースに保存
        
        Args:
            db: データベースセッション
            cve_data: NVD APIから取得したCVEデータ
            
        Returns:
            保存されたVulnerabilityオブジェクト
        """
        try:
            cve = cve_data.get('cve', {})
            cve_id = cve.get('id')
            
            if not cve_id:
                logger.warning("CVE ID not found in data")
                return None
            
            # 既存レコードを確認
            existing = db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()
            
            # CVSS情報の抽出
            cvss_score = None
            cvss_vector = None
            severity = "UNKNOWN"
            
            metrics = cve.get('metrics', {})
            
            # CVSS 3.x を優先
            if 'cvssMetricV31' in metrics and metrics['cvssMetricV31']:
                cvss_data = metrics['cvssMetricV31'][0].get('cvssData', {})
                cvss_score = cvss_data.get('baseScore')
                cvss_vector = cvss_data.get('vectorString')
                severity = cvss_data.get('baseSeverity', 'UNKNOWN')
            elif 'cvssMetricV30' in metrics and metrics['cvssMetricV30']:
                cvss_data = metrics['cvssMetricV30'][0].get('cvssData', {})
                cvss_score = cvss_data.get('baseScore')
                cvss_vector = cvss_data.get('vectorString')
                severity = cvss_data.get('baseSeverity', 'UNKNOWN')
            elif 'cvssMetricV2' in metrics and metrics['cvssMetricV2']:
                cvss_data = metrics['cvssMetricV2'][0].get('cvssData', {})
                cvss_score = cvss_data.get('baseScore')
                cvss_vector = cvss_data.get('vectorString')
                # CVSS v2には severity がないのでスコアから判定
                if cvss_score:
                    if cvss_score >= 9.0:
                        severity = "CRITICAL"
                    elif cvss_score >= 7.0:
                        severity = "HIGH"
                    elif cvss_score >= 4.0:
                        severity = "MEDIUM"
                    else:
                        severity = "LOW"
            
            # 説明文の取得
            descriptions = cve.get('descriptions', [])
            description = ""
            for desc in descriptions:
                if desc.get('lang') == 'en':
                    description = desc.get('value', '')
                    break
            
            # CPEマッチ情報の抽出
            configurations = cve.get('configurations', [])
            cpe_match = []
            for config in configurations:
                for node in config.get('nodes', []):
                    for match in node.get('cpeMatch', []):
                        if match.get('vulnerable', False):
                            cpe_match.append({
                                'criteria': match.get('criteria'),
                                'matchCriteriaId': match.get('matchCriteriaId'),
                                'versionStartIncluding': match.get('versionStartIncluding'),
                                'versionEndExcluding': match.get('versionEndExcluding'),
                                'versionStartExcluding': match.get('versionStartExcluding'),
                                'versionEndIncluding': match.get('versionEndIncluding')
                            })
            
            # 参考リンク
            references = []
            for ref in cve.get('references', []):
                references.append({
                    'url': ref.get('url'),
                    'source': ref.get('source')
                })
            
            # 日付情報
            published_date = cve.get('published')
            modified_date = cve.get('lastModified')
            
            if published_date:
                published_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
            if modified_date:
                modified_date = datetime.fromisoformat(modified_date.replace('Z', '+00:00'))
            
            # 既存レコードの更新または新規作成
            if existing:
                existing.severity = severity
                existing.description = description
                existing.cvss_score = cvss_score
                existing.cvss_vector = cvss_vector
                existing.published_date = published_date
                existing.modified_date = modified_date
                existing.cpe_match = cpe_match
                existing.references = references
                existing.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Updated CVE: {cve_id}")
                return existing
            else:
                vulnerability = Vulnerability(
                    cve_id=cve_id,
                    severity=severity,
                    description=description,
                    cvss_score=cvss_score,
                    cvss_vector=cvss_vector,
                    published_date=published_date,
                    modified_date=modified_date,
                    cpe_match=cpe_match,
                    references=references
                )
                db.add(vulnerability)
                db.commit()
                logger.info(f"Saved new CVE: {cve_id}")
                return vulnerability
                
        except Exception as e:
            logger.error(f"Failed to save vulnerability {cve_id}: {str(e)}", exc_info=True)
            db.rollback()
            return None
    
    def update_database(self, db: Session, days: int = 30) -> Dict[str, int]:
        """
        脆弱性データベースを更新
        
        Args:
            db: データベースセッション
            days: 過去何日分のデータを取得するか
            
        Returns:
            統計情報
        """
        logger.info("Starting NVD database update...")
        
        cves = self.fetch_recent_cves(days=days)
        
        stats = {
            'total_fetched': len(cves),
            'new_count': 0,
            'updated_count': 0,
            'failed_count': 0
        }
        
        for cve_data in cves:
            result = self.save_vulnerability_to_db(db, cve_data)
            if result:
                if result.created_at >= datetime.utcnow() - timedelta(minutes=1):
                    stats['new_count'] += 1
                else:
                    stats['updated_count'] += 1
            else:
                stats['failed_count'] += 1
        
        logger.info(f"NVD update completed: {stats}")
        return stats


# シングルトンインスタンス
nvd_service = NVDService()
