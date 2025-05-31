import xml.etree.ElementTree as ET
import sys
import traceback

# Import both converters
try:
    from Main_Beyone_final import UppaalConverter
    print("Imported UppaalConverter from Main_Beyone_final.py")
except Exception as e:
    print(f"Failed to import UppaalConverter: {e}")
    sys.exit(1)

try:
    from Main_Beyone_Refactored import xmlConverter
    print("Imported xmlConverter from Main_Beyone_Refactored.py")
except Exception as e:
    print(f"Failed to import xmlConverter: {e}")
    sys.exit(1)

def analyze_xml(xml_content, name):
    if not xml_content or xml_content.strip() == "":
        return {'name': name, 'error': 'Empty XML', 'locations': 0, 'transitions': 0, 'templates': 0, 'xml_length': 0}
    
    try:
        root = ET.fromstring(xml_content)
        locations = root.findall(".//location")
        transitions = root.findall(".//transition") 
        templates = root.findall(".//template")
        
        fork_templates = []
        for template in templates:
            name_elem = template.find("name")
            if name_elem is not None and name_elem.text != "Template":
                fork_templates.append(name_elem.text)
        
        return {
            'name': name,
            'error': None,
            'locations': len(locations),
            'transitions': len(transitions), 
            'templates': len(templates),
            'fork_templates': len(fork_templates),
            'fork_template_names': fork_templates,
            'xml_length': len(xml_content)
        }
    except Exception as e:
        return {'name': name, 'error': str(e), 'locations': 0, 'transitions': 0, 'templates': 0, 'xml_length': len(xml_content)}

def test_converters():
    xml_file = "Example_XML/Demo_Final.xml"
    print(f"Testing both converters with: {xml_file}")
    print("=" * 60)
    
    # Test UppaalConverter
    print("\n[1] Testing UppaalConverter")
    print("-" * 30)
    
    try:
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        root = ET.fromstring(xml_content)
        activity = None
        for elem in root.findall(".//*"):
            xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
            if xmi_type == 'uml:Activity':
                activity = elem
                break
        if activity is None:
            activity = root
        
        converter1 = UppaalConverter()
        converter1.set_activity_root(activity)
        print("Processing nodes...")
        converter1.process_nodes()
        print("Generating XML...")
        result1 = converter1.generate_xml()
        analysis1 = analyze_xml(result1, "UppaalConverter")
        print("UuppaalConverter completed successfully")
        
    except Exception as e:
        print(f"UuppaalConverter failed: {e}")
        result1 = ""
        analysis1 = {'name': 'UppaalConverter', 'error': str(e), 'locations': 0, 'transitions': 0, 'templates': 0, 'xml_length': 0}
    
    # Test xmlConverter
    print("\n[2] Testing xmlConverter")
    print("-" * 30)
    
    try:
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        root = ET.fromstring(xml_content)
        activity = None
        for elem in root.findall(".//*"):
            xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
            if xmi_type == 'uml:Activity':
                activity = elem
                break
        if activity is None:
            activity = root
        
        converter2 = xmlConverter()
        converter2.set_activity_root(activity)
        print("Processing nodes...")
        converter2.process_nodes()
        print("Generating XML...")
        result2 = converter2.generate_xml()
        analysis2 = analyze_xml(result2, "xmlConverter")
        print("xmlConverter completed successfully")
        
    except Exception as e:
        print(f"xmlConverter failed: {e}")
        result2 = ""
        analysis2 = {'name': 'xmlConverter', 'error': str(e), 'locations': 0, 'transitions': 0, 'templates': 0, 'xml_length': 0}
    
    # Compare results
    print("\nCOMPARISON RESULTS")
    print("=" * 60)
    
    print("[1] UppaalConverter results:")
    if analysis1['error']:
        print(f"   Error: {analysis1['error']}")
    else:
        print(f"   Locations: {analysis1['locations']}")
        print(f"   Transitions: {analysis1['transitions']}")
        print(f"   Templates: {analysis1['templates']} (Fork: {analysis1['fork_templates']})")
        print(f"   XML Length: {analysis1['xml_length']:,} characters")
    
    print("\n[2] xmlConverter results:")
    if analysis2['error']:
        print(f"   Error: {analysis2['error']}")
    else:
        print(f"   Locations: {analysis2['locations']}")
        print(f"   Transitions: {analysis2['transitions']}")
        print(f"   Templates: {analysis2['templates']} (Fork: {analysis2['fork_templates']})")
        print(f"   XML Length: {analysis2['xml_length']:,} characters")
    
    # Calculate differences
    if not analysis1['error'] and not analysis2['error']:
        print("\nDIFFERENCES:")
        location_diff = analysis2['locations'] - analysis1['locations']
        transition_diff = analysis2['transitions'] - analysis1['transitions']
        template_diff = analysis2['templates'] - analysis1['templates']
        xml_length_diff = analysis2['xml_length'] - analysis1['xml_length']
        
        print(f"   Locations: {location_diff:+d} ({analysis1['locations']} -> {analysis2['locations']})")
        print(f"   Transitions: {transition_diff:+d} ({analysis1['transitions']} -> {analysis2['transitions']})")
        print(f"   Templates: {template_diff:+d} ({analysis1['templates']} -> {analysis2['templates']})")
        print(f"   XML Length: {xml_length_diff:+,d} chars ({analysis1['xml_length']:,} -> {analysis2['xml_length']:,})")
        
        if analysis1['xml_length'] > 0:
            percent_diff = (xml_length_diff / analysis1['xml_length']) * 100
            print(f"   XML Change: {percent_diff:+.1f}%")
        
        if (location_diff == 0 and transition_diff == 0 and template_diff == 0 and xml_length_diff == 0):
            print("\n*** RESULTS ARE IDENTICAL! ***")
            print("Refactoring SUCCESS - 100% match achieved!")
        else:
            print("\nResults differ - refactoring needs more work")
    
    return analysis1, analysis2

