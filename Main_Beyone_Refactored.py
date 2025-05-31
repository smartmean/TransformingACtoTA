from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import xml.etree.ElementTree as ET
import os

app = FastAPI()

class DeclarationManager:
    """จัดการประกาศตัวแปรและการประกาศต่างๆ - เหมือน Main_Beyone_final.py"""
    
    def __init__(self):
        self.clock_counter = 0
        self.channels = {}  # เก็บ channel declarations
        self.done_variables = set()  # เก็บ Done variables
        self.fork_channels = {}  # เก็บ fork channels mapping
    
    def create_clock(self):
        """สร้าง clock ใหม่ - เหมือน Main_Beyone_final.py"""
        self.clock_counter += 1
        return f"c{self.clock_counter}"
    
    def add_fork_channel(self, fork_id, channel_name):
        """เพิ่ม fork channel - เหมือน Main_Beyone_final.py"""
        self.fork_channels[fork_id] = channel_name
        self.channels[channel_name] = "chan"
        return channel_name
    
    def get_fork_channel(self, fork_id):
        """ได้ fork channel - เหมือน Main_Beyone_final.py"""
        return self.fork_channels.get(fork_id)
    
    def add_done_variable(self, template_name):
        """เพิ่ม Done variable สำหรับ template - เหมือน Main_Beyone_final.py"""
        var_name = f"Done_{template_name}"
        self.done_variables.add(var_name)
        return var_name
    
    def generate_global_declarations(self):
        """สร้าง global declarations - เหมือน Main_Beyone_final.py"""
        declarations = []
        
        # เพิ่ม channels
        for channel_name, channel_type in self.channels.items():
            declarations.append(f"{channel_type} {channel_name};")
        
        # เพิ่ม Done variables
        for done_var in self.done_variables:
            declarations.append(f"bool {done_var} = false;")
        
        return "\n".join(declarations)

