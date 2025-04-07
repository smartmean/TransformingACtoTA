from fastapi import FastAPI, File, UploadFile  # type: ignore
import xml.etree.ElementTree as ET
from fastapi.responses import Response  # type: ignore

app = FastAPI()

class UppaalConverter:
    """ แปลง Activity Diagram XML → UPPAAL XML """

    def __init__(self):
        self.nta = ET.Element("nta")
        self.declarations = ["clock t;"]
        self.templates = []
        self.edge_guards = {}
        self.decision_vars = {}
        self.location_y_positions = {}
        self.current_y_offset = 100
        self.fork_count = 0
        self.fork_templates = []
        self.join_nodes = {}
        self.clock_counter = 0  # Counter for unique clock names
        self.activity_root = None
        self.node_info = {}
        self.node_types = {}
        self.fork_channels = {}  # Dictionary to store fork channel names

    def add_declaration(self, text):
        self.declarations.append(text)

    def create_template(self, name="Template"):
        # Check if template name already exists
        base_name = name
        counter = 1
        while any(t["name"] == name for t in self.templates):
            name = f"{base_name}{counter}"
            counter += 1

        # Generate unique clock name
        clock_name = "t" if self.clock_counter == 0 else f"t{self.clock_counter}"
        self.clock_counter += 1

        template = ET.Element("template")
        ET.SubElement(template, "name").text = name
        ET.SubElement(template, "declaration").text = f"// Local declarations\nclock {clock_name};"
        self.templates.append({
            "name": name,
            "element": template,
            "state_map": {},
            "id_counter": 0,
            "x_offset": 0,
            "position_map": {},
            "initial_id": None,
            "clock_name": clock_name  # Store clock name for this template
        })
        return self.templates[-1]

    def add_location(self, template, node_id, node_name, node_type):
        loc_id = node_id
        template['state_map'][node_id] = loc_id

        x = template['x_offset']
        
        if node_type in ("uml:DecisionNode", "DecisionNode"):
            y = self.current_y_offset + 100
            self.current_y_offset = y
        elif node_type in ("uml:ForkNode", "ForkNode"):
            y = self.current_y_offset + 100
            self.current_y_offset = y
        elif node_type in ("uml:JoinNode", "JoinNode"):
            y = self.current_y_offset + 100
            self.current_y_offset = y
        else:
            is_after_decision = False
            for edge in template["element"].findall(".//transition"):
                if edge.find("target").get("ref") == loc_id:
                    source_id = edge.find("source").get("ref")
                    if source_id in self.decision_vars:
                        is_after_decision = True
                        break
            
            if is_after_decision:
                y = self.current_y_offset + 150
                self.current_y_offset = y
            else:
                y = self.current_y_offset

        template['position_map'][node_id] = (x, y)
        self.location_y_positions[node_id] = y

        location = ET.SubElement(template["element"], "location", id=loc_id, x=str(x), y=str(y))
        
        clean_name = node_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_")
        
        if node_type in ("uml:DecisionNode", "DecisionNode"):
            label_name = f"{clean_name}_Decision"
            self.decision_vars[node_id] = clean_name
            self.declarations.append(f"int {clean_name};")
        elif node_type in ("uml:ForkNode", "ForkNode"):
            label_name = f"{clean_name}_Fork"
            self.fork_count += 1
            # Create dynamic broadcast channel name
            channel_name = f"fork_{clean_name}"
            self.declarations.append(f"broadcast chan {channel_name};")
            self.declarations.append(f"bool Done_{clean_name};")
            # Store channel name for this fork node
            self.fork_channels[node_id] = channel_name
        elif node_type in ("uml:JoinNode", "JoinNode"):
            label_name = f"{clean_name}_Join"
            self.join_nodes[node_id] = template['name']
        else:
            label_name = clean_name
            
        ET.SubElement(location, "name", x=str(x - 50), y=str(y - 30)).text = label_name

        if node_type in ("uml:InitialNode", "InitialNode"):
            template["initial_id"] = loc_id

        template['id_counter'] += 1
        template['x_offset'] += 300

    def create_fork_template(self, fork_name, fork_id, outgoing_edge, node_info, node_types):
        # Create new template for forked process
        fork_template = self.create_template(f"{fork_name}_Process")
        self.fork_templates.append(fork_template)
        
        # Add initial location
        initial_id = f"fork_{fork_name}"
        self.add_location(fork_template, initial_id, f"InitialNode_{fork_name}", "InitialNode")
        
        # Track current node and its edges
        current_node = None
        current_edges = []
        processed_nodes = set()
        
        # Start from the target node of the outgoing edge
        target_id = outgoing_edge
        current_node = target_id
        current_edges = []
        
        # Find all edges where this node is the source
        for edge in self.activity_root.findall(".//{*}edge"):
            if edge.get("source") == current_node:
                current_edges.append(edge.get("xmi:id"))
        
        # Process nodes in sequence until we reach a join node
        while current_node and current_node not in processed_nodes:
            processed_nodes.add(current_node)
            
            # Add location for current node
            node_name = node_info.get(current_node, "")
            node_type = node_types.get(current_node, "")
            self.add_location(fork_template, current_node, node_name, node_type)
            
            # If this is a join node, add it and stop
            if node_type in ("uml:JoinNode", "JoinNode"):
                # Add join node location with template name
                join_name = f"JoinNode_{fork_template['name']}"
                self.add_location(fork_template, f"join_{join_name}", join_name, "JoinNode")
                break
            
            # Find next node from current edges
            next_node = None
            for edge_id in current_edges:
                for edge in self.activity_root.findall(".//{*}edge"):
                    if edge.get("xmi:id") == edge_id:
                        next_node = edge.get("target")
                        break
                if next_node:
                    break
            
            # Update current node and edges
            current_node = next_node
            current_edges = []
            if current_node:
                for edge in self.activity_root.findall(".//{*}edge"):
                    if edge.get("source") == current_node:
                        current_edges.append(edge.get("xmi:id"))
        
        # Add transitions between locations
        locations = fork_template["element"].findall(".//location")
        for i in range(len(locations) - 1):
            source = locations[i].get("id")
            target = locations[i + 1].get("id")
            source_name = node_info.get(source, "")
            target_name = node_info.get(target, "")
            target_type = node_types.get(target, "")
            self.add_transition(fork_template, source, target, source_name, target_name, target_type)
        
        return fork_template

    def add_transition(self, template, source_id, target_id, source_name="", target_name="", target_type=""):
        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        if source and target:
            trans_id = f"{source_id}_{target_id}"
            transition = ET.SubElement(template["element"], "transition", id=trans_id)
            ET.SubElement(transition, "source", ref=source)
            ET.SubElement(transition, "target", ref=target)
            template['id_counter'] += 1

            x1, y1 = template["position_map"].get(source_id, (0, 0))
            x2, y2 = template["position_map"].get(target_id, (0, 0))
            x_mid = (x1 + x2) // 2
            y_mid = (y1 + y2) // 2

            if "," in source_name and "t=" in source_name:
                try:
                    time_val = int(source_name.split("t=")[-1].strip())
                    clock_name = template["clock_name"]
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 60)).text = f"{clock_name}>{time_val}"
                    ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"{clock_name}:=0"
                except:
                    pass

            edge_label = self.edge_guards.get((source_id, target_id))
            if target_type == "uml:DecisionNode":
                decision_var = target_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_")
            else:
                decision_var = "Is_Success"

            if edge_label and "=" in edge_label:
                condition = edge_label.strip("[]").split("=")[1].strip().lower()
                if condition == "yes":
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = f"{decision_var}==1"
                elif condition == "no":
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = f"{decision_var}==0"

            if target_type == "uml:DecisionNode":
                var_name = f"i{template['id_counter']}"
                ET.SubElement(transition, "label", kind="select", x=str(x_mid), y=str(y_mid - 100)).text = f"{var_name}: int[0,1]"
                existing_assign = transition.find("label[@kind='assignment']")
                if existing_assign is not None:
                    existing_assign.text += f", {decision_var} = {var_name}"
                else:
                    clock_name = template["clock_name"]
                    ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"{clock_name}:=0, {decision_var} = {var_name}"
            
            # Handle Fork and Join
            source_type = self.get_node_type(source_id)
            if source_type in ("uml:ForkNode", "ForkNode"):
                # Get all outgoing edges for this fork node
                fork_edges = []
                for edge in self.activity_root.findall(".//{*}edge"):
                    if edge.get("source") == source_id:
                        fork_edges.append(edge.get("target"))
                
                # Create fork template for each outgoing edge only if not already created
                fork_name = source_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_")
                for i, outgoing_edge in enumerate(fork_edges):
                    template_name = f"{fork_name}_Process{i+1}"
                    # Check if template already exists
                    if not any(t["name"] == template_name for t in self.fork_templates):
                        self.create_fork_template(fork_name, source_id, outgoing_edge, self.node_info, self.node_types)
                
                # Find the join node that this fork node connects to
                join_node = None
                for edge in self.activity_root.findall(".//{*}edge"):
                    if edge.get("source") == source_id:
                        target_id = edge.get("target")
                        target_type = self.node_types.get(target_id, "")
                        if target_type in ("uml:JoinNode", "JoinNode"):
                            join_node = target_id
                            break
                
                # If join node found, create transition from fork to join in main template
                if join_node:
                    # Add synchronisation label
                    ET.SubElement(transition, "label", kind="synchronisation", x=str(x_mid), y=str(y_mid - 80)).text = "fork!"
                    # Skip creating transitions to intermediate nodes
                    return
            
            if target_type in ("uml:JoinNode", "JoinNode"):
                # Add guard to check if all forked processes are done
                guard_conditions = []
                for fork_template in self.fork_templates:
                    fork_name = fork_template["name"].replace("_Process", "")
                    guard_conditions.append(f"Done_{fork_name}==true")
                ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = " && ".join(guard_conditions)

    def get_node_type(self, node_id):
        for template in self.templates:
            for node in template["element"].findall(".//location"):
                if node.get("id") == node_id:
                    name = node.find("name").text
                    if "_Decision" in name:
                        return "uml:DecisionNode"
                    elif "_Fork" in name:
                        return "uml:ForkNode"
                    elif "_Join" in name:
                        return "uml:JoinNode"
        return ""

    def generate_xml(self):
        # Clear any existing elements
        for elem in list(self.nta):
            self.nta.remove(elem)

        # Add declaration
        decl_elem = ET.SubElement(self.nta, "declaration")
        decl_elem.text = "\n".join(sorted(set(self.declarations)))

        # Add templates
        for template in self.templates:
            element = template["element"]
            name_el = element.find("name")
            decl_el = element.find("declaration")
            locations = element.findall("location")
            transitions = element.findall("transition")

            # Clear existing children
            for child in list(element):
                element.remove(child)

            # Re-add elements in correct order
            if name_el is not None:
                element.append(name_el)
            if decl_el is not None:
                element.append(decl_el)
            for loc in locations:
                element.append(loc)
            if template["initial_id"] is not None:
                ET.SubElement(element, "init", ref=template["initial_id"])
            for trans in transitions:
                element.append(trans)

            self.nta.append(element)

        # Add system declaration with dynamic template names
        system_text = []
        for i, template in enumerate(self.templates, 1):
            system_text.append(f"T{i} = {template['name']}();")
        system_text.append("system " + ", ".join(f"T{i}" for i in range(1, len(self.templates) + 1)) + ";")
        
        system_elem = ET.SubElement(self.nta, "system")
        system_elem.text = "\n".join(system_text)

        # Add queries
        queries = ET.SubElement(self.nta, "queries")
        query = ET.SubElement(queries, "query")
        ET.SubElement(query, "formula").text = "A[] not deadlock"
        ET.SubElement(query, "comment").text = "Check for deadlocks"

        # Generate final XML
        raw_xml = ET.tostring(self.nta, encoding="utf-8", method="xml").decode()
        header = '<?xml version="1.0" encoding="utf-8"?>\n'
        doctype = "<!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.6//EN' 'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd'>\n"
        return header + doctype + raw_xml


@app.post("/convert-xml")
async def convert_xml(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        activity_root = ET.fromstring(contents)

        converter = UppaalConverter()
        converter.activity_root = activity_root
        main_template = converter.create_template("Template")

        # First collect all node information
        converter.node_info = {}
        converter.node_types = {}
        for node in activity_root.findall(".//{*}node"):
            node_id = node.get("{http://www.omg.org/spec/XMI/20131001}id")
            node_name = node.get("name", "unnamed")
            node_type = node.get("{http://www.omg.org/spec/XMI/20131001}type", node.tag.split("}")[-1])
            converter.node_info[node_id] = node_name
            converter.node_types[node_id] = node_type

        # Collect all edges first
        edges = []
        for edge in activity_root.findall(".//{*}edge"):
            src = edge.get("source")
            tgt = edge.get("target")
            label = edge.get("name", "")
            if label:
                converter.edge_guards[(src, tgt)] = label
            edges.append((src, tgt))

        # Create locations in order of edges
        processed_nodes = set()
        for src, tgt in edges:
            # Process source node if not already processed
            if src not in processed_nodes:
                converter.add_location(main_template, src, converter.node_info[src], converter.node_types[src])
                processed_nodes.add(src)
            
            # Process target node if not already processed
            if tgt not in processed_nodes:
                converter.add_location(main_template, tgt, converter.node_info[tgt], converter.node_types[tgt])
                processed_nodes.add(tgt)

        # Add transitions after all locations are created
        for src, tgt in edges:
            converter.add_transition(
                main_template, src, tgt,
                source_name=converter.node_info.get(src, ""),
                target_name=converter.node_info.get(tgt, ""),
                target_type=converter.node_types.get(tgt, "")
            )

        uppaal_xml = converter.generate_xml()
        return Response(content=uppaal_xml, media_type="application/xml")

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import os
    
    # Read input file
    input_file = "test02.xml"
    output_file = "res02.xml"
    
    try:
        # Read the input XML file
        with open(input_file, 'r', encoding='utf-8') as f:
            contents = f.read()
        
        # Parse the XML
        activity_root = ET.fromstring(contents)
        
        # Create converter and process
        converter = UppaalConverter()
        converter.activity_root = activity_root
        main_template = converter.create_template("Template")
        
        # First collect all node information
        converter.node_info = {}
        converter.node_types = {}
        for node in activity_root.findall(".//{*}node"):
            node_id = node.get("{http://www.omg.org/spec/XMI/20131001}id")
            node_name = node.get("name", "unnamed")
            node_type = node.get("{http://www.omg.org/spec/XMI/20131001}type", node.tag.split("}")[-1])
            converter.node_info[node_id] = node_name
            converter.node_types[node_id] = node_type

        # Collect all edges first
        edges = []
        for edge in activity_root.findall(".//{*}edge"):
            src = edge.get("source")
            tgt = edge.get("target")
            label = edge.get("name", "")
            if label:
                converter.edge_guards[(src, tgt)] = label
            edges.append((src, tgt))

        # Create locations in order of edges
        processed_nodes = set()
        for src, tgt in edges:
            # Process source node if not already processed
            if src not in processed_nodes:
                converter.add_location(main_template, src, converter.node_info[src], converter.node_types[src])
                processed_nodes.add(src)
            
            # Process target node if not already processed
            if tgt not in processed_nodes:
                converter.add_location(main_template, tgt, converter.node_info[tgt], converter.node_types[tgt])
                processed_nodes.add(tgt)

        # Add transitions after all locations are created
        for src, tgt in edges:
            converter.add_transition(
                main_template, src, tgt,
                source_name=converter.node_info.get(src, ""),
                target_name=converter.node_info.get(tgt, ""),
                target_type=converter.node_types.get(tgt, "")
            )
        
        # Generate UPPAAL XML
        uppaal_xml = converter.generate_xml()
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(uppaal_xml)
            
        print(f"Successfully converted {input_file} to {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
