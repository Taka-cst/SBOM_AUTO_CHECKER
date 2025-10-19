import React, { useState, useEffect } from 'react'
import './App.css'
import { sbomApi } from './services/api'
import ScanResult from './components/ScanResult'

interface SBOMItem {
  id: string  // UUID
  file_name: string
  file_format: string
  uploaded_at: string
}

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [sbomList, setSbomList] = useState<SBOMItem[]>([])
  const [selectedSbomId, setSelectedSbomId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchSbomList()
  }, [])

  const fetchSbomList = async () => {
    try {
      setLoading(true)
      const response = await sbomApi.getAll()
      setSbomList(response.data.items || [])
    } catch (err) {
      console.error('Failed to fetch SBOM list:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0])
      setError(null)
      setUploadSuccess(false)
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('ファイルを選択してください')
      return
    }

    setUploading(true)
    setError(null)

    try {
      console.log('Uploading file:', file.name)
      const response = await sbomApi.upload(file)
      console.log('Upload response:', response)
      
      setUploadSuccess(true)
      setError(null)
      
      // SBOM一覧を更新
      fetchSbomList()
      
      // アップロード成功メッセージを表示
      if (response.data.is_duplicate) {
        const prevScan = response.data.previous_scan
        const scanInfo = prevScan 
          ? `\n\n前回のスキャン結果:\n- 脆弱性: ${prevScan.vulnerable_count}件\n- Critical: ${prevScan.critical_count}件\n- High: ${prevScan.high_count}件`
          : ''
        
        alert(`🔄 このSBOMは既にアップロード済みです\n\nファイル: ${file.name}\nSBOM ID: ${response.data.sbom_id}${scanInfo}\n\n最新の脆弱性データベースで再スキャンを開始しました!`)
      } else {
        alert(`✅ アップロード成功!\n\nファイル: ${file.name}\nSBOM ID: ${response.data.sbom_id}\n\nスキャンが開始されました。結果は数分後に表示されます。`)
      }
      
      // ファイルをリセット
      setFile(null)
      
    } catch (err: any) {
      console.error('Upload error:', err)
      const errorMessage = err.response?.data?.error?.message || err.message || 'アップロードに失敗しました'
      setError(errorMessage)
      alert(`❌ エラー: ${errorMessage}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-4">
        <h1 className="text-2xl font-bold">SBOM Vulnerability Checker</h1>
      </header>
      
      <main className="container mx-auto p-8">
        {selectedSbomId ? (
          <ScanResult 
            sbomId={selectedSbomId} 
            onClose={() => setSelectedSbomId(null)} 
          />
        ) : (
          <>
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4">SBOMファイルをアップロード</h2>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <input
                  type="file"
                  onChange={handleFileSelect}
                  accept=".json,.xml"
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer inline-block bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition"
                >
                  📁 ファイルを選択
                </label>
                
                {file && (
                  <div className="mt-4">
                    <div className="text-gray-600">
                      選択されたファイル: <span className="font-semibold">{file.name}</span>
                    </div>
                    <button
                      onClick={handleUpload}
                      disabled={uploading}
                      className={`mt-4 px-8 py-3 rounded-lg font-semibold text-white transition ${
                        uploading 
                          ? 'bg-gray-400 cursor-not-allowed' 
                          : 'bg-green-500 hover:bg-green-600'
                      }`}
                    >
                      {uploading ? '⏳ アップロード中...' : '🚀 アップロードして診断開始'}
                    </button>
                  </div>
                )}
                
                {error && (
                  <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                    ❌ {error}
                  </div>
                )}
                
                {uploadSuccess && (
                  <div className="mt-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
                    ✅ アップロード成功! スキャンを開始しました。
                  </div>
                )}
              </div>

              <div className="mt-8">
                <h3 className="text-lg font-semibold mb-2">対応形式</h3>
                <ul className="list-disc list-inside text-gray-600">
                  <li>CycloneDX (JSON/XML)</li>
                  <li>SPDX (JSON/XML)</li>
                </ul>
              </div>
            </div>

            <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4">アップロード済みSBOM</h2>
              {loading ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <p className="mt-4 text-gray-600">読み込み中...</p>
                </div>
              ) : sbomList.length === 0 ? (
                <p className="text-gray-600 text-center py-8">まだSBOMがアップロードされていません</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ファイル名</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">形式</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">アップロード日時</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {sbomList.map((sbom) => (
                        <tr key={sbom.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{sbom.id}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{sbom.file_name}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{sbom.file_format}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {new Date(sbom.uploaded_at).toLocaleString('ja-JP')}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <button
                              onClick={() => setSelectedSbomId(sbom.id)}
                              className="text-blue-600 hover:text-blue-800 font-medium mr-4"
                            >
                              結果を表示
                            </button>
                            <button
                              onClick={async () => {
                                if (confirm(`${sbom.file_name}を削除しますか?`)) {
                                  try {
                                    await sbomApi.delete(sbom.id)
                                    fetchSbomList()
                                  } catch (err) {
                                    alert('削除に失敗しました')
                                  }
                                }
                              }}
                              className="text-red-600 hover:text-red-800 font-medium"
                            >
                              削除
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default App