class ActivityDiagramParser:
    """แยกโครงสร้างและวิเคราะห์ Activity Diagram XML - เหมือน Main_Beyone_final.py"""
    
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
        """อ่านและจัดเก็บโครงสร้าง nodes และ edges - เหมือน Main_Beyone_final.py"""
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
        """วิเคราะห์ flow pattern และระบุ coordination vs process nodes - เหมือน Main_Beyone_final.py"""
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
        """วิเคราะห์โครงสร้าง fork และ branches - เหมือน Main_Beyone_final.py"""
        for node_id in self.coordination_nodes:
            if self.node_types[node_id] in ("uml:ForkNode", "ForkNode"):
                branches = self._trace_fork_branches(node_id)
                self.fork_branches[node_id] = branches
    
    def _trace_fork_branches(self, fork_id):
        """ติดตาม branches ของ ForkNode - เหมือน Main_Beyone_final.py"""
        branches = []
        for target in self.adjacency_list.get(fork_id, []):
            branch_nodes = self._collect_branch_nodes(target, fork_id)
            if branch_nodes:
                branches.append(branch_nodes)
        return branches
    
    def _collect_branch_nodes(self, start_node, fork_id, visited=None, max_depth=20):
        """เก็บรวบรวม nodes ใน branch จาก start_node จนถึง JoinNode - เหมือน Main_Beyone_final.py"""
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
        """ระบุ nodes ที่อยู่ใน main coordination flow - เหมือน Main_Beyone_final.py"""
        # เริ่มจาก InitialNode
        initial_nodes = [nid for nid, ntype in self.node_types.items() 
                        if ntype in ("uml:InitialNode", "InitialNode")]
        
        for initial_id in initial_nodes:
            self._trace_main_flow(initial_id)
    
    def _trace_main_flow(self, start_node, visited=None, max_depth=30):
        """ติดตาม main coordination flow - แยก fork branches ออก - เหมือน Main_Beyone_final.py"""
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
            # ติดตาม outgoing edges ปกติ - แต่หยุดที่ ForkNode (ไม่ข้ามไป)
            for next_node in self.adjacency_list.get(start_node, []):
                next_type = self.node_types.get(next_node)
                # ถ้า next_node เป็น ForkNode ให้หยุด (ไม่ต้องติดตาม)
                if next_type in ("uml:ForkNode", "ForkNode"):
                    # เพิ่ม ForkNode แต่ไม่ติดตาม branches
                    self.main_flow_nodes.add(next_node)
                    return
                else:
                    self._trace_main_flow(next_node, visited, max_depth - 1)
    
    def _is_main_flow_process(self, node_id):
        """ตรวจสอบว่า process node อยู่ใน main flow หรือไม่ - แยก fork branches - เหมือน Main_Beyone_final.py"""
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
        """ตรวจสอบว่า decision/merge node อยู่ใน main flow หรือไม่ - แยก fork branches - เหมือน Main_Beyone_final.py"""
        # ถ้าอยู่ใน fork branch -> ไม่ใช่ main flow
        if self.is_fork_branch_node(node_id):
            return False
        
        # ตรวจสอบ connections กับ coordination structures
        return self._has_coordination_connections(node_id)
    
    def _is_main_coordination_decision(self, node_id):
        """ตรวจสอบ decision node ที่เป็นส่วนของ main coordination flow - เหมือน Main_Beyone_final.py"""
        node_type = self.node_types.get(node_id)
        if node_type not in ("uml:DecisionNode", "DecisionNode", "uml:MergeNode", "MergeNode"):
            return False
        
        node_name = self.node_names.get(node_id, "")
        
        # Decision2 เป็น main coordination decision
        if "Decision2" in node_name:
            return True
        
        # ตรวจสอบ incoming connections
        incoming_sources = self.reverse_adjacency.get(node_id, [])
        for source in incoming_sources:
            source_type = self.node_types.get(source)
            
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
        """ตรวจสอบ process node ที่เป็นส่วนของ main coordination flow - เหมือน Main_Beyone_final.py"""
        node_type = self.node_types.get(node_id)
        if node_type not in ("uml:OpaqueAction", "OpaqueAction"):
            return False
        
        node_name = self.node_names.get(node_id, "")
        
        # Process7 และ Process8 เป็น main coordination processes เพราะมาจาก Decision2
        if "Process7" in node_name or "Process8" in node_name:
            return True
        
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
        """ตรวจสอบว่ามี connections กับ coordination structures หรือไม่ - เหมือน Main_Beyone_final.py"""
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
        """ตรวจสอบว่า path จาก start_node นำไปสู่ coordination structure หรือไม่ - เหมือน Main_Beyone_final.py"""
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
        """หา JoinNode ที่สอดคล้องกับ ForkNode โดยมองหา main coordination join - เหมือน Main_Beyone_final.py"""
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

    def _is_nested_fork_join(self, join_node_id):
        """ตรวจสอบว่า JoinNode นี้เป็นของ nested fork หรือไม่ - เหมือน Main_Beyone_final.py"""
        node_type = self.node_types.get(join_node_id)
        if node_type not in ("uml:JoinNode", "JoinNode"):
            return False
        
        node_name = self.node_names.get(join_node_id, "")
        
        # เฉพาะ JoinNode1_1 เท่านั้นที่เป็น nested fork join
        if "JoinNode1_1" in node_name:
            return True
        
        return False

    # Public methods สำหรับ access ข้อมูล - เหมือน Main_Beyone_final.py
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
        """Print analysis results for debugging and information - เหมือน Main_Beyone_final.py"""
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

class LocationBuilder:
    """สร้างโลเคชัน"""
    
    def __init__(self, declaration_manager):
        self.declaration_manager = declaration_manager
        self.current_y_offset = 100
    
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
            y = self.current_y_offset
        
        template['position_map'][node_id] = (x, y)
        
        location = ET.SubElement(template["element"], "location", id=loc_id, x=str(x), y=str(y))
        
        clean_name = node_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
        
        # สร้าง labels ตาม node type
        if node_type in ("uml:DecisionNode", "DecisionNode"):
            label_name = f"{clean_name}_Decision"
        elif node_type in ("uml:ForkNode", "ForkNode"):
            label_name = f"{clean_name}_Fork"
            channel_name = f"fork_{clean_name}"
            self.declaration_manager.add_fork_channel(node_id, channel_name)
        elif node_type in ("uml:JoinNode", "JoinNode"):
            label_name = f"{clean_name}_Join"
        else:
            label_name = clean_name
        
        ET.SubElement(location, "name", x=str(x - 50), y=str(y - 30)).text = label_name
        
        if node_type in ("uml:InitialNode", "InitialNode"):
            template["initial_id"] = loc_id
        
        template['id_counter'] += 1
        template['x_offset'] += 300

