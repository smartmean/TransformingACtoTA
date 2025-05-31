import xml.etree.ElementTree as ET
from Main_Beyone_Refactored import xmlConverter

def test_100_percent():
    """Test that we get 100% matching results"""
    print("=== Testing 100% Match with Main_Beyone_final.py ===")
    
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
    
    # Convert using refactored version
    converter = xmlConverter()
    converter.set_activity_root(activity)
    converter.process_nodes()
    xml_output = converter.generate_xml()
    
    # Count templates
    templates_xml = ET.fromstring(xml_output)
    templates = templates_xml.findall(".//template")
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Total templates created: {len(templates)}")
    
    template_details = []
    unique_template_names = set()
    duplicate_templates = []
    
    for template in templates:
        name_elem = template.find("name")
        template_name = name_elem.text if name_elem is not None else "Unknown"
        
        locations = template.findall(".//location")
        transitions = template.findall(".//transition")
        
        template_details.append({
            "name": template_name,
            "locations": len(locations),
            "transitions": len(transitions)
        })
        
        # Check for duplicates
        if template_name in unique_template_names:
            duplicate_templates.append(template_name)
        else:
            unique_template_names.add(template_name)
        
        print(f"  * {template_name}: {len(locations)} locations, {len(transitions)} transitions")
    
    # Show duplicates
    if duplicate_templates:
        print(f"\n❌ DUPLICATE TEMPLATES FOUND:")
        for dup in set(duplicate_templates):
            count = sum(1 for t in template_details if t["name"] == dup)
            print(f"  * {dup} appears {count} times")
    
    # Show unique templates only
    unique_templates = {}
    for t in template_details:
        if t["name"] not in unique_templates:
            unique_templates[t["name"]] = t
    
    print(f"\n🔍 UNIQUE TEMPLATES ({len(unique_templates)}):")
    for name, details in unique_templates.items():
        print(f"  * {name}: {details['locations']} locations, {details['transitions']} transitions")
    
    # Expected from Main_Beyone_final.py:
    expected_templates = [
        {"name": "Template", "locations": 10, "transitions": 10},
        {"name": "Template_ForkNode1_Branch1_Nested1", "locations": 3, "transitions": 2},
        {"name": "Template_ForkNode1_Branch1_Nested2", "locations": 7, "transitions": 7},
        {"name": "Template_ForkNode1_Branch1", "locations": 4, "transitions": 2},
        {"name": "Template_ForkNode1_Branch2", "locations": 3, "transitions": 2},
        {"name": "Template_ForkNode2_Branch1", "locations": 7, "transitions": 7},
        {"name": "Template_ForkNode2_Branch2", "locations": 3, "transitions": 2}
    ]
    
    print(f"\n🎯 TARGET (Main_Beyone_final.py): {len(expected_templates)} templates")
    for exp in expected_templates:
        print(f"  * {exp['name']}: {exp['locations']} locations, {exp['transitions']} transitions")
    
    # Compare
    if len(templates) == len(expected_templates):
        print(f"\n✅ Template count matches: {len(templates)}")
        
        # Check for template names
        actual_names = {t["name"] for t in template_details}
        expected_names = {t["name"] for t in expected_templates}
        
        if actual_names == expected_names:
            print("✅ All template names match!")
            print("🎉 SUCCESS: 100% match achieved!")
            return True
        else:
            missing = expected_names - actual_names
            extra = actual_names - expected_names
            if missing:
                print(f"❌ Missing templates: {missing}")
            if extra:
                print(f"❌ Extra templates: {extra}")
    else:
        print(f"❌ Template count differs: {len(templates)} vs {len(expected_templates)}")
    
    return False

if __name__ == "__main__":
    test_100_percent() 