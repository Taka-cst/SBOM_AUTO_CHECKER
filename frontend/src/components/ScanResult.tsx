import React, { useEffect, useState } from 'react';
import { scanApi } from '../services/api';

interface Vulnerability {
  cve_id: string;
  severity: string;
  cvss_score: number | null;
  cvss_vector: string | null;
  description: string;
  component_name: string;
  component_version: string;
  published_date: string | null;
  references: any;
}

interface SeverityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

interface ScanResultData {
  scan_id: number;
  sbom_id: string;  // UUID
  scan_date: string;
  status: string;
  total_components: number;
  vulnerable_count: number;
  severity_counts: SeverityCounts;
  scan_duration_seconds: number | null;
  vulnerabilities: Vulnerability[];
}

interface ScanResultProps {
  sbomId: string;  // UUID
  onClose?: () => void;
}

const ScanResult: React.FC<ScanResultProps> = ({ sbomId, onClose }) => {
  const [result, setResult] = useState<ScanResultData | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterComponent, setFilterComponent] = useState<string>('');

  useEffect(() => {
    fetchScanResult();
    fetchSummary();
  }, [sbomId]);

  const fetchScanResult = async () => {
    try {
      setLoading(true);
      const data = await scanApi.getResult(sbomId);
      setResult(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'スキャン結果の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const data = await scanApi.getSummary(sbomId);
      setSummary(data);
    } catch (err) {
      console.error('Summary fetch failed:', err);
    }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const blob = await scanApi.exportReport(sbomId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scan_report_${sbomId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      alert('レポートのエクスポートに失敗しました');
    }
  };

  const handleRescan = async () => {
    try {
      setLoading(true);
      await scanApi.rescan(sbomId);
      alert('再スキャンを開始しました。しばらくお待ちください。');
      // 10秒後に結果を再取得
      setTimeout(() => {
        fetchScanResult();
        fetchSummary();
      }, 10000);
    } catch (err: any) {
      alert(err.response?.data?.detail || '再スキャンの開始に失敗しました');
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    const severityLower = severity.toLowerCase();
    switch (severityLower) {
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'CRITICAL':
        return 'text-red-600';
      case 'HIGH':
        return 'text-orange-600';
      case 'MEDIUM':
        return 'text-yellow-600';
      case 'LOW':
        return 'text-blue-600';
      default:
        return 'text-green-600';
    }
  };

  // UTC日時を日本時間に変換する関数
  const formatJSTDate = (utcDateString: string) => {
    const date = new Date(utcDateString);
    return date.toLocaleString('ja-JP', {
      timeZone: 'Asia/Tokyo',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const filteredVulnerabilities = result?.vulnerabilities.filter((vuln) => {
    const severityMatch = filterSeverity === 'all' || vuln.severity.toLowerCase() === filterSeverity;
    const componentMatch = filterComponent === '' || 
      vuln.component_name.toLowerCase().includes(filterComponent.toLowerCase());
    return severityMatch && componentMatch;
  }) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">スキャン結果を読み込んでいます...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-600">{error}</p>
        {onClose && (
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            閉じる
          </button>
        )}
      </div>
    );
  }

  if (!result) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">SBOM ID: {result.sbom_id}</h2>
          <p className="text-gray-600 mt-1">
            スキャン日時: {formatJSTDate(result.scan_date)}
          </p>
          <p className="text-gray-600">
            ステータス: <span className="font-semibold">{result.status}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('json')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            JSON出力
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition"
          >
            CSV出力
          </button>
          <button
            onClick={handleRescan}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition"
          >
            再スキャン
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition"
            >
              閉じる
            </button>
          )}
        </div>
      </div>

      {/* サマリー */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <p className="text-gray-600 text-sm">総コンポーネント数</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{result.total_components}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <p className="text-gray-600 text-sm">脆弱性のあるコンポーネント</p>
          <p className="text-3xl font-bold text-red-600 mt-2">{result.vulnerable_count}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <p className="text-gray-600 text-sm">脆弱性の総数</p>
          <p className="text-3xl font-bold text-orange-600 mt-2">{result.vulnerabilities.length}</p>
        </div>
        {summary && (
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-gray-600 text-sm">リスクレベル</p>
            <p className={`text-3xl font-bold mt-2 ${getRiskLevelColor(summary.risk_level)}`}>
              {summary.risk_level}
            </p>
          </div>
        )}
      </div>

      {/* 深刻度別カウント */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">深刻度別の脆弱性</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 rounded-lg bg-red-50">
            <p className="text-sm text-gray-600">Critical</p>
            <p className="text-2xl font-bold text-red-600 mt-1">{result.severity_counts.critical}</p>
          </div>
          <div className="text-center p-4 rounded-lg bg-orange-50">
            <p className="text-sm text-gray-600">High</p>
            <p className="text-2xl font-bold text-orange-600 mt-1">{result.severity_counts.high}</p>
          </div>
          <div className="text-center p-4 rounded-lg bg-yellow-50">
            <p className="text-sm text-gray-600">Medium</p>
            <p className="text-2xl font-bold text-yellow-600 mt-1">{result.severity_counts.medium}</p>
          </div>
          <div className="text-center p-4 rounded-lg bg-blue-50">
            <p className="text-sm text-gray-600">Low</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">{result.severity_counts.low}</p>
          </div>
        </div>
      </div>

      {/* 推奨事項 */}
      {summary && summary.recommendations && summary.recommendations.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">推奨事項</h3>
          <ul className="space-y-2">
            {summary.recommendations.map((rec: string, index: number) => (
              <li key={index} className="text-gray-700">
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* フィルター */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              深刻度でフィルター
            </label>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">すべて</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              コンポーネント名で検索
            </label>
            <input
              type="text"
              value={filterComponent}
              onChange={(e) => setFilterComponent(e.target.value)}
              placeholder="コンポーネント名を入力..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* 脆弱性リスト */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800">
            検出された脆弱性 ({filteredVulnerabilities.length}件)
          </h3>
        </div>
        {filteredVulnerabilities.length === 0 ? (
          <div className="p-8 text-center text-gray-600">
            {result.vulnerabilities.length === 0 
              ? '脆弱性は検出されませんでした 🎉' 
              : 'フィルター条件に一致する脆弱性はありません'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    CVE ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    深刻度
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    コンポーネント
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    バージョン
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    説明
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    公開日
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredVulnerabilities.map((vuln, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <a
                        href={`https://nvd.nist.gov/vuln/detail/${vuln.cve_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline font-medium"
                      >
                        {vuln.cve_id}
                      </a>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${getSeverityColor(vuln.severity)}`}>
                        {vuln.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {vuln.component_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {vuln.component_version}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700 max-w-md">
                      <div className="line-clamp-2">
                        {vuln.description || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {vuln.published_date ? new Date(vuln.published_date).toLocaleDateString('ja-JP') : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanResult;