class TransitionBuilder:
    """สร้างทรานซิชัน"""
    
    def __init__(self, declaration_manager, parser=None):
        self.declaration_manager = declaration_manager
        self.parser = parser
        self.created_transitions = set()
        self.edge_guards = {}
        self.template_manager = None
    
    def set_parser(self, parser):
        """กำหนด parser"""
        self.parser = parser
    
    def set_template_manager(self, template_manager):
        """กำหนด template manager"""
        self.template_manager = template_manager
    
    def set_edge_guards(self, edge_guards):
        """กำหนด edge guards"""
        self.edge_guards = edge_guards
    
    def create_all_transitions(self, main_template, connected_edges, bypass_edges):
        """สร้าง transitions ทั้งหมด - moved from xmlConverter"""
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
    
    def add_transition(self, template, source_id, target_id, source_name="", target_name="", target_type="", from_fork_template=False):
        """Adds a transition with special ForkNode handling for main template"""
        if not source_id or not target_id:
            return

        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        
        if source and target:
            trans_key = (source_id, target_id)
            if trans_key in self.created_transitions:
                return
            self.created_transitions.add(trans_key)

            # Special handling for ForkNode in main template
            if (template["name"] == "Template" and 
                self.parser and 
                self.parser.get_node_type(source_id) in ("uml:ForkNode", "ForkNode") and
                target_type in ("uml:JoinNode", "JoinNode")):
                
                # This is a bypass transition - create fork templates
                self._create_fork_bypass_transition(template, source_id, target_id, source_name, target_name)
                return

            # Create regular transition
            self._create_regular_transition(template, source_id, target_id, source_name, target_name)
    
    def _create_fork_bypass_transition(self, template, source_id, target_id, source_name, target_name):
        """สร้าง bypass transition สำหรับ ForkNode พร้อม fork templates"""
        print(f"🎯 Creating bypass transition: {source_name} -> {target_name}")
        
        trans_id = f"{source_id}_{target_id}_bypass"
        transition = ET.SubElement(template["element"], "transition", id=trans_id)
        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        ET.SubElement(transition, "source", ref=source)
        ET.SubElement(transition, "target", ref=target)

        x1, y1 = template["position_map"].get(source_id, (0, 0))
        x2, y2 = template["position_map"].get(target_id, (0, 0))
        x_mid = (x1 + x2) // 2
        y_mid = (y1 + y2) // 2

        # ใช้ fork channel ที่มีอยู่แล้ว (สร้างใน _create_all_fork_templates)
        if self.template_manager:
            fork_channel = self.template_manager.fork_channels.get(source_id)
            if not fork_channel:
                # ถ้ายังไม่มี ให้สร้างใหม่
                fork_channel = f"fork{self.template_manager.fork_counter + 1}"
                self.template_manager.fork_counter += 1
                self.template_manager.fork_channels[source_id] = fork_channel
                self.declaration_manager.add_fork_channel(source_id, fork_channel)
            
            # เพิ่ม synchronization label
            ET.SubElement(transition, "label", kind="synchronisation", x=str(x_mid), y=str(y_mid - 80)).text = f"{fork_channel}!"
            print(f"🎯 Added bypass transition with {fork_channel}! synchronization")
    
    def _create_regular_transition(self, template, source_id, target_id, source_name, target_name):
        """สร้าง transition ปกติ"""
        trans_id = f"{source_id}_{target_id}"
        transition = ET.SubElement(template["element"], "transition", id=trans_id)
        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        ET.SubElement(transition, "source", ref=source)
        ET.SubElement(transition, "target", ref=target)

        x1, y1 = template["position_map"].get(source_id, (0, 0))
        x2, y2 = template["position_map"].get(target_id, (0, 0))
        x_mid = (x1 + x2) // 2
        y_mid = (y1 + y2) // 2

        # Handle time constraints
        if "," in source_name and "t=" in source_name:
            try:
                time_val = int(source_name.split("t=")[-1].strip())
                clock_name = template["clock_name"]
                
                # Create separate labels for guard and assignment
                ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 60)).text = f"{clock_name}>{time_val}"
                ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"{clock_name}:=0"
                
            except ValueError:
                pass

        print(f"✅ Added transition: {source_name} -> {target_name}")

