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
        self.decision_vars = {}  # Store decision variables for each node
        self.location_y_positions = {}  # Track y positions for each location
        self.current_y_offset = 100  # Track current y offset

    def add_declaration(self, text):
        self.declarations.append(text)

    def create_template(self, name="Template"):
        template = ET.Element("template")
        ET.SubElement(template, "name").text = name
        ET.SubElement(template, "declaration").text = "// Local declarations\nclock t;"
        self.templates.append({
            "name": name,
            "element": template,
            "state_map": {},
            "id_counter": 0,
            "x_offset": 0,
            "position_map": {},
            "initial_id": None
        })
        return self.templates[-1]

    def add_location(self, template, node_id, node_name, node_type):
        # Use original node_id instead of generating new one
        loc_id = node_id
        template['state_map'][node_id] = loc_id

        x = template['x_offset']
        
        # Calculate y position based on node type and connections
        if node_type in ("uml:DecisionNode", "DecisionNode"):
            y = self.current_y_offset + 100  # Decision nodes are placed higher
            self.current_y_offset = y  # Update current y offset
        else:
            # Check if this location is connected to a decision node
            is_after_decision = False
            for edge in template["element"].findall(".//transition"):
                if edge.find("target").get("ref") == loc_id:
                    source_id = edge.find("source").get("ref")
                    if source_id in self.decision_vars:
                        is_after_decision = True
                        break
            
            if is_after_decision:
                y = self.current_y_offset + 150  # Locations after decision nodes are placed higher
                self.current_y_offset = y  # Update current y offset
            else:
                y = self.current_y_offset  # Use current y offset for regular nodes

        template['position_map'][node_id] = (x, y)
        self.location_y_positions[node_id] = y

        location = ET.SubElement(template["element"], "location", id=loc_id, x=str(x), y=str(y))
        
        # Clean up node name - replace spaces with underscores
        clean_name = node_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_")
        
        # Add _Decision suffix for decision nodes
        if node_type in ("uml:DecisionNode", "DecisionNode"):
            label_name = f"{clean_name}_Decision"
            # Store decision variable name for this node
            self.decision_vars[node_id] = clean_name
            # Add variable declaration
            self.declarations.append(f"int {clean_name};")
        else:
            label_name = clean_name
            
        ET.SubElement(location, "name", x=str(x - 50), y=str(y - 30)).text = label_name

        if node_type in ("uml:InitialNode", "InitialNode"):
            template["initial_id"] = loc_id

        template['id_counter'] += 1
        template['x_offset'] += 300

    def add_transition(self, template, source_id, target_id, source_name="", target_name="", target_type=""):
        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        if source and target:
            # Use original IDs for transition
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
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 60)).text = f"t>{time_val}"
                    ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = "t:=0"
                except:
                    pass

            edge_label = self.edge_guards.get((source_id, target_id))
            # Get the decision variable name based on target type
            if target_type == "uml:DecisionNode":
                decision_var = target_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_")
            else:
                decision_var = "Is_Success"

            # Check condition from [IsSuccess=Yes] or [IsSuccess=No] format
            if edge_label and "=" in edge_label:
                condition = edge_label.strip("[]").split("=")[1].strip().lower()
                if condition == "yes":
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = f"{decision_var}==Yes"
                elif condition == "no":
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = f"{decision_var}==No"

            if target_type == "uml:DecisionNode":
                var_name = f"i{template['id_counter']}"
                ET.SubElement(transition, "label", kind="select", x=str(x_mid), y=str(y_mid - 100)).text = f"{var_name}: int[0,1]"
                existing_assign = transition.find("label[@kind='assignment']")
                if existing_assign is not None:
                    existing_assign.text += f", {decision_var} = {var_name}"
                else:
                    ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"t:=0, {decision_var} = {var_name}"

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
        main_template = converter.create_template("Template")

        # First collect all node information
        node_info = {}
        node_types = {}
        for node in activity_root.findall(".//{*}node"):
            node_id = node.get("{http://www.omg.org/spec/XMI/20131001}id")
            node_name = node.get("name", "unnamed")
            node_type = node.get("{http://www.omg.org/spec/XMI/20131001}type", node.tag.split("}")[-1])
            node_info[node_id] = node_name
            node_types[node_id] = node_type

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
                converter.add_location(main_template, src, node_info[src], node_types[src])
                processed_nodes.add(src)
            
            # Process target node if not already processed
            if tgt not in processed_nodes:
                converter.add_location(main_template, tgt, node_info[tgt], node_types[tgt])
                processed_nodes.add(tgt)

        # Add transitions after all locations are created
        for src, tgt in edges:
            converter.add_transition(
                main_template, src, tgt,
                source_name=node_info.get(src, ""),
                target_name=node_info.get(tgt, ""),
                target_type=node_types.get(tgt, "")
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
        main_template = converter.create_template("Template")
        
        # First collect all node information
        node_info = {}
        node_types = {}
        for node in activity_root.findall(".//{*}node"):
            node_id = node.get("{http://www.omg.org/spec/XMI/20131001}id")
            node_name = node.get("name", "unnamed")
            node_type = node.get("{http://www.omg.org/spec/XMI/20131001}type", node.tag.split("}")[-1])
            node_info[node_id] = node_name
            node_types[node_id] = node_type

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
                converter.add_location(main_template, src, node_info[src], node_types[src])
                processed_nodes.add(src)
            
            # Process target node if not already processed
            if tgt not in processed_nodes:
                converter.add_location(main_template, tgt, node_info[tgt], node_types[tgt])
                processed_nodes.add(tgt)

        # Add transitions after all locations are created
        for src, tgt in edges:
            converter.add_transition(
                main_template, src, tgt,
                source_name=node_info.get(src, ""),
                target_name=node_info.get(tgt, ""),
                target_type=node_types.get(tgt, "")
            )
        
        # Generate UPPAAL XML
        uppaal_xml = converter.generate_xml()
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(uppaal_xml)
            
        print(f"Successfully converted {input_file} to {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
