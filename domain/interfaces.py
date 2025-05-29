"""
Interfaces และ Abstract Classes สำหรับระบบแปลง Activity Diagram เป็น Timed Automata
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
import xml.etree.ElementTree as ET


class IXMLParser(ABC):
    """Interface สำหรับการ parse XML"""
    
    @abstractmethod
    def parse_activity_diagram(self, xml_content: str) -> Dict[str, Any]:
        """Parse Activity Diagram XML และคืนข้อมูลที่จำเป็น"""
        pass
    
    @abstractmethod
    def extract_nodes(self, root: ET.Element) -> Dict[str, str]:
        """แยกข้อมูล nodes จาก XML"""
        pass
    
    @abstractmethod
    def extract_edges(self, root: ET.Element) -> List[Tuple[str, str, str]]:
        """แยกข้อมูล edges จาก XML"""
        pass


class ITemplateManager(ABC):
    """Interface สำหรับการจัดการ Templates"""
    
    @abstractmethod
    def create_template(self, name: str) -> Dict[str, Any]:
        """สร้าง template ใหม่"""
        pass
    
    @abstractmethod
    def get_template(self, name: str) -> Dict[str, Any]:
        """ดึง template ตามชื่อ"""
        pass
    
    @abstractmethod
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """ดึง templates ทั้งหมด"""
        pass


class ILocationBuilder(ABC):
    """Interface สำหรับการสร้าง Locations"""
    
    @abstractmethod
    def add_location(self, template: Dict[str, Any], node_id: str, 
                    node_name: str, node_type: str) -> None:
        """เพิ่ม location เข้าไปใน template"""
        pass
    
    @abstractmethod
    def calculate_position(self, template: Dict[str, Any], node_type: str) -> Tuple[int, int]:
        """คำนวณตำแหน่งของ location"""
        pass


class ITransitionBuilder(ABC):
    """Interface สำหรับการสร้าง Transitions"""
    
    @abstractmethod
    def add_transition(self, template: Dict[str, Any], source_id: str, 
                      target_id: str, edge_info: Dict[str, Any]) -> None:
        """เพิ่ม transition ระหว่าง locations"""
        pass
    
    @abstractmethod
    def add_transition_labels(self, transition: ET.Element, 
                            label_info: Dict[str, str]) -> None:
        """เพิ่ม labels ให้กับ transition"""
        pass


class IDeclarationManager(ABC):
    """Interface สำหรับการจัดการ Declarations ตามหลัก OOP"""
    
    @abstractmethod
    def add_declaration(self, declaration: str) -> None:
        """เพิ่ม declaration"""
        pass
    
    @abstractmethod
    def get_declarations(self) -> List[str]:
        """ดึง declarations ทั้งหมด"""
        pass
    
    @abstractmethod
    def add_template_done_variable(self, template_name: str) -> None:
        """เพิ่ม Done variable สำหรับ template ตามหลัก Open/Closed Principle"""
        pass
    
    @abstractmethod
    def clear_declarations(self) -> None:
        """ล้าง declarations ทั้งหมด"""
        pass
    
    @abstractmethod
    def add_clock_declaration(self, clock_name: str) -> None:
        """เพิ่ม clock declaration"""
        pass
    
    @abstractmethod
    def add_bool_declaration(self, var_name: str) -> None:
        """เพิ่ม boolean variable declaration"""
        pass
    
    @abstractmethod
    def add_decision_variable(self, var_name: str) -> None:
        """เพิ่ม decision variable declaration"""
        pass
    
    @abstractmethod
    def has_declaration(self, declaration: str) -> bool:
        """ตรวจสอบว่ามี declaration อยู่แล้วหรือไม่"""
        pass


class IXMLGenerator(ABC):
    """Interface สำหรับการสร้าง XML output"""
    
    @abstractmethod
    def generate_xml(self, templates: List[Dict[str, Any]], 
                    declarations: List[str]) -> str:
        """สร้าง Timed Automata XML ผลลัพธ์"""
        pass
    
    @abstractmethod
    def format_xml(self, xml_element: ET.Element) -> str:
        """จัดรูปแบบ XML"""
        pass


class INodeProcessor(ABC):
    """Interface สำหรับการ process แต่ละประเภทของ node"""
    
    @abstractmethod
    def can_process(self, node_type: str) -> bool:
        """ตรวจสอบว่า processor นี้สามารถจัดการ node type นี้ได้หรือไม่"""
        pass
    
    @abstractmethod
    def process_node(self, node_id: str, node_name: str, node_type: str, 
                    context: Dict[str, Any]) -> Dict[str, Any]:
        """ประมวลผล node และคืนข้อมูลที่ต้องการ"""
        pass


class IConverter(ABC):
    """Interface หลักสำหรับการแปลง Activity Diagram เป็น Timed Automata"""
    
    @abstractmethod
    def convert(self, activity_xml: str) -> str:
        """แปลง Activity Diagram XML เป็น Timed Automata XML"""
        pass 