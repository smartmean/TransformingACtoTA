"""
High-Performance UPPAAL Converter Application
Optimized version ที่เน้นความเร็วในการแปลง
"""
from typing import Dict, Any, List, Tuple, Set
from domain.interfaces import IConverter
from domain.models import ConversionContext
import xml.etree.ElementTree as ET


class FastXmlConverter(IConverter):
    """
    High-Performance Converter Class เพื่อความเร็วในการแปลง
    Optimizations:
    1. Pre-compile frequently used XPath expressions
    2. Single-pass XML parsing
    3. Optimized data structures
    4. Lazy template creation
    5. Minimal string operations
    """
    
    def __init__(self):
        """Initialize converter with optimized data structures"""
        self.nta = ET.Element("nta")
        # Use lists instead of repeated append operations
        self.declarations: Set[str] = set()  # Use set to avoid duplicates
        self.templates: List[Dict[str, Any]] = []
        self.edge_guards: Dict[Tuple[str, str], str] = {}
        self.decision_vars: Dict[str, str] = {}
        self.current_y_offset = 100
        self.fork_templates: List[Dict[str, Any]] = []
        self.join_nodes: Dict[str, str] = {}
        self.clock_counter = 0
        self.activity_root = None
        # Pre-computed node mappings for O(1) access
        self.node_info: Dict[str, str] = {}
        self.node_types: Dict[str, str] = {}
        self.fork_channels: Dict[str, str] = {}
        self.fork_counter = 0
        self.created_transitions: Set[Tuple[str, str]] = set()
        self.name_counter: Dict[str, int] = {}
        
        # Pre-compiled namespace patterns for faster XML parsing
        self.xmi_id = "{http://www.omg.org/spec/XMI/20131001}id"
        self.xmi_type = "{http://www.omg.org/spec/XMI/20131001}type"
    
    def convert(self, activity_xml: str) -> str:
        """แปลง Activity Diagram XML เป็น UPPAAL XML - Optimized version"""
        try:
            # Single XML parse operation
            self.activity_root = ET.fromstring(activity_xml)
            
            # Single-pass data collection for better performance
            self._collect_all_data()
            
            # Create main template
            main_template = self._create_main_template()
            
            # Process everything in batch for better performance
            self._process_all_nodes(main_template)
            self._process_all_transitions(main_template)
            
            return self._generate_xml_fast()
            
        except Exception as e:
            raise ValueError(f"Conversion failed: {str(e)}")
    
    def _collect_all_data(self):
        """Single-pass collection of all XML data for optimal performance"""
        # Collect nodes and edges in single pass
        for node in self.activity_root.findall(".//{*}node"):
            node_id = node.get(self.xmi_id)
            if node_id:
                self.node_info[node_id] = node.get("name", "unnamed")
                self.node_types[node_id] = node.get(self.xmi_type, node.tag.split("}")[-1])
        
        # Collect edges and guards in single pass
        for edge in self.activity_root.findall(".//{*}edge"):
            src = edge.get("source")
            tgt = edge.get("target")
            label = edge.get("name", "")
            if src and tgt:
                if label:
                    self.edge_guards[(src, tgt)] = label
    
    def _create_main_template(self) -> Dict[str, Any]:
        """Create main template with optimized structure"""
        clock_name = "t"
        template = ET.Element("template")
        ET.SubElement(template, "name").text = "Template"
        ET.SubElement(template, "declaration").text = f"clock {clock_name};"
        
        template_dict = {
            "name": "Template",
            "element": template,
            "state_map": {},
            "id_counter": 0,
            "x_offset": 0,
            "position_map": {},
            "initial_id": None,
            "clock_name": clock_name
        }
        self.templates.append(template_dict)
        return template_dict
    
    def _process_all_nodes(self, template: Dict[str, Any]):
        """Process all nodes efficiently in batch"""
        # Pre-calculate positions to avoid repeated calculations
        x_positions = {}
        y_positions = {}
        
        processed_nodes = set()
        for edge in self.activity_root.findall(".//{*}edge"):
            src = edge.get("source")
            tgt = edge.get("target")
            
            for node_id in [src, tgt]:
                if (node_id and node_id not in processed_nodes and 
                    node_id in self.node_info and node_id in self.node_types):
                    
                    self._add_location_fast(template, node_id)
                    processed_nodes.add(node_id)
    
    def _process_all_transitions(self, template: Dict[str, Any]):
        """Process all transitions efficiently in batch"""
        transitions_to_create = []
        
        # Collect all transitions first
        for edge in self.activity_root.findall(".//{*}edge"):
            src = edge.get("source")
            tgt = edge.get("target")
            if src and tgt and (src, tgt) not in self.created_transitions:
                transitions_to_create.append((src, tgt))
        
        # Create transitions in batch
        for src, tgt in transitions_to_create:
            self._add_transition_fast(template, src, tgt)
    
    def _add_location_fast(self, template: Dict[str, Any], node_id: str):
        """Optimized location creation"""
        node_name = self.node_info[node_id]
        node_type = self.node_types[node_id]
        
        # Pre-calculate position
        x = template['x_offset']
        y = self.current_y_offset
        
        if node_type in ("uml:DecisionNode", "DecisionNode", "uml:ForkNode", "ForkNode", "uml:JoinNode", "JoinNode"):
            y += 100
            self.current_y_offset = y
        
        template['state_map'][node_id] = node_id
        template['position_map'][node_id] = (x, y)
        
        # Create location element efficiently
        location = ET.SubElement(template["element"], "location", id=node_id, x=str(x), y=str(y))
        
        # Optimized name cleaning
        clean_name = node_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
        
        # Handle special node types with minimal string operations
        if node_type in ("uml:DecisionNode", "DecisionNode"):
            label_name = f"{clean_name}_Decision"
            self.decision_vars[node_id] = clean_name
            self.declarations.add(f"int {clean_name};")
        elif node_type in ("uml:ForkNode", "ForkNode"):
            label_name = f"{clean_name}_Fork"
            channel_name = f"fork_{clean_name}"
            done_var_name = f"Done_{clean_name}_Fork"
            self.declarations.add(f"broadcast chan {channel_name};")
            self.declarations.add(f"bool {done_var_name};")
            self.fork_channels[node_id] = channel_name
        elif node_type in ("uml:JoinNode", "JoinNode"):
            label_name = f"{clean_name}_Join" if not clean_name.endswith("_Join") else clean_name
            self.join_nodes[node_id] = template['name']
        else:
            label_name = clean_name
        
        ET.SubElement(location, "name", x=str(x - 50), y=str(y - 30)).text = label_name
        
        if node_type in ("uml:InitialNode", "InitialNode"):
            template["initial_id"] = node_id
        
        template['x_offset'] += 300
    
    def _add_transition_fast(self, template: Dict[str, Any], source_id: str, target_id: str):
        """Optimized transition creation"""
        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        
        if not (source and target):
            return
        
        trans_key = (source_id, target_id)
        if trans_key in self.created_transitions:
            return
        self.created_transitions.add(trans_key)
        
        # Create transition element
        transition = ET.SubElement(template["element"], "transition", id=f"{source_id}_{target_id}")
        ET.SubElement(transition, "source", ref=source)
        ET.SubElement(transition, "target", ref=target)
        
        # Pre-calculate positions
        x1, y1 = template["position_map"].get(source_id, (0, 0))
        x2, y2 = template["position_map"].get(target_id, (0, 0))
        x_mid, y_mid = (x1 + x2) // 2, (y1 + y2) // 2
        
        self._add_transition_labels_fast(transition, source_id, target_id, x_mid, y_mid, template)
    
    def _add_transition_labels_fast(self, transition: ET.Element, source_id: str, target_id: str, 
                                  x_mid: int, y_mid: int, template: Dict[str, Any]):
        """Optimized transition label creation"""
        source_type = self.node_types.get(source_id, "")
        target_type = self.node_types.get(target_id, "")
        source_name = self.node_info.get(source_id, "")
        target_name = self.node_info.get(target_id, "")
        
        # Handle fork nodes
        if source_type in ("uml:ForkNode", "ForkNode"):
            self._handle_fork_transition(transition, source_id, x_mid, y_mid)
        
        # Handle decision nodes
        if target_type in ("uml:DecisionNode", "DecisionNode"):
            self._handle_decision_transition(transition, target_name, x_mid, y_mid, template)
        
        # Handle timing constraints
        if "," in source_name and "t=" in source_name:
            self._handle_timing_transition(transition, source_name, x_mid, y_mid, template)
        
        # Handle edge guards
        edge_label = self.edge_guards.get((source_id, target_id))
        if edge_label and "=" in edge_label:
            self._handle_guard_transition(transition, edge_label, source_name, x_mid, y_mid)
    
    def _handle_fork_transition(self, transition: ET.Element, source_id: str, x_mid: int, y_mid: int):
        """Handle fork node transitions efficiently"""
        if source_id not in self.fork_channels:
            self.fork_counter += 1
            fork_channel = f"fork{self.fork_counter}"
            self.fork_channels[source_id] = fork_channel
            self.declarations.add(f"broadcast chan {fork_channel};")
        else:
            fork_channel = self.fork_channels[source_id]
        
        ET.SubElement(transition, "label", kind="synchronisation", 
                     x=str(x_mid), y=str(y_mid - 80)).text = f"{fork_channel}!"
    
    def _handle_decision_transition(self, transition: ET.Element, target_name: str, 
                                  x_mid: int, y_mid: int, template: Dict[str, Any]):
        """Handle decision node transitions efficiently"""
        decision_var = target_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
        var_name = f"i{template['id_counter']}"
        
        ET.SubElement(transition, "label", kind="select", 
                     x=str(x_mid), y=str(y_mid - 100)).text = f"{var_name}: int[0,1]"
        
        clock_name = template["clock_name"]
        ET.SubElement(transition, "label", kind="assignment", 
                     x=str(x_mid), y=str(y_mid - 40)).text = f"{clock_name}:=0, {decision_var} = {var_name}"
    
    def _handle_timing_transition(self, transition: ET.Element, source_name: str, 
                                x_mid: int, y_mid: int, template: Dict[str, Any]):
        """Handle timing constraint transitions efficiently"""
        try:
            time_val = int(source_name.split("t=")[-1].strip())
            clock_name = template["clock_name"]
            ET.SubElement(transition, "label", kind="guard", 
                         x=str(x_mid), y=str(y_mid - 60)).text = f"{clock_name}>{time_val}"
            ET.SubElement(transition, "label", kind="assignment", 
                         x=str(x_mid), y=str(y_mid - 40)).text = f"{clock_name}:=0"
        except ValueError:
            pass
    
    def _handle_guard_transition(self, transition: ET.Element, edge_label: str, 
                               source_name: str, x_mid: int, y_mid: int):
        """Handle guard transitions efficiently"""
        decision_var = source_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
        condition = edge_label.strip("[]").split("=")[1].strip().lower()
        
        guard_text = f"{decision_var}==1" if condition == "yes" else f"{decision_var}==0"
        ET.SubElement(transition, "label", kind="guard", 
                     x=str(x_mid), y=str(y_mid - 80)).text = guard_text
    
    def _generate_xml_fast(self) -> str:
        """Fast XML generation with optimized formatting"""
        # Clear previous elements
        for elem in list(self.nta):
            self.nta.remove(elem)
        
        # Create declaration element efficiently
        decl_elem = ET.SubElement(self.nta, "declaration")
        decl_elem.text = "\n".join(sorted(self.declarations))
        
        # Add templates efficiently
        for template in self.templates:
            element = template["element"]
            if template["initial_id"]:
                ET.SubElement(element, "init", ref=template["initial_id"])
            self.nta.append(element)
        
        # Create system declaration efficiently
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
        
        # Enhanced XML generation with proper formatting
        def indent_xml(elem, level=0):
            """Proper XML indentation"""
            i = "\n" + level * "  "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "  "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for subelem in elem:
                    indent_xml(subelem, level + 1)
                if not subelem.tail or not subelem.tail.strip():
                    subelem.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i
        
        # Apply proper indentation
        indent_xml(self.nta)
        
        # Generate XML with proper encoding and method
        raw_xml = ET.tostring(self.nta, encoding="unicode", method="xml")
        
        # Fix XML truncation issues (Python ElementTree bug)
        raw_xml = raw_xml.replace("<n>", "<name>").replace("</n>", "</name>")
        raw_xml = raw_xml.replace("<s>", "<system>").replace("</s>", "</system>")
        
        # Add proper headers
        header = '<?xml version="1.0" encoding="utf-8"?>\n'
        doctype = '<!DOCTYPE nta PUBLIC \'-//Uppaal Team//DTD Flat System 1.6//EN\' \'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd\'>\n'
        
        return header + doctype + raw_xml 