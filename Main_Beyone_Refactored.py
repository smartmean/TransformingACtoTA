from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import xml.etree.ElementTree as ET
import os
import traceback

app = FastAPI()

class DeclarationManager:
    """จัดการ declarations และตัวแปร"""
    
    def __init__(self):
        self.declarations = []
        self.clocks = []
        # เพิ่ม dictionaries สำหรับเก็บตัวแปรแต่ละประเภท
        self.decision_variables = {}
        self.fork_channels = {}
        self.done_variables = {}
        self.clock_counter = 0
    
    def create_clock(self):
        """สร้าง clock ใหม่"""
        self.clock_counter += 1
        clock_name = f"x{self.clock_counter}"
        self.add_clock(clock_name)
        return clock_name
    
    def add_done_variable(self, template_name):
        """เพิ่ม Done variable สำหรับ template"""
        done_var_name = f"Done_{template_name}"
        if done_var_name not in self.done_variables:
            self.done_variables[done_var_name] = True
            self.declarations.append(f"bool {done_var_name};")
    
    def add_clock(self, clock_name):
        """เพิ่ม clock declaration"""
        if clock_name not in self.clocks:
            self.clocks.append(clock_name)
            self.declarations.append(f"clock {clock_name};")
    
    def add_decision_variable(self, var_name):
        """เพิ่ม decision variable"""
        if var_name not in self.decision_variables:
            self.decision_variables[var_name] = True
            self.declarations.append(f"int {var_name};")
    
    def add_fork_channel(self, node_id, channel_name):
        """เพิ่ม fork channel และ done variable"""
        if node_id not in self.fork_channels:
            self.fork_channels[node_id] = channel_name
            self.declarations.append(f"broadcast chan {channel_name};")
            
            # Extract clean name from channel_name (e.g., fork_ForkNode1 -> ForkNode1)
            clean_name = channel_name.replace("fork_", "")
            done_var_name = f"Done_{clean_name}_Fork"
            self.declarations.append(f"bool {done_var_name};")
    
    def add_variable(self, declaration):
        """เพิ่มตัวแปรทั่วไป"""
        if declaration not in self.declarations:
            self.declarations.append(declaration)
    
    def get_declaration_text(self):
        """ได้ declaration text ในรูปแบบเดียวกับ Main_Beyone_final.py"""
        declarations = []
        
        # Add Done variables first (sorted)
        done_vars = sorted([f"bool {var};" for var in self.done_variables.keys()])
        declarations.extend(done_vars)
        
        # Add fork channels (sorted)
        fork_channels = sorted([f"broadcast chan {channel};" for channel in self.fork_channels.values()])
        declarations.extend(fork_channels)
        
        # Add global clock
        declarations.append("clock total_time=0;")
        
        # Add decision variables (sorted)
        decision_vars = sorted([f"int {var};" for var in self.decision_variables.keys()])
        declarations.extend(decision_vars)
        
        # Add any additional declarations
        for decl in self.declarations:
            if decl not in declarations:
                declarations.append(decl)
        
        return "\n".join(declarations)