def compare_main_template_labels():
    print("🔍 MAIN TEMPLATE TRANSITION LABELS COMPARISON")
    print("="*80)
    
    # Parse both files
    tree1 = ET.parse('Result/Result_5.xml')  # Refactor version
    tree2 = ET.parse('Result/Result_8.xml')  # Original version
    
    print("\n📋 REFACTOR VERSION (LocationBuilder):")
    print("-" * 50)
    
    # Get main template from refactor version
    for template in tree1.getroot().findall('.//template'):
        name_elem = template.find('name')
        if name_elem is not None and name_elem.text == 'Template':
            transitions = template.findall('.//transition')
            print(f"Found {len(transitions)} transitions in main template")
            
            for i, trans in enumerate(transitions, 1):
                source = trans.find('source').get('ref')[:8] + "..."
                target = trans.find('target').get('ref')[:8] + "..."
                print(f"\n  Transition {i}: {source} → {target}")
                
                labels = trans.findall('label')
                if labels:
                    for label in labels:
                        kind = label.get('kind', 'unknown')
                        text = label.text or ''
                        if kind == 'guard':
                            print(f"    🛡️  Guard: {text}")
                        elif kind == 'assignment':
                            print(f"    📝 Assignment: {text}")
                        elif kind == 'select':
                            print(f"    🎯 Select: {text}")
                        elif kind == 'synchronisation':
                            print(f"    🔗 Sync: {text}")
                else:
                    print(f"    ⚪ No labels")
            break
    
    print("\n" + "="*50)
    print("\n📋 ORIGINAL VERSION (UppaalConverter):")
    print("-" * 50)
    
    # Get main template from original version
    for template in tree2.getroot().findall('.//template'):
        name_elem = template.find('name')
        if name_elem is not None and name_elem.text == 'Template':
            transitions = template.findall('.//transition')
            print(f"Found {len(transitions)} transitions in main template")
            
            for i, trans in enumerate(transitions, 1):
                source = trans.find('source').get('ref')[:8] + "..."
                target = trans.find('target').get('ref')[:8] + "..."
                print(f"\n  Transition {i}: {source} → {target}")
                
                labels = trans.findall('label')
                if labels:
                    for label in labels:
                        kind = label.get('kind', 'unknown')
                        text = label.text or ''
                        if kind == 'guard':
                            print(f"    🛡️  Guard: {text}")
                        elif kind == 'assignment':
                            print(f"    📝 Assignment: {text}")
                        elif kind == 'select':
                            print(f"    🎯 Select: {text}")
                        elif kind == 'synchronisation':
                            print(f"    🔗 Sync: {text}")
                else:
                    print(f"    ⚪ No labels")
            break

def count_labels():
    print("\n\n📊 LABEL COUNTS SUMMARY")
    print("="*80)
    
    files = [
        ('Result/Result_5.xml', 'REFACTOR VERSION'),
        ('Result/Result_8.xml', 'ORIGINAL VERSION')
    ]
    
    for file_path, version_name in files:
        tree = ET.parse(file_path)
        
        guard_count = len([l for l in tree.getroot().findall('.//label') if l.get('kind') == 'guard'])
        assignment_count = len([l for l in tree.getroot().findall('.//label') if l.get('kind') == 'assignment'])
        select_count = len([l for l in tree.getroot().findall('.//label') if l.get('kind') == 'select'])
        sync_count = len([l for l in tree.getroot().findall('.//label') if l.get('kind') == 'synchronisation'])
        
        print(f"\n{version_name}:")
        print(f"  🛡️  Guard labels: {guard_count}")
        print(f"  📝 Assignment labels: {assignment_count}")
        print(f"  🎯 Select labels: {select_count}")
        print(f"  🔗 Sync labels: {sync_count}")
        print(f"  📊 Total labels: {guard_count + assignment_count + select_count + sync_count}")

if __name__ == "__main__":
    try:
        test_converters()
        compare_main_template_labels()
        count_labels()
        print("\n✅ Comparison complete!")
    except Exception as e:
        print(f"Test failed: {e}")
        traceback.print_exc() 