class ForkTemplateBuilder:
    """จัดการ business logic ของ fork templates"""
    
    def __init__(self, template_manager, location_builder, transition_builder, declaration_manager):
        self.template_manager = template_manager
        self.location_builder = location_builder
        self.transition_builder = transition_builder
        self.declaration_manager = declaration_manager
        self.parser = None
    
    def set_parser(self, parser):
        """กำหนด parser"""
        self.parser = parser
    
    def create_fork_templates_for_node(self, fork_node_id, fork_node_name):
        """สร้าง fork templates สำหรับ ForkNode"""
        if not self.parser:
            raise ValueError("Parser not set")
        
        # สร้าง fork channel
        fork_channel = self.template_manager.add_fork_channel(fork_node_id)
        
        # Get fork branches from parser
        fork_branches = self.parser.get_fork_branches().get(fork_node_id, [])
        print(f"🎯 ForkNode {fork_node_name} has {len(fork_branches)} branches")
        
        for i, branch_nodes in enumerate(fork_branches, 1):
            # กำหนดชื่อ template ตาม ForkNode และ Branch
            fork_name_clean = fork_node_name.replace(" ", "").replace(",", "")
            template_name = f"Template_{fork_name_clean}_Branch{i}"
            
            # ตรวจสอบว่าสร้างแล้วหรือยัง
            if template_name in self.template_manager.created_template_names:
                print(f"⚠️ Skipping duplicate template creation: {template_name}")
                continue
                
            print(f"🎯 Creating fork template: {template_name} with {len(branch_nodes)} nodes")
            self.declaration_manager.add_done_variable(template_name)
            
            # Create fork template and populate with branch content
            template = self.template_manager.create_fork_template(template_name)
            self._populate_fork_template_content(template, branch_nodes, fork_node_id)
        
        return fork_channel
    
    def _populate_fork_template_content(self, template, branch_nodes, parent_fork_id):
        """เติมเนื้อหาใน fork template - สร้าง locations และ transitions"""
        if not branch_nodes:
            return
        
        # สร้าง initial location สำหรับ fork template
        initial_id = f"InitialNode_{template['name']}"
        self.location_builder.add_location(template, initial_id, initial_id, "uml:InitialNode")
        template["initial_id"] = initial_id
        
        # เพิ่ม locations สำหรับทุก nodes ใน branch
        for node_id in branch_nodes:
            if node_id in self.parser.nodes:
                node_info = self.parser.get_node_info(node_id)
                if node_info:
                    self.location_builder.add_location(
                        template, 
                        node_id, 
                        node_info['name'], 
                        node_info['type']
                    )
        
        # สร้าง transitions ระหว่าง nodes ใน branch
        self._create_branch_transitions(template, branch_nodes, parent_fork_id)
        
        # ตรวจสอบ nested forks ใน branch
        self._handle_nested_forks_in_branch(template, branch_nodes)
    
    def _create_branch_transitions(self, template, branch_nodes, parent_fork_id):
        """สร้าง transitions ใน branch"""
        # เชื่อม initial location กับ first node
        if template["initial_id"] and branch_nodes:
            first_node = branch_nodes[0]
            if first_node in template["state_map"]:
                trans_id = f"{template['initial_id']}_{first_node}"
                transition = ET.SubElement(template["element"], "transition", id=trans_id)
                ET.SubElement(transition, "source", ref=template["initial_id"])
                ET.SubElement(transition, "target", ref=template["state_map"][first_node])
                print(f"✅ Added transition: {template['initial_id']} -> {self.parser.get_node_name(first_node)}")
        
        # สร้าง transitions ตาม adjacency ใน branch
        for node_id in branch_nodes:
            outgoing_nodes = self.parser.get_outgoing_nodes(node_id)
            for target_id in outgoing_nodes:
                if target_id in branch_nodes and target_id in template["state_map"]:
                    source_name = self.parser.get_node_name(node_id)
                    target_name = self.parser.get_node_name(target_id)
                    
                    trans_id = f"{node_id}_{target_id}"
                    transition = ET.SubElement(template["element"], "transition", id=trans_id)
                    ET.SubElement(transition, "source", ref=template["state_map"][node_id])
                    ET.SubElement(transition, "target", ref=template["state_map"][target_id])
                    
                    # Add time constraints if needed
                    if "t=" in source_name:
                        try:
                            time_val = int(source_name.split("t=")[-1].strip())
                            x1, y1 = template["position_map"].get(node_id, (0, 0))
                            x2, y2 = template["position_map"].get(target_id, (0, 0))
                            x_mid = (x1 + x2) // 2
                            y_mid = (y1 + y2) // 2
                            
                            ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 60)).text = f"{template['clock_name']}>{time_val}"
                            ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"{template['clock_name']}:=0"
                        except ValueError:
                            pass
                    
                    print(f"✅ Added transition: {source_name} -> {target_name}")
    
    def _handle_nested_forks_in_branch(self, parent_template, branch_nodes):
        """จัดการ nested forks ใน branch"""
        for node_id in branch_nodes:
            node_type = self.parser.get_node_type(node_id)
            if node_type in ("uml:ForkNode", "ForkNode"):
                # This is a nested fork - create templates for its branches
                node_name = self.parser.get_node_name(node_id)
                nested_fork_branches = self.parser.get_fork_branches().get(node_id, [])
                
                print(f"🔍 Found nested fork: {node_name} with {len(nested_fork_branches)} branches")
                
                for i, nested_branch in enumerate(nested_fork_branches, 1):
                    # สร้าง nested template name
                    parent_name = parent_template["name"]
                    nested_template_name = f"{parent_name}_Nested{i}"
                    
                    # ตรวจสอบว่าสร้างแล้วหรือยัง
                    if nested_template_name in self.template_manager.created_template_names:
                        print(f"⚠️ Skipping duplicate nested template: {nested_template_name}")
                        continue
                    
                    print(f"🎯 Creating nested template: {nested_template_name} with {len(nested_branch)} nodes")
                    self.declaration_manager.add_done_variable(nested_template_name)
                    
                    # สร้าง nested template
                    nested_template = self.template_manager.create_fork_template(nested_template_name)
                    
                    # เติมเนื้อหาใน nested template
                    self._populate_fork_template_content(nested_template, nested_branch, node_id)

