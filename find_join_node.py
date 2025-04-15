import xml.etree.ElementTree as ET

def find_join_node(fork_node_id, xml_file):
    try:
        # Register namespaces
        ET.register_namespace('uml', 'http://www.eclipse.org/uml2/5.0.0/UML')
        ET.register_namespace('xmi', 'http://www.omg.org/spec/XMI/20131001')
        
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Define namespaces for searching
        ns = {
            'uml': 'http://www.eclipse.org/uml2/5.0.0/UML',
            'xmi': 'http://www.omg.org/spec/XMI/20131001'
        }
        
        # Find the ForkNode with the given ID
        fork_node = root.find(f".//uml:node[@xmi:id='{fork_node_id}'][@xmi:type='uml:ForkNode']", ns)
        
        if fork_node is None:
            print("ForkNode not found")
            return None
        
        # Get all outgoing edges from the ForkNode
        fork_node_edges = []
        for edge in root.findall(".//uml:edge", ns):
            if edge.get('source') == fork_node_id:
                fork_node_edges.append(edge.get('target'))
        
        if not fork_node_edges:
            print("No outgoing edges found from ForkNode")
            return None
        
        # Find all nodes that are targets of the ForkNode's outgoing edges
        target_nodes = []
        for target_id in fork_node_edges:
            target_node = root.find(f".//uml:node[@xmi:id='{target_id}']", ns)
            if target_node is not None:
                target_nodes.append(target_node)
        
        if not target_nodes:
            print("No target nodes found")
            return None
        
        # Find the JoinNode that receives edges from all the target nodes
        join_nodes = root.findall(".//uml:node[@xmi:type='uml:JoinNode']", ns)
        for join_node in join_nodes:
            join_id = join_node.get('{http://www.omg.org/spec/XMI/20131001}id')
            incoming_edges = []
            for edge in root.findall(".//uml:edge", ns):
                if edge.get('target') == join_id:
                    incoming_edges.append(edge.get('source'))
            
            # Check if all target nodes of the ForkNode connect to this JoinNode
            all_connected = True
            for target in target_nodes:
                target_id = target.get('{http://www.omg.org/spec/XMI/20131001}id')
                if target_id not in incoming_edges:
                    all_connected = False
                    break
            
            if all_connected:
                return join_id
        
        print("No JoinNode found that connects to all target nodes")
        return None
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None

# Test the function
if __name__ == "__main__":
    xml_file = "Example_XML/ForkJoin.xml"
    fork_node_id = "_TVYLgBE8EfCgidtTHikwVg"
    
    join_node_id = find_join_node(fork_node_id, xml_file)
    if join_node_id:
        print(f"Input ForkNode ID: {fork_node_id}")
        print(f"Found JoinNode ID: {join_node_id}")
    else:
        print("No corresponding JoinNode found") 