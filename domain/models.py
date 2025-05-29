"""
Domain Models สำหรับระบบแปลง Activity Diagram เป็น Timed Automata
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET


@dataclass
class NodeInfo:
    """ข้อมูลของ Node ใน Activity Diagram"""
    node_id: str
    name: str
    node_type: str
    
    def clean_name(self) -> str:
        """ทำความสะอาดชื่อ node เพื่อใช้ในการประกาศตัวแปร"""
        return (self.name.split(",")[0].strip()
                .replace(" ", "_")
                .replace("-", "_")
                .replace(".", "_")
                .replace("?", ""))


@dataclass
class EdgeInfo:
    """ข้อมูลของ Edge ใน Activity Diagram"""
    source_id: str
    target_id: str
    label: str = ""
    
    def has_condition(self) -> bool:
        """ตรวจสอบว่า edge มีเงื่อนไขหรือไม่"""
        return "=" in self.label
    
    def get_condition_value(self) -> Optional[str]:
        """ดึงค่าเงื่อนไขจาก label"""
        if self.has_condition():
            return self.label.strip("[]").split("=")[1].strip().lower()
        return None


@dataclass
class Position:
    """ตำแหน่งของ element ใน Timed Automata"""
    x: int
    y: int
    
    def offset(self, dx: int, dy: int) -> 'Position':
        """สร้าง Position ใหม่ที่เลื่อนจากตำแหน่งปัจจุบัน"""
        return Position(self.x + dx, self.y + dy)


@dataclass
class Location:
    """Location ใน Template"""
    id: str
    name: str
    position: Position
    is_initial: bool = False
    is_urgent: bool = False
    invariant: Optional[str] = None
    
    def to_xml_element(self) -> ET.Element:
        """แปลงเป็น XML Element"""
        location = ET.Element("location", 
                            id=self.id, 
                            x=str(self.position.x), 
                            y=str(self.position.y))
        
        # เพิ่ม name
        name_elem = ET.SubElement(location, "name", 
                                x=str(self.position.x - 50), 
                                y=str(self.position.y - 30))
        name_elem.text = self.name
        
        # เพิ่ม invariant ถ้ามี
        if self.invariant:
            inv_elem = ET.SubElement(location, "label", 
                                   kind="invariant",
                                   x=str(self.position.x), 
                                   y=str(self.position.y + 20))
            inv_elem.text = self.invariant
            
        return location


@dataclass
class TransitionLabel:
    """Label สำหรับ Transition"""
    kind: str  # guard, synchronisation, assignment, select
    text: str
    position: Position


@dataclass
class Transition:
    """Transition ใน Template"""
    id: str
    source_id: str
    target_id: str
    labels: List[TransitionLabel] = field(default_factory=list)
    
    def add_guard(self, condition: str, position: Position) -> None:
        """เพิ่ม guard condition"""
        self.labels.append(TransitionLabel("guard", condition, position))
    
    def add_synchronisation(self, sync: str, position: Position) -> None:
        """เพิ่ม synchronisation"""
        self.labels.append(TransitionLabel("synchronisation", sync, position))
    
    def add_assignment(self, assignment: str, position: Position) -> None:
        """เพิ่ม assignment"""
        self.labels.append(TransitionLabel("assignment", assignment, position))
    
    def add_select(self, select: str, position: Position) -> None:
        """เพิ่ม select"""
        self.labels.append(TransitionLabel("select", select, position))
    
    def to_xml_element(self) -> ET.Element:
        """แปลงเป็น XML Element"""
        transition = ET.Element("transition", id=self.id)
        ET.SubElement(transition, "source", ref=self.source_id)
        ET.SubElement(transition, "target", ref=self.target_id)
        
        # เพิ่ม labels
        for label in self.labels:
            label_elem = ET.SubElement(transition, "label", 
                                     kind=label.kind,
                                     x=str(label.position.x),
                                     y=str(label.position.y))
            label_elem.text = label.text
            
        return transition


@dataclass
class Template:
    """Template ใน Timed Automata"""
    name: str
    clock_name: str
    locations: Dict[str, Location] = field(default_factory=dict)
    transitions: List[Transition] = field(default_factory=list)
    initial_location_id: Optional[str] = None
    declarations: List[str] = field(default_factory=list)
    
    def add_location(self, location: Location) -> None:
        """เพิ่ม location"""
        self.locations[location.id] = location
        if location.is_initial:
            self.initial_location_id = location.id
    
    def add_transition(self, transition: Transition) -> None:
        """เพิ่ม transition"""
        self.transitions.append(transition)
    
    def get_location(self, location_id: str) -> Optional[Location]:
        """ดึง location ตาม ID"""
        return self.locations.get(location_id)
    
    def to_xml_element(self) -> ET.Element:
        """แปลงเป็น XML Element"""
        template = ET.Element("template")
        
        # เพิ่ม name
        name_elem = ET.SubElement(template, "name")
        name_elem.text = self.name
        
        # เพิ่ม declaration (clock + อื่นๆ)
        decl_elem = ET.SubElement(template, "declaration")
        all_declarations = [f"clock {self.clock_name};"] + self.declarations
        decl_elem.text = "\n".join(all_declarations) if all_declarations else f"clock {self.clock_name};"
        
        # เพิ่ม locations
        for location in self.locations.values():
            template.append(location.to_xml_element())
        
        # เพิ่ม init
        if self.initial_location_id:
            ET.SubElement(template, "init", ref=self.initial_location_id)
        
        # เพิ่ม transitions
        for transition in self.transitions:
            template.append(transition.to_xml_element())
            
        return template


@dataclass
class ConversionContext:
    """Context สำหรับการแปลง ใช้เก็บข้อมูลระหว่างการ process"""
    nodes: Dict[str, NodeInfo] = field(default_factory=dict)
    edges: List[EdgeInfo] = field(default_factory=list)
    templates: List[Template] = field(default_factory=list)
    declarations: List[str] = field(default_factory=list)
    edge_guards: Dict[Tuple[str, str], str] = field(default_factory=dict)
    decision_vars: Dict[str, str] = field(default_factory=dict)
    fork_channels: Dict[str, str] = field(default_factory=dict)
    join_nodes: Dict[str, str] = field(default_factory=dict)
    created_transitions: set = field(default_factory=set)
    current_y_offset: int = 100
    clock_counter: int = 0
    fork_counter: int = 0
    
    def get_next_clock_name(self) -> str:
        """ได้ชื่อ clock ถัดไป"""
        clock_name = "t" if self.clock_counter == 0 else f"t{self.clock_counter}"
        self.clock_counter += 1
        return clock_name
    
    def get_next_fork_channel(self) -> str:
        """ได้ชื่อ fork channel ถัดไป"""
        self.fork_counter += 1
        return f"fork{self.fork_counter}" 