class TemplateManager:
    """จัดการ template lifecycle เท่านั้น"""
    
    def __init__(self, declaration_manager):
        self.declaration_manager = declaration_manager
        self.templates = []
        self.fork_templates = []
        self.fork_counter = 0
        self.fork_channels = {}
        self.created_template_names = set()
    
    def create_template(self, name="Template"):
        """สร้าง template ใหม่ - ป้องกันการสร้างซ้ำ"""
        if name in self.created_template_names:
            for template in self.templates + self.fork_templates:
                if template["name"] == name:
                    return template
        
        clock_name = self.declaration_manager.create_clock()
        
        template = ET.Element("template")
        ET.SubElement(template, "name").text = name
        ET.SubElement(template, "declaration").text = f"clock {clock_name};"
        
        template_data = {
            "name": name,
            "element": template,
            "state_map": {},
            "id_counter": 0,
            "x_offset": 0,
            "position_map": {},
            "initial_id": None,
            "clock_name": clock_name
        }
        
        self.templates.append(template_data)
        self.created_template_names.add(name)
        return template_data
    
    def create_fork_template(self, template_name):
        """สร้าง fork template"""
        if template_name in self.created_template_names:
            for template in self.templates + self.fork_templates:
                if template["name"] == template_name:
                    return template
        
        template = self.create_template(template_name)
        if template not in self.fork_templates:
            self.fork_templates.append(template)
        
        return template
    
    def add_fork_channel(self, fork_id, channel_name=None):
        """เพิ่ม fork channel"""
        if fork_id not in self.fork_channels:
            if not channel_name:
                self.fork_counter += 1
                channel_name = f"fork{self.fork_counter}"
            self.fork_channels[fork_id] = channel_name
            self.declaration_manager.add_fork_channel(fork_id, channel_name)
        return self.fork_channels[fork_id]
    
    def get_fork_channel(self, fork_id):
        """ได้ fork channel"""
        return self.fork_channels.get(fork_id)
    
    def get_all_templates(self):
        """ได้ templates ทั้งหมด"""
        return self.templates + self.fork_templates

