import xml.etree.ElementTree as ET
from Main_Beyone_Refactored import ActivityDiagramParser, xmlConverter

def debug_parser():
    """Debug ActivityDiagramParser"""
    print("🔍 Debugging ActivityDiagramParser...")
    
    # อ่านไฟล์ XML
    with open("Example_XML/Full_Node_simple.xml", "r", encoding="utf-8") as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    # หา activity element
    activity = None
    for elem in root.findall(".//packagedElement"):
        xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
        if xmi_type == 'uml:Activity':
            activity = elem
            print(f"Found Activity: {elem.get('name', 'unnamed')}")
            break
    
    if activity is None:
        print("❌ No activity element found!")
        return
    
    print(f"✅ Activity element found: {activity.tag}")
    print(f"Nodes in activity: {len(activity.findall('.//node'))}")
    print(f"Edges in activity: {len(activity.findall('.//edge'))}")
    
    # สร้าง parser
    parser = ActivityDiagramParser(activity)
    
    # แสดงผลการวิเคราะห์
    parser.print_analysis()
    
    # ทดสอบ converter
    print("\n" + "="*50)
    print("TESTING CONVERTER")
    print("="*50)
    
    converter = xmlConverter()
    converter.set_activity_root(activity)
    
    # ประมวลผล nodes
    main_template = converter.process_nodes()
    
    print(f"\nMain template info:")
    print(f"  Name: {main_template['name']}")
    print(f"  State map entries: {len(main_template['state_map'])}")
    print(f"  Clock name: {main_template['clock_name']}")
    print(f"  Initial ID: {main_template['initial_id']}")
    
    print("Locations:")
    for node_id, state_id in main_template['state_map'].items():
        print(f"  • {node_id} -> {state_id}")
    
    # ดู template element structure
    template_element = main_template['element']
    print(f"\nTemplate element children: {len(list(template_element))}")
    for child in template_element:
        print(f"  • {child.tag}: {child.text}")
    
    # ทดสอบ XML generation
    print("\n" + "="*50)
    print("TESTING XML GENERATION")
    print("="*50)
    
    uppaal_xml = converter.generate_xml()
    print(f"Generated XML length: {len(uppaal_xml)} characters")
    
    # บันทึกและแสดงตัวอย่าง
    with open("debug_output.xml", "w", encoding="utf-8") as f:
        f.write(uppaal_xml)
    
    print("First 200 characters of generated XML:")
    print(uppaal_xml[:200] + "...")

if __name__ == "__main__":
    debug_parser() 