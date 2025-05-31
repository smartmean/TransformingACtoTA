import xml.etree.ElementTree as ET
import sys
import traceback

# Import both converters
try:
    from Main_Beyone_final import UppaalConverter
    print("✓ Imported UppaalConverter from Main_Beyone_final.py")
except Exception as e:
    print(f"✗ Failed to import UppaalConverter: {e}")
    sys.exit(1)

try:
    # Import xmlConverter from refactored version
    from Main_Beyone_Refactored import xmlConverter
    print("✓ Imported xmlConverter from Main_Beyone_Refactored.py")
except Exception as e:
    print(f"✗ Failed to import xmlConverter: {e}")
    sys.exit(1)

def analyze_xml_structure(xml_content, name):
    """วิเคราะห์โครงสร้าง XML"""
    try:
        if not xml_content or xml_content.strip() == "":
            return {
                'name': name,
                'error': 'Empty XML content',
                'locations': 0,
                'transitions': 0,
                'templates': 0,
                'xml_length': 0
            }
        
        root = ET.fromstring(xml_content)
        
        # Count locations
        locations = root.findall(".//location")
        
        # Count transitions  
        transitions = root.findall(".//transition")
        
        # Count templates
        templates = root.findall(".//template")
        
        # Count fork templates (templates that are not main "Template")
        fork_templates = []
        main_templates = []
        
        for template in templates:
            name_elem = template.find("name")
            if name_elem is not None:
                template_name = name_elem.text
                if template_name == "Template":
                    main_templates.append(template_name)
                else:
                    fork_templates.append(template_name)
        
        return {
            'name': name,
            'error': None,
            'locations': len(locations),
            'transitions': len(transitions), 
            'templates': len(templates),
            'main_templates': len(main_templates),
            'fork_templates': len(fork_templates),
            'fork_template_names': fork_templates,
            'xml_length': len(xml_content)
        }
        
    except Exception as e:
        return {
            'name': name,
            'error': str(e),
            'locations': 0,
            'transitions': 0,
            'templates': 0,
            'xml_length': len(xml_content) if xml_content else 0
        }