class ActivityDiagramParser:
    """แยกโครงสร้างและวิเคราะห์ Activity Diagram XML - เหมือน Main_Beyone_final.py"""
    
    def __init__(self, activity_root=None):
        self.activity_root = activity_root
        self.nodes = {}  # node_id -> node_info
        self.edges = {}  # (source, target) -> edge_info
        self.edge_guards = {}  # (source, target) -> guard_text - เพิ่มบรรทัดนี้
        self.node_types = {}  # node_id -> node_type
        self.node_names = {}  # node_id -> node_name
        self.adjacency_list = {}  # node_id -> [outgoing_targets]
        self.reverse_adjacency = {}  # node_id -> [incoming_sources]
        self.coordination_nodes = set()  # nodes ที่เป็น coordination structure
        self.fork_branches = {}  # fork_id -> [branch_nodes]
        self.main_flow_nodes = set()  # nodes ที่อยู่ใน main coordination flow
        
        if activity_root is not None:
            self._parse_structure()
            self._analyze_flow()
    
    def set_activity_root(self, activity_root):
        """ตั้งค่า activity root และ parse ใหม่"""
        self.activity_root = activity_root
        self._parse_structure()
        self._analyze_flow()
    
    def parse_file(self, file_path):
        """Parse XML file"""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # หา activity element
            activity = None
            for elem in root.findall(".//*"):
                xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
                if xmi_type == 'uml:Activity':
                    activity = elem
                    break
            
            if activity is None:
                activity = root
            
            self.set_activity_root(activity)
            return True
        except Exception as e:
            print(f"Error parsing file: {e}")
            return False
    
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
                
                # เพิ่ม edge_guards สำหรับใช้กับ TransitionBuilder
                if guard or edge_name:
                    self.edge_guards[(source, target)] = guard or edge_name
                
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
            # ติดตาม outgoing edges ปกติ
            for next_node in self.adjacency_list.get(start_node, []):
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
        # เพิ่ม members ที่ขาดหายไป
        self.decision_vars = {}
        self.declarations = []
        self.fork_channels = {}
        self.join_nodes = {}
    
    def add_location(self, template, node_id, node_name, node_type):
        """เพิ่ม location เข้าไปใน template - เหมือน UppaalConverter"""
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
        
        if node_type in ("uml:DecisionNode", "DecisionNode"):
            label_name = f"{clean_name}_Decision"
            # เพิ่ม decision variable ไปยัง DeclarationManager
            self.declaration_manager.add_decision_variable(clean_name)
        elif node_type in ("uml:ForkNode", "ForkNode"):
            label_name = f"{clean_name}_Fork"
            # เพิ่ม fork declarations
            channel_name = f"fork_{clean_name}"
            done_var_name = f"Done_{clean_name}_Fork"
            self.declaration_manager.add_fork_channel(node_id, channel_name)
            self.declaration_manager.add_done_variable(f"{clean_name}_Fork")
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
    """สร้าง transitions"""
    
    def __init__(self, declaration_manager, location_builder):
        self.declaration_manager = declaration_manager
        self.location_builder = location_builder
        # เพิ่ม members ที่ขาดหายไป
        self.template_hierarchy = {}
        self.fork_templates = []
        self.template_manager = None
        self.parser = None
    
    def set_template_manager(self, template_manager):
        """Set template manager"""
        self.template_manager = template_manager
    
    def set_parser(self, parser):
        """Set parser"""
        self.parser = parser
    
    def create_all_transitions(self, main_template, connected_edges, bypass_edges):
        """สร้าง transitions ทั้งหมดสำหรับ main template"""
        # สร้าง transitions จาก connected edges
        for edge_data in connected_edges:
            source = edge_data['source']
            target = edge_data['target']
            edge_name = edge_data.get('name', '')
            guard = edge_data.get('guard', '')
            self.add_transition(main_template, source, target, edge_name, guard)
        
        # สร้าง transitions จาก bypass edges
        for edge_data in bypass_edges:
            source = edge_data['source']
            target = edge_data['target']
            edge_name = edge_data.get('name', '')
            guard = edge_data.get('guard', '')
            self.add_transition(main_template, source, target, edge_name, guard)
    
    def add_transition(self, template, source_id, target_id, edge_name=None, guard_condition=None, source_name=None, target_name=None, target_type=None, from_fork_template=False):
        """เพิ่ม transition เข้าไปใน template - เหมือน UppaalConverter ทุกอย่าง"""
        if not source_id or not target_id:
            return

        source_loc_id = template['state_map'].get(source_id)
        target_loc_id = template['state_map'].get(target_id)
        
        if source_loc_id is None or target_loc_id is None:
            return

        # ตรวจสอบว่า transition นี้ได้ถูกสร้างแล้วหรือไม่
        trans_key = (source_id, target_id)
        created_transitions = getattr(template, '_created_transitions', set())
        if trans_key in created_transitions:
            return
        created_transitions.add(trans_key)
        template['_created_transitions'] = created_transitions

        # Get node information
        if hasattr(self, 'parser') and self.parser:
            source_info = self.parser.get_node_info(source_id)
            target_info = self.parser.get_node_info(target_id)
            
            if not source_name and source_info:
                source_name = source_info.get('name', '')
            if not target_name and target_info:
                target_name = target_info.get('name', '')
            if not target_type and target_info:
                target_type = target_info.get('type', '')

        # สำหรับ main template: special handling for ForkNode transitions
        if (template["name"] == "Template" and 
            hasattr(self, 'parser') and self.parser and
            self.parser.get_node_type(source_id) in ("uml:ForkNode", "ForkNode")):
            
            # ตรวจสอบว่าเป็น bypass transition หรือไม่
            if self.parser.get_node_type(target_id) in ("uml:JoinNode", "JoinNode"):
                # สร้าง bypass transition with synchronization
                transition = ET.SubElement(template["element"], "transition")
                transition.set("id", f"{source_id}_{target_id}_bypass")
                ET.SubElement(transition, "source", ref=source_loc_id)
                ET.SubElement(transition, "target", ref=target_loc_id)

                x1, y1 = template["position_map"].get(source_id, (0, 0))
                x2, y2 = template["position_map"].get(target_id, (0, 0))
                x_mid = (x1 + x2) // 2
                y_mid = (y1 + y2) // 2

                # สร้าง fork channel และ templates
                outgoing_edges = self.parser.get_outgoing_nodes(source_id)
                
                # สร้าง fork channel
                if source_id not in self.template_manager.fork_channels:
                    fork_channel = f"fork_{source_name.replace(' ', '').replace(',', '')}"
                    self.template_manager.add_fork_channel(source_id, fork_channel)
                else:
                    fork_channel = self.template_manager.get_fork_channel(source_id)

                # สร้าง Done variables และ fork templates สำหรับแต่ละ branch
                for i, outgoing_edge in enumerate(outgoing_edges):
                    fork_name_clean = source_name.replace(" ", "").replace(",", "")
                    template_name = f"Template_{fork_name_clean}_Branch{i+1}"
                    
                    self.declaration_manager.add_done_variable(template_name)

                # เพิ่ม synchronization label
                ET.SubElement(transition, "label", kind="synchronisation", x=str(x_mid), y=str(y_mid - 80)).text = f"{fork_channel}!"
                return

        # สร้าง transition ปกติ
        transition = ET.SubElement(template["element"], "transition")
        transition.set("id", f"{source_id}_{target_id}")
        ET.SubElement(transition, "source", ref=source_loc_id)
        ET.SubElement(transition, "target", ref=target_loc_id)

        x1, y1 = template["position_map"].get(source_id, (0, 0))
        x2, y2 = template["position_map"].get(target_id, (0, 0))
        x_mid = (x1 + x2) // 2
        y_mid = (y1 + y2) // 2

        # Handle time constraints like Main_Beyone_final.py
        if source_name and "," in source_name and "t=" in source_name:
            try:
                time_val = int(source_name.split("t=")[-1].strip())
                clock_name = template.get("clock_name", "x1")
                
                # Add guard and assignment labels
                ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 60)).text = f"{clock_name}>{time_val}"
                
                # สร้าง assignment text
                assignment_text = f"{clock_name}:=0"
                
                # Add Done variable assignment for fork templates
                if template["name"].startswith("Template") and template in getattr(self.template_manager, 'fork_templates', []):
                    # ตรวจสอบว่าเป็น final transition ของ template หรือไม่
                    if hasattr(self, 'parser') and self.parser:
                        target_node_type = self.parser.get_node_type(target_id)
                        if target_node_type in ("uml:JoinNode", "JoinNode", "uml:FinalNode", "FinalNode") or not target_id:
                            assignment_text += f", Done_{template['name']} = true"
                
                ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = assignment_text
                
            except ValueError:
                pass

        # Handle JoinNode guard conditions like Main_Beyone_final.py
        if hasattr(self, 'parser') and self.parser and self.parser.get_node_type(source_id) in ("uml:JoinNode", "JoinNode"):
            guard_conditions = []
            
            # สำหรับ main template
            if template["name"] == "Template" and not from_fork_template:
                # หา ForkNode ที่ corresponding กับ JoinNode นี้
                corresponding_fork = self._find_fork_for_join(source_id)
                
                if corresponding_fork:
                    # หา templates ที่ถูกสร้างจาก ForkNode นี้
                    fork_templates = self._get_templates_for_fork(corresponding_fork)
                    guard_conditions = [f"Done_{template_name}==true" for template_name in fork_templates]
            
            if guard_conditions:
                ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = " && ".join(guard_conditions)

        # Handle decision node variables like Main_Beyone_final.py
        if hasattr(self, 'parser') and self.parser and self.parser.get_node_type(target_id) in ("uml:DecisionNode", "DecisionNode"):
            decision_var = target_name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
            var_name = f"i{template['id_counter']}"
            
            ET.SubElement(transition, "label", kind="select", x=str(x_mid), y=str(y_mid - 100)).text = f"{var_name}: int[0,1]"
            
            clock_name = template.get("clock_name", "x1")
            assignment_text = f"{clock_name}:=0, {decision_var} = {var_name}"
            ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = assignment_text

        # Handle edge guards for decision branches like Main_Beyone_final.py
        if hasattr(self, 'parser') and self.parser:
            edge_info = self.parser.get_edge_info(source_id, target_id)
            if edge_info:
                guard_text = edge_info.get('guard', '') or edge_info.get('name', '')
                
                if guard_text and "=" in guard_text:
                    # ตั้งชื่อ decision variable จาก source node
                    source_node_info = self.parser.get_node_info(source_id)
                    if source_node_info:
                        decision_var = source_node_info['name'].split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
                        
                        condition = guard_text.strip("[]").split("=")[1].strip().lower()
                        if condition == "yes":
                            ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = f"{decision_var}==1"
                        elif condition == "no":
                            ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 80)).text = f"{decision_var}==0"

        # Handle Done variable assignment for non-time transitions in fork templates
        if (template["name"].startswith("Template") and 
            template in getattr(self.template_manager, 'fork_templates', []) and
            not (source_name and "t=" in source_name)):
            
            if hasattr(self, 'parser') and self.parser:
                target_node_type = self.parser.get_node_type(target_id)
                if target_node_type in ("uml:JoinNode", "JoinNode", "uml:FinalNode", "FinalNode") or not target_id:
                    # Check if there's already an assignment label
                    existing_assign = transition.find("label[@kind='assignment']")
                    if existing_assign is not None:
                        existing_assign.text += f", Done_{template['name']} = true"
                    else:
                        ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid - 40)).text = f"Done_{template['name']} = true"

    def _find_fork_for_join(self, join_node_id):
        """หา ForkNode ที่ corresponding กับ JoinNode นี้"""
        if not hasattr(self, 'parser') or not self.parser:
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
        
        if not hasattr(self, 'parser') or not self.parser:
            return fork_templates
        
        # วิเคราะห์จาก template names ที่เป็น top-level และไม่ใช่ main
        fork_name = self.parser.get_node_name(fork_id)
        fork_name_clean = fork_name.replace(" ", "").replace(",", "")
        fork_pattern = f"Template_{fork_name_clean}_"
        
        if hasattr(self.template_manager, 'templates'):
            for template in self.template_manager.templates:
                template_name = template["name"]
                if (template_name != "Template" and 
                    fork_pattern in template_name and
                    "_Nested" not in template_name):  # เฉพาะ top-level templates
                    fork_templates.append(template_name)
        
        return fork_templates

