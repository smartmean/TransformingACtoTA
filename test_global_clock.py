import xml.etree.ElementTree as ET
from Main_Beyone import UppaalConverter

# Test with a simple file
with open('Example_XML/test02.xml', 'r', encoding='utf-8') as f:
    contents = f.read()

activity_root = ET.fromstring(contents)
converter = UppaalConverter()
converter.activity_root = activity_root
main_template = converter.create_template('Template')

# Process nodes and edges (simplified)
converter.node_info = {}
converter.node_types = {}
for node in activity_root.findall('.//{*}node'):
    node_id = node.get('{http://www.omg.org/spec/XMI/20131001}id')
    node_name = node.get('name', 'unnamed')
    node_type = node.get('{http://www.omg.org/spec/XMI/20131001}type', node.tag.split('}')[-1])
    converter.node_info[node_id] = node_name
    converter.node_types[node_id] = node_type

# Generate XML and check for total_time
uppaal_xml = converter.generate_xml()
print('=== Global Declarations Test ===')
if 'clock total_time=0;' in uppaal_xml:
    print('✅ SUCCESS: Global clock total_time=0; found in output!')
else:
    print('❌ ERROR: Global clock total_time=0; NOT found in output!')

# Show the declarations section
import re
decl_match = re.search(r'<declaration>(.*?)</declaration>', uppaal_xml, re.DOTALL)
if decl_match:
    print('\nDeclarations content:')
    print(decl_match.group(1).strip()) 