def test_both_converters(xml_file_path):
    """ทดสอบทั้ง 2 converters กับไฟล์เดียวกัน"""
    print(f"Testing both converters with: {xml_file_path}")
    print("=" * 80)
    
    # Test 1: UppaalConverter (Main_Beyone_final.py)
    print(f"\n[1] Testing UppaalConverter (Main_Beyone_final.py)")
    print("-" * 50)
    
    try:
        # Read and parse XML
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        root = ET.fromstring(xml_content)
        
        # Find activity
        activity = None
        for elem in root.findall(".//*"):
            xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
            if xmi_type == 'uml:Activity':
                activity = elem
                break
        
        if activity is None:
            activity = root
        
        # Create and run converter
        converter1 = UppaalConverter()
        converter1.set_activity_root(activity)
        
        print("Processing nodes...")
        main_template = converter1.process_nodes()
        
        print("Generating XML...")
        result1 = converter1.generate_xml()
        
        analysis1 = analyze_xml_structure(result1, "UppaalConverter")
        print(f"✓ UppaalConverter completed successfully")
        
    except Exception as e:
        print(f"✗ UppaalConverter failed: {e}")
        traceback.print_exc()
        result1 = ""
        analysis1 = {
            'name': 'UppaalConverter',
            'error': str(e),
            'locations': 0,
            'transitions': 0,
            'templates': 0,
            'xml_length': 0
        }
    
    # Test 2: xmlConverter (Main_Beyone_Refactored.py)  
    print(f"\n[2] Testing xmlConverter (Main_Beyone_Refactored.py)")
    print("-" * 50)
    
    try:
        # Read and parse XML
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        root = ET.fromstring(xml_content)
        
        # Find activity
        activity = None
        for elem in root.findall(".//*"):
            xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
            if xmi_type == 'uml:Activity':
                activity = elem
                break
        
        if activity is None:
            activity = root
        
        # Create and run converter
        converter2 = xmlConverter()
        converter2.set_activity_root(activity)
        
        print("Processing nodes...")
        main_template = converter2.process_nodes()
        
        print("Generating XML...")
        result2 = converter2.generate_xml()
        
        analysis2 = analyze_xml_structure(result2, "xmlConverter")
        print(f"✓ xmlConverter completed successfully")
        
    except Exception as e:
        print(f"✗ xmlConverter failed: {e}")
        traceback.print_exc()
        result2 = ""
        analysis2 = {
            'name': 'xmlConverter',  
            'error': str(e),
            'locations': 0,
            'transitions': 0,
            'templates': 0,
            'xml_length': 0
        }
    
    # Compare results
    print(f"\nCOMPARISON RESULTS")
    print("=" * 80)
    
    print(f"[1] UppaalConverter (Main_Beyone_final.py):")
    if analysis1['error']:
        print(f"   ✗ Error: {analysis1['error']}")
    else:
        print(f"   Locations: {analysis1['locations']}")
        print(f"   Transitions: {analysis1['transitions']}")
        print(f"   Templates: {analysis1['templates']} (Main: {analysis1.get('main_templates', 0)}, Fork: {analysis1.get('fork_templates', 0)})")
        print(f"   XML Length: {analysis1['xml_length']:,} characters")
        if analysis1.get('fork_template_names'):
            print(f"   Fork Templates: {', '.join(analysis1['fork_template_names'][:5])}{'...' if len(analysis1['fork_template_names']) > 5 else ''}")
    
    print(f"\n[2] xmlConverter (Main_Beyone_Refactored.py):")
    if analysis2['error']:
        print(f"   ✗ Error: {analysis2['error']}")
    else:
        print(f"   Locations: {analysis2['locations']}")
        print(f"   Transitions: {analysis2['transitions']}")
        print(f"   Templates: {analysis2['templates']} (Main: {analysis2.get('main_templates', 0)}, Fork: {analysis2.get('fork_templates', 0)})")
        print(f"   XML Length: {analysis2['xml_length']:,} characters")
        if analysis2.get('fork_template_names'):
            print(f"   Fork Templates: {', '.join(analysis2['fork_template_names'][:5])}{'...' if len(analysis2['fork_template_names']) > 5 else ''}")
    
    # Calculate differences
    if not analysis1['error'] and not analysis2['error']:
        print(f"\nDIFFERENCES:")
        
        location_diff = analysis2['locations'] - analysis1['locations']
        transition_diff = analysis2['transitions'] - analysis1['transitions']
        template_diff = analysis2['templates'] - analysis1['templates']
        xml_length_diff = analysis2['xml_length'] - analysis1['xml_length']
        
        print(f"   Locations: {location_diff:+d} ({analysis1['locations']} -> {analysis2['locations']})")
        print(f"   Transitions: {transition_diff:+d} ({analysis1['transitions']} -> {analysis2['transitions']})")
        print(f"   Templates: {template_diff:+d} ({analysis1['templates']} -> {analysis2['templates']})")
        print(f"   XML Length: {xml_length_diff:+,d} characters ({analysis1['xml_length']:,} -> {analysis2['xml_length']:,})")
        
        # Calculate percentage difference
        if analysis1['xml_length'] > 0:
            xml_percent_diff = (xml_length_diff / analysis1['xml_length']) * 100
            print(f"   XML Length Change: {xml_percent_diff:+.1f}%")
        
        # Check if identical
        if (location_diff == 0 and transition_diff == 0 and 
            template_diff == 0 and xml_length_diff == 0):
            print(f"   *** RESULTS ARE IDENTICAL! ***")
        else:
            print(f"   Results differ - refactoring needs adjustment")
    
    return analysis1, analysis2

if __name__ == "__main__":
    # Test with the demo file
    xml_file = "Example_XML/Demo_Final.xml"
    
    try:
        analysis1, analysis2 = test_both_converters(xml_file)
        
        print(f"\nFINAL SUMMARY")
        print("=" * 80)
        
        if analysis1['error'] or analysis2['error']:
            print("✗ One or both converters failed")
        else:
            # Compare key metrics
            are_identical = (
                analysis1['locations'] == analysis2['locations'] and
                analysis1['transitions'] == analysis2['transitions'] and
                analysis1['templates'] == analysis2['templates'] and
                analysis1['xml_length'] == analysis2['xml_length']
            )
            
            if are_identical:
                print("*** SUCCESS: Both converters produce identical results! ***")
                print("✓ Refactoring completed successfully - 100% match achieved")
            else:
                print("! PARTIAL SUCCESS: Converters produce different results")
                print("Further refactoring adjustments needed")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        traceback.print_exc() 