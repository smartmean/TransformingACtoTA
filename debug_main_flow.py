import xml.etree.ElementTree as ET
from Main_Beyone_fixed import *

# Read and parse XML
with open('Example_XML/Full_Node_simple.xml', 'r', encoding='utf-8') as f:
    contents = f.read()
activity_root = ET.fromstring(contents)

# Create parser and analyze
parser = ActivityDiagramParser(activity_root)

print("=== DEBUG MAIN FLOW ANALYSIS ===")
print(f"Total nodes: {len(parser.nodes)}")
print(f"Main flow nodes: {len(parser.main_flow_nodes)}")

# Debug JoinNode1
for node_id, node_info in parser.nodes.items():
    if 'JoinNode1' in node_info['name'] and 'JoinNode1_1' not in node_info['name']:
        print(f'\nFound JoinNode1: {node_info["name"]} (ID: {node_id})')
        print(f'  Is in main flow: {node_id in parser.main_flow_nodes}')
        print(f'  Is nested fork join: {parser._is_nested_fork_join(node_id)}')
        
        # Check corresponding fork
        for fork_id in parser.coordination_nodes:
            if parser.node_types[fork_id] in ('uml:ForkNode', 'ForkNode'):
                corresponding = parser._find_corresponding_join(fork_id)
                if corresponding == node_id:
                    fork_name = parser.node_names[fork_id]
                    print(f'  Corresponding to: {fork_name} (ID: {fork_id})')
                    print(f'  Fork is in main flow: {fork_id in parser.main_flow_nodes}')

# Check what nodes come after ForkNode1
for fork_id in parser.coordination_nodes:
    if parser.node_types[fork_id] in ('uml:ForkNode', 'ForkNode'):
        fork_name = parser.node_names[fork_id]
        if 'ForkNode1' in fork_name and 'ForkNode1_1' not in fork_name:
            print(f'\nForkNode1: {fork_name} (ID: {fork_id})')
            print(f'  Is in main flow: {fork_id in parser.main_flow_nodes}')
            
            corresponding_join = parser._find_corresponding_join(fork_id)
            if corresponding_join:
                join_name = parser.node_names[corresponding_join]
                print(f'  Corresponding join: {join_name} (ID: {corresponding_join})')
                print(f'  Join is in main flow: {corresponding_join in parser.main_flow_nodes}')
                
                # Check what comes after the join
                outgoing = parser.adjacency_list.get(corresponding_join, [])
                print(f'  Outgoing from join: {[parser.node_names[n] for n in outgoing]}')
                for next_node in outgoing:
                    print(f'    {parser.node_names[next_node]} in main flow: {next_node in parser.main_flow_nodes}')

print("\n=== ALL MAIN FLOW NODES ===")
for node_id in parser.main_flow_nodes:
    node_info = parser.nodes[node_id]
    print(f"  • {node_info['type']:<20} | {node_info['name']}") 