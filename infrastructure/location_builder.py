"""
Location Builder Implementation สำหรับการสร้าง Locations
"""
from typing import Dict, Any, Tuple
from domain.interfaces import ILocationBuilder, IDeclarationManager
from domain.models import Location, Position, ConversionContext, Template


class LocationBuilder(ILocationBuilder):
    """Builder สำหรับการสร้าง Locations ใน Templates"""
    
    def __init__(self, context: ConversionContext, declaration_manager: IDeclarationManager):
        self._context = context
        self._declaration_manager = declaration_manager
        self._location_counter = 0
        self._y_offset = 100
    
    def add_location(self, template: Template, location_id: str, node_name: str, node_type: str) -> None:
        """เพิ่ม location เข้าไปใน template (เหมือน Main_Beyone.py)"""
        if location_id in template.locations:
            return  # ไม่เพิ่มซ้ำ
        
        # คำนวณตำแหน่ง
        position = self._calculate_position(template, node_type)
        
        # ทำความสะอาดชื่อ location แบบ Main_Beyone.py
        clean_name = node_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
        
        # กำหนดชื่อ label ตาม type แบบ Main_Beyone.py
        if node_type in ("uml:DecisionNode", "DecisionNode"):
            label_name = f"{clean_name}_Decision"
        elif node_type in ("uml:ForkNode", "ForkNode"):
            label_name = f"{clean_name}_Fork"
        elif node_type in ("uml:JoinNode", "JoinNode"):
            # ตรวจสอบว่า clean_name มี _Join อยู่แล้วหรือไม่
            if clean_name.endswith("_Join"):
                label_name = clean_name  # ไม่เพิ่ม _Join ซ้ำ
            else:
                label_name = f"{clean_name}_Join"
        else:
            label_name = clean_name
        
        # สร้าง location
        location = Location(
            id=location_id,
            name=label_name,
            position=position,
            is_initial=(node_type in ("uml:InitialNode", "InitialNode"))
        )
        
        template.add_location(location)
        
        # เพิ่ม declarations สำหรับ decision และ fork nodes
        if node_type in ("uml:DecisionNode", "DecisionNode"):
            if clean_name not in [decl.split()[1].rstrip(';') for decl in self._context.declarations if decl.startswith('int ')]:
                self._declaration_manager.add_declaration(f"int {clean_name};")
        elif node_type in ("uml:ForkNode", "ForkNode"):
            channel_name = f"fork_{clean_name}"
            done_var_name = f"Done_{clean_name}_Fork"
            self._declaration_manager.add_declaration(f"broadcast chan {channel_name};")
            self._declaration_manager.add_declaration(f"bool {done_var_name};")
    
    def calculate_position(self, template: Dict[str, Any], node_type: str) -> Tuple[int, int]:
        """คำนวณตำแหน่งของ location"""
        x = 100 + (self._location_counter % 5) * 200
        y = self._y_offset + (self._location_counter // 5) * 150
        self._location_counter += 1
        return (x, y)
    
    def _calculate_position(self, template: Dict[str, Any], node_type: str) -> Position:
        """คำนวณตำแหน่งของ location"""
        x = 100 + (self._location_counter % 5) * 200
        y = self._y_offset + (self._location_counter // 5) * 150
        self._location_counter += 1
        return Position(x, y)
    
    def _handle_special_node_types(self, template: Any, location: Location, 
                                 node_name: str, node_type: str) -> None:
        """จัดการ node types พิเศษ"""
        if node_type in ["uml:InitialNode", "InitialNode"]:
            template.initial_location_id = location.id
        
        elif node_type in ["uml:ForkNode", "ForkNode"]:
            # เพิ่ม Done variable สำหรับ fork (เหมือน Main_Beyone.py)
            clean_name = node_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
            done_var = f"Done_{clean_name}_Fork"
            self._declaration_manager.add_declaration(f"bool {done_var};")
            
            # เพิ่ม broadcast channel
            fork_channel = f"fork_{clean_name}"
            self._declaration_manager.add_declaration(f"broadcast chan {fork_channel};")
        
        elif node_type in ["uml:DecisionNode", "DecisionNode"]:
            # Decision variables จะถูกสร้างใน application converter แล้ว 
            # ไม่ต้องสร้างซ้ำที่นี่
            pass
        
        elif node_type in ["uml:ActivityFinalNode", "ActivityFinalNode", "FinalNode"]:
            location.is_urgent = True 