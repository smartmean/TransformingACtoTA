import xml.etree.ElementTree as ET
from Main_Beyone_Refactored import xmlConverter
import os

def test_conversion():
    try:
        # โหลด XML file
        xml_file = "Example_XML/Full_Node_simple.xml"
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # หา activity element แบบเดียวกับ FastAPI
        activity = None
        
        # ลองหาจาก packagedElement ที่เป็น Activity
        for elem in root.findall(".//packagedElement"):
            xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
            if xmi_type == 'uml:Activity':
                activity = elem
                print(f"Found Activity: {elem.get('name', 'unnamed')}")
                break
        
        if activity is None:
            print("ไม่พบ Activity element")
            # แสดงข้อมูลเพิ่มเติมเพื่อ debug
            print("Available elements:")
            for elem in root.iter():
                print(f"  - {elem.tag}: {elem.get('xmi:type', elem.get('type', 'no type'))}")
            return
        
        print(f"Found activity element: {activity.tag}")
        
        # แสดงข้อมูลที่พบ
        print(f"Activity nodes found: {len(activity.findall('.//node'))}")
        print(f"Activity edges found: {len(activity.findall('.//edge'))}")
        
        # สร้าง converter และทดสอบ
        converter = xmlConverter()
        converter.set_activity_root(activity)
        
        # Debug: ตรวจสอบ adjacency_list (แก้ไขจาก adjacency)
        print("\nDEBUG: Adjacency list for key nodes:")
        for node_id, node_info in converter.parser.nodes.items():
            if node_info['name'] in ['Decision2', 'Process8', 'MergeNode36', 'ForkNode1']:
                outgoing = converter.parser.adjacency_list.get(node_id, [])
                outgoing_names = [converter.parser.get_node_name(n) for n in outgoing]
                print(f"  {node_info['name']} ({node_id}) -> {outgoing_names}")
        
        # ประมวลผล nodes และสร้าง templates
        converter.process_nodes()
        
        # แปลงเป็น UPPAAL XML
        uppaal_xml = converter.generate_xml()
        
        # สร้าง Result directory ถ้ายังไม่มี
        os.makedirs("Result", exist_ok=True)
        
        # บันทึกผลลัพธ์
        result_file = "Result/test_result.xml"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(uppaal_xml)
        
        print(f"Successfully converted to {result_file}")
        print(f"File size: {len(uppaal_xml)} characters")
        
        # แสดงสถิติ
        lines = uppaal_xml.split('\n')
        print(f"Total lines: {len(lines)}")
        
        # นับ templates
        template_count = uppaal_xml.count('<template>')
        print(f"Templates created: {template_count}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_conversion() 