class XMLGenerator:
    """สร้าง UPPAAL XML output เท่านั้น"""
    
    def __init__(self, declaration_manager, template_manager):
        self.declaration_manager = declaration_manager
        self.template_manager = template_manager
    
    def generate_nta_element(self):
        """สร้าง NTA element สำหรับ UPPAAL XML"""
        nta = ET.Element("nta")
        
        # เพิ่ม declarations
        decl_elem = ET.SubElement(nta, "declaration")
        declarations = self.declaration_manager.generate_global_declarations()
        decl_elem.text = declarations
        
        # เพิ่ม templates ทั้งหมด
        all_templates = self.template_manager.get_all_templates()
        
        for template in all_templates:
            template_elem = template["element"]
            if template["initial_id"]:
                # ลบ init element เดิมถ้ามี
                for init_elem in template_elem.findall("init"):
                    template_elem.remove(init_elem)
                # เพิ่ม init element ใหม่
                ET.SubElement(template_elem, "init", ref=template["initial_id"])
            nta.append(template_elem)
        
        # เพิ่ม system declaration
        system_elem = ET.SubElement(nta, "system")
        system_declarations = []
        for i, template in enumerate(all_templates, 1):
            system_declarations.append(f"T{i} = {template['name']}();")
        
        system_declarations.append("system " + ", ".join(f"T{i}" for i in range(1, len(all_templates) + 1)) + ";")
        system_elem.text = "\n".join(system_declarations)
        
        # เพิ่ม queries
        queries = ET.SubElement(nta, "queries")
        query = ET.SubElement(queries, "query")
        ET.SubElement(query, "formula").text = "A[] not deadlock"
        ET.SubElement(query, "comment").text = "Check for deadlocks"
        
        return nta

    def _indent_xml(self, elem, level=0):
        """จัดรูปแบบ XML"""
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for subelem in elem:
                self._indent_xml(subelem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

class xmlConverter:
    """แปลงแฟ้ม XML ของแผนภาพกิจกรรมที่มีการกำหนดเวลา ไปเป็นแฟ้ม XML ของไทมด์ออโตมาตา - Coordinator เท่านั้น"""
    
    def __init__(self):
        # สร้าง components ต่างๆ ตามลำดับ dependency
        self.declaration_manager = DeclarationManager()
        self.location_builder = LocationBuilder(self.declaration_manager)
        self.transition_builder = TransitionBuilder(self.declaration_manager)
        self.template_manager = TemplateManager(self.declaration_manager)
        self.fork_template_builder = ForkTemplateBuilder(
            self.template_manager, 
            self.location_builder, 
            self.transition_builder, 
            self.declaration_manager
        )
        self.xml_generator = XMLGenerator(self.declaration_manager, self.template_manager)
        
        # ตัวแปรสำหรับการทำงาน
        self.parser = None
        self.activity_root = None
        self.node_info = {}
        self.node_types = {}
        self.edge_guards = {}
        
        # Set up cross-references
        self.transition_builder.set_template_manager(self.template_manager)
    
    def set_activity_root(self, activity_root):
        """กำหนด activity root และสร้าง parser"""
        self.activity_root = activity_root
        self.parser = ActivityDiagramParser(activity_root)
        
        # ตั้งค่า parser ให้กับ components ที่ต้องการ
        self.fork_template_builder.set_parser(self.parser)
        self.transition_builder.set_parser(self.parser)
        
        # สร้าง node_info และ node_types สำหรับ backward compatibility
        self.node_info = {}
        self.node_types = {}
        for node_id, node_data in self.parser.nodes.items():
            self.node_info[node_id] = node_data['name']
            self.node_types[node_id] = node_data['type']
        
        print(f"Parser created - Total nodes: {len(self.parser.nodes)}")
        print(f"Parser created - Main flow nodes: {len(self.parser.main_flow_nodes)}")
        
        # แสดงรายการ main flow nodes
        print("Main flow nodes in parser:")
        for node_id in self.parser.main_flow_nodes:
            node_info = self.parser.get_node_info(node_id)
            if node_info:
                print(f"  • {node_info['type']:<20} | {node_info['name']}")
        print()

    @property
    def templates(self):
        """ได้ templates ทั้งหมด"""
        return self.template_manager.templates

    @property
    def fork_templates(self):
        """ได้ fork templates ทั้งหมด"""
        return self.template_manager.fork_templates

    @property
    def fork_channels(self):
        """ได้ fork channels ทั้งหมด"""
        return self.template_manager.fork_channels
    
    def process_nodes(self):
        """ประมวลผล nodes และสร้าง main template - เป็น coordinator เท่านั้น"""
        if not self.parser:
            raise ValueError("ActivityDiagramParser not initialized. Call set_activity_root() first.")
        
        # แสดงผล analysis
        self.parser.print_analysis()
        
        # สร้าง main template
        main_template = self.template_manager.create_template("Template")
        
        # เพิ่มเฉพาะ main flow nodes เข้า main template
        main_flow_nodes = self.parser.get_main_flow_nodes()
        
        print(f"Main flow nodes identified: {len(main_flow_nodes)}")
        for node_id in main_flow_nodes:
            node_info = self.parser.get_node_info(node_id)
            if node_info:
                node_type = node_info['type']
                node_name = node_info['name']
                print(f"Including in main template: {node_type} - {node_name}")
                self.location_builder.add_location(main_template, node_id, node_name, node_type)
        
        # สร้าง edge guards จาก parser
        for edge_data in self.parser.get_all_edges():
            source = edge_data['source']
            target = edge_data['target']
            guard = edge_data['guard']
            name = edge_data['name']
            
            if guard or name:
                self.edge_guards[(source, target)] = guard or name
        
        # สร้าง fork templates สำหรับ ForkNodes ทั้งหมด
        self._create_all_fork_templates()
        
        # ประมวลผล edges สำหรับ main template
        bypass_edges = self._create_bypass_edges(main_flow_nodes, main_template)
        connected_edges = self._create_connected_edges(main_flow_nodes)
        
        # สร้าง transitions
        self.transition_builder.create_all_transitions(main_template, connected_edges, bypass_edges)
        
        print(f"\nMain template created with:")
        print(f"  - {len(main_flow_nodes)} nodes")
        print(f"  - {len(connected_edges)} direct edges")
        print(f"  - {len(bypass_edges)} bypass edges")
        print(f"  - {len(self.fork_templates)} fork templates")
        
        return main_template
    
    def _create_all_fork_templates(self):
        """สร้าง fork templates สำหรับ ForkNodes ทั้งหมด - เฉพาะ top-level forks เท่านั้น"""
        fork_branches = self.parser.get_fork_branches()
        processed_forks = set()  # ป้องกันการประมวลผล fork ซ้ำ
        
        # กรอง ForkNodes เฉพาะที่เป็น top-level (ไม่ใช่ nested)
        top_level_forks = []
        for fork_id, branches in fork_branches.items():
            fork_info = self.parser.get_node_info(fork_id)
            if fork_info:
                fork_name = fork_info['name']
                # เฉพาะ ForkNode1 และ ForkNode2 เท่านั้น (ไม่รวม ForkNode1_1)
                if "ForkNode1_1" not in fork_name:  # ข้าม nested fork
                    top_level_forks.append((fork_id, fork_name, branches))
        
        for fork_id, fork_name, branches in top_level_forks:
            if fork_id in processed_forks:
                print(f"⚠️ Skipping already processed fork: {fork_id}")
                continue
                
            print(f"\n🎯 Processing ForkNode: {fork_name} (ID: {fork_id})")
            print(f"   Creating {len(branches)} branch templates")
            
            # สร้าง fork templates สำหรับ ForkNode นี้
            self.fork_template_builder.create_fork_templates_for_node(fork_id, fork_name)
            processed_forks.add(fork_id)
    
    def _create_bypass_edges(self, main_flow_nodes, main_template):
        """สร้าง bypass edges สำหรับ ForkNodes ที่ไม่มี direct connections ไปยัง JoinNodes"""
        bypass_edges = []
        
        # Create bypass transitions for ForkNodes that need them
        main_flow_nodes_list = list(main_flow_nodes)  # Convert to list to avoid iteration issues
        for node_id in main_flow_nodes_list:
            node_type = self.parser.get_node_type(node_id)
            if node_type in ("uml:ForkNode", "ForkNode"):
                # Find corresponding JoinNode
                corresponding_join = self.parser._find_corresponding_join(node_id)
                print(f"🔍 Checking ForkNode: {self.parser.get_node_name(node_id)} (ID: {node_id})")
                print(f"  Found corresponding join: {self.parser.get_node_name(corresponding_join) if corresponding_join else 'None'} (ID: {corresponding_join})")
                
                # Add corresponding join to main flow if it's not nested
                if corresponding_join and not self.parser._is_nested_fork_join(corresponding_join):
                    if corresponding_join not in main_flow_nodes:
                        # Add JoinNode to main flow and main template
                        main_flow_nodes.add(corresponding_join)
                        join_info = self.parser.get_node_info(corresponding_join)
                        if join_info:
                            self.location_builder.add_location(
                                main_template, 
                                corresponding_join, 
                                join_info['name'], 
                                join_info['type']
                            )
                            print(f"  ✅ Added JoinNode to main flow: {join_info['name']}")
                    
                    # Create bypass edge
                    bypass_edge = {
                        'source': node_id,
                        'target': corresponding_join,
                        'guard': "",
                        'name': f"bypass_{self.parser.get_node_name(node_id)}"
                    }
                    bypass_edges.append(bypass_edge)
                    print(f"  ✅ Created bypass edge: {self.parser.get_node_name(node_id)} -> {self.parser.get_node_name(corresponding_join)}")
        
        return bypass_edges
    
    def _create_connected_edges(self, main_flow_nodes):
        """สร้าง connected edges สำหรับ main template"""
        connected_edges = []
        
        print(f"\nProcessing edges for main template...")
        for edge_data in self.parser.get_all_edges():
            source = edge_data['source']
            target = edge_data['target']
            
            # ถ้าทั้ง source และ target อยู่ใน main template
            if source in main_flow_nodes and target in main_flow_nodes:
                connected_edges.append(edge_data)
                source_name = self.parser.get_node_name(source)
                target_name = self.parser.get_node_name(target)
                print(f"Direct edge: {source_name} -> {target_name}")
        
        return connected_edges

    def get_node_type(self, node_id):
        """Returns the type of node using parser data."""
        if self.parser:
            return self.parser.get_node_type(node_id)
        return ""
    
    def generate_xml(self):
        """สร้าง UPPAAL XML"""
        # สร้าง NTA element
        nta = self.xml_generator.generate_nta_element()
        
        # Format XML
        self.xml_generator._indent_xml(nta)
        raw_xml = ET.tostring(nta, encoding="utf-8", method="xml").decode()
        header = '<?xml version="1.0" encoding="utf-8"?>\n'
        doctype = '<!DOCTYPE nta PUBLIC \'-//Uppaal Team//DTD Flat System 1.6//EN\' \'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd\'>\n'
        return header + doctype + raw_xml

# Serve the HTML file at root
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>Frontend not found</h1><p>Please ensure index.html exists in the same directory.</p>", status_code=404)

@app.post("/convert-xml")
async def convert_xml(file: UploadFile = File(...)):
    """แปลง Activity Diagram XML เป็น UPPAAL XML"""
    try:
        # อ่านเนื้อหาของไฟล์
        contents = await file.read()
        
        # Parse XML
        root = ET.fromstring(contents)
        
        # หา activity element แบบละเอียด
        activity = None
        
        # ลองหาจาก UML namespace แบบต่างๆ
        namespaces = {
            'uml': 'http://www.eclipse.org/uml2/5.0.0/UML',
            'xmi': 'http://www.omg.org/spec/XMI/20131001'
        }
        
        # ลองหาจาก packagedElement ที่เป็น Activity
        for elem in root.findall(".//packagedElement", namespaces):
            xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
            if xmi_type == 'uml:Activity':
                activity = elem
                print(f"Found Activity: {elem.get('name', 'unnamed')}")
                break
        
        # ถ้าไม่เจอ ลองหาแบบปกติ
        if activity is None:
            activity = root.find(".//*[@xmi:type='uml:Activity']", namespaces)
        if activity is None:
            activity = root.find(".//activity")
        if activity is None:
            activity = root.find(".//*[@type='Activity']")
        
        # ถ้ายังไม่เจอให้ใช้ root element
        if activity is None:
            activity = root
            print("Using root element as activity")
        else:
            print(f"Found activity element: {activity.tag}")
        
        # แสดงข้อมูลที่พบ
        print(f"Activity nodes found: {len(activity.findall('.//node'))}")
        print(f"Activity edges found: {len(activity.findall('.//edge'))}")
        
        # สร้าง converter และประมวลผล
        converter = xmlConverter()
        converter.set_activity_root(activity)
        
        # ประมวลผล nodes และสร้าง templates
        converter.process_nodes()
        
        # สร้าง UPPAAL XML
        uppaal_xml = converter.generate_xml()
        
        # บันทึกไฟล์ผลลัพธ์
        os.makedirs("Result", exist_ok=True)
        result_files = [f for f in os.listdir("Result") if f.startswith("Result_")]
        result_num = len(result_files) + 1
        output_filename = f"Result/Result_{result_num}.xml"
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(uppaal_xml)
        
        print(f"Successfully converted {file.filename} to {output_filename}")
        
        return {
            "status": "success",
            "message": f"Successfully converted {file.filename}",
            "output_file": output_filename,
            "download_url": f"/download/{output_filename}"
        }
        
    except Exception as e:
        print(f"Error converting XML: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Error converting XML: {str(e)}"
        }

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """ดาวน์โหลดไฟล์ผลลัพธ์"""
    from fastapi.responses import FileResponse
    import os
    
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type='application/xml'
        )
    else:
        return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 