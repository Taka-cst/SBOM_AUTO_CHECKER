"""Vulnerability Scanner Service"""
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Vulnerability, ScanResult, ScanVulnerability
from app.services.sbom_parser import Component
from packaging import version as pkg_version

logger = logging.getLogger(__name__)


class VulnerabilityScanner:
    """脆弱性スキャンサービス"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def scan_components(self, components: List[Component]) -> Dict[str, Any]:
        """
        コンポーネントリストをスキャンして脆弱性を検出
        
        Args:
            components: スキャン対象のコンポーネントリスト
            
        Returns:
            スキャン結果の統計情報
        """
        logger.info(f"Starting vulnerability scan for {len(components)} components")
        
        results = {
            'total_components': len(components),
            'vulnerable_components': [],
            'vulnerabilities_found': [],
            'severity_counts': {
                'CRITICAL': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0,
                'UNKNOWN': 0
            }
        }
        
        for component in components:
            vulnerabilities = self._find_vulnerabilities_for_component(component)
            
            if vulnerabilities:
                results['vulnerable_components'].append({
                    'component': component,
                    'vulnerabilities': vulnerabilities
                })
                
                for vuln in vulnerabilities:
                    results['vulnerabilities_found'].append(vuln)
                    severity = vuln.severity or 'UNKNOWN'
                    results['severity_counts'][severity] = results['severity_counts'].get(severity, 0) + 1
        
        logger.info(f"Scan completed: {len(results['vulnerable_components'])} vulnerable components found")
        return results
    
    def _find_vulnerabilities_for_component(
        self, 
        component: Component
    ) -> List[Vulnerability]:
        """
        特定のコンポーネントに対する脆弱性を検索
        
        Args:
            component: スキャン対象のコンポーネント
            
        Returns:
            該当する脆弱性のリスト
        """
        vulnerabilities = []
        
        # コンポーネント名を正規化
        normalized_name = self._normalize_component_name(component.name)
        
        # データベースから関連しそうな脆弱性を取得
        # CPEマッチを使って検索
        candidates = self.db.query(Vulnerability).filter(
            Vulnerability.cpe_match.isnot(None)
        ).all()
        
        for vuln in candidates:
            if self._is_vulnerable(component, vuln):
                vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _is_vulnerable(self, component: Component, vulnerability: Vulnerability) -> bool:
        """
        コンポーネントが脆弱性の影響を受けるか判定
        
        Args:
            component: コンポーネント
            vulnerability: 脆弱性
            
        Returns:
            影響を受ける場合True
        """
        if not vulnerability.cpe_match:
            return False
        
        cpe_matches = vulnerability.cpe_match
        if isinstance(cpe_matches, str):
            import json
            try:
                cpe_matches = json.loads(cpe_matches)
            except:
                return False
        
        normalized_name = self._normalize_component_name(component.name)
        
        for cpe_match in cpe_matches:
            criteria = cpe_match.get('criteria', '')
            
            # CPE文字列から製品名を抽出
            # 形式: cpe:2.3:a:vendor:product:version:...
            if self._match_cpe_product(criteria, normalized_name):
                # バージョンチェック
                if self._check_version_range(
                    component.version,
                    cpe_match.get('versionStartIncluding'),
                    cpe_match.get('versionStartExcluding'),
                    cpe_match.get('versionEndIncluding'),
                    cpe_match.get('versionEndExcluding')
                ):
                    return True
        
        return False
    
    def _match_cpe_product(self, cpe: str, component_name: str) -> bool:
        """
        CPE文字列とコンポーネント名がマッチするか判定
        
        Args:
            cpe: CPE文字列
            component_name: 正規化されたコンポーネント名
            
        Returns:
            マッチする場合True
        """
        # CPE形式: cpe:2.3:a:vendor:product:version:...
        parts = cpe.split(':')
        if len(parts) < 5:
            return False
        
        product = parts[4].lower()
        vendor = parts[3].lower() if len(parts) > 3 else ""
        
        # 製品名の比較
        if product in component_name or component_name in product:
            return True
        
        # ベンダー名も含めて比較
        if vendor and (vendor in component_name or f"{vendor}_{product}" in component_name):
            return True
        
        return False
    
    def _check_version_range(
        self,
        component_version: str,
        version_start_including: Optional[str],
        version_start_excluding: Optional[str],
        version_end_including: Optional[str],
        version_end_excluding: Optional[str]
    ) -> bool:
        """
        コンポーネントのバージョンが脆弱性の影響範囲に含まれるか判定
        
        Args:
            component_version: コンポーネントのバージョン
            version_start_including: 開始バージョン(含む)
            version_start_excluding: 開始バージョン(含まない)
            version_end_including: 終了バージョン(含む)
            version_end_excluding: 終了バージョン(含まない)
            
        Returns:
            範囲に含まれる場合True
        """
        try:
            comp_ver = pkg_version.parse(component_version)
            
            # 開始バージョンチェック
            if version_start_including:
                start_ver = pkg_version.parse(version_start_including)
                if comp_ver < start_ver:
                    return False
            
            if version_start_excluding:
                start_ver = pkg_version.parse(version_start_excluding)
                if comp_ver <= start_ver:
                    return False
            
            # 終了バージョンチェック
            if version_end_including:
                end_ver = pkg_version.parse(version_end_including)
                if comp_ver > end_ver:
                    return False
            
            if version_end_excluding:
                end_ver = pkg_version.parse(version_end_excluding)
                if comp_ver >= end_ver:
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Version comparison failed: {component_version} - {str(e)}")
            # バージョン比較に失敗した場合、文字列完全一致で判定
            if version_start_including and component_version == version_start_including:
                return True
            return False
    
    def _normalize_component_name(self, name: str) -> str:
        """
        コンポーネント名を正規化(小文字、記号除去)
        
        Args:
            name: コンポーネント名
            
        Returns:
            正規化された名前
        """
        # 小文字に変換
        normalized = name.lower()
        # 記号を_に置換
        normalized = re.sub(r'[^a-z0-9]', '_', normalized)
        # 連続するアンダースコアを1つに
        normalized = re.sub(r'_+', '_', normalized)
        # 前後のアンダースコアを削除
        normalized = normalized.strip('_')
        return normalized
    
    def save_scan_result(
        self,
        sbom_id: int,
        scan_results: Dict[str, Any],
        scan_duration: int
    ) -> ScanResult:
        """
        スキャン結果をデータベースに保存
        
        Args:
            sbom_id: SBOM ID
            scan_results: スキャン結果
            scan_duration: スキャン所要時間(秒)
            
        Returns:
            保存されたScanResultオブジェクト
        """
        try:
            # ScanResultの作成
            scan_result = ScanResult(
                sbom_id=sbom_id,
                scan_date=datetime.utcnow(),
                status='completed',
                total_components=scan_results['total_components'],
                vulnerable_count=len(scan_results['vulnerable_components']),
                critical_count=scan_results['severity_counts'].get('CRITICAL', 0),
                high_count=scan_results['severity_counts'].get('HIGH', 0),
                medium_count=scan_results['severity_counts'].get('MEDIUM', 0),
                low_count=scan_results['severity_counts'].get('LOW', 0),
                scan_duration_seconds=scan_duration
            )
            
            self.db.add(scan_result)
            self.db.flush()  # IDを取得
            
            # ScanVulnerabilityの作成
            for vuln_comp in scan_results['vulnerable_components']:
                component = vuln_comp['component']
                for vulnerability in vuln_comp['vulnerabilities']:
                    scan_vuln = ScanVulnerability(
                        scan_result_id=scan_result.id,
                        vulnerability_id=vulnerability.id,
                        component_name=component.name,
                        component_version=component.version,
                        matched_cpe=self._extract_matched_cpe(component, vulnerability)
                    )
                    self.db.add(scan_vuln)
            
            self.db.commit()
            logger.info(f"Scan result saved: ID={scan_result.id}")
            return scan_result
            
        except Exception as e:
            logger.error(f"Failed to save scan result: {str(e)}", exc_info=True)
            self.db.rollback()
            raise
    
    def _extract_matched_cpe(self, component: Component, vulnerability: Vulnerability) -> Optional[str]:
        """
        マッチしたCPE文字列を取得
        
        Args:
            component: コンポーネント
            vulnerability: 脆弱性
            
        Returns:
            CPE文字列
        """
        if not vulnerability.cpe_match:
            return None
        
        cpe_matches = vulnerability.cpe_match
        if isinstance(cpe_matches, str):
            import json
            try:
                cpe_matches = json.loads(cpe_matches)
            except:
                return None
        
        for cpe_match in cpe_matches:
            criteria = cpe_match.get('criteria', '')
            if criteria:
                return criteria
        
        return None
