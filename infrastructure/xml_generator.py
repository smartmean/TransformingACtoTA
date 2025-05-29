"""
XML Generator Implementation สำหรับการสร้าง UPPAAL XML
"""
import sys
import os
# เพิ่ม parent directory เข้า Python path สำหรับ standalone run
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xml.etree.ElementTree as ET
from typing import List, Dict
from domain.interfaces import IXMLGenerator
from domain.models import Template


class XMLGenerator(IXMLGenerator):
    """Generator สำหรับการสร้าง Timed Automata XML output"""
    
    def generate_xml(self, templates: List[Template], declarations: List[str]) -> str:
        """สร้าง UPPAAL XML สมบูรณ์ (เหมือน Main_Beyone.py)"""
        # สร้าง root element
        nta = ET.Element("nta")
        
        # เพิ่ม global declarations (เรียงใหม่แบบ Main_Beyone.py)
        sorted_declarations = self._sort_declarations_like_main_beyone(declarations)
        decl_elem = ET.SubElement(nta, "declaration")
        decl_elem.text = "\n".join(sorted_declarations)
        
        # เพิ่ม templates โดยใช้ Template.to_xml_element()
        for template in templates:
            template_elem = template.to_xml_element()
            nta.append(template_elem)
        
        # เพิ่ม system declarations แบบ Main_Beyone.py
        system_elem = ET.SubElement(nta, "system")
        system_text = []
        for i, template in enumerate(templates, 1):
            system_text.append(f"T{i} = {template.name}();")
        system_text.append("system " + ", ".join(f"T{i}" for i in range(1, len(templates) + 1)) + ";")
        system_elem.text = "\n".join(system_text)
        
        # เพิ่ม queries แบบ Main_Beyone.py
        queries_elem = ET.SubElement(nta, "queries")
        query_elem = ET.SubElement(queries_elem, "query")
        ET.SubElement(query_elem, "formula").text = "A[] not deadlock"
        ET.SubElement(query_elem, "comment").text = "Check for deadlocks"
        
        # Format XML ให้สวยงาม
        self._indent_xml(nta)
        
        # สร้าง XML string และแก้ไข short tags
        xml_str = ET.tostring(nta, encoding="utf-8", method="xml").decode()
        
        # แก้ไข abbreviated tags ให้เป็น full form
        xml_str = self._fix_abbreviated_tags(xml_str)
        
        header = '<?xml version="1.0" encoding="utf-8"?>\n'
        doctype = '<!DOCTYPE nta PUBLIC \'-//Uppaal Team//DTD Flat System 1.6//EN\' \'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd\'>\n'
        
        return header + doctype + xml_str

    def _sort_declarations_like_main_beyone(self, declarations: List[str]) -> List[str]:
        """เรียงลำดับ declarations แบบ Main_Beyone.py"""
        bool_decls = []
        chan_decls = []
        clock_decls = []
        int_decls = []
        
        for decl in declarations:
            if decl.startswith("bool"):
                bool_decls.append(decl)
            elif decl.startswith("broadcast chan"):
                chan_decls.append(decl)
            elif decl.startswith("clock"):
                clock_decls.append(decl)
            elif decl.startswith("int"):
                int_decls.append(decl)
        
        # Main_Beyone.py order: bool, chan, clock, int
        return bool_decls + chan_decls + clock_decls + int_decls
    
    def format_xml(self, xml_element: ET.Element) -> str:
        """จัดรูปแบบ XML แบบ Main_Beyone.py"""
        # เพิ่ม DOCTYPE declaration
        xml_str = '<!DOCTYPE nta PUBLIC \'-//Uppaal Team//DTD Flat System 1.6//EN\' \'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd\'>\n'
        
        # จัดรูปแบบ XML แบบ indentation (เหมือน Main_Beyone.py)
        self._indent_xml(xml_element)
        xml_str += ET.tostring(xml_element, encoding='unicode')
        
        return xml_str
    
    def _indent_xml(self, elem, level=0):
        """จัดรูปแบบ XML ให้มี indentation (เหมือน Main_Beyone.py)"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def _generate_location_xml(self, location) -> ET.Element:
        """สร้าง XML element สำหรับ location"""
        return location.to_xml_element()
    
    def _generate_transition_xml(self, transition) -> ET.Element:
        """สร้าง XML element สำหรับ transition"""
        return transition.to_xml_element()
    
    def generate_uppaal_xml(self, templates: List[Template], declarations: List[str]) -> str:
        """สร้าง UPPAAL XML (alias สำหรับ generate_xml)"""
        return self.generate_xml(templates, declarations)
    
    def _fix_abbreviated_tags(self, xml_str: str) -> str:
        """แก้ไข abbreviated XML tags ให้เป็น full form"""
        output = xml_str
        output = output.replace("<n>", "<name>")
        output = output.replace("</n>", "</name>")
        output = output.replace("<s>", "<system>")
        output = output.replace("</s>", "</system>")
        return output 