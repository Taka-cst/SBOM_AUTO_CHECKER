"""SBOM Parser Service - CycloneDX and SPDX format support"""
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SBOMParserException(Exception):
    """SBOM解析エラー"""
    pass


class Component:
    """コンポーネント情報"""
    def __init__(self, name: str, version: str, purl: Optional[str] = None, 
                 component_type: Optional[str] = None):
        self.name = name
        self.version = version
        self.purl = purl  # Package URL
        self.component_type = component_type


class SBOMParser:
    """SBOM Parser Base Class"""
    
    @staticmethod
    def parse(content: bytes, filename: str) -> Dict[str, Any]:
        """
        SBOMファイルを解析してコンポーネントを抽出
        
        Args:
            content: ファイル内容(bytes)
            filename: ファイル名
            
        Returns:
            解析結果の辞書
            {
                "format": "cyclonedx" or "spdx",
                "version": "1.4",
                "components": [Component, ...],
                "metadata": {...}
            }
        """
        try:
            # JSON形式を試す
            if filename.endswith('.json'):
                return SBOMParser._parse_json(content)
            # XML形式を試す
            elif filename.endswith('.xml'):
                return SBOMParser._parse_xml(content)
            else:
                raise SBOMParserException(f"Unsupported file format: {filename}")
                
        except Exception as e:
            logger.error(f"SBOM parsing failed: {str(e)}", exc_info=True)
            raise SBOMParserException(f"Failed to parse SBOM: {str(e)}")
    
    @staticmethod
    def _parse_json(content: bytes) -> Dict[str, Any]:
        """JSON形式のSBOMを解析"""
        try:
            data = json.loads(content.decode('utf-8'))
            
            # CycloneDX JSON
            if "bomFormat" in data and data["bomFormat"] == "CycloneDX":
                return CycloneDXParser.parse_json(data)
            
            # SPDX JSON
            elif "spdxVersion" in data:
                return SPDXParser.parse_json(data)
            
            else:
                raise SBOMParserException("Unknown SBOM format in JSON")
                
        except json.JSONDecodeError as e:
            raise SBOMParserException(f"Invalid JSON: {str(e)}")
    
    @staticmethod
    def _parse_xml(content: bytes) -> Dict[str, Any]:
        """XML形式のSBOMを解析"""
        try:
            root = ET.fromstring(content.decode('utf-8'))
            
            # CycloneDX XML
            if 'cyclonedx' in root.tag.lower():
                return CycloneDXParser.parse_xml(root)
            
            # SPDX XML
            elif 'spdx' in root.tag.lower():
                return SPDXParser.parse_xml(root)
            
            else:
                raise SBOMParserException("Unknown SBOM format in XML")
                
        except ET.ParseError as e:
            raise SBOMParserException(f"Invalid XML: {str(e)}")


class CycloneDXParser:
    """CycloneDX形式のパーサー"""
    
    @staticmethod
    def parse_json(data: Dict[str, Any]) -> Dict[str, Any]:
        """CycloneDX JSON形式を解析"""
        components = []
        
        # コンポーネントリストの抽出
        for comp in data.get("components", []):
            component = Component(
                name=comp.get("name", "unknown"),
                version=comp.get("version", "unknown"),
                purl=comp.get("purl"),
                component_type=comp.get("type", "library")
            )
            components.append(component)
        
        # メタデータの抽出
        metadata = data.get("metadata", {})
        
        return {
            "format": "cyclonedx",
            "version": data.get("specVersion", "unknown"),
            "components": components,
            "metadata": {
                "timestamp": metadata.get("timestamp"),
                "tools": metadata.get("tools", []),
                "component": metadata.get("component", {})
            },
            "serial_number": data.get("serialNumber"),
            "raw_data": data
        }
    
    @staticmethod
    def parse_xml(root: ET.Element) -> Dict[str, Any]:
        """CycloneDX XML形式を解析"""
        components = []
        
        # 名前空間を取得
        ns = {'': 'http://cyclonedx.org/schema/bom/1.4'}
        
        # コンポーネントの抽出
        for comp in root.findall('.//components/component', ns):
            name_elem = comp.find('name', ns)
            version_elem = comp.find('version', ns)
            purl_elem = comp.find('purl', ns)
            
            component = Component(
                name=name_elem.text if name_elem is not None else "unknown",
                version=version_elem.text if version_elem is not None else "unknown",
                purl=purl_elem.text if purl_elem is not None else None,
                component_type=comp.get('type', 'library')
            )
            components.append(component)
        
        return {
            "format": "cyclonedx",
            "version": root.get("version", "unknown"),
            "components": components,
            "metadata": {},
            "serial_number": root.get("serialNumber"),
            "raw_data": {}
        }


class SPDXParser:
    """SPDX形式のパーサー"""
    
    @staticmethod
    def parse_json(data: Dict[str, Any]) -> Dict[str, Any]:
        """SPDX JSON形式を解析"""
        components = []
        
        # パッケージリストの抽出
        for pkg in data.get("packages", []):
            # SPDX形式ではバージョンがname内に含まれることが多い
            name = pkg.get("name", "unknown")
            version = pkg.get("versionInfo", "unknown")
            
            component = Component(
                name=name,
                version=version,
                purl=None,  # SPDXにはpurlがない場合が多い
                component_type="library"
            )
            components.append(component)
        
        return {
            "format": "spdx",
            "version": data.get("spdxVersion", "unknown"),
            "components": components,
            "metadata": {
                "created": data.get("creationInfo", {}).get("created"),
                "creators": data.get("creationInfo", {}).get("creators", []),
                "document_name": data.get("name")
            },
            "raw_data": data
        }
    
    @staticmethod
    def parse_xml(root: ET.Element) -> Dict[str, Any]:
        """SPDX XML形式を解析"""
        components = []
        
        # SPDX XML解析(簡易版)
        for pkg in root.findall('.//Package'):
            name_elem = pkg.find('name')
            version_elem = pkg.find('versionInfo')
            
            component = Component(
                name=name_elem.text if name_elem is not None else "unknown",
                version=version_elem.text if version_elem is not None else "unknown",
                purl=None,
                component_type="library"
            )
            components.append(component)
        
        return {
            "format": "spdx",
            "version": root.get("spdxVersion", "unknown"),
            "components": components,
            "metadata": {},
            "raw_data": {}
        }


def extract_components_from_sbom(sbom_data: Dict[str, Any]) -> List[Component]:
    """
    解析済みSBOMデータからコンポーネントリストを抽出
    
    Args:
        sbom_data: SBOMParser.parse()の戻り値
        
    Returns:
        コンポーネントリスト
    """
    return sbom_data.get("components", [])