class ForkTemplateBuilder:
    """จัดการ business logic ของ fork templates - ครบถ้วนแบบ Main_Beyone_final.py"""
    
    def __init__(self, template_manager, location_builder, transition_builder, declaration_manager):
        self.template_manager = template_manager
        self.location_builder = location_builder
        self.transition_builder = transition_builder
        self.declaration_manager = declaration_manager
        self.parser = None
        self.template_hierarchy = {}  # เก็บ hierarchy ของ templates
        self.nested_fork_structure = {}  # เก็บโครงสร้าง nested fork
        self.created_template_names = set()  # ป้องกันการสร้างซ้ำ
    
    def set_parser(self, parser):
        """กำหนด parser"""
        self.parser = parser
    
    def create_fork_template(self, template_name, fork_id, outgoing_edge, parent_template=None, level=0):
        """Creates a new template for forked processes - เหมือน UuppaalConverter"""
        hierarchical_name = template_name
            
        self.template_hierarchy[hierarchical_name] = {
            'parent': parent_template,
            'level': level,
            'fork_id': fork_id
        }
        
        # Create template with hierarchical name
        fork_template = self.template_manager.create_fork_template(hierarchical_name)
        
        # If template already exists, return it without modifying
        if len(fork_template["state_map"]) > 0:
            return fork_template
        
        initial_id = f"fork_{hierarchical_name}"
        self.location_builder.add_location(fork_template, initial_id, f"InitialNode_{hierarchical_name}", "InitialNode")
        
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
                    self.location_builder.add_location(fork_template, node_id, node_name, node_type)
                    
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
        """เก็บรวบรวม nodes ใน branch - รวม JoinNode ที่สอดคล้องกับ nested ForkNode - เหมือน Main_Beyone_final.py"""
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
        """สร้าง transitions สำหรับ template แบบเหมือน Main_Beyone_final.py"""
        # หา first process node ที่เป็น direct outgoing จาก parent ForkNode
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
        
        # วิธี 2: ถ้าไม่พบ ให้หา node แรกที่ไม่ใช่ coordination
        if not first_process_node:
            for node_id in branch_nodes:
                node_type = self.parser.get_node_type(node_id) if self.parser else ""
                if node_type in ("uml:OpaqueAction", "OpaqueAction", "uml:DecisionNode", "DecisionNode", "uml:MergeNode", "MergeNode"):
                    first_process_node = node_id
                    break
        
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
            fork_channel = self.template_manager.get_fork_channel(parent_fork_id)
            
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
        
        # สร้าง transitions ระหว่าง nodes ใน branch ตาม edges ที่มี
        if self.parser:
            for edge_data in self.parser.get_all_edges():
                source = edge_data['source']
                target = edge_data['target']
                
                # ถ้าทั้ง source และ target อยู่ใน branch นี้
                if (source in branch_nodes and target in branch_nodes and source != initial_id):
                    # สร้าง transition ผ่าน transition_builder
                    self.transition_builder.add_transition(
                        fork_template, source, target, 
                        from_fork_template=True
                    )
        
        # สร้าง nested fork synchronization ถ้ามี
        if nested_fork_id and corresponding_join_id and level == 0:
            # สร้าง intermediate location สำหรับ nested fork synchronization
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
            
            # สร้าง nested fork channel
            if nested_fork_id not in self.template_manager.fork_channels:
                nested_fork_name = self.parser.get_node_name(nested_fork_id) if self.parser else "nested_fork"
                nested_channel = f"fork_{nested_fork_name}"
                self.template_manager.add_fork_channel(nested_fork_id, nested_channel)
            else:
                nested_channel = self.template_manager.get_fork_channel(nested_fork_id)
            
            # Transition 1: ForkNode → Intermediate (ส่ง fork signal)
            transition1 = ET.SubElement(fork_template["element"], "transition")
            ET.SubElement(transition1, "source", ref=nested_fork_id)
            ET.SubElement(transition1, "target", ref=intermediate_id)
            
            x1, y1 = fork_template["position_map"].get(nested_fork_id, (0, 0))
            x2, y2 = fork_template["position_map"].get(intermediate_id, (0, 0))
            x_mid1 = (x1 + x2) // 2
            y_mid1 = (y1 + y2) // 2
            
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
            
            # เพิ่ม assignment Done_Template = true
            assignment_text = f"Done_{template_name} = true"
            ET.SubElement(transition2, "label", kind="assignment", x=str(x_mid2), y=str(y_mid2 - 40)).text = assignment_text

    def create_fork_templates_for_node(self, fork_node_id, fork_node_name):
        """สร้าง fork templates สำหรับ ForkNode - แยกตาม Main_Beyone_final.py"""
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
            if template_name in self.created_template_names:
                print(f"⚠️ Skipping duplicate template creation: {template_name}")
                continue
                
            print(f"🎯 Creating fork template: {template_name} with {len(branch_nodes)} nodes")
            self.declaration_manager.add_done_variable(template_name)
            
            # เลือก first node ของ branch เป็น outgoing_edge
            outgoing_edge = branch_nodes[0] if branch_nodes else None
            if outgoing_edge:
                # Create fork template using the complete logic
                template = self.create_fork_template(template_name, fork_node_id, outgoing_edge)
                self.created_template_names.add(template_name)
        
        return fork_channel
    
    def create_fork_templates(self):
        """สร้าง fork templates ทั้งหมด"""
        if not self.parser:
            return []
        
        fork_templates = []
        
        # หา ForkNodes ทั้งหมด
        for node_id in self.parser.get_coordination_nodes():
            node_type = self.parser.get_node_type(node_id)
            if node_type in ("uml:ForkNode", "ForkNode"):
                node_name = self.parser.get_node_name(node_id)
                print(f"Creating fork templates for: {node_name}")
                self.create_fork_templates_for_node(node_id, node_name)
        
        # ส่งคืน fork templates ที่สร้างแล้ว
        return self.template_manager.fork_templates

    def initialize_nested_fork_variables(self):
        """Initialize Done variables for all nested fork templates - เหมือน Main_Beyone_final.py"""
        # เพิ่ม Done variables สำหรับทุก template ที่เป็น fork template
        for template in self.template_manager.fork_templates:
            template_name = template["name"]
            done_var = f"Done_{template_name}"
            if done_var not in self.declaration_manager.done_variables:
                self.declaration_manager.add_done_variable(template_name)

    def validate_fork_template_coverage(self):
        """ตรวจสอบว่า templates ถูกสร้างครบตาม fork branches หรือไม่ - เหมือน Main_Beyone_final.py"""
        print("\n" + "="*100)
        print("🔍 FORK TEMPLATE COVERAGE ANALYSIS")
        print("="*100)
        
        if not self.parser:
            print("❌ No parser available for analysis")
            return False
        
        # วิเคราะห์ทุก ForkNode และ branches
        all_forks = []
        for node_id in self.parser.get_coordination_nodes():
            node_type = self.parser.get_node_type(node_id)
            if node_type in ("uml:ForkNode", "ForkNode"):
                all_forks.append(node_id)
        
        print(f"\n📊 FOUND {len(all_forks)} FORK NODES:")
        print("-" * 80)
        
        total_expected_templates = 0
        total_created_templates = len(self.template_manager.fork_templates)
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
                found_template = None
                
                # ตรวจสอบใน template_hierarchy
                for template_name, hierarchy_info in self.template_hierarchy.items():
                    if hierarchy_info.get('fork_id') == fork_id:
                        created_templates_for_fork.append(template_name)
                        found_template = template_name
                        break
                
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

