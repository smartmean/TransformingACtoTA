"""
Template Manager Implementation สำหรับการจัดการ Templates
"""
from typing import Dict, List, Any
from domain.interfaces import ITemplateManager
from domain.models import Template, ConversionContext


class TemplateManager(ITemplateManager):
    """Manager สำหรับการจัดการ Templates"""
    
    def __init__(self, context: ConversionContext):
        self._templates: Dict[str, Template] = {}
        self._context = context
    
    def create_template(self, name: str) -> Template:
        """สร้าง template ใหม่ (เหมือน Main_Beyone.py) รวมถึง nested templates"""
        # สร้าง clock name แบบ Main_Beyone.py: t, t1, t2, t3, t1_1, t1_2, etc.
        if name == "Template":
            clock_name = "t"
        elif name == "Template1":
            clock_name = "t1"
        elif name == "Template2":
            clock_name = "t2"
        elif name == "Template3":
            clock_name = "t3"
        elif "_" in name:  # Nested templates like Template1_1, Template1_2
            # For nested templates, use format like t1_1, t1_2
            parts = name.split("_")
            if len(parts) == 2:
                parent_num = parts[0].replace("Template", "")
                child_num = parts[1]
                clock_name = f"t{parent_num}_{child_num}"
            else:
                clock_name = f"t{len(self._context.templates)}"
        else:
            # Fallback for other template names
            clock_name = f"t{len(self._context.templates)}"
        
        template = Template(
            name=name,
            clock_name=clock_name
        )
        
        return template
    
    def get_template(self, name: str) -> Template:
        """ดึง template ตามชื่อ"""
        if name not in self._templates:
            raise ValueError(f"Template '{name}' not found")
        return self._templates[name]
    
    def get_all_templates(self) -> List[Template]:
        """ดึง templates ทั้งหมด"""
        return list(self._templates.values())
    
    def template_exists(self, name: str) -> bool:
        """ตรวจสอบว่า template มีอยู่หรือไม่"""
        return name in self._templates
    
    def clear_templates(self) -> None:
        """ลบ templates ทั้งหมด"""
        self._templates.clear() 