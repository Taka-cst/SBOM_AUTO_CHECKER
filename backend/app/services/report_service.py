"""Report Generation Service - JSON and CSV export"""
import json
import csv
import io
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """レポート生成サービス"""
    
    @staticmethod
    def generate_json_report(scan_data: Dict[str, Any]) -> str:
        """
        JSON形式のレポートを生成
        
        Args:
            scan_data: スキャン結果データ
            
        Returns:
            JSON文字列
        """
        try:
            report = {
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "format": "json",
                    "version": "1.0"
                },
                "scan_summary": {
                    "scan_id": scan_data.get("scan_id"),
                    "sbom_id": scan_data.get("sbom_id"),
                    "scan_date": scan_data.get("scan_date"),
                    "status": scan_data.get("status"),
                    "total_components": scan_data.get("total_components"),
                    "vulnerable_count": scan_data.get("vulnerable_count"),
                    "severity_counts": scan_data.get("severity_counts"),
                    "scan_duration_seconds": scan_data.get("scan_duration_seconds")
                },
                "vulnerabilities": scan_data.get("vulnerabilities", [])
            }
            
            return json.dumps(report, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Failed to generate JSON report: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def generate_csv_report(scan_data: Dict[str, Any]) -> str:
        """
        CSV形式のレポートを生成
        
        Args:
            scan_data: スキャン結果データ
            
        Returns:
            CSV文字列
        """
        try:
            output = io.StringIO()
            
            # CSVライター作成
            writer = csv.writer(output)
            
            # ヘッダー行
            writer.writerow([
                "CVE ID",
                "Severity",
                "CVSS Score",
                "Component Name",
                "Component Version",
                "Description",
                "Published Date",
                "CVSS Vector"
            ])
            
            # 脆弱性データを書き込み
            vulnerabilities = scan_data.get("vulnerabilities", [])
            for vuln in vulnerabilities:
                writer.writerow([
                    vuln.get("cve_id", ""),
                    vuln.get("severity", ""),
                    vuln.get("cvss_score", ""),
                    vuln.get("component_name", ""),
                    vuln.get("component_version", ""),
                    vuln.get("description", "")[:200],  # 200文字に制限
                    vuln.get("published_date", ""),
                    vuln.get("cvss_vector", "")
                ])
            
            # サマリー情報を追加
            writer.writerow([])  # 空行
            writer.writerow(["Summary"])
            writer.writerow(["Total Components", scan_data.get("total_components", 0)])
            writer.writerow(["Vulnerable Components", scan_data.get("vulnerable_count", 0)])
            writer.writerow(["Critical", scan_data.get("severity_counts", {}).get("critical", 0)])
            writer.writerow(["High", scan_data.get("severity_counts", {}).get("high", 0)])
            writer.writerow(["Medium", scan_data.get("severity_counts", {}).get("medium", 0)])
            writer.writerow(["Low", scan_data.get("severity_counts", {}).get("low", 0)])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate CSV report: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def generate_summary_report(scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        サマリーレポートを生成
        
        Args:
            scan_data: スキャン結果データ
            
        Returns:
            サマリー情報
        """
        try:
            severity_counts = scan_data.get("severity_counts", {})
            total_vulnerabilities = sum(severity_counts.values())
            
            # 深刻度別の割合を計算
            severity_percentages = {}
            if total_vulnerabilities > 0:
                for severity, count in severity_counts.items():
                    severity_percentages[severity] = round((count / total_vulnerabilities) * 100, 1)
            else:
                severity_percentages = {k: 0 for k in severity_counts.keys()}
            
            # リスクレベルの判定
            critical_count = severity_counts.get("critical", 0)
            high_count = severity_counts.get("high", 0)
            
            if critical_count > 0:
                risk_level = "CRITICAL"
            elif high_count > 5:
                risk_level = "HIGH"
            elif high_count > 0:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            return {
                "scan_id": scan_data.get("scan_id"),
                "scan_date": scan_data.get("scan_date"),
                "total_components": scan_data.get("total_components"),
                "vulnerable_count": scan_data.get("vulnerable_count"),
                "total_vulnerabilities": total_vulnerabilities,
                "severity_counts": severity_counts,
                "severity_percentages": severity_percentages,
                "risk_level": risk_level,
                "recommendations": ReportService._generate_recommendations(scan_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate summary report: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def _generate_recommendations(scan_data: Dict[str, Any]) -> List[str]:
        """
        推奨事項を生成
        
        Args:
            scan_data: スキャン結果データ
            
        Returns:
            推奨事項のリスト
        """
        recommendations = []
        severity_counts = scan_data.get("severity_counts", {})
        
        critical_count = severity_counts.get("critical", 0)
        high_count = severity_counts.get("high", 0)
        medium_count = severity_counts.get("medium", 0)
        
        if critical_count > 0:
            recommendations.append(
                f"🔴 {critical_count}件のCRITICAL脆弱性が検出されました。直ちに対応してください。"
            )
        
        if high_count > 0:
            recommendations.append(
                f"🟠 {high_count}件のHIGH脆弱性が検出されました。優先的に対応してください。"
            )
        
        if medium_count > 5:
            recommendations.append(
                f"🟡 {medium_count}件のMEDIUM脆弱性が検出されました。計画的に対応してください。"
            )
        
        if critical_count == 0 and high_count == 0:
            recommendations.append(
                "✅ 深刻な脆弱性は検出されませんでした。"
            )
        
        recommendations.append(
            "💡 定期的なスキャンを実施して、最新の脆弱性情報を確認してください。"
        )
        
        return recommendations


# シングルトンインスタンス
report_service = ReportService()
