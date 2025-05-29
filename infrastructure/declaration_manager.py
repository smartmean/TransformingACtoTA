"""
Declaration Manager Implementation สำหรับการจัดการ Declarations
"""
from typing import List, Set
from domain.interfaces import IDeclarationManager


class DeclarationManager(IDeclarationManager):
    """Manager สำหรับ declarations ใน UPPAAL template ตามหลัก OOP"""
    
    def __init__(self):
        self._declarations: Set[str] = set()
        self._template_done_vars: Set[str] = set()
        
    def add_declaration(self, declaration: str) -> None:
        """เพิ่ม declaration โดยใช้ Set เพื่อป้องกันการซ้ำ"""
        if declaration and declaration.strip():
            self._declarations.add(declaration.strip())
    
    def get_declarations(self) -> List[str]:
        """ดึง declarations ทั้งหมด รวมทั้ง Done variables ตามหลัก OOP"""
        all_declarations = set(self._declarations)
        
        # เพิ่ม template Done variables ตาม Repository Pattern
        all_declarations.update(self._get_template_done_variables())
        
        # เพิ่ม global clock ตาม OOP best practices
        all_declarations.add("clock total_time=0;")
        
        return sorted(list(all_declarations))
    
    def add_template_done_variable(self, template_name: str) -> None:
        """เพิ่ม Done variable สำหรับ template ตามหลัก Open/Closed Principle"""
        if template_name and template_name != "Template":  # ไม่ต้อง Done variable สำหรับ main template
            done_var = f"bool Done_{template_name};"
            self._template_done_vars.add(done_var)
    
    def _get_template_done_variables(self) -> Set[str]:
        """สร้าง template Done variables ตามหลัก Strategy Pattern"""
        done_vars = set(self._template_done_vars)
        
        # เพิ่ม standard Done variables สำหรับ templates ที่จำเป็น
        standard_templates = ["Template1", "Template1_1", "Template1_2", "Template2"]
        for template in standard_templates:
            done_vars.add(f"bool Done_{template};")
        
        return done_vars
    
    def clear_declarations(self) -> None:
        """ล้าง declarations ทั้งหมด (สำหรับ testing)"""
        self._declarations.clear()
        self._template_done_vars.clear()
    
    def add_clock_declaration(self, clock_name: str) -> None:
        """เพิ่ม clock declaration"""
        clock_decl = f"clock {clock_name};"
        self.add_declaration(clock_decl)
    
    def add_channel_declaration(self, channel_name: str, is_broadcast: bool = False) -> None:
        """เพิ่ม channel declaration"""
        if is_broadcast:
            declaration = f"broadcast chan {channel_name};"
        else:
            declaration = f"chan {channel_name};"
        self.add_declaration(declaration)
    
    def add_bool_declaration(self, var_name: str) -> None:
        """เพิ่ม boolean variable declaration"""
        bool_decl = f"bool {var_name};"
        self.add_declaration(bool_decl)
    
    def add_decision_variable(self, var_name: str) -> None:
        """เพิ่ม decision variable declaration"""
        self.add_bool_declaration(var_name)
    
    def add_int_declaration(self, var_name: str, initial_value: int = 0) -> None:
        """เพิ่ม integer variable declaration"""
        declaration = f"int {var_name};"
        self.add_declaration(declaration)
    
    def add_boolean_declaration(self, var_name: str) -> None:
        """เพิ่ม boolean variable declaration (alias สำหรับ add_bool_declaration)"""
        self.add_bool_declaration(var_name)
    
    def has_declaration(self, declaration: str) -> bool:
        """ตรวจสอบว่ามี declaration อยู่แล้วหรือไม่"""
        return declaration in self._declarations 