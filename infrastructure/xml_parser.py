"""
XML Parser Implementation สำหรับการ parse Activity Diagram
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Any
from domain.interfaces import IXMLParser
from domain.models import NodeInfo, EdgeInfo


class ActivityDiagramParser(IXMLParser):
    """Parser สำหรับ Activity Diagram XML"""
    
    def parse_activity_diagram(self, xml_content: str) -> Tuple[List[NodeInfo], List[EdgeInfo]]:
        """Parse Activity Diagram XML และคืนข้อมูลที่จำเป็น"""
        try:
            root = ET.fromstring(xml_content)
            
            nodes_dict = self._parse_nodes(root)
            edges = self._parse_edges(root)
            
            # Convert dict to list
            nodes = list(nodes_dict.values())
            
            return nodes, edges
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
    
    def extract_nodes(self, root: ET.Element) -> Dict[str, NodeInfo]:
        """แยกข้อมูล nodes จาก XML"""
        return self._parse_nodes(root)
    
    def extract_edges(self, root: ET.Element) -> List[EdgeInfo]:
        """แยกข้อมูล edges จาก XML"""
        return self._parse_edges(root)
    
    def _parse_nodes(self, root: ET.Element) -> Dict[str, NodeInfo]:
        """Parse nodes จาก XML root"""
        nodes = {}
        
        for node in root.findall(".//{*}node"):
            node_id = node.get("{http://www.omg.org/spec/XMI/20131001}id")
            if not node_id:
                continue
                
            node_name = node.get("name", "unnamed")
            node_type = node.get("{http://www.omg.org/spec/XMI/20131001}type", 
                               node.tag.split("}")[-1])
            
            nodes[node_id] = NodeInfo(
                node_id=node_id,
                name=node_name,
                node_type=node_type
            )
        
        return nodes
    
    def _parse_edges(self, root: ET.Element) -> List[EdgeInfo]:
        """Parse edges จาก XML root"""
        edges = []
        
        for edge in root.findall(".//{*}edge"):
            source_id = edge.get("source")
            target_id = edge.get("target")
            label = edge.get("name", "")
            
            if source_id and target_id:
                edges.append(EdgeInfo(
                    source_id=source_id,
                    target_id=target_id,
                    label=label
                ))
        
        return edges 