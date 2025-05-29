"""
Node Processors Implementation ใช้ Strategy Pattern
"""
from abc import ABC
from typing import Dict, Any
from domain.interfaces import INodeProcessor
from domain.models import NodeInfo, Location, Position, ConversionContext


class BaseNodeProcessor(INodeProcessor):
    """Base class สำหรับ Node Processors"""
    
    def __init__(self, context: ConversionContext):
        self._context = context


class InitialNodeProcessor(BaseNodeProcessor):
    """Processor สำหรับ Initial Node"""
    
    def can_process(self, node_type: str) -> bool:
        return node_type in ("uml:InitialNode", "InitialNode")
    
    def process_node(self, node_id: str, node_name: str, node_type: str, 
                    context: Dict[str, Any]) -> Dict[str, Any]:
        clean_name = NodeInfo(node_id=node_id, name=node_name, node_type=node_type).clean_name()
        label_name = clean_name
        
        # คำนวณตำแหน่ง
        x = context.get('x_offset', 0)
        y = self._context.current_y_offset
        
        # สร้าง location
        location = Location(
            id=node_id,
            name=label_name,
            position=Position(x, y),
            is_initial=True
        )
        
        return {
            'location': location,
            'is_initial': True,
            'declarations': []
        }


class DecisionNodeProcessor(BaseNodeProcessor):
    """Processor สำหรับ Decision Node"""
    
    def can_process(self, node_type: str) -> bool:
        return node_type in ("uml:DecisionNode", "DecisionNode")
    
    def process_node(self, node_id: str, node_name: str, node_type: str, 
                    context: Dict[str, Any]) -> Dict[str, Any]:
        clean_name = NodeInfo(node_id=node_id, name=node_name, node_type=node_type).clean_name()
        label_name = f"{clean_name}_Decision"
        
        # เก็บ decision variable ตามรูปแบบที่ถูกต้อง
        decision_var_name = f"Is_{clean_name}_Decision"
        self._context.decision_vars[node_id] = decision_var_name
        
        # คำนวณตำแหน่ง
        x = context.get('x_offset', 0)
        y = self._context.current_y_offset + 100
        self._context.current_y_offset = y
        
        # สร้าง location
        location = Location(
            id=node_id,
            name=label_name,
            position=Position(x, y)
        )
        
        return {
            'location': location,
            'is_initial': False,
            'declarations': [f"int {decision_var_name};"]
        }


class ForkNodeProcessor(BaseNodeProcessor):
    """Processor สำหรับ Fork Node"""
    
    def can_process(self, node_type: str) -> bool:
        return node_type in ("uml:ForkNode", "ForkNode")
    
    def process_node(self, node_id: str, node_name: str, node_type: str, 
                    context: Dict[str, Any]) -> Dict[str, Any]:
        clean_name = NodeInfo(node_id=node_id, name=node_name, node_type=node_type).clean_name()
        label_name = f"{clean_name}_Fork"
        
        # สร้าง channel และ done variable
        channel_name = f"fork_{clean_name}"
        done_var_name = f"Done_{clean_name}_Fork"
        
        # เก็บ fork channel
        self._context.fork_channels[node_id] = channel_name
        
        # คำนวณตำแหน่ง
        x = context.get('x_offset', 0)
        y = self._context.current_y_offset + 100
        self._context.current_y_offset = y
        
        # สร้าง location
        location = Location(
            id=node_id,
            name=label_name,
            position=Position(x, y)
        )
        
        return {
            'location': location,
            'is_initial': False,
            'declarations': [
                f"broadcast chan {channel_name};",
                f"bool {done_var_name};"
            ]
        }


class JoinNodeProcessor(BaseNodeProcessor):
    """Processor สำหรับ Join Node"""
    
    def can_process(self, node_type: str) -> bool:
        return node_type in ("uml:JoinNode", "JoinNode")
    
    def process_node(self, node_id: str, node_name: str, node_type: str, 
                    context: Dict[str, Any]) -> Dict[str, Any]:
        clean_name = NodeInfo(node_id=node_id, name=node_name, node_type=node_type).clean_name()
        label_name = f"{clean_name}_Join"
        
        # เก็บ join node
        template_name = context.get('template_name', 'Template')
        self._context.join_nodes[node_id] = template_name
        
        # คำนวณตำแหน่ง
        x = context.get('x_offset', 0)
        y = self._context.current_y_offset + 100
        self._context.current_y_offset = y
        
        # สร้าง location
        location = Location(
            id=node_id,
            name=label_name,
            position=Position(x, y)
        )
        
        return {
            'location': location,
            'is_initial': False,
            'declarations': []
        }


class OpaqueActionProcessor(BaseNodeProcessor):
    """Processor สำหรับ Opaque Action"""
    
    def can_process(self, node_type: str) -> bool:
        return node_type in ("uml:OpaqueAction", "OpaqueAction")
    
    def process_node(self, node_id: str, node_name: str, node_type: str, 
                    context: Dict[str, Any]) -> Dict[str, Any]:
        clean_name = NodeInfo(node_id=node_id, name=node_name, node_type=node_type).clean_name()
        label_name = clean_name
        
        # คำนวณตำแหน่ง - ต่างจาก decision node
        x = context.get('x_offset', 0)
        y = self._context.current_y_offset
        
        # ตรวจสอบว่าอยู่หลัง decision node หรือไม่
        is_after_decision = any(
            target_id == node_id for source_id, target_id in 
            [(edge.source_id, edge.target_id) for edge in self._context.edges]
            if source_id in self._context.decision_vars
        )
        
        if is_after_decision:
            y += 150
        
        # สร้าง location
        location = Location(
            id=node_id,
            name=label_name,
            position=Position(x, y)
        )
        
        return {
            'location': location,
            'is_initial': False,
            'declarations': []
        }


class NodeProcessorFactory:
    """Factory สำหรับสร้าง Node Processors"""
    
    def __init__(self, context: ConversionContext):
        self._context = context
        self._processors = [
            InitialNodeProcessor(context),
            DecisionNodeProcessor(context),
            ForkNodeProcessor(context),
            JoinNodeProcessor(context),
            OpaqueActionProcessor(context)
        ]
    
    def get_processor(self, node_type: str) -> INodeProcessor:
        """ดึง processor ที่เหมาะสมสำหรับ node type"""
        for processor in self._processors:
            if processor.can_process(node_type):
                return processor
        
        # Default processor
        return OpaqueActionProcessor(self._context) 