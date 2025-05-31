import xml.etree.ElementTree as ET
from Main_Beyone_fixed import *

# Read XML
with open('Example_XML/Full_Node_simple.xml', 'r', encoding='utf-8') as f:
    contents = f.read()
activity_root = ET.fromstring(contents)

# สร้าง converter และ parser
converter = UppaalConverter()
converter.set_activity_root(activity_root)

print(f"After set_activity_root:")
print(f"  Parser ID: {id(converter.parser)}")
print(f"  Main flow nodes: {len(converter.parser.main_flow_nodes)}")

# เรียก print_analysis
print(f"\nCalling print_analysis...")
converter.parser.print_analysis()

print(f"\nAfter print_analysis:")
print(f"  Parser ID: {id(converter.parser)}")
print(f"  Main flow nodes: {len(converter.parser.main_flow_nodes)}")

# เรียก get_main_flow_nodes
main_flow_nodes = converter.parser.get_main_flow_nodes()
print(f"\nAfter get_main_flow_nodes:")
print(f"  Parser ID: {id(converter.parser)}")
print(f"  Returned nodes count: {len(main_flow_nodes)}")
print(f"  Parser internal count: {len(converter.parser.main_flow_nodes)}")

# ตรวจสอบว่า ID ของ nodes เหมือนกันหรือไม่
if main_flow_nodes == converter.parser.main_flow_nodes:
    print("✅ Same node sets")
else:
    print("❌ Different node sets")
    print(f"get_main_flow_nodes returned: {main_flow_nodes}")
    print(f"parser.main_flow_nodes: {converter.parser.main_flow_nodes}") 