class TemplateManager:
    """จัดการ template lifecycle เท่านั้น"""
    
    def __init__(self, declaration_manager):
        self.declaration_manager = declaration_manager
        self.templates = []
        self.fork_templates = []
        self.fork_counter = 0
        self.fork_channels = {}
        self.created_template_names = set()
        self.main_template = None  # เพิ่มบรรทัดนี้
    
    def create_template(self, name="Template"):
        """สร้าง template ใหม่พร้อม clock เหมือน Main_Beyone_final.py"""
        # ตรวจสอบว่ามี template ชื่อนี้อยู่แล้วหรือไม่
        for template in self.templates:
            if template["name"] == name:
                return template

        # สร้าง clock name เหมือน Main_Beyone_final.py
        if name == "Template":
            clock_name = "t"
        else:
            # สำหรับ fork templates ใช้ t2, t3, t4, ...
            self.clock_counter += 1
            clock_name = f"t{self.clock_counter}"

        template = ET.Element("template")
        ET.SubElement(template, "name").text = name
        ET.SubElement(template, "declaration").text = f"clock {clock_name};"
        
        template_dict = {
            "name": name,
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
    
    def create_main_template(self):
        """สร้าง main template - เพิ่มเมธอดนี้"""
        if self.main_template is None:
            self.main_template = self.create_template("Template")
        return self.main_template
    
    def create_fork_template(self, template_name):
        """สร้าง fork template"""
        if template_name in self.created_template_names:
            for template in self.templates + self.fork_templates:
                if template["name"] == template_name:
                    return template
        
        template = self.create_template(template_name)
        # ย้าย template จาก self.templates ไปยัง self.fork_templates
        if template in self.templates:
            self.templates.remove(template)
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
    """สร้าง XML ขั้นสุดท้าย"""
    
    def __init__(self):
        pass
    
    def generate_nta_element(self):
        """สร้าง NTA element หลัก"""
        nta = ET.Element("nta")
        
        # เพิ่ม declarations
        decl_elem = ET.SubElement(nta, "declaration")
        decl_elem.text = ""  # จะถูกเติมภายหลัง
        
        return nta
    
    def _indent_xml(self, elem, level=0):
        """เพิ่ม indentation ให้ XML - เหมือน _indent"""
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
    
    def generate_xml(self, main_template, fork_templates, declarations):
        """สร้าง XML ขั้นสุดท้าย - เหมือน UuppaalConverter"""
        nta = ET.Element("nta")
        
        # เพิ่ม declarations
        decl_elem = ET.SubElement(nta, "declaration")
        decl_elem.text = declarations
        
        # เพิ่ม main template
        nta.append(main_template["element"])
        
        # เพิ่ม fork templates
        for template in fork_templates:
            nta.append(template["element"])
        
        # เพิ่ม system
        system_text = []
        template_count = 1
        system_text.append(f"T{template_count} = {main_template['name']}();")
        template_count += 1
        
        for template in fork_templates:
            system_text.append(f"T{template_count} = {template['name']}();")
            template_count += 1
        
        system_text.append("system " + ", ".join(f"T{i}" for i in range(1, template_count)) + ";")
        
        system_elem = ET.SubElement(nta, "system")
        system_elem.text = "\n".join(system_text)
        
        # เพิ่ม queries
        queries = ET.SubElement(nta, "queries")
        query = ET.SubElement(queries, "query")
        ET.SubElement(query, "formula").text = "A[] not deadlock"
        ET.SubElement(query, "comment").text = "Check for deadlocks"
        
        # Format XML
        self._indent(nta)
        raw_xml = ET.tostring(nta, encoding="utf-8", method="xml").decode()
        header = '<?xml version="1.0" encoding="utf-8"?>\n'
        doctype = '<!DOCTYPE nta PUBLIC \'-//Uppaal Team//DTD Flat System 1.6//EN\' \'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd\'>\n'
        return header + doctype + raw_xml
    
    def _indent(self, elem, level=0):
        """เพิ่ม indentation ให้ XML"""
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for subelem in elem:
                self._indent(subelem, level+1)
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
        self.transition_builder = TransitionBuilder(self.declaration_manager, self.location_builder)
        self.template_manager = TemplateManager(self.declaration_manager)
        self.fork_template_builder = ForkTemplateBuilder(
            self.template_manager, 
            self.location_builder, 
            self.transition_builder, 
            self.declaration_manager
        )
        self.xml_generator = XMLGenerator()
        
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
        # ใช้ template ที่มีอยู่แล้ว
        if not self.template_manager.templates:
            print("No templates available for XML generation")
            return ""
        
        main_template = self.template_manager.templates[0] if self.template_manager.templates else None
        fork_templates = self.template_manager.fork_templates
        declarations = self.declaration_manager.get_declaration_text()
        
        # สร้าง XML ผ่าน XMLGenerator
        return self.xml_generator.generate_xml(main_template, fork_templates, declarations)

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

class ActivityDiagramToXML:
    """Main converter class - โครงสร้างแบบ modular"""
    
    def __init__(self):
        self.parser = ActivityDiagramParser()
        self.declaration_manager = DeclarationManager()
        self.location_builder = LocationBuilder(self.declaration_manager)
        self.transition_builder = TransitionBuilder(self.declaration_manager, self.location_builder)
        self.template_manager = TemplateManager(self.declaration_manager)
        self.fork_template_builder = ForkTemplateBuilder(
            self.template_manager, 
            self.location_builder, 
            self.transition_builder,
            self.declaration_manager
        )
        self.xml_generator = XMLGenerator()
        
        # เพิ่ม compatibility properties
        self.activity_root = None
        
    def set_activity_root(self, xmi_content):
        """ตั้งค่า activity root"""
        self.activity_root = xmi_content
        self.parser.set_activity_root(xmi_content)
    
    def _find_fork_for_join(self, join_node_id):
        """หา ForkNode ที่ corresponding กับ JoinNode นี้"""
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
        
        for template_name, hierarchy_info in self.transition_builder.template_hierarchy.items():
            if hierarchy_info.get('fork_id') == fork_id and hierarchy_info.get('level') == 0:
                fork_templates.append(template_name)
        
        if not fork_templates:
            for template in self.transition_builder.fork_templates:
                template_name = template["name"] if isinstance(template, dict) else template
                if (template_name in self.transition_builder.template_hierarchy and 
                    self.transition_builder.template_hierarchy[template_name].get('fork_id') == fork_id and
                    self.transition_builder.template_hierarchy[template_name].get('level') == 0):
                    fork_templates.append(template_name)
        
        if not fork_templates:
            fork_name = self.parser.get_node_name(fork_id)
            outgoing_edges = self.parser.get_outgoing_nodes(fork_id)
            
            fork_name_clean = fork_name.replace(" ", "").replace(",", "")
            for i, outgoing_edge in enumerate(outgoing_edges):
                template_name = f"Template_{fork_name_clean}_Branch{i+1}"
                self.declaration_manager.add_variable(f"bool Done_{template_name};")
                fork_templates.append(template_name)
        
        return fork_templates
    
    def _get_dynamic_guard_conditions(self, join_node_id):
        """หา guard conditions สำหรับ JoinNode โดยวิเคราะห์โครงสร้าง fork"""
        guard_conditions = []
        
        corresponding_fork = self._find_fork_for_join(join_node_id)
        
        if corresponding_fork:
            template_names = self._get_templates_for_fork(corresponding_fork)
            guard_conditions = [f"Done_{template_name}==true" for template_name in template_names]
        
        return guard_conditions
    
    def print_main_template_structure(self, template):
        """แสดงโครงสร้างของ main template"""
        print(f"\n📊 MAIN TEMPLATE STRUCTURE: {template['name']}")
        print("-" * 80)
        
        # แสดง locations
        locations = template["element"].findall(".//location")
        print(f"🎯 Locations ({len(locations)}):")
        for loc in locations:
            loc_id = loc.get("id")
            name_elem = loc.find("name")
            loc_name = name_elem.text if name_elem is not None else "Unnamed"
            x, y = loc.get("x", "0"), loc.get("y", "0")
            print(f"   • {loc_id}: {loc_name} at ({x}, {y})")
        
        # แสดง transitions
        transitions = template["element"].findall(".//transition")
        print(f"\n🔄 Transitions ({len(transitions)}):")
        for trans in transitions:
            source_ref = trans.find("source").get("ref")
            target_ref = trans.find("target").get("ref")
            
            # หา labels
            labels = []
            for label in trans.findall("label"):
                kind = label.get("kind")
                text = label.text or ""
                labels.append(f"{kind}:{text}")
            
            label_text = " | ".join(labels) if labels else "No labels"
            print(f"   • {source_ref} → {target_ref} [{label_text}]")
        
        print("-" * 80)
    
    def validate_main_template_transitions(self, main_template):
        """ตรวจสอบและแก้ไข transitions ใน main template"""
        if not main_template:
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
                print(f"   • {source_name} → {target_name}")
                
                # เพิ่ม transition ที่หายไป
                self.transition_builder.add_transition(main_template, source, target, source_name)
        else:
            print(f"✅ All expected transitions present ({len(expected_transitions)} total)")
        
        print(f"✅ Validation complete")
        print("-" * 80)
    
    def validate_fork_template_coverage(self, fork_templates):
        """ตรวจสอบว่า fork templates ครอบคลุมทุก fork node หรือไม่"""
        print(f"\n🔧 VALIDATING FORK TEMPLATE COVERAGE...")
        print("-" * 80)
        
        fork_nodes = [node for node in self.parser.get_coordination_nodes() 
                     if self.parser.get_node_type(node) in ("uml:ForkNode", "ForkNode")]
        
        print(f"🎯 Found {len(fork_nodes)} fork nodes")
        print(f"🎯 Created {len(fork_templates)} fork templates")
        
        for fork_node in fork_nodes:
            fork_name = self.parser.get_node_name(fork_node)
            print(f"   • Fork: {fork_name}")
        
        print("-" * 80)
        return len(fork_templates) >= len(fork_nodes)
    
    def convert_to_uppaal(self, file_path):
        """Convert XML to UPPAAL format - เหมือน UuppaalConverter"""
        try:
            # Parse the XML file
            if not self.parser.parse_file(file_path):
                return None
            
            # ใช้ process_nodes เหมือน UuppaalConverter
            main_template = self.process_nodes()
            
            if not main_template:
                print("❌ Failed to create main template")
                return None
            
            # Create fork templates
            fork_templates = self.fork_template_builder.create_fork_templates()
            
            # Generate final XML
            result_xml = self.xml_generator.generate_xml(
                main_template, 
                fork_templates, 
                self.declaration_manager.get_declaration_text()
            )
            
            return result_xml
            
        except Exception as e:
            print(f"❌ Error converting file: {e}")
            return None
    
    def process_nodes(self):
        """Processes nodes and creates main template - เหมือน UuppaalConverter ทุกอย่าง"""
        if not self.parser:
            raise ValueError("ActivityDiagramParser not initialized. Call set_activity_root() first.")
        
        # Print analysis results
        self.parser.print_analysis()
        
        # Create main template
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
        
        # ประมวลผล edges สำหรับ main template
        print(f"\nProcessing edges for main template...")
        
        # สร้าง transitions
        for edge_data in self.parser.get_all_edges():
            source = edge_data['source']
            target = edge_data['target']
            
            # ถ้าทั้ง source และ target อยู่ใน main template
            if source in main_flow_nodes and target in main_flow_nodes:
                edge_name = edge_data.get('name', '')
                guard = edge_data.get('guard', '')
                self.transition_builder.add_transition(main_template, source, target, edge_name, guard)
        
        print(f"\nMain template created with:")
        print(f"  - {len(main_flow_nodes)} nodes")
        
        return main_template

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 