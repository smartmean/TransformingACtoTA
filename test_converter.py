import xml.etree.ElementTree as ET
from Main_Beyone_Refactored import xmlConverter

# Test the converter
def test_fork_template_creation():
    print("Testing fork template creation...")
    
    # Read test XML
    try:
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
        
        print(f"Activity nodes found: {len(activity.findall('.//{*}node'))}")
        print(f"Activity edges found: {len(activity.findall('.//{*}edge'))}")
        
        # Create converter and test
        converter = xmlConverter()
        converter.set_activity_root(activity)
        
        # Process nodes
        main_template = converter.process_nodes()
        
        print(f"\nResults:")
        print(f"  Templates created: {len(converter.templates)}")
        print(f"  Fork templates created: {len(converter.fork_templates)}")
        print(f"  Fork channels: {len(converter.fork_channels)}")
        print(f"  Done variables: {len(converter.declaration_manager.done_variables)}")
        
        # Show template names
        print("\nTemplate names:")
        for template in converter.templates:
            print(f"  - {template['name']}")
        for fork_template in converter.fork_templates:
            print(f"  - {fork_template['name']} (fork)")
        
        return converter
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_fork_template_creation() 