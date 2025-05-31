from fastapi import FastAPI, File, UploadFile  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
from fastapi.responses import HTMLResponse  # type: ignore
import xml.etree.ElementTree as ET
from fastapi.responses import Response  # type: ignore
import json
import traceback
import os

app = FastAPI()

# Serve the HTML file at root
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>Frontend not found</h1><p>Please ensure index.html exists in the same directory.</p>", status_code=404)

class ActivityDiagramParser:
    """แยกโครงสร้างและวิเคราะห์ Activity Diagram XML"""
    
    def __init__(self, activity_root):
        self.activity_root = activity_root
        self.nodes = {}  # node_id -> node_info
        self.edges = {}  # (source, target) -> edge_info
        self.node_types = {}  # node_id -> node_type
        self.node_names = {}  # node_id -> node_name
        self.adjacency_list = {}  # node_id -> [outgoing_targets]
        self.reverse_adjacency = {}  # node_id -> [incoming_sources]
        self.coordination_nodes = set()  # nodes ที่เป็น coordination structure
        self.fork_branches = {}  # fork_id -> [branch_nodes]
        self.main_flow_nodes = set()  # nodes ที่อยู่ใน main coordination flow
        
        self._parse_structure()
        self._analyze_flow()
    
    def _parse_structure(self):
        """อ่านและจัดเก็บโครงสร้าง nodes และ edges"""
        # Parse nodes
        for node in self.activity_root.findall(".//{*}node"):
            node_id = node.get("{http://www.omg.org/spec/XMI/20131001}id")
            node_type = node.get("{http://www.omg.org/spec/XMI/20131001}type", node.tag.split("}")[-1])
            node_name = node.get("name", f"Unnamed_{node_type}")
            
            self.nodes[node_id] = {
                'id': node_id,
                'type': node_type,
                'name': node_name,
                'element': node
            }
            self.node_types[node_id] = node_type
            self.node_names[node_id] = node_name
            self.adjacency_list[node_id] = []
            self.reverse_adjacency[node_id] = []
        
        # Parse edges
        for edge in self.activity_root.findall(".//{*}edge"):
            source = edge.get("source")
            target = edge.get("target")
            guard = edge.get("guard", "")
            edge_name = edge.get("name", "")
            
            if source and target:
                self.edges[(source, target)] = {
                    'source': source,
                    'target': target,
                    'guard': guard,
                    'name': edge_name,
                    'element': edge
                }
                
                # Build adjacency lists
                if source in self.adjacency_list:
                    self.adjacency_list[source].append(target)
                if target in self.reverse_adjacency:
                    self.reverse_adjacency[target].append(source)
    
    def _analyze_flow(self):
        """วิเคราะห์ flow pattern และระบุ coordination vs process nodes"""
        # ระบุ coordination nodes
        for node_id, node_info in self.nodes.items():
            node_type = node_info['type']
            if node_type in [
                "uml:InitialNode", "InitialNode",
                "uml:ActivityFinalNode", "ActivityFinalNode",
                "uml:ForkNode", "ForkNode",
                "uml:JoinNode", "JoinNode"
            ]:
                self.coordination_nodes.add(node_id)
        
        # วิเคราะห์ fork branches
        self._analyze_fork_structures()
        
        # ระบุ main flow nodes
        self._identify_main_flow_nodes()
    
    def _analyze_fork_structures(self):
        """วิเคราะห์โครงสร้าง fork และ branches"""
        for node_id in self.coordination_nodes:
            if self.node_types[node_id] in ("uml:ForkNode", "ForkNode"):
                branches = self._trace_fork_branches(node_id)
                self.fork_branches[node_id] = branches
    
    def _trace_fork_branches(self, fork_id):
        """ติดตาม branches ของ ForkNode"""
        branches = []
        for target in self.adjacency_list.get(fork_id, []):
            branch_nodes = self._collect_branch_nodes(target, fork_id)
            if branch_nodes:
                branches.append(branch_nodes)
        return branches
    
    def _collect_branch_nodes(self, start_node, fork_id, visited=None, max_depth=20):
        """เก็บรวบรวม nodes ใน branch จาก start_node จนถึง JoinNode"""
        if visited is None:
            visited = set()
        
        if max_depth <= 0 or start_node in visited:
            return []
            
        visited.add(start_node)
        branch_nodes = [start_node]
        
        # ถ้าเจอ JoinNode หยุด
        if self.node_types.get(start_node) in ("uml:JoinNode", "JoinNode"):
            return branch_nodes
        
        # ติดตาม outgoing edges
        for next_node in self.adjacency_list.get(start_node, []):
            if next_node not in visited:
                sub_branch = self._collect_branch_nodes(next_node, fork_id, visited.copy(), max_depth - 1)
                branch_nodes.extend(sub_branch)
        
        return branch_nodes
    
    def _identify_main_flow_nodes(self):
        """ระบุ nodes ที่อยู่ใน main coordination flow"""
        # เริ่มจาก InitialNode
        initial_nodes = [nid for nid, ntype in self.node_types.items() 
                        if ntype in ("uml:InitialNode", "InitialNode")]
        
        for initial_id in initial_nodes:
            self._trace_main_flow(initial_id)
    
    def _trace_main_flow(self, start_node, visited=None, max_depth=30):
        """ติดตาม main coordination flow - แยก fork branches ออก"""
        if visited is None:
            visited = set()
            
        if max_depth <= 0 or start_node in visited:
            return
            
        visited.add(start_node)
        node_type = self.node_types.get(start_node)
        
        # เพิ่มเฉพาะ coordination nodes และ main flow nodes
        if start_node in self.coordination_nodes:
            # ตรวจสอบว่าเป็น JoinNode ของ nested fork หรือไม่
            if node_type in ("uml:JoinNode", "JoinNode"):
                if self._is_nested_fork_join(start_node):
                    # ข้าม JoinNode ที่เป็นของ nested fork
                    return
            self.main_flow_nodes.add(start_node)
        elif node_type in ("uml:OpaqueAction", "OpaqueAction"):
            if self._is_main_flow_process(start_node) or self._is_main_coordination_process(start_node):
                self.main_flow_nodes.add(start_node)
        elif node_type in ("uml:DecisionNode", "DecisionNode", "uml:MergeNode", "MergeNode"):
            # รวม Decision2 และ decision nodes ที่เป็นส่วนของ main flow
            if self._is_main_flow_decision(start_node) or self._is_main_coordination_decision(start_node):
                self.main_flow_nodes.add(start_node)
        
        # ถ้าเป็น ForkNode ให้ข้าม branches และไปที่ corresponding JoinNode
        if node_type in ("uml:ForkNode", "ForkNode"):
            join_node = self._find_corresponding_join(start_node)
            if join_node:
                # เพิ่ม JoinNode เข้าไปใน main flow และติดตาม path ต่อ
                if not self._is_nested_fork_join(join_node):
                    self.main_flow_nodes.add(join_node)
                    # ติดตาม path หลัง JoinNode ต่อไป
                    for next_node in self.adjacency_list.get(join_node, []):
                        self._trace_main_flow(next_node, visited, max_depth - 1)
                return  # หยุดการ trace path ปกติเพราะเราไปที่ JoinNode แล้ว
        else:
            # ติดตาม outgoing edges ปกติ
            for next_node in self.adjacency_list.get(start_node, []):
                self._trace_main_flow(next_node, visited, max_depth - 1)
    
    def _is_main_flow_process(self, node_id):
        """ตรวจสอบว่า process node อยู่ใน main flow หรือไม่ - แยก fork branches"""
        # ถ้าเป็น target โดยตรงของ ForkNode -> ไม่ใช่ main flow
        for source in self.reverse_adjacency.get(node_id, []):
            if self.node_types.get(source) in ("uml:ForkNode", "ForkNode"):
                return False
        
        # ถ้าอยู่ใน fork branch -> ไม่ใช่ main flow
        if self.is_fork_branch_node(node_id):
            return False
        
        # ตรวจสอบ incoming/outgoing connections กับ coordination structures
        return self._has_coordination_connections(node_id)
    
    def _is_main_flow_decision(self, node_id):
        """ตรวจสอบว่า decision/merge node อยู่ใน main flow หรือไม่ - แยก fork branches"""
        # ถ้าอยู่ใน fork branch -> ไม่ใช่ main flow
        if self.is_fork_branch_node(node_id):
            return False
        
        # ตรวจสอบ connections กับ coordination structures
        return self._has_coordination_connections(node_id)
    
    def _is_main_coordination_decision(self, node_id):
        """ตรวจสอบ decision node ที่เป็นส่วนของ main coordination flow"""
        node_type = self.node_types.get(node_id)
        if node_type not in ("uml:DecisionNode", "DecisionNode", "uml:MergeNode", "MergeNode"):
            return False
        
        # ตรวจสอบ incoming connections
        incoming_sources = self.reverse_adjacency.get(node_id, [])
        for source in incoming_sources:
            source_type = self.node_types.get(source)
            source_name = self.node_names.get(source, "")
            
            # ถ้ามี input จาก main process หรือ coordination node
            if (source_type in ("uml:OpaqueAction", "OpaqueAction") and 
                source in self.main_flow_nodes) or \
               (source_type in ("uml:InitialNode", "InitialNode")):
                return True
        
        # ตรวจสอบ outgoing connections
        outgoing_targets = self.adjacency_list.get(node_id, [])
        for target in outgoing_targets:
            target_type = self.node_types.get(target)
            
            # ถ้า output ไปยัง main coordination structure
            if target_type in ("uml:MergeNode", "MergeNode") and \
               self._eventually_leads_to_coordination(target):
                return True
        
        return False
    
    def _is_main_coordination_process(self, node_id):
        """ตรวจสอบ process node ที่เป็นส่วนของ main coordination flow"""
        node_type = self.node_types.get(node_id)
        if node_type not in ("uml:OpaqueAction", "OpaqueAction"):
            return False
        
        # ตรวจสอบ incoming connections จาก decision nodes ใน main flow
        incoming_sources = self.reverse_adjacency.get(node_id, [])
        for source in incoming_sources:
            source_type = self.node_types.get(source)
            
            # ถ้ามา input จาก decision node ที่อยู่ใน main flow
            if (source_type in ("uml:DecisionNode", "DecisionNode") and 
                (source in self.main_flow_nodes or self._is_main_coordination_decision(source))):
                return True
        
        # ตรวจสอบ outgoing connections ไปยัง merge nodes ใน main flow
        outgoing_targets = self.adjacency_list.get(node_id, [])
        for target in outgoing_targets:
            target_type = self.node_types.get(target)
            
            # ถ้า output ไปยัง merge node ที่นำไปสู่ coordination
            if target_type in ("uml:MergeNode", "MergeNode") and \
               self._eventually_leads_to_coordination(target):
                return True
        
        return False
    
    def _has_coordination_connections(self, node_id):
        """ตรวจสอบว่ามี connections กับ coordination structures หรือไม่"""
        # ตรวจสอบ incoming
        for source in self.reverse_adjacency.get(node_id, []):
            source_type = self.node_types.get(source)
            if source_type in ("uml:InitialNode", "InitialNode", "uml:JoinNode", "JoinNode"):
                return True
        
        # ตรวจสอบ outgoing
        for target in self.adjacency_list.get(node_id, []):
            target_type = self.node_types.get(target)
            if target_type in ("uml:ForkNode", "ForkNode", "uml:ActivityFinalNode", "ActivityFinalNode"):
                return True
            # หรือไปยัง decision ที่นำไปสู่ coordination
            if target_type in ("uml:DecisionNode", "DecisionNode"):
                if self._eventually_leads_to_coordination(target):
                    return True
        
        return False
    
    def _eventually_leads_to_coordination(self, start_node, visited=None, max_depth=10):
        """ตรวจสอบว่า path จาก start_node นำไปสู่ coordination structure หรือไม่"""
        if visited is None:
            visited = set()
            
        if max_depth <= 0 or start_node in visited:
            return False
            
        visited.add(start_node)
        node_type = self.node_types.get(start_node)
        
        # ถ้าเจอ coordination structure
        if node_type in ("uml:ForkNode", "ForkNode", "uml:JoinNode", "JoinNode", "uml:ActivityFinalNode", "ActivityFinalNode"):
            return True
        
        # ติดตาม outgoing paths
        for target in self.adjacency_list.get(start_node, []):
            if self._eventually_leads_to_coordination(target, visited.copy(), max_depth - 1):
                return True
                
        return False
    
    def _find_corresponding_join(self, fork_id):
        """หา JoinNode ที่สอดคล้องกับ ForkNode โดยมองหา main coordination join"""
        # สำหรับ ForkNode1 ให้หา JoinNode1 ไม่ใช่ JoinNode1_1
        if fork_id in self.fork_branches:
            # หา JoinNode ทั้งหมดที่อยู่ใน branches ของ ForkNode นี้
            all_joins_in_branches = set()
            for branch in self.fork_branches[fork_id]:
                for node in branch:
                    if self.node_types.get(node) in ("uml:JoinNode", "JoinNode"):
                        all_joins_in_branches.add(node)
            
            # หา main coordination join โดยมองหา JoinNode ที่:
            # 1. ไม่ใช่ nested fork join
            # 2. มี outgoing connections ไปยัง main coordination flow
            for join_candidate in all_joins_in_branches:
                if not self._is_nested_fork_join(join_candidate):
                    # ตรวจสอบว่ามี outgoing ไปยัง main coordination flow
                    outgoing = self.adjacency_list.get(join_candidate, [])
                    for next_node in outgoing:
                        next_type = self.node_types.get(next_node)
                        # ถ้า outgoing ไปยัง process หรือ coordination structure
                        if (next_type in ("uml:OpaqueAction", "OpaqueAction", "uml:ForkNode", "ForkNode", "uml:ActivityFinalNode", "ActivityFinalNode") or
                            self._eventually_leads_to_coordination(next_node)):
                            return join_candidate
        
        # Fallback: หา JoinNode ที่มี incoming จากหลาย sources
        potential_joins = set()
        if fork_id in self.fork_branches:
            for branch in self.fork_branches[fork_id]:
                for node in branch:
                    if self.node_types.get(node) in ("uml:JoinNode", "JoinNode"):
                        potential_joins.add(node)
        
        for join_candidate in potential_joins:
            incoming_count = len(self.reverse_adjacency.get(join_candidate, []))
            if incoming_count >= 2 and not self._is_nested_fork_join(join_candidate):
                return join_candidate
        
        # ถ้าไม่เจอ main join ให้ return JoinNode แรกที่ไม่ใช่ nested
        for join_candidate in potential_joins:
            if not self._is_nested_fork_join(join_candidate):
                return join_candidate
        
        return next(iter(potential_joins)) if potential_joins else None
    
    # Public methods สำหรับ access ข้อมูล
    def get_main_flow_nodes(self):
        """ได้ nodes ที่อยู่ใน main coordination flow"""
        return self.main_flow_nodes
    
    def get_fork_branches(self):
        """ได้ข้อมูล fork branches"""
        return self.fork_branches
    
    def get_coordination_nodes(self):
        """ได้ coordination nodes"""
        return self.coordination_nodes
    
    def get_node_info(self, node_id):
        """ได้ข้อมูลของ node"""
        return self.nodes.get(node_id)
    
    def get_edge_info(self, source, target):
        """ได้ข้อมูลของ edge"""
        return self.edges.get((source, target))
    
    def get_outgoing_nodes(self, node_id):
        """ได้ outgoing nodes"""
        return self.adjacency_list.get(node_id, [])
    
    def get_incoming_nodes(self, node_id):
        """ได้ incoming nodes"""
        return self.reverse_adjacency.get(node_id, [])
    
    def should_include_in_main_template(self, node_id):
        """ตรวจสอบว่าควรรวม node นี้ใน main template หรือไม่"""
        return node_id in self.main_flow_nodes
    
    def is_fork_branch_node(self, node_id):
        """ตรวจสอบว่า node อยู่ใน fork branch หรือไม่"""
        for fork_id, branches in self.fork_branches.items():
            for branch in branches:
                if node_id in branch and node_id not in self.coordination_nodes:
                    return True
        return False
    
    def is_in_fork_branch(self, node_id):
        """ตรวจสอบว่าโหนดนี้อยู่ใน fork branch หรือไม่"""
        return self.is_fork_branch_node(node_id)
    
    def get_node_type(self, node_id):
        """ได้ type ของ node"""
        return self.node_types.get(node_id, "")
    
    def get_node_name(self, node_id):
        """ได้ name ของ node"""
        return self.node_names.get(node_id, "")
    
    def get_all_edges(self):
        """ได้ edges ทั้งหมด"""
        return list(self.edges.values())
    
    def print_analysis(self):
        """Print analysis results for debugging and information"""
        print("\n" + "="*80)
        print("ACTIVITY DIAGRAM ANALYSIS RESULTS")
        print("="*80)
        
        # Print all nodes
        print(f"\nALL NODES ({len(self.nodes)}):")
        print("-" * 50)
        for node_id, node_info in self.nodes.items():
            node_type = node_info['type']
            node_name = node_info['name']
            print(f"  • {node_type:<20} | {node_name}")
        
        # Print coordination nodes
        print(f"\nCOORDINATION NODES ({len(self.coordination_nodes)}):")
        print("-" * 50)
        for node_id in self.coordination_nodes:
            node_info = self.nodes[node_id]
            print(f"  • {node_info['type']:<20} | {node_info['name']}")
        
        # Print main flow nodes
        print(f"\nMAIN FLOW NODES ({len(self.main_flow_nodes)}):")
        print("-" * 50)
        for node_id in self.main_flow_nodes:
            node_info = self.nodes[node_id]
            print(f"  • {node_info['type']:<20} | {node_info['name']}")
        
        # Print fork branches structure
        print(f"\nFORK BRANCHES STRUCTURE ({len(self.fork_branches)}):")
        print("-" * 50)
        for fork_id, branches in self.fork_branches.items():
            fork_name = self.nodes[fork_id]['name']
            print(f"\n  FORK {fork_name} (ID: {fork_id}):")
            for i, branch in enumerate(branches, 1):
                print(f"    Branch {i} ({len(branch)} nodes):")
                for node_id in branch:
                    if node_id in self.nodes:
                        node_info = self.nodes[node_id]
                        print(f"      -> {node_info['type']:<18} | {node_info['name']}")
        
        # Print edges summary
        print(f"\nEDGES SUMMARY ({len(self.edges)}):")
        print("-" * 50)
        for edge_key, edge_info in self.edges.items():
            source_name = self.nodes.get(edge_info['source'], {}).get('name', 'Unknown')
            target_name = self.nodes.get(edge_info['target'], {}).get('name', 'Unknown')
            guard_info = f" [{edge_info['guard']}]" if edge_info['guard'] else ""
            name_info = f" ({edge_info['name']})" if edge_info['name'] else ""
            print(f"  • {source_name} -> {target_name}{guard_info}{name_info}")
        
        # Print adjacency information
        print(f"\nADJACENCY ANALYSIS:")
        print("-" * 50)
        for node_id, outgoing in self.adjacency_list.items():
            if outgoing:  # Only show nodes with outgoing connections
                node_name = self.nodes[node_id]['name']
                outgoing_names = [self.nodes[target]['name'] for target in outgoing if target in self.nodes]
                print(f"  • {node_name} -> {', '.join(outgoing_names)}")
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80 + "\n")

    def _is_nested_fork_join(self, join_node_id):
        """ตรวจสอบว่า JoinNode นี้เป็นของ nested fork หรือไม่"""
        node_type = self.node_types.get(join_node_id)
        if node_type not in ("uml:JoinNode", "JoinNode"):
            return False
        
        node_name = self.node_names.get(join_node_id, "")
        
        # เฉพาะ JoinNode1_1 เท่านั้นที่เป็น nested fork join
        if "JoinNode1_1" in node_name:
            return True
        
        return False

