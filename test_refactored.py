import xml.etree.ElementTree as ET
from Main_Beyone_Refactored import xmlConverter

# Test the converter
def test_converter():
    print("Testing refactored converter...")
    
    # Read test XML
    with open('Example_XML/Full_Node_simple.xml', 'r', encoding='utf-8') as f:
        contents = f.read()
    
    # Parse XML
    root = ET.fromstring(contents)
    
    # Find activity element
    activity = None
    for elem in root.findall(".//packagedElement"):
        xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
        if xmi_type == 'uml:Activity':
            activity = elem
            break
    
    if activity is None:
        activity = root
    
    print(f"Activity nodes found: {len(list(activity.findall('.//node')))}")
    print(f"Activity edges found: {len(list(activity.findall('.//edge')))}")
    
    # Create converter and process
    converter = xmlConverter()
    converter.set_activity_root(activity)
    main_template = converter.process_nodes()
    
    # Generate XML
    uppaal_xml = converter.generate_xml()
    
    print(f"Templates created: {len(converter.templates)}")
    print(f"Fork templates created: {len(converter.fork_templates)}")
    
    for template in converter.templates:
        print(f"  Main template: {template['name']} with {len(template['state_map'])} locations")
    
    for template in converter.fork_templates:
        print(f"  Fork template: {template['name']} with {len(template['state_map'])} locations")
    
    print("✅ Refactored test completed successfully!")
    return len(converter.templates), len(converter.fork_templates)

if __name__ == "__main__":
    test_converter() 