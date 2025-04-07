from fastapi import FastAPI, File, UploadFile  # type: ignore
import xml.etree.ElementTree as ET
from fastapi.responses import Response  # type: ignore
import json

app = FastAPI()

class UppaalConverter:
    """ แปลง Activity Diagram XML → UPPAAL XML """

    def __init__(self):
        self.nta = ET.Element("nta")
        self.declarations = ["clock t;"]
        self.templates = []
        self.edge_guards = {}
        self.decision_vars = {}
        self.current_y_offset = 100
        self.fork_templates = []
        self.join_nodes = {}
        self.clock_counter = 0
        self.activity_root = None
        self.node_info = {}
        self.node_types = {}
        self.fork_channels = {}
        self.fork_counter = 0  # Add counter for fork channels

    def add_declaration(self, text):
        """Adds a declaration to the UPPAAL model."""
        if text not in self.declarations:
            self.declarations.append(text)

    def create_template(self, name="Template"):
        """Creates a new template with unique name and clock."""
        # Check if template name already exists
        if any(t["name"] == name for t in self.templates):
            return next(t for t in self.templates if t["name"] == name)

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
        """Adds a location to the template with specified properties."""
        loc_id = node_id
        template['state_map'][node_id] = loc_id

        x = template['x_offset']
        
        if node_type in ("uml:DecisionNode", "DecisionNode", "uml:ForkNode", "ForkNode", "uml:JoinNode", "JoinNode"):
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
            
            y = self.current_y_offset + 150 if is_after_decision else self.current_y_offset

        template['position_map'][node_id] = (x, y)

        location = ET.SubElement(template["element"], "location", id=loc_id, x=str(x), y=str(y))
        
        clean_name = node_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_")
        
        if node_type in ("uml:DecisionNode", "DecisionNode"):
            label_name = f"{clean_name}_Decision"
            self.decision_vars[node_id] = clean_name
            self.declarations.append(f"int {clean_name};")
        elif node_type in ("uml:ForkNode", "ForkNode"):
            label_name = f"{clean_name}_Fork"
            channel_name = f"fork_{clean_name}"
            done_var_name = f"Done_{clean_name}_Fork"
            self.declarations.append(f"broadcast chan {channel_name};")
            self.declarations.append(f"bool {done_var_name};")
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

    def create_fork_template(self, template_name, fork_id, outgoing_edge, node_info, node_types):
        """Creates a new template for forked processes."""
        # Create template with exact name (no counter suffix)
        fork_template = self.create_template(template_name)
        if fork_template not in self.fork_templates:
            self.fork_templates.append(fork_template)
        
        # If template already exists, return it without modifying
        if len(fork_template["state_map"]) > 0:
            return fork_template
        
        initial_id = f"fork_{template_name}"
        self.add_location(fork_template, initial_id, f"InitialNode_{template_name}", "InitialNode")
        
        current_node = outgoing_edge
        processed_nodes = set()
        
        while current_node and current_node not in processed_nodes:
            processed_nodes.add(current_node)
            
            node_name = node_info.get(current_node, "")
            node_type = node_types.get(current_node, "")
            self.add_location(fork_template, current_node, node_name, node_type)
            
            if node_type in ("uml:JoinNode", "JoinNode"):
                join_name = f"JoinNode_{fork_template['name']}"
                self.add_location(fork_template, f"join_{join_name}", join_name, "JoinNode")
                break
            
            # หา node ถัดไป
            next_node = None
            for edge in self.activity_root.findall(".//{*}edge"):
                if edge.get("source") == current_node:
                    next_node = edge.get("target")
                    break
            current_node = next_node
        
        # สร้าง transitions
        locations = fork_template["element"].findall(".//location")
        for i in range(len(locations) - 1):
            source = locations[i].get("id")
            target = locations[i + 1].get("id")
            source_name = node_info.get(source, "")
            target_name = node_info.get(target, "")
            target_type = node_types.get(target, "")
            
            # Add fork? synchronization to initial transition with specific fork channel
            if source == initial_id:
                transition = ET.SubElement(fork_template["element"], "transition")
                ET.SubElement(transition, "source", ref=source)
                ET.SubElement(transition, "target", ref=target)
                x1, y1 = fork_template["position_map"].get(source, (0, 0))
                x2, y2 = fork_template["position_map"].get(target, (0, 0))
                x_mid = (x1 + x2) // 2
                y_mid = (y1 + y2) // 2
                fork_channel = self.fork_channels.get(fork_id, "fork1")  # Get specific fork channel
                ET.SubElement(transition, "label", kind="synchronisation", x=str(x_mid), y=str(y_mid - 80)).text = f"{fork_channel}?"
            else:
                self.add_transition(fork_template, source, target, source_name, target_name, target_type)
        
        return fork_template

    def add_transition(self, template, source_id, target_id, source_name="", target_name="", target_type=""):
        """Adds a transition between two locations in the template."""
        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        
        if source and target:
            trans_id = f"{source_id}_{target_id}"
            transition = ET.SubElement(template["element"], "transition", id=trans_id)
            ET.SubElement(transition, "source", ref=source)
            ET.SubElement(transition, "target", ref=target)

            x1, y1 = template["position_map"].get(source_id, (0, 0))
            x2, y2 = template["position_map"].get(target_id, (0, 0))
            x_mid = (x1 + x2) // 2
            y_mid = (y1 + y2) // 2

            source_type = self.get_node_type(source_id)
            if source_type in ("uml:ForkNode", "ForkNode"):
                # Create new fork channel if not exists for this ForkNode
                if source_id not in self.fork_channels:
                    self.fork_counter += 1
                    fork_channel = f"fork{self.fork_counter}"
                    self.fork_channels[source_id] = fork_channel
                    self.add_declaration(f"broadcast chan {fork_channel};")
                else:
                    fork_channel = self.fork_channels[source_id]
                
                # Count outgoing edges from ForkNode
                outgoing_edges = []
                for edge in self.activity_root.findall(".//{*}edge"):
                    if edge.get("source") == source_id:
                        outgoing_edges.append(edge.get("target"))
                
                # Add Done variables for each outgoing edge
                for i in range(len(outgoing_edges)):
                    template_name = f"Template{i+1}"
                    self.add_declaration(f"bool Done_{template_name};")
                
                # Create fork templates for each outgoing edge
                for i, outgoing_edge in enumerate(outgoing_edges):
                    template_name = f"Template{i+1}"
                    if not any(t["name"] == template_name for t in self.fork_templates):
                        self.create_fork_template(template_name, source_id, outgoing_edge, self.node_info, self.node_types)
                
                # Add synchronisation label with specific fork channel
                ET.SubElement(transition, "label", kind="synchronisation", x=str(x_mid), y=str(y_mid - 80)).text = f"{fork_channel}!"

            if target_type in ("uml:JoinNode", "JoinNode"):
                # Add guard to check if all forked processes are done
                guard_conditions = []
                # Find Process nodes connected to the corresponding ForkNode
                fork_node = None
                process_count = 0
                for edge in self.activity_root.findall(".//{*}edge"):
                    if edge.get("target") == target_id:
                        for node in self.activity_root.findall(".//{*}node"):
                            node_id = node.get("{http://www.omg.org/spec/XMI/20131001}id")
                            if node_id and self.get_node_type(node_id) in ("uml:ForkNode", "ForkNode"):
                                # Count only edges to Process nodes
                                process_count = sum(1 for e in self.activity_root.findall(".//{*}edge") 
                                                 if e.get("source") == node_id 
                                                 and "Process" in self.node_info.get(e.get("target"), ""))
                                if process_count > 0:
                                    fork_node = node_id
                                    break
                        break
                
                if fork_node:
                    for i in range(process_count):
                        template_name = f"Template{i+1}"
                        guard_conditions.append(f"Done_{template_name}==true")
                    if guard_conditions:
                        ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = " && ".join(guard_conditions)

            if "," in source_name and "t=" in source_name:
                try:
                    time_val = int(source_name.split("t=")[-1].strip())
                    clock_name = template["clock_name"]
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 60)).text = f"{clock_name}>{time_val}"
                    ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"{clock_name}:=0"
                    
                    # Add Done variable assignment only for fork templates
                    if template["name"].startswith("Template") and template in self.fork_templates:
                        ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"{clock_name}:=0,\nDone_{template['name']} = true"
                except ValueError:
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

    def get_node_type(self, node_id):
        """Returns the type of node ('uml:DecisionNode', 'uml:ForkNode', 'uml:JoinNode', or '') based on its ID."""
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
        """Generates the final UPPAAL XML with proper formatting."""
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

        # Generate final XML with proper indentation
        def indent(elem, level=0):
            i = "\n" + level*"  "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "  "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for subelem in elem:
                    indent(subelem, level+1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i

        indent(self.nta)
        raw_xml = ET.tostring(self.nta, encoding="utf-8", method="xml").decode()
        header = '<?xml version="1.0" encoding="utf-8"?>\n'
        doctype = '<!DOCTYPE nta PUBLIC \'-//Uppaal Team//DTD Flat System 1.6//EN\' \'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd\'>\n'
        return header + doctype + raw_xml

    def xml_to_json(self, xml_string):
        """Converts XML string to JSON format."""
        root = ET.fromstring(xml_string)
        
        def _xml_to_dict(element):
            result = {}
            
            # Add attributes
            if element.attrib:
                result['@attributes'] = element.attrib
                
            # Add text content if it exists and is not just whitespace
            if element.text and element.text.strip():
                result['#text'] = element.text.strip()
                
            # Process child elements
            for child in element:
                child_data = _xml_to_dict(child)
                child_tag = child.tag
                
                if child_tag in result:
                    if isinstance(result[child_tag], list):
                        result[child_tag].append(child_data)
                    else:
                        result[child_tag] = [result[child_tag], child_data]
                else:
                    result[child_tag] = child_data
                    
            return result
            
        return _xml_to_dict(root)

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

    except ET.ParseError as e:
        return {"error": f"XML parsing error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    import os
    
    # Define input and output folders
    input_file = "Example_XML/ForkJoin.xml"
    base_output_file = "Result/Result_ForkJoin"
    
    # Create Result directory if it doesn't exist
    os.makedirs("Result", exist_ok=True)
    
    # Find next available file number
    counter = 1
    while os.path.exists(f"{base_output_file}_{counter}.xml"):
        counter += 1
    
    output_file = f"{base_output_file}_{counter}.xml"
    
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
        
    except ET.ParseError as e:
        print(f"XML parsing error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