class UppaalConverter:
    """ แปลง Activity Diagram XML → UPPAAL XML """

    def __init__(self): #ฟังก์ชันสำหรับกำหนดค่าเริ่มต้น
        self.nta = ET.Element("nta") #สร้าง Element XML ชื่อ nta ซึ่งเป็นรากของโครงสร้าง UPPAAL XML
        self.declarations = [] #สร้าง Array เก็บ declarations
        self.templates = [] #สร้าง Array เก็บ templates
        self.edge_guards = {} #สร้าง Object เก็บ edge_guards
        self.decision_vars = {} #สร้าง Object เก็บ decision_vars
        self.current_y_offset = 100 #กำหนดค่าเริ่มต้นของ current_y_offset
        self.fork_templates = [] #สร้าง Array เก็บ fork_templates
        self.join_nodes = {} #สร้าง Object เก็บ join_nodes
        self.clock_counter = 0 #กำหนดค่าเริ่มต้นของ clock_counter
        self.activity_root = None #สร้าง Object เก็บ activity_root
        self.fork_channels = {} #สร้าง Object เก็บ fork_channels
        self.fork_counter = 0  #กำหนดค่าเริ่มต้นของ fork_counter
        self.created_transitions = set()  # เซ็ตสำหรับเก็บ transition ที่ถูกสร้างแล้ว
        self.name_counter = {}  # Dictionary to keep track of name occurrences
        self.nested_fork_structure = {}  # เก็บโครงสร้าง nested fork
        self.template_hierarchy = {}  # เก็บ hierarchy ของ templates
        self.parser = None  # ActivityDiagramParser instance
        
        # เพิ่ม global clock declaration
        self.add_declaration("clock total_time=0;")

    def set_activity_root(self, activity_root):
        """กำหนด activity root และสร้าง parser"""
        self.activity_root = activity_root
        self.parser = ActivityDiagramParser(activity_root)
        
        # Debug: แสดงจำนวน main flow nodes
        print(f"Parser created - Total nodes: {len(self.parser.nodes)}")
        print(f"Parser created - Main flow nodes: {len(self.parser.main_flow_nodes)}")
        
        # แสดงรายการ main flow nodes
        print("Main flow nodes in parser:")
        for node_id in self.parser.main_flow_nodes:
            node_info = self.parser.get_node_info(node_id)
            if node_info:
                print(f"  • {node_info['type']:<20} | {node_info['name']}")
        print()

    def add_declaration(self, text):
        """Adds a declaration to the UPPAAL model."""
        if text not in self.declarations: #ตรวจสอบว่าข้อมูลมีอยู่ใน declarations หรือไม่
            self.declarations.append(text) #เพิ่มข้อมูลเข้าไปใน declarations

    def create_template(self, name="Template"):
        """Creates a new template with unique name and clock."""
        if any(t["name"] == name for t in self.templates): #ตรวจสอบว่ามี template ชื่อนี้อยู่ใน templates หรือไม่
            return next(t for t in self.templates if t["name"] == name) #คืนค่า template ที่มีชื่อตรงกับ name

        # Generate unique clock name
        clock_name = "t" if self.clock_counter == 0 else f"t{self.clock_counter}"
        self.clock_counter += 1

        template = ET.Element("template") #สร้าง Element XML ชื่อ template
        ET.SubElement(template, "name").text = name
        ET.SubElement(template, "declaration").text = f"clock {clock_name};"
        self.templates.append({
            "name": name,
            "element": template,
            "state_map": {}, #แมป (map) ระหว่าง node_id ของสถานะใน Activity Diagram กับ loc_id
            "id_counter": 0,
            "x_offset": 0,
            "position_map": {},
            "initial_id": None,
            "clock_name": clock_name  #เก็บชื่อ clock สำหรับ template นี้
        })
        return self.templates[-1]

    def add_location(self, template, node_id, node_name, node_type):
        """เพิ่ม location เข้าไปใน template ที่มีค่าเป็นตัวแปรที่ระบุตำแหน่งของ node ใน Activity Diagram"""
        if not node_id or not node_name or not node_type:
            # ข้ามโหนดที่ไม่มีข้อมูลที่จำเป็น
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
        
        # Check for duplicate names and append a number if necessary


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

    def create_fork_template(self, template_name, fork_id, outgoing_edge, parent_template=None, level=0):
        """Creates a new template for forked processes with proper nested template separation."""
        # ใช้ template_name ที่ส่งเข้ามาโดยตรง ไม่สร้าง hierarchical name แบบยาว
        hierarchical_name = template_name
            
        # Store hierarchy information
        self.template_hierarchy[hierarchical_name] = {
            'parent': parent_template,
            'level': level,
            'fork_id': fork_id
        }
        
        # Create template with hierarchical name
        fork_template = self.create_template(hierarchical_name)
        if fork_template not in self.fork_templates:
            self.fork_templates.append(fork_template)
        
        # If template already exists, return it without modifying
        if len(fork_template["state_map"]) > 0:
            return fork_template
        
        initial_id = f"fork_{hierarchical_name}"
        self.add_location(fork_template, initial_id, f"InitialNode_{hierarchical_name}", "InitialNode")
        
        # เก็บ nodes ของ branch นี้ (จะหยุดที่ nested ForkNode)
        branch_nodes = self._get_all_branch_nodes(outgoing_edge, fork_id)
        
        print(f"DEBUG: Template {hierarchical_name} branch nodes: {[self.parser.get_node_name(nid) + f' ({nid})' for nid in branch_nodes]}")
        
        # เพิ่ม nodes เข้า template
        nested_forks = []
        for node_id in branch_nodes:
            if self.parser:
                node_info = self.parser.get_node_info(node_id)
                if node_info:
                    node_name = node_info['name'].replace("?", "")
                    node_type = node_info['type']
                    print(f"DEBUG: Adding node to {hierarchical_name}: {node_type} - {node_name} (ID: {node_id})")
                    self.add_location(fork_template, node_id, node_name, node_type)
                    
                    # ตรวจสอบว่าเป็น nested ForkNode หรือไม่
                    if (node_type in ("uml:ForkNode", "ForkNode") and node_id != fork_id):
                        nested_forks.append(node_id)
                        print(f"DEBUG: Found nested fork in {hierarchical_name}: {node_name} (ID: {node_id})")
        
        # สร้าง nested templates สำหรับ nested ForkNodes
        for nested_fork_id in nested_forks:
            nested_outgoing_edges = self.parser.get_outgoing_nodes(nested_fork_id)
            
            for i, nested_edge in enumerate(nested_outgoing_edges):
                # ใช้ชื่อสั้นๆ โดยไม่ซ้ำคำ Template
                nested_template_name = f"{template_name}_Nested{i+1}"
                self.create_fork_template(
                    nested_template_name, 
                    nested_fork_id, 
                    nested_edge, 
                    template_name,  # ใช้ template_name แทน base_name
                    level + 1
                )
        
        # สร้าง transitions สำหรับ template นี้
        self._create_template_transitions_clean(fork_template, initial_id, hierarchical_name, level, branch_nodes)
        
        return fork_template
    
    def _get_all_branch_nodes(self, start_node, fork_id, visited=None, max_depth=20):
        """เก็บรวบรวม nodes ใน branch - รวม JoinNode ที่สอดคล้องกับ nested ForkNode"""
        if visited is None:
            visited = set()
        
        if max_depth <= 0 or start_node in visited:
            return []
            
        visited.add(start_node)
        node_type = self.parser.get_node_type(start_node) if self.parser else ""
        
        # ถ้าเป็น JoinNode ให้หยุดและรวมเข้าไป
        if node_type in ("uml:JoinNode", "JoinNode"):
            return [start_node]
        
        # ถ้าเป็น nested ForkNode (ไม่ใช่ fork_id หลัก) ให้รวม ForkNode และ corresponding JoinNode
        if (node_type in ("uml:ForkNode", "ForkNode") and start_node != fork_id):
            corresponding_join = self.parser._find_corresponding_join(start_node)
            if corresponding_join:
                return [start_node, corresponding_join]  # รวมทั้ง ForkNode และ JoinNode
            else:
                return [start_node]  # รวม ForkNode แต่ไม่มี JoinNode
        
        branch_nodes = [start_node]
        
        # ติดตาม outgoing nodes
        if self.parser:
            outgoing_nodes = self.parser.get_outgoing_nodes(start_node)
            for next_node in outgoing_nodes:
                if next_node not in visited:
                    sub_branch = self._get_all_branch_nodes(next_node, fork_id, visited.copy(), max_depth - 1)
                    branch_nodes.extend(sub_branch)
        
        return list(set(branch_nodes))  # Remove duplicates
    
    def _create_template_transitions_clean(self, fork_template, initial_id, template_name, level, branch_nodes):
        """สร้าง transitions สำหรับ template แบบยืดหยุ่น"""
        # หา first node ที่เป็น direct outgoing จาก parent ForkNode ก่อน
        first_process_node = None
        parent_fork_id = self.template_hierarchy[template_name]['fork_id']
        
        # วิธี 1: หา node ที่เป็น direct target ของ ForkNode
        if self.parser:
            outgoing_from_fork = self.parser.get_outgoing_nodes(parent_fork_id)
            for node_id in branch_nodes:
                if node_id in outgoing_from_fork:
                    node_type = self.parser.get_node_type(node_id)
                    if node_type in ("uml:OpaqueAction", "OpaqueAction", "uml:DecisionNode", "DecisionNode", "uml:MergeNode", "MergeNode"):
                        first_process_node = node_id
                        break
        
        # วิธี 2: ถ้าไม่พบ ให้หา node ตามเดิม
        if not first_process_node:
            for node_id in branch_nodes:
                node_type = self.parser.get_node_type(node_id) if self.parser else ""
                if node_type in ("uml:OpaqueAction", "OpaqueAction", "uml:DecisionNode", "DecisionNode", "uml:MergeNode", "MergeNode"):
                    first_process_node = node_id
                    break
        
        print(f"DEBUG: First process node for {template_name}: {self.parser.get_node_name(first_process_node) if first_process_node and self.parser else 'None'}")
        
        # สร้าง initial transition ไปยัง first process node
        if first_process_node:
            transition = ET.SubElement(fork_template["element"], "transition")
            ET.SubElement(transition, "source", ref=initial_id)
            ET.SubElement(transition, "target", ref=first_process_node)
            
            x1, y1 = fork_template["position_map"].get(initial_id, (0, 0))
            x2, y2 = fork_template["position_map"].get(first_process_node, (0, 0))
            x_mid = (x1 + x2) // 2
            y_mid = (y1 + y2) // 2
            
            # ใช้ fork channel
            parent_fork_id = self.template_hierarchy[template_name]['fork_id']
            fork_channel = self.fork_channels.get(parent_fork_id, "fork1")
            ET.SubElement(transition, "label", kind="synchronisation", x=str(x_mid), y=str(y_mid - 80)).text = f"{fork_channel}?"
        
        # หา nested ForkNode และ corresponding JoinNode ใน branch นี้
        nested_fork_id = None
        corresponding_join_id = None
        
        for node_id in branch_nodes:
            node_type = self.parser.get_node_type(node_id) if self.parser else ""
            if (node_type in ("uml:ForkNode", "ForkNode") and 
                node_id != self.template_hierarchy[template_name]['fork_id']):
                nested_fork_id = node_id
                corresponding_join_id = self.parser._find_corresponding_join(node_id) if self.parser else None
                break
        
        # สร้าง intermediate location สำหรับ nested fork synchronization
        intermediate_id = None
        if nested_fork_id and corresponding_join_id and level == 0:
            # สร้าง intermediate location
            intermediate_id = f"Nested_{template_name}"
            intermediate_name = f"Nested_{template_name}"
            
            # เพิ่ม intermediate location
            x_intermediate = fork_template['x_offset']
            y_intermediate = fork_template['position_map'].get(nested_fork_id, (0, 0))[1] + 100
            fork_template['position_map'][intermediate_id] = (x_intermediate, y_intermediate)
            fork_template['state_map'][intermediate_id] = intermediate_id
            
            location = ET.SubElement(fork_template["element"], "location", id=intermediate_id, x=str(x_intermediate), y=str(y_intermediate))
            ET.SubElement(location, "name", x=str(x_intermediate - 50), y=str(y_intermediate - 30)).text = intermediate_name
            
            fork_template['x_offset'] += 300
        
        # สร้าง transitions ระหว่าง nodes ใน branch ตาม edges ที่มี
        if self.parser:
            for edge_data in self.parser.get_all_edges():
                source = edge_data['source']
                target = edge_data['target']
                
                # ถ้าทั้ง source และ target อยู่ใน branch นี้ แต่ไม่ใช่ nested fork to join
                if (source in branch_nodes and target in branch_nodes and source != initial_id and
                    not (source == nested_fork_id and target == corresponding_join_id)):
                    source_name = self.parser.get_node_name(source)
                    target_name = self.parser.get_node_name(target)
                    target_type = self.parser.get_node_type(target)
                    
                    self.add_transition(fork_template, source, target, source_name, target_name, target_type, from_fork_template=True)
        
        # สร้าง fork synchronization transitions แยกเป็น 2 ขั้นตอน
        if nested_fork_id and corresponding_join_id and intermediate_id and level == 0:
            # สร้าง nested fork channel
            if nested_fork_id not in self.fork_channels:
                nested_fork_name = self.parser.get_node_name(nested_fork_id) if self.parser else "nested_fork"
                nested_channel = f"fork_{nested_fork_name}"
                self.fork_channels[nested_fork_id] = nested_channel
                self.add_declaration(f"broadcast chan {nested_channel};")
            else:
                nested_channel = self.fork_channels[nested_fork_id]
            
            # Transition 1: ForkNode → Intermediate (ส่ง fork signal)
            transition1 = ET.SubElement(fork_template["element"], "transition")
            ET.SubElement(transition1, "source", ref=nested_fork_id)
            ET.SubElement(transition1, "target", ref=intermediate_id)
            
            x1, y1 = fork_template["position_map"].get(nested_fork_id, (0, 0))
            x2, y2 = fork_template["position_map"].get(intermediate_id, (0, 0))
            x_mid1 = (x1 + x2) // 2
            y_mid1 = (y1 + y2) // 2
            
            # เพิ่ม synchronization label
            ET.SubElement(transition1, "label", kind="synchronisation", x=str(x_mid1), y=str(y_mid1 - 80)).text = f"{nested_channel}!"
            
            # Transition 2: Intermediate → JoinNode (รอ Done conditions)
            transition2 = ET.SubElement(fork_template["element"], "transition")
            ET.SubElement(transition2, "source", ref=intermediate_id)
            ET.SubElement(transition2, "target", ref=corresponding_join_id)
            
            x3, y3 = fork_template["position_map"].get(corresponding_join_id, (0, 0))
            x_mid2 = (x2 + x3) // 2
            y_mid2 = (y2 + y3) // 2
            
            # สร้าง guard สำหรับรอ nested templates
            outgoing_edges = self.parser.get_outgoing_nodes(nested_fork_id) if self.parser else []
            guard_conditions = []
            
            for i in range(len(outgoing_edges)):
                nested_template_name = f"{template_name}_Nested{i+1}"
                guard_conditions.append(f"Done_{nested_template_name}==true")
            
            if guard_conditions:
                ET.SubElement(transition2, "label", kind="guard", x=str(x_mid2), y=str(y_mid2 - 60)).text = " && ".join(guard_conditions)
            
            # เพิ่ม assignment Done_Template = true สำหรับ template นี้ (ไม่ต้อง reset clock สำหรับ non-time transitions)
            assignment_text = f"Done_{template_name} = true"
            ET.SubElement(transition2, "label", kind="assignment", x=str(x_mid2), y=str(y_mid2 - 40)).text = assignment_text

    def add_transition(self, template, source_id, target_id, source_name="", target_name="", target_type="", from_fork_template=False):
        """Adds a transition between two locations in the template."""
        if not source_id or not target_id:
            # ข้ามการสร้าง transition ถ้าไม่มีข้อมูลที่จำเป็น
            return

        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        
        if source and target:
            # ตรวจสอบว่า transition นี้ได้ถูกสร้างแล้วหรือไม่
            trans_key = (source_id, target_id)
            if trans_key in self.created_transitions:
                return  # ข้ามการสร้างถ้า transition นี้ได้ถูกสร้างแล้ว
            self.created_transitions.add(trans_key)

            source_type = self.get_node_type(source_id)
            target_type = self.parser.get_node_type(target_id) if self.parser else target_type

            # Special handling for ForkNode in main template
            if (template["name"] == "Template" and 
                source_type in ("uml:ForkNode", "ForkNode")):
                
                # ตรวจสอบว่าเป็น bypass transition หรือ fork activation
                if target_type in ("uml:JoinNode", "JoinNode"):
                    # นี่คือ bypass transition
                    print(f"Creating bypass transition: {source_name} -> {target_name}")
                    
                    trans_id = f"{source_id}_{target_id}_bypass"
                    transition = ET.SubElement(template["element"], "transition", id=trans_id)
                    ET.SubElement(transition, "source", ref=source)
                    ET.SubElement(transition, "target", ref=target)

                    x1, y1 = template["position_map"].get(source_id, (0, 0))
                    x2, y2 = template["position_map"].get(target_id, (0, 0))
                    x_mid = (x1 + x2) // 2
                    y_mid = (y1 + y2) // 2

                    # สร้าง fork templates และ synchronization
                    outgoing_edges = self.parser.get_outgoing_nodes(source_id) if self.parser else []
                    
                    # สร้าง fork channel
                    if source_id not in self.fork_channels:
                        self.fork_counter += 1
                        fork_channel = f"fork{self.fork_counter}"
                        self.fork_channels[source_id] = fork_channel
                        self.add_declaration(f"broadcast chan {fork_channel};")
                    else:
                        fork_channel = self.fork_channels[source_id]

                    # สร้าง Done variables และ fork templates สำหรับแต่ละ branch
                    for i, outgoing_edge in enumerate(outgoing_edges):
                        # กำหนดชื่อ template ตาม ForkNode และ Branch
                        fork_name_clean = source_name.replace(" ", "").replace(",", "")
                        template_name = f"Template_{fork_name_clean}_Branch{i+1}"
                        
                        self.add_declaration(f"bool Done_{template_name};")
                        self.create_fork_template(template_name, source_id, outgoing_edge)

                    # เพิ่ม synchronization label
                    ET.SubElement(transition, "label", kind="synchronisation", x=str(x_mid), y=str(y_mid - 80)).text = f"{fork_channel}!"
                    
                    return  # ไม่ต้องสร้าง transition ปกติ
                else:
                    # ไม่ใช่ bypass -> ไม่ควรเกิดขึ้นใน main template
                    print(f"Warning: ForkNode {source_name} has non-bypass target {target_name} in main template")

            # ถ้าไม่ใช่ special case ให้ทำแบบปกติ
            trans_id = f"{source_id}_{target_id}"
            transition = ET.SubElement(template["element"], "transition", id=trans_id)
            ET.SubElement(transition, "source", ref=source)
            ET.SubElement(transition, "target", ref=target)

            x1, y1 = template["position_map"].get(source_id, (0, 0))
            x2, y2 = template["position_map"].get(target_id, (0, 0))
            x_mid = (x1 + x2) // 2
            y_mid = (y1 + y2) // 2

            # Check if the source is a JoinNode
            if self.get_node_type(source_id) == "uml:JoinNode":
                guard_conditions = []
                
                # สำหรับ main template - เพิ่ม guard conditions แบบ dynamic
                if template["name"] == "Template" and not from_fork_template:
                    # หา ForkNode ที่ corresponding กับ JoinNode นี้
                    corresponding_fork = self._find_fork_for_join(source_id)
                    
                    if corresponding_fork:
                        # หา templates ที่ถูกสร้างจาก ForkNode นี้
                        fork_templates = self._get_templates_for_fork(corresponding_fork)
                        guard_conditions = [f"Done_{template_name}==true" for template_name in fork_templates]
                    else:
                        # ถ้าไม่เจอ corresponding fork ให้ใช้ dynamic analysis
                        guard_conditions = self._get_dynamic_guard_conditions(source_id)
                
                # สำหรับ fork templates - guard conditions ตามเดิม
                else:
                    # ตรวจสอบว่า JoinNode นี้อยู่ใน nested structure หรือไม่
                    join_level = 0
                    parent_template = None
                    
                    if source_id in self.nested_fork_structure:
                        join_level = self.nested_fork_structure[source_id]['level']
                        parent_template = self.nested_fork_structure[source_id]['parent_template']
                    
                    # Construct guard conditions based on appropriate templates
                    if join_level == 0:
                        # Top level JoinNode - รอ top level templates
                        for i, template_obj in enumerate(self.fork_templates):
                            if template_obj["name"].startswith("Template") and not "_" in template_obj["name"]:
                                guard_conditions.append(f"Done_{template_obj['name']}==true")
                    else:
                        # Nested JoinNode - รอ nested templates ใน level เดียวกัน
                        for template_obj in self.fork_templates:
                            template_name = template_obj["name"]
                            if (f"NestedTemplate{join_level}" in template_name and 
                                parent_template and parent_template in template_name):
                                guard_conditions.append(f"Done_{template_name}==true")
                
                if guard_conditions:
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = " && ".join(guard_conditions)

            # Handle time constraints
            if "," in source_name and "t=" in source_name:
                try:
                    time_val = int(source_name.split("t=")[-1].strip())
                    clock_name = template["clock_name"]
                    
                    # สร้าง assignment text สำหรับ clock reset
                    assignment_text = f"{clock_name}:=0"
                    
                    # Add Done variable assignment for fork templates
                    if template["name"].startswith("Template") and template in self.fork_templates:
                        # ตรวจสอบว่าเป็น final transition ของ template หรือไม่
                        target_node_type = self.get_node_type(target_id)
                        if target_node_type in ("uml:JoinNode", "JoinNode", "uml:FinalNode", "FinalNode") or not target_id:
                            assignment_text += f", Done_{template['name']} = true"
                    
                    # Create separate labels for guard and assignment
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 60)).text = f"{clock_name}>{time_val}"
                    ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = assignment_text
                    
                except ValueError:
                    pass
            else:
                # Handle Done variable assignment for non-time transitions
                if template["name"].startswith("Template") and template in self.fork_templates:
                    target_node_type = self.get_node_type(target_id)
                    if target_node_type in ("uml:JoinNode", "JoinNode", "uml:FinalNode", "FinalNode") or not target_id:
                        # Check if there's already an assignment label
                        existing_assign = transition.find("label[@kind='assignment']")
                        if existing_assign is not None:
                            existing_assign.text += f", Done_{template['name']} = true"
                        else:
                            # สำหรับ non-time transitions ไม่ต้อง reset clock เพียงแค่ set Done variable
                            ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"Done_{template['name']} = true"

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
        """Returns the type of node using parser data."""
        if self.parser:
            return self.parser.get_node_type(node_id)
        
        # Fallback for compatibility
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
    
    def _find_fork_for_join(self, join_node_id):
        """หา ForkNode ที่ corresponding กับ JoinNode นี้"""
        if not self.parser:
            return None
        
        # ตรวจสอบทุก ForkNode เพื่อหาว่า JoinNode นี้เป็น corresponding join ของ fork ไหน
        for fork_id in self.parser.get_coordination_nodes():
            fork_type = self.parser.get_node_type(fork_id)
            if fork_type in ("uml:ForkNode", "ForkNode"):
                corresponding_join = self.parser._find_corresponding_join(fork_id)
                if corresponding_join == join_node_id:
                    return fork_id
        
        return None
    
    def _get_templates_for_fork(self, fork_id):
        """หา templates ที่ถูกสร้างจาก ForkNode นี้"""
        fork_templates = []
        
        print(f"DEBUG: Looking for templates for fork_id: {fork_id}")
        print(f"DEBUG: Available template_hierarchy: {list(self.template_hierarchy.keys())}")
        
        # วิธี 1: หาใน template_hierarchy ว่า templates ไหนบ้างที่ถูกสร้างจาก fork_id นี้
        for template_name, hierarchy_info in self.template_hierarchy.items():
            if hierarchy_info.get('fork_id') == fork_id and hierarchy_info.get('level') == 0:
                # เฉพาะ top-level templates (level 0) ที่เป็นของ fork นี้
                fork_templates.append(template_name)
                print(f"DEBUG: Found template {template_name} for fork {fork_id} (from hierarchy)")
        
        # วิธี 2: ถ้าไม่เจอใน hierarchy ให้ดูจาก fork_templates ที่มีอยู่จริง
        if not fork_templates:
            print(f"DEBUG: No templates found in hierarchy, checking existing fork_templates")
            print(f"DEBUG: Available fork_templates: {[t['name'] for t in self.fork_templates]}")
            
            for template in self.fork_templates:
                template_name = template["name"]
                # ตรวจสอบว่า template นี้เป็นของ ForkNode นี้หรือไม่โดยดูจาก hierarchy
                if (template_name in self.template_hierarchy and 
                    self.template_hierarchy[template_name].get('fork_id') == fork_id and
                    self.template_hierarchy[template_name].get('level') == 0):
                    fork_templates.append(template_name)
                    print(f"DEBUG: Found template {template_name} for fork {fork_id} (from existing templates)")
        
        # วิธี 3: ถ้ายังไม่เจอ ให้วิเคราะห์จาก template names ที่เป็น top-level และไม่ใช่ main
        if not fork_templates:
            print(f"DEBUG: Still no templates found, checking by pattern")
            fork_name = self.parser.get_node_name(fork_id) if self.parser else ""
            print(f"DEBUG: Fork name: {fork_name}")
            
            # จับคู่ templates ตามชื่อ ForkNode ใหม่
            fork_name_clean = fork_name.replace(" ", "").replace(",", "")
            fork_pattern = f"Template_{fork_name_clean}_"
            
            for template in self.templates:
                template_name = template["name"]
                if (template_name != "Template" and 
                    template in self.fork_templates and
                    fork_pattern in template_name):
                    fork_templates.append(template_name)
                    print(f"DEBUG: Found template {template_name} for {fork_name} by pattern")
        
        # วิธี 4: ถ้ายังไม่เจอ ให้สร้าง templates สำหรับ ForkNode ทั้งคู่
        if not fork_templates and self.parser:
            fork_name = self.parser.get_node_name(fork_id)
            print(f"DEBUG: Creating templates for {fork_name}")
            outgoing_edges = self.parser.get_outgoing_nodes(fork_id)
            
            # สร้าง templates ด้วยชื่อที่สื่อความหมาย
            fork_name_clean = fork_name.replace(" ", "").replace(",", "")
            for i, outgoing_edge in enumerate(outgoing_edges):
                template_name = f"Template_{fork_name_clean}_Branch{i+1}"
                self.add_declaration(f"bool Done_{template_name};")
                self.create_fork_template(template_name, fork_id, outgoing_edge)
                fork_templates.append(template_name)
                print(f"DEBUG: Created template {template_name} for {fork_name}")
        
        print(f"DEBUG: Final templates for fork {fork_id}: {fork_templates}")
        return fork_templates

    def _get_dynamic_guard_conditions(self, join_node_id):
        """หา guard conditions สำหรับ JoinNode โดยวิเคราะห์โครงสร้าง fork ที่เกี่ยวข้อง"""
        guard_conditions = []
        
        if not self.parser:
            return guard_conditions
        
        print(f"DEBUG: Getting dynamic guard conditions for JoinNode: {self.parser.get_node_name(join_node_id)}")
        
        # หา ForkNode ที่นำไปสู่ JoinNode นี้ผ่าน reverse path analysis
        corresponding_fork = self._analyze_join_to_fork_relationship(join_node_id)
        
        print(f"DEBUG: Corresponding fork: {self.parser.get_node_name(corresponding_fork) if corresponding_fork else 'None'}")
        
        if corresponding_fork:
            # หา templates ที่ถูกสร้างจริงๆ จาก ForkNode นี้
            template_names = self._get_templates_for_fork(corresponding_fork)
            
            # สร้าง guard conditions
            guard_conditions = [f"Done_{template_name}==true" for template_name in template_names]
            print(f"DEBUG: Generated guard conditions: {guard_conditions}")
        
        return guard_conditions
    
    def _analyze_join_to_fork_relationship(self, join_node_id):
        """วิเคราะห์ความสัมพันธ์ระหว่าง JoinNode กับ ForkNode โดย trace backward"""
        if not self.parser:
            return None
        
        # วิธี 1: ใช้ _find_corresponding_join ย้อนกลับ
        for node_id in self.parser.get_coordination_nodes():
            node_type = self.parser.get_node_type(node_id)
            if node_type in ("uml:ForkNode", "ForkNode"):
                corresponding_join = self.parser._find_corresponding_join(node_id)
                if corresponding_join == join_node_id:
                    return node_id
        
        # วิธี 2: วิเคราะห์จาก incoming paths ของ JoinNode
        visited = set()
        return self._trace_backward_to_fork(join_node_id, visited, max_depth=10)
    
    def _trace_backward_to_fork(self, current_node, visited, max_depth=10):
        """ติดตาม backward path เพื่อหา ForkNode ที่เกี่ยวข้อง"""
        if max_depth <= 0 or current_node in visited:
            return None
        
        visited.add(current_node)
        
        # ตรวจสอบ incoming nodes
        incoming_nodes = self.parser.get_incoming_nodes(current_node)
        
        for incoming_node in incoming_nodes:
            node_type = self.parser.get_node_type(incoming_node)
            
            # ถ้าเจอ ForkNode
            if node_type in ("uml:ForkNode", "ForkNode"):
                return incoming_node
            
            # ถ้าเป็น node อื่น ให้ trace ต่อ
            result = self._trace_backward_to_fork(incoming_node, visited.copy(), max_depth - 1)
            if result:
                return result
        
        return None

    def initialize_nested_fork_variables(self):
        """Initialize Done variables for all nested fork templates"""
        # เพิ่ม Done variables สำหรับทุก template ที่เป็น fork template
        for template in self.fork_templates:
            template_name = template["name"]
            if f"bool Done_{template_name};" not in self.declarations:
                self.add_declaration(f"bool Done_{template_name};")

    def generate_xml(self):
        """Generates the final UPPAAL XML with proper formatting and nested fork support."""
        # Initialize nested fork variables
        self.initialize_nested_fork_variables()
        
        # Clear any existing elements
        for elem in list(self.nta):
            self.nta.remove(elem)

        # Add declaration
        decl_elem = ET.SubElement(self.nta, "declaration")
        decl_elem.text = "\n".join(sorted(set(self.declarations)))

        # Add templates in hierarchical order (parent templates first)
        sorted_templates = []
        
        # Add main template first
        for template in self.templates:
            if template["name"] == "Template":
                sorted_templates.append(template)
                break
        
        # Add top-level fork templates
        for template in self.templates:
            if (template["name"].startswith("Template") and 
                template["name"] != "Template" and 
                "_" not in template["name"]):
                sorted_templates.append(template)
        
        # Add nested templates by level
        max_level = 0
        for template_name in self.template_hierarchy:
            level = self.template_hierarchy[template_name]['level']
            max_level = max(max_level, level)
        
        for level in range(1, max_level + 1):
            for template in self.templates:
                template_name = template["name"]
                if (template_name in self.template_hierarchy and 
                    self.template_hierarchy[template_name]['level'] == level):
                    sorted_templates.append(template)

        # Add remaining templates
        for template in self.templates:
            if template not in sorted_templates:
                sorted_templates.append(template)

        # Process templates in sorted order
        for template in sorted_templates:
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

        # Add system declaration with hierarchical template names
        system_text = []
        for i, template in enumerate(sorted_templates, 1):
            system_text.append(f"T{i} = {template['name']}();")
        system_text.append("system " + ", ".join(f"T{i}" for i in range(1, len(sorted_templates) + 1)) + ";")
        
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

    def clean_result(self):
        """Removes entire transitions with duplicate synchronisation labels in the main template, keeping only one instance of each unique label. Also removes locations with no transitions connected to them."""
        for template in self.templates:
            if template["name"] == "Template":  # Check if it's the main template
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
                            template["element"].remove(transition)  # Remove entire transition
                            break  # Exit the label loop since the transition is removed
                        else:
                            seen_labels.add(label_text)
                # Remove locations not connected by any transitions
                locations = template["element"].findall(".//location")
                for location in locations:
                    if location.get("id") not in connected_locations:
                        template["element"].remove(location)

    def process_nodes(self):
        """Processes nodes and creates main template using ActivityDiagramParser."""
        if not self.parser:
            raise ValueError("ActivityDiagramParser not initialized. Call set_activity_root() first.")
        
        # Print analysis results
        self.parser.print_analysis()
        
        # Create main template with filtered nodes
        main_template = self.create_template("Template")
        
        # เพิ่มเฉพาะ main flow nodes เข้า main template
        main_flow_nodes = self.parser.get_main_flow_nodes()
        
        print(f"Main flow nodes identified: {len(main_flow_nodes)}")
        for node_id in main_flow_nodes:
            node_info = self.parser.get_node_info(node_id)
            if node_info:
                node_type = node_info['type']
                node_name = node_info['name']
                print(f"Including in main template: {node_type} - {node_name}")
                self.add_location(main_template, node_id, node_name, node_type)
        
        # สร้าง edge guards จาก parser
        for edge_data in self.parser.get_all_edges():
            source = edge_data['source']
            target = edge_data['target']
            guard = edge_data['guard']
            name = edge_data['name']
            
            if guard or name:
                self.edge_guards[(source, target)] = guard or name
        
        # ประมวลผล edges สำหรับ main template
        print(f"\nProcessing edges for main template...")
        
        # สร้าง connections ระหว่าง nodes ที่อยู่ใน main template
        connected_edges = []
        bypass_edges = []  # เก็บ edges ที่ต้อง bypass ผ่าน fork branches
        
        for edge_data in self.parser.get_all_edges():
            source = edge_data['source']
            target = edge_data['target']
            
            # ถ้าทั้ง source และ target อยู่ใน main template
            if source in main_flow_nodes and target in main_flow_nodes:
                connected_edges.append(edge_data)
                source_name = self.parser.get_node_name(source)
                target_name = self.parser.get_node_name(target)
                print(f"Direct edge: {source_name} -> {target_name}")
            
            # ถ้า source อยู่ใน main template แต่ target อยู่ใน fork branch
            elif source in main_flow_nodes and target not in main_flow_nodes:
                source_type = self.parser.get_node_type(source)
                
                # ถ้า source เป็น ForkNode ให้หา corresponding JoinNode
                if source_type in ("uml:ForkNode", "ForkNode"):
                    corresponding_join = self.parser._find_corresponding_join(source)
                    if corresponding_join and corresponding_join in main_flow_nodes:
                        bypass_edge = {
                            'source': source,
                            'target': corresponding_join,
                            'guard': "",
                            'name': f"bypass_{self.parser.get_node_name(source)}"
                        }
                        bypass_edges.append(bypass_edge)
                        source_name = self.parser.get_node_name(source)
                        target_name = self.parser.get_node_name(corresponding_join)
                        print(f"Bypass edge: {source_name} -> {target_name} (bypass)")
        
        # สร้าง transitions สำหรับ direct connections
        for edge_data in connected_edges:
            source = edge_data['source']
            target = edge_data['target']
            source_name = self.parser.get_node_name(source)
            target_name = self.parser.get_node_name(target)
            target_type = self.parser.get_node_type(target)
            
            self.add_transition(main_template, source, target, source_name, target_name, target_type)
        
        # สร้าง bypass transitions สำหรับ ForkNodes
        for bypass_edge in bypass_edges:
            source = bypass_edge['source']
            target = bypass_edge['target']
            source_name = self.parser.get_node_name(source)
            target_name = self.parser.get_node_name(target)
            target_type = self.parser.get_node_type(target)
            
            self.add_transition(main_template, source, target, source_name, target_name, target_type)
        
        print(f"\nMain template created with:")
        print(f"  - {len(main_flow_nodes)} nodes")
        print(f"  - {len(connected_edges)} direct edges")
        print(f"  - {len(bypass_edges)} bypass edges")
        
        return main_template

    def print_main_template_structure(self):
        """แสดงโครงสร้างของ main template อย่างละเอียด"""
        print("\n" + "="*100)
        print("🏗️  MAIN TEMPLATE STRUCTURE")
        print("="*100)
        
        # หา main template
        main_template = None
        for template in self.templates:
            if template["name"] == "Template":
                main_template = template
                break
        
        if not main_template:
            print("❌ Main template not found!")
            return
        
        # แสดงข้อมูลทั่วไป
        print(f"\n📋 TEMPLATE INFO:")
        print(f"   Name: {main_template['name']}")
        print(f"   Clock: {main_template['clock_name']}")
        print(f"   Total Locations: {len(main_template['state_map'])}")
        print(f"   Initial Location: {main_template['initial_id']}")
        
        # แสดง locations/nodes
        print(f"\n🎯 LOCATIONS ({len(main_template['state_map'])}):")
        print("-" * 80)
        for node_id, loc_id in main_template['state_map'].items():
            if self.parser:
                node_info = self.parser.get_node_info(node_id)
                if node_info:
                    node_type = node_info['type']
                    node_name = node_info['name']
                    x, y = main_template['position_map'].get(node_id, (0, 0))
                    initial_mark = " [INITIAL]" if node_id == main_template['initial_id'] else ""
                    print(f"   • {loc_id:<25} | {node_type:<20} | {node_name:<20} | ({x}, {y}){initial_mark}")
        
        # แสดง transitions
        transitions = main_template["element"].findall(".//transition")
        print(f"\n🔗 TRANSITIONS ({len(transitions)}):")
        print("-" * 80)
        
        for i, transition in enumerate(transitions, 1):
            source_ref = transition.find("source").get("ref")
            target_ref = transition.find("target").get("ref")
            
            # หา node names
            source_name = "Unknown"
            target_name = "Unknown"
            if self.parser:
                source_info = self.parser.get_node_info(source_ref)
                target_info = self.parser.get_node_info(target_ref)
                if source_info:
                    source_name = source_info['name']
                if target_info:
                    target_name = target_info['name']
            
            print(f"\n   🔄 Transition {i}:")
            print(f"      Source: {source_ref} ({source_name})")
            print(f"      Target: {target_ref} ({target_name})")
            
            # แสดง labels
            labels = transition.findall("label")
            if labels:
                print(f"      Labels:")
                for label in labels:
                    kind = label.get("kind", "unknown")
                    text = label.text or ""
                    x = label.get("x", "0")
                    y = label.get("y", "0")
                    print(f"        - {kind}: '{text}' at ({x}, {y})")
            else:
                print(f"      Labels: None")
        
        # แสดง flow path
        print(f"\n🔄 MAIN FLOW PATH:")
        print("-" * 80)
        if main_template['initial_id'] and self.parser:
            self._trace_flow_path(main_template['initial_id'], main_template, set())
        
        print("\n" + "="*100)
        print("✅ MAIN TEMPLATE STRUCTURE COMPLETE")
        print("="*100 + "\n")
    
    def _trace_flow_path(self, current_node, template, visited, level=0):
        """ติดตาม flow path ใน main template"""
        if current_node in visited or level > 20:
            return
        
        visited.add(current_node)
        indent = "   " * level
        
        # แสดง current node
        if self.parser:
            node_info = self.parser.get_node_info(current_node)
            if node_info:
                node_type = node_info['type']
                node_name = node_info['name']
                print(f"{indent}→ {node_type}: {node_name}")
        
        # หา outgoing transitions
        transitions = template["element"].findall(".//transition")
        outgoing = []
        for transition in transitions:
            source_ref = transition.find("source").get("ref")
            target_ref = transition.find("target").get("ref")
            if source_ref == current_node:
                outgoing.append(target_ref)
        
        # ถ้าเป็น Decision Node แสดง branches แยกกัน
        node_info = self.parser.get_node_info(current_node) if self.parser else None
        if node_info and isinstance(node_info, dict) and node_info.get('type') in ("uml:DecisionNode", "DecisionNode"):
            print(f"{indent}   ┌─ Decision Branches:")
            for i, next_node in enumerate(outgoing):
                branch_visited = visited.copy()
                print(f"{indent}   ├─ Branch {i+1}:")
                self._trace_flow_path(next_node, template, branch_visited, level + 2)
        else:
            # ติดตาม outgoing nodes ปกติ
            for next_node in outgoing:
                if next_node not in visited:
                    self._trace_flow_path(next_node, template, visited, level + 1)

    def validate_main_template_transitions(self):
        """ตรวจสอบและแก้ไข transitions ใน main template"""
        main_template = None
        for template in self.templates:
            if template["name"] == "Template":
                main_template = template
                break
        
        if not main_template or not self.parser:
            return
        
        print(f"\n🔧 VALIDATING MAIN TEMPLATE TRANSITIONS...")
        print("-" * 80)
        
        # รายการ transitions ที่ควรมี
        expected_transitions = []
        main_flow_nodes = list(main_template["state_map"].keys())
        
        # ตรวจสอบ transitions ที่หายไป
        for edge_data in self.parser.get_all_edges():
            source = edge_data['source']
            target = edge_data['target']
            
            # ถ้าทั้ง source และ target อยู่ใน main template
            if source in main_flow_nodes and target in main_flow_nodes:
                expected_transitions.append((source, target))
        
        # ตรวจสอบ transitions ที่มีอยู่
        existing_transitions = set()
        transitions = main_template["element"].findall(".//transition")
        
        for transition in transitions:
            source_ref = transition.find("source").get("ref")
            target_ref = transition.find("target").get("ref")
            existing_transitions.add((source_ref, target_ref))
        
        # หา transitions ที่หายไป
        missing_transitions = []
        for expected in expected_transitions:
            if expected not in existing_transitions:
                missing_transitions.append(expected)
        
        if missing_transitions:
            print(f"❌ Missing {len(missing_transitions)} transitions:")
            for source, target in missing_transitions:
                source_name = self.parser.get_node_name(source)
                target_name = self.parser.get_node_name(target)
                target_type = self.parser.get_node_type(target)
                print(f"   • {source_name} → {target_name}")
                
                # เพิ่ม transition ที่หายไป
                self.add_transition(main_template, source, target, source_name, target_name, target_type)
        else:
            print(f"✅ All expected transitions present ({len(expected_transitions)} total)")
        
        print(f"✅ Validation complete")
        print("-" * 80)

    def print_fork_templates_analysis(self):
        """วิเคราะห์และแสดงโครงสร้างของ fork templates"""
        print("\n" + "="*100)
        print("🍴 FORK TEMPLATES ANALYSIS")
        print("="*100)
        
        # หา fork templates
        fork_templates = [template for template in self.templates if template in self.fork_templates]
        
        if not fork_templates:
            print("❌ No fork templates found!")
            return
        
        print(f"\n📊 FOUND {len(fork_templates)} FORK TEMPLATES:")
        print("-" * 80)
        
        for i, template in enumerate(fork_templates, 1):
            print(f"\n🎯 TEMPLATE {i}: {template['name']}")
            print("=" * 60)
            
            # แสดงข้อมูลทั่วไป
            print(f"   📋 Template Info:")
            print(f"      Name: {template['name']}")
            print(f"      Clock: {template['clock_name']}")
            print(f"      Total Locations: {len(template['state_map'])}")
            print(f"      Initial Location: {template['initial_id']}")
            
            # แสดง hierarchy info ถ้ามี
            if template['name'] in self.template_hierarchy:
                hierarchy = self.template_hierarchy[template['name']]
                print(f"      Parent Template: {hierarchy.get('parent', 'None')}")
                print(f"      Level: {hierarchy.get('level', 0)}")
                print(f"      Fork ID: {hierarchy.get('fork_id', 'Unknown')}")
            
            # แสดง locations/nodes
            print(f"\n   🎯 LOCATIONS ({len(template['state_map'])}):")
            print("   " + "-" * 70)
            
            for node_id, loc_id in template['state_map'].items():
                if self.parser:
                    node_info = self.parser.get_node_info(node_id)
                    if node_info:
                        node_type = node_info['type']
                        node_name = node_info['name']
                        x, y = template['position_map'].get(node_id, (0, 0))
                        initial_mark = " [INITIAL]" if node_id == template['initial_id'] else ""
                        
                        # แสดงว่า node นี้เป็น coordination หรือ process
                        if node_id in self.parser.get_coordination_nodes():
                            node_category = " (Coordination)"
                        elif node_type in ("uml:OpaqueAction", "OpaqueAction"):
                            node_category = " (Process)"
                        elif node_type in ("uml:DecisionNode", "DecisionNode", "uml:MergeNode", "MergeNode"):
                            node_category = " (Decision/Merge)"
                        else:
                            node_category = ""
                            
                        print(f"      • {loc_id:<25} | {node_type:<20} | {node_name:<20}{node_category} | ({x}, {y}){initial_mark}")
            
            # แสดง transitions
            transitions = template["element"].findall(".//transition")
            print(f"\n   🔗 TRANSITIONS ({len(transitions)}):")
            print("   " + "-" * 70)
            
            for j, transition in enumerate(transitions, 1):
                source_ref = transition.find("source").get("ref")
                target_ref = transition.find("target").get("ref")
                
                # หา node names
                source_name = "Unknown"
                target_name = "Unknown"
                if self.parser:
                    source_info = self.parser.get_node_info(source_ref)
                    target_info = self.parser.get_node_info(target_ref)
                    if source_info:
                        source_name = source_info['name']
                    if target_info:
                        target_name = target_info['name']
                
                print(f"\n      🔄 Transition {j}:")
                print(f"         Source: {source_ref} ({source_name})")
                print(f"         Target: {target_ref} ({target_name})")
                
                # แสดง labels
                labels = transition.findall("label")
                if labels:
                    print(f"         Labels:")
                    for label in labels:
                        kind = label.get("kind", "unknown")
                        text = label.text or ""
                        print(f"           - {kind}: '{text}'")
                else:
                    print(f"         Labels: None")
            
            # แสดง flow path ของ template นี้
            print(f"\n   🔄 TEMPLATE FLOW PATH:")
            print("   " + "-" * 70)
            if template['initial_id'] and self.parser:
                self._trace_template_flow_path(template['initial_id'], template, set(), 0, "      ")
        
        print("\n" + "="*100)
        print("✅ FORK TEMPLATES ANALYSIS COMPLETE")
        print("="*100 + "\n")
    
    def _trace_template_flow_path(self, current_node, template, visited, level=0, prefix=""):
        """ติดตาม flow path ใน fork template"""
        if current_node in visited or level > 20:
            return
        
        visited.add(current_node)
        indent = prefix + ("   " * level)
        
        # แสดง current node
        if self.parser:
            node_info = self.parser.get_node_info(current_node)
            if node_info:
                node_type = node_info['type']
                node_name = node_info['name']
                print(f"{indent}→ {node_type}: {node_name}")
        
        # หา outgoing transitions
        transitions = template["element"].findall(".//transition")
        outgoing = []
        for transition in transitions:
            source_ref = transition.find("source").get("ref")
            target_ref = transition.find("target").get("ref")
            if source_ref == current_node:
                outgoing.append(target_ref)
        
        # ถ้าเป็น Decision Node แสดง branches แยกกัน
        node_info = self.parser.get_node_info(current_node) if self.parser else None
        if node_info and isinstance(node_info, dict) and node_info.get('type') in ("uml:DecisionNode", "DecisionNode"):
            print(f"{indent}   ┌─ Decision Branches:")
            for i, next_node in enumerate(outgoing):
                branch_visited = visited.copy()
                print(f"{indent}   ├─ Branch {i+1}:")
                self._trace_template_flow_path(next_node, template, branch_visited, level + 2, prefix)
        else:
            # ติดตาม outgoing nodes ปกติ
            for next_node in outgoing:
                if next_node not in visited:
                    self._trace_template_flow_path(next_node, template, visited, level + 1, prefix)

    def validate_fork_template_coverage(self):
        """ตรวจสอบว่า templates ถูกสร้างครบตาม fork branches หรือไม่"""
        print("\n" + "="*100)
        print("🔍 FORK TEMPLATE COVERAGE ANALYSIS")
        print("="*100)
        
        if not self.parser:
            print("❌ No parser available for analysis")
            return
        
        # วิเคราะห์ทุก ForkNode และ branches
        all_forks = []
        for node_id in self.parser.get_coordination_nodes():
            node_type = self.parser.get_node_type(node_id)
            if node_type in ("uml:ForkNode", "ForkNode"):
                all_forks.append(node_id)
        
        print(f"\n📊 FOUND {len(all_forks)} FORK NODES:")
        print("-" * 80)
        
        total_expected_templates = 0
        total_created_templates = len(self.fork_templates)
        missing_templates = []
        
        for fork_id in all_forks:
            fork_name = self.parser.get_node_name(fork_id)
            fork_branches = self.parser.fork_branches.get(fork_id, [])
            expected_count = len(fork_branches)
            total_expected_templates += expected_count
            
            print(f"\n🍴 {fork_name} (ID: {fork_id}):")
            print(f"   Expected templates: {expected_count}")
            print(f"   Branches:")
            
            created_templates_for_fork = []
            
            for i, branch in enumerate(fork_branches, 1):
                print(f"     Branch {i} ({len(branch)} nodes): {[self.parser.get_node_name(nid) for nid in branch[:3]]}{'...' if len(branch) > 3 else ''}")
                
                # หา template ที่ควรจะถูกสร้างสำหรับ branch นี้
                expected_template_name = None
                found_template = None
                
                # ตรวจสอบใน template_hierarchy
                for template_name, hierarchy_info in self.template_hierarchy.items():
                    if hierarchy_info.get('fork_id') == fork_id:
                        created_templates_for_fork.append(template_name)
                        found_template = template_name
                        break
                
                # ถ้าไม่พบใน hierarchy ให้ตรวจสอบใน fork_templates โดยตรง
                if not found_template:
                    for template in self.fork_templates:
                        template_name = template["name"]
                        # ตรวจสอบการตั้งชื่อแบบ pattern
                        if ("ForkNode1" in fork_name and template_name in ["Template1", "Template2"]) or \
                           ("ForkNode2" in fork_name and template_name in ["Template5", "Template7"]) or \
                           ("ForkNode1_1" in fork_name and "NestedTemplate" in template_name):
                            if template_name not in created_templates_for_fork:
                                created_templates_for_fork.append(template_name)
                                found_template = template_name
                
                if found_template:
                    print(f"       ✅ Template: {found_template}")
                else:
                    missing_template = f"{fork_name}_Branch{i}"
                    missing_templates.append(missing_template)
                    print(f"       ❌ Missing template for this branch")
            
            print(f"   Created templates: {created_templates_for_fork}")
            print(f"   Coverage: {len(created_templates_for_fork)}/{expected_count}")
        
        print(f"\n📈 SUMMARY:")
        print("-" * 80)
        print(f"   Total ForkNodes: {len(all_forks)}")
        print(f"   Expected templates: {total_expected_templates}")
        print(f"   Created templates: {total_created_templates}")
        print(f"   Coverage: {total_created_templates}/{total_expected_templates}")
        
        if missing_templates:
            print(f"\n❌ MISSING TEMPLATES:")
            for missing in missing_templates:
                print(f"   • {missing}")
        else:
            print(f"\n✅ ALL TEMPLATES CREATED SUCCESSFULLY!")
        
        print("\n" + "="*100)
        print("✅ FORK TEMPLATE COVERAGE ANALYSIS COMPLETE")
        print("="*100 + "\n")
        
        return len(missing_templates) == 0

