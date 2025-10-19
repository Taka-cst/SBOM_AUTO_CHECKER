-- データベース初期化スクリプト

-- Extensionの有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- インデックスの作成
CREATE INDEX IF NOT EXISTS idx_sboms_file_hash ON sboms(file_hash);
CREATE INDEX IF NOT EXISTS idx_sboms_uploaded_at ON sboms(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_cve_id ON vulnerabilities(cve_id);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_severity ON vulnerabilities(severity);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_modified_date ON vulnerabilities(modified_date DESC);
CREATE INDEX IF NOT EXISTS idx_scan_results_sbom_id ON scan_results(sbom_id);
CREATE INDEX IF NOT EXISTS idx_scan_results_scan_date ON scan_results(scan_date DESC);
CREATE INDEX IF NOT EXISTS idx_scan_vulnerabilities_scan_result_id ON scan_vulnerabilities(scan_result_id);
CREATE INDEX IF NOT EXISTS idx_scan_vulnerabilities_vulnerability_id ON scan_vulnerabilities(vulnerability_id);

-- 初期データの挿入(サンプル)
-- 必要に応じて追加
