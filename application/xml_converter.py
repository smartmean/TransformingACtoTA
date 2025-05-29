"""
Main UPPAAL Converter Application ที่ใช้หลักการ OOP
กู้คืนจาก Main_Beyone_OOP.py ที่ทำงานได้ดี
"""
from typing import Dict, Any
from domain.interfaces import IConverter
from domain.models import ConversionContext
import xml.etree.ElementTree as ET


class xmlConverter(IConverter):
    """
    Main Converter Class ที่ใช้โครงสร้างจาก Main_Beyone_OOP.py ที่ทำงานได้ดี
    """
    
    def __init__(self):
        """Initialize converter with all dependencies"""
        self.nta = ET.Element("nta")
        self.declarations = []
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
        self.fork_counter = 0
        self.created_transitions = set()
        self.name_counter = {}
    
    def convert(self, activity_xml: str) -> str:
        """แปลง Activity Diagram XML เป็น UPPAAL XML"""
        try:
            # Parse XML
            self.activity_root = ET.fromstring(activity_xml)
            
            # Create main template
            main_template = self.create_template("Template")

            # Collect node information
            self.node_info = {}
            self.node_types = {}
            for node in self.activity_root.findall(".//{*}node"):
                node_id = node.get("{http://www.omg.org/spec/XMI/20131001}id")
                node_name = node.get("name", "unnamed")
                node_type = node.get("{http://www.omg.org/spec/XMI/20131001}type", node.tag.split("}")[-1])
                self.node_info[node_id] = node_name
                self.node_types[node_id] = node_type

            # Collect edges
            edges = []
            for edge in self.activity_root.findall(".//{*}edge"):
                src = edge.get("source")
                tgt = edge.get("target")
                label = edge.get("name", "")
                if label:
                    self.edge_guards[(src, tgt)] = label
                edges.append((src, tgt))

            # Create locations in order of edges
            processed_nodes = set()
            for src, tgt in edges:
                if src not in processed_nodes and src in self.node_info and src in self.node_types:
                    self.add_location(main_template, src, self.node_info[src], self.node_types[src])
                    processed_nodes.add(src)
                
                if tgt not in processed_nodes and tgt in self.node_info and tgt in self.node_types:
                    self.add_location(main_template, tgt, self.node_info[tgt], self.node_types[tgt])
                    processed_nodes.add(tgt)

            # Add transitions
            for src, tgt in edges:
                self.add_transition(
                    main_template, src, tgt,
                    source_name=self.node_info.get(src, ""),
                    target_name=self.node_info.get(tgt, ""),
                    target_type=self.node_types.get(tgt, "")
                )

            self.clean_result()
            return self.generate_xml()
            
        except Exception as e:
            raise ValueError(f"Conversion failed: {str(e)}")
    
    def add_declaration(self, text):
        """Adds a declaration to the UPPAAL model."""
        if text not in self.declarations:
            self.declarations.append(text)

    def create_template(self, name="Template"):
        """Creates a new template with unique name and clock."""
        if any(t["name"] == name for t in self.templates):
            return next(t for t in self.templates if t["name"] == name)

        clock_name = "t" if self.clock_counter == 0 else f"t{self.clock_counter}"
        self.clock_counter += 1

        template = ET.Element("template")
        ET.SubElement(template, "name").text = name
        ET.SubElement(template, "declaration").text = f"clock {clock_name};"
        self.templates.append({
            "name": name,
            "element": template,
            "state_map": {},
            "id_counter": 0,
            "x_offset": 0,
            "position_map": {},
            "initial_id": None,
            "clock_name": clock_name
        })
        return self.templates[-1]

    def add_location(self, template, node_id, node_name, node_type):
        """เพิ่ม location เข้าไปใน template"""
        if not node_id or not node_name or not node_type:
            return

        loc_id = node_id
        template['state_map'][node_id] = loc_id

        x = template['x_offset']
        
        if node_type in ("uml:DecisionNode", "DecisionNode", "uml:ForkNode", "ForkNode", "uml:JoinNode", "JoinNode"):
            y = self.current_y_offset + 100
            self.current_y_offset = y
        else:
            is_after_decision = False
            for trans in template["element"].findall(".//transition"):
                if trans.find("target").get("ref") == loc_id:
                    source_id = trans.find("source").get("ref")
                    if source_id in self.decision_vars:
                        is_after_decision = True
                        break
            
            y = self.current_y_offset + 150 if is_after_decision else self.current_y_offset

        template['position_map'][node_id] = (x, y)

        location = ET.SubElement(template["element"], "location", id=loc_id, x=str(x), y=str(y))
        
        clean_name = node_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
        
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
            # ตรวจสอบว่า clean_name มี _Join อยู่แล้วหรือไม่ (แก้ไข Template2 duplicate)
            if clean_name.endswith("_Join"):
                label_name = clean_name  # ไม่เพิ่ม _Join ซ้ำ
            else:
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
        fork_template = self.create_template(template_name)
        if fork_template not in self.fork_templates:
            self.fork_templates.append(fork_template)
        
        if len(fork_template["state_map"]) > 0:
            return fork_template
        
        initial_id = f"fork_{template_name}"
        self.add_location(fork_template, initial_id, f"InitialNode_{template_name}", "InitialNode")
        
        current_node = outgoing_edge
        local_processed_nodes = set()
        
        while current_node and current_node not in local_processed_nodes:
            local_processed_nodes.add(current_node)
            
            current_node_name = node_info.get(current_node, "").replace("?", "")
            current_node_type = node_types.get(current_node, "")
            current_node_id = current_node
            self.add_location(fork_template, current_node_id, current_node_name, current_node_type)
            
            if current_node_type in ("uml:JoinNode", "JoinNode"):
                join_name = f"JoinNode_{fork_template['name']}"
                print(f"JoinNode found: {join_name}")
                break
                
            next_node = None
            for next_edge in self.activity_root.findall(".//{*}edge"):
                if next_edge.get("source") == current_node:
                    next_node = next_edge.get("target")
                    break
            current_node = next_node
        
        # Create transitions
        locations = fork_template["element"].findall(".//location")
        for i in range(len(locations) - 1):
            source = locations[i].get("id")
            target = locations[i + 1].get("id")
            source_name = node_info.get(source, "").replace("?", "")
            target_name = node_info.get(target, "").replace("?", "")
            target_type = node_types.get(target, "")
            
            if source == initial_id:
                transition = ET.SubElement(fork_template["element"], "transition")
                ET.SubElement(transition, "source", ref=source)
                ET.SubElement(transition, "target", ref=target)
                x1, y1 = fork_template["position_map"].get(source, (0, 0))
                x2, y2 = fork_template["position_map"].get(target, (0, 0))
                x_mid = (x1 + x2) // 2
                y_mid = (y1 + y2) // 2
                fork_channel = self.fork_channels.get(fork_id, "fork1")
                ET.SubElement(transition, "label", kind="synchronisation", x=str(x_mid), y=str(y_mid - 80)).text = f"{fork_channel}?"
            else:
                self.add_transition(fork_template, source, target, source_name, target_name, target_type, from_fork_template=True)
        
        return fork_template

    def add_transition(self, template, source_id, target_id, source_name="", target_name="", target_type="", from_fork_template=False):
        """Adds a transition between two locations in the template."""
        if not source_id or not target_id:
            return

        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        
        if source and target:
            trans_key = (source_id, target_id)
            if trans_key in self.created_transitions:
                return
            self.created_transitions.add(trans_key)

            source_type = self.get_node_type(source_id)
            target_type = self.node_types.get(target_id)

            # If this is a transition from ForkNode to OpaqueAction in main template,
            # find the corresponding JoinNode instead
            if (template["name"] == "Template" and 
                source_type in ("uml:ForkNode", "ForkNode") and 
                target_type == "uml:OpaqueAction"):
                
                # Find the JoinNode that this OpaqueAction connects to
                join_node = None
                for edge in self.activity_root.findall(".//{*}edge"):
                    edge_source = edge.get("source")
                    edge_target = edge.get("target")
                    if (edge_source == target_id and  # OpaqueAction is the source
                        self.node_types.get(edge_target) == "uml:JoinNode"):  # Target is JoinNode
                        join_node = edge_target
                        print(f"JoinNode found: {join_node}")
                        break
                
                if join_node:
                    # Create transition to JoinNode instead
                    target = template["state_map"][join_node]

            trans_id = f"{source_id}_{target_id}"
            transition = ET.SubElement(template["element"], "transition", id=trans_id)
            ET.SubElement(transition, "source", ref=source)
            ET.SubElement(transition, "target", ref=target)

            x1, y1 = template["position_map"].get(source_id, (0, 0))
            x2, y2 = template["position_map"].get(target_id, (0, 0))
            x_mid = (x1 + x2) // 2
            y_mid = (y1 + y2) // 2

            # Handle JoinNode guards
            if self.node_types.get(source_id) == "uml:JoinNode":
                guard_conditions = []
                for i, template in enumerate(self.fork_templates):
                    template_name = template["name"]
                    guard_conditions.append(f"Done_{template_name}==true")
                
                if guard_conditions and not from_fork_template:
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = " && ".join(guard_conditions)

            # Handle ForkNode synchronization
            if source_type in ("uml:ForkNode", "ForkNode"):
                if source_id not in self.fork_channels:
                    self.fork_counter += 1
                    fork_channel = f"fork{self.fork_counter}"
                    self.fork_channels[source_id] = fork_channel
                    self.add_declaration(f"broadcast chan {fork_channel};")
                else:
                    fork_channel = self.fork_channels[source_id]
                
                outgoing_edges = []
                for edge in self.activity_root.findall(".//{*}edge"):
                    if edge.get("source") == source_id:
                        outgoing_edges.append(edge.get("target"))
                
                for i in range(len(outgoing_edges)):
                    template_name = f"Template{i+1}"
                    self.add_declaration(f"bool Done_{template_name};")
                
                for i, outgoing_edge in enumerate(outgoing_edges):
                    template_name = f"Template{i+1}"
                    if not any(t["name"] == template_name for t in self.fork_templates):
                        self.create_fork_template(template_name, source_id, outgoing_edge, self.node_info, self.node_types)
                
                ET.SubElement(transition, "label", kind="synchronisation", x=str(x_mid), y=str(y_mid - 80)).text = f"{fork_channel}!"

            # Handle timing constraints from node names
            if "," in source_name and "t=" in source_name:
                try:
                    time_val = int(source_name.split("t=")[-1].strip())
                    clock_name = template["clock_name"]
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 60)).text = f"{clock_name}>{time_val}"
                    ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"{clock_name}:=0"
                    
                    if template["name"].startswith("Template") and template in self.fork_templates:
                        ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"{clock_name}:=0,\nDone_{template['name']} = true"
                except ValueError:
                    pass

            # Handle edge guards
            edge_label = self.edge_guards.get((source_id, target_id))
            if target_type == "uml:DecisionNode":
                decision_var = target_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
            else:
                decision_var = source_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")

            if edge_label and "=" in edge_label:
                condition = edge_label.strip("[]").split("=")[1].strip().lower()
                if condition == "yes":
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = f"{decision_var}==1"
                elif condition == "no":
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = f"{decision_var}==0"

            # Handle decision nodes
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
        """Returns the type of node based on its ID."""
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
        # Clear previous elements
        for elem in list(self.nta):
            self.nta.remove(elem)

        # Create declaration element
        decl_elem = ET.SubElement(self.nta, "declaration")
        decl_elem.text = "\n".join(sorted(set(self.declarations)))

        # Add all templates with proper structure
        for template in self.templates:
            element = template["element"]
            name_el = element.find("name")
            decl_el = element.find("declaration")
            locations = element.findall("location")
            transitions = element.findall("transition")

            # Clear and rebuild template structure
            for child in list(element):
                element.remove(child)

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

        # Create system declaration
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

    def clean_result(self):
        """Removes duplicate transitions and unconnected locations."""
        for template in self.templates:
            if template["name"] == "Template":
                transitions = template["element"].findall(".//transition")
                seen_labels = set()
                connected_locations = set()
                for transition in transitions:
                    source_ref = transition.find("source").get("ref")
                    target_ref = transition.find("target").get("ref")
                    connected_locations.update([source_ref, target_ref])
                    labels = transition.findall("label[@kind='synchronisation']")
                    for label in labels:
                        label_text = label.text
                        if label_text in seen_labels:
                            template["element"].remove(transition)
                            break
                        else:
                            seen_labels.add(label_text)
                
                locations = template["element"].findall(".//location")
                for location in locations:
                    if location.get("id") not in connected_locations:
                        template["element"].remove(location)

        # Remove empty or duplicate declarations
        unique_declarations = []
        for decl in self.declarations:
            if decl and decl not in unique_declarations:
                unique_declarations.append(decl)
        self.declarations = unique_declarations 