@app.post("/convert-xml")
async def convert_xml(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        activity_root = ET.fromstring(contents)

        converter = UppaalConverter()
        converter.set_activity_root(activity_root)
        main_template = converter.process_nodes()

        # Initialize variables
        converter.created_transitions = set()
        
        # Generate UPPAAL XML
        result_xml = converter.generate_xml()
        
        # ตรวจสอบและแก้ไข main template transitions
        converter.validate_main_template_transitions()
        
        # Generate UPPAAL XML อีกครั้งหลังแก้ไข
        result_xml = converter.generate_xml()
        
        # แสดงโครงสร้าง main template
        converter.print_main_template_structure()
        
        # วิเคราะห์ fork templates
        converter.print_fork_templates_analysis()
        
        # ตรวจสอบความครบถ้วนของ fork templates
        converter.validate_fork_template_coverage()
        
        # Write to output file
        with open(f"Result/Result_{len(converter.templates)}.xml", 'w', encoding='utf-8') as f:
            f.write(result_xml)
            
        return {"result": "Conversion successful"}

    except ET.ParseError as e:
        return {"error": f"XML parsing error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        return {"error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    import os
    
    # Define input and output folders
    input_file = "Example_XML/Full_Node_simple.xml"
    base_output_file = "Result/Result"
    
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
        converter.set_activity_root(activity_root)
        main_template = converter.process_nodes()
        
        # Initialize variables
        converter.created_transitions = set()
        
        # Generate UPPAAL XML
        result_xml = converter.generate_xml()
        
        # ตรวจสอบและแก้ไข main template transitions
        converter.validate_main_template_transitions()
        
        # Generate UPPAAL XML อีกครั้งหลังแก้ไข
        result_xml = converter.generate_xml()
        
        # แสดงโครงสร้าง main template
        converter.print_main_template_structure()
        
        # วิเคราะห์ fork templates
        converter.print_fork_templates_analysis()
        
        # ตรวจสอบความครบถ้วนของ fork templates
        converter.validate_fork_template_coverage()
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result_xml)
            
        print(f"Successfully converted {input_file} to {output_file}")
        
    except ET.ParseError as e:
        print(f"XML parsing error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
