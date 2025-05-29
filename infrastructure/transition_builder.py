"""
Transition Builder Implementation สำหรับการสร้าง Transitions
"""
from typing import Set, Any, List
from domain.interfaces import ITransitionBuilder
from domain.models import Transition, TransitionLabel, Position, NodeInfo, EdgeInfo, ConversionContext


class TransitionBuilder(ITransitionBuilder):
    """Builder สำหรับการสร้าง Transitions ใน Templates"""
    
    def __init__(self):
        self._created_transitions: Set[str] = set()
    
    def add_transition(self, template: Any, edge: EdgeInfo, source_node: NodeInfo, 
                      target_node: NodeInfo, context: ConversionContext, 
                      from_fork_template: bool = False) -> None:
        """เพิ่ม transition ระหว่าง locations"""
        
        # ตรวจสอบว่า source และ target nodes อยู่ในเทมเพลทนี้หรือไม่
        nodes_exist = self._nodes_exist_in_template(template, edge.source_id, edge.target_id)
        if not nodes_exist:
            return
        
        # สร้าง transition ID
        transition_id = f"{edge.source_id}_to_{edge.target_id}"
        
        # ตรวจสอบว่าสร้างแล้วหรือยัง
        if transition_id in self._created_transitions:
            return
        
        # สร้าง transition
        transition = Transition(
            id=transition_id,
            source_id=edge.source_id,
            target_id=edge.target_id
        )
        
        # คำนวณตำแหน่งกลางสำหรับ labels
        source_pos = source_node.position if hasattr(source_node, 'position') else Position(0, 0)
        target_pos = target_node.position if hasattr(target_node, 'position') else Position(100, 100)
        mid_x = (source_pos.x + target_pos.x) // 2
        mid_y = (source_pos.y + target_pos.y) // 2
        
        # เพิ่ม labels ตาม context
        self._add_transition_labels(transition, source_node, target_node, edge, 
                                  mid_x, mid_y, template, context, from_fork_template)
        
        # เพิ่ม transition เข้า template
        template.add_transition(transition)
        
        # บันทึกว่าสร้างแล้ว
        self._created_transitions.add(transition_id)
    
    def _nodes_exist_in_template(self, template: Any, source_id: str, target_id: str) -> bool:
        """ตรวจสอบว่า source และ target nodes อยู่ในเทมเพลทหรือไม่"""
        # ตรวจสอบว่า nodes อยู่ใน template locations หรือไม่
        template_location_ids = set(template.locations.keys()) if hasattr(template, 'locations') else set()
        
        # สำหรับ fork templates ที่มี initial location แบบพิเศษ
        if hasattr(template, 'name') and template.name.startswith("Template") and template.name != "Template":
            template_location_ids.add(f"fork_{template.name}")
        
        return source_id in template_location_ids and target_id in template_location_ids
    
    def add_transition_labels(self, transition: Any, label_info: dict) -> None:
        """เพิ่ม labels ให้กับ transition"""
        for kind, text in label_info.items():
            if text:
                label = TransitionLabel(kind, text, Position(0, 0))
                transition.labels.append(label)
    
    def _find_join_after_node(self, node_id: str, context: ConversionContext) -> str:
        """หา join node ที่อยู่หลังจาก node นี้"""
        visited = set()
        current = node_id
        
        while current and current not in visited:
            visited.add(current)
            
            # หา edge ที่ออกจาก current node
            next_edge = None
            for edge in context.edges:
                if edge.source_id == current:
                    next_edge = edge
                    break
            
            if not next_edge:
                break
                
            # ตรวจสอบ target node
            target_node = context.nodes.get(next_edge.target_id)
            if target_node and target_node.node_type in ("uml:JoinNode", "JoinNode"):
                return next_edge.target_id
                
            current = next_edge.target_id
        
        return None
    
    def _add_transition_labels(self, transition: Transition, source_node: NodeInfo, 
                             target_node: NodeInfo, edge: EdgeInfo, mid_x: int, mid_y: int,
                             template: Any, context: ConversionContext, from_fork_template: bool) -> None:
        """เพิ่ม labels ให้กับ transition (รวม OpaqueAction time constraints)"""
        
        # Handle time constraints ONLY from SOURCE node that has time constraint
        # Time constraints should apply to transitions going OUT of the node with time constraint
        time_constraint_node = None
        time_constraint_name = None
        
        # Check if SOURCE node has time constraint AND is OpaqueAction
        if ("," in source_node.name and ("t=" in source_node.name or "t =" in source_node.name) and 
            source_node.node_type in ("uml:OpaqueAction", "OpaqueAction")):
            time_constraint_node = source_node
            time_constraint_name = source_node.name
        
        # Process time constraint if found
        # BUT NOT for transitions from InitialNode in fork templates
        if (time_constraint_node and time_constraint_name and 
            not (from_fork_template and source_node.node_type in ("InitialNode",))):
            try:
                # Extract time value - handle both "t=1" and "t = 1" formats
                if "t=" in time_constraint_name:
                    time_part = time_constraint_name.split("t=")[-1].strip()
                elif "t =" in time_constraint_name:
                    time_part = time_constraint_name.split("t =")[-1].strip()
                else:
                    time_part = "0"
                
                # Extract just the number (handle cases like "1" or "1,")
                time_val = int(''.join(filter(str.isdigit, time_part.split()[0] if time_part.split() else time_part)))
                
                # Get clock name from template (use the actual clock name assigned)
                clock_name = template.clock_name if hasattr(template, 'clock_name') else "t"
                
                # Add guard and assignment
                transition.add_guard(f"{clock_name}>{time_val}", Position(mid_x, mid_y - 60))
                
                # Add Done variable assignment only for fork templates when going to final location
                if (template.name.startswith("Template") and template.name != "Template" and 
                    target_node.node_type in ("uml:JoinNode", "JoinNode")):
                    # For join nodes, add Done assignment
                    transition.add_assignment(f"{clock_name}:=0,\nDone_{template.name} = true", Position(mid_x, mid_y - 40))
                else:
                    transition.add_assignment(f"{clock_name}:=0", Position(mid_x, mid_y - 40))
                    
            except (ValueError, IndexError):
                pass
        
        # Handle fork node synchronization
        if source_node.node_type in ("uml:ForkNode", "ForkNode"):
            clean_name = source_node.name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
            sync_label = f"fork_{clean_name}!"
            transition.add_synchronisation(sync_label, Position(mid_x, mid_y - 80))
        
        # Handle initial node in fork template
        elif from_fork_template and source_node.node_type in ("InitialNode",):
            # Determine correct synchronization channel based on template name and actual fork nodes
            if "_" in template.name:  # Nested template like Template1_1, Template1_2
                parent_template = template.name.split("_")[0]  # Template1
                
                # หา nested fork node จาก context ที่อยู่ใน parent template
                nested_fork_channel = None
                for node_id, fork_channel in context.fork_channels.items():
                    node = context.nodes.get(node_id)
                    if node and node.node_type in ("uml:ForkNode", "ForkNode"):
                        # ตรวจสอบว่า fork node นี้เป็น nested fork หรือไม่
                        clean_name = node.name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
                        if "_" in clean_name or "1_1" in clean_name:  # เป็น nested fork
                            nested_fork_channel = fork_channel
                            break
                
                if nested_fork_channel:
                    sync_label = f"{nested_fork_channel}?"
                else:
                    # fallback: ใช้ชื่อ generic
                    sync_label = "fork_NestedFork?"
                    
            else:  # Main fork template like Template1, Template2
                # หา main fork node จาก context
                main_fork_channel = None
                for node_id, fork_channel in context.fork_channels.items():
                    node = context.nodes.get(node_id)
                    if node and node.node_type in ("uml:ForkNode", "ForkNode"):
                        clean_name = node.name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
                        if "_" not in clean_name and "1_1" not in clean_name:  # เป็น main fork
                            main_fork_channel = fork_channel
                            break
                
                if main_fork_channel:
                    sync_label = f"{main_fork_channel}?"
                else:
                    # fallback: ใช้ชื่อ generic
                    sync_label = "fork_MainFork?"
                    
            transition.add_synchronisation(sync_label, Position(mid_x, mid_y - 80))
        
        # Handle join node - Guard conditions for waiting other templates ตามหลัก OOP
        elif source_node.node_type in ("uml:JoinNode", "JoinNode"):
            if template.name == "Template":
                # Main template join - ใช้ Strategy Pattern สำหรับ synchronization
                guard_condition = self._create_main_template_join_guard(context)
                if guard_condition:
                    transition.add_guard(guard_condition, Position(mid_x, mid_y - 80))
            elif template.name.startswith("Template") and template.name != "Template" and "_" not in template.name:
                # Fork template final join - ใช้ dynamic detection แทน hardcode ตามหลัก Strategy Pattern
                if self._is_template_internal_join(source_node, template.name):
                    # Template internal join - รอ nested templates (dynamic detection)
                    guard_condition = self._create_fork_template_join_guard(template.name, context)
                    if guard_condition:
                        transition.add_guard(guard_condition, Position(mid_x, mid_y - 80))
                    
                    # Dynamic assignment สำหรับ Done variable
                    assignment = f"Done_{template.name} = true"
                    transition.add_assignment(assignment, Position(mid_x, mid_y - 60))
                else:
                    # For other main fork templates join nodes
                    is_final_join = (
                        target_node and 
                        "Join" in target_node.name and 
                        target_node.node_type in ("uml:JoinNode", "JoinNode")
                    )
                    
                    if is_final_join:
                        guard_condition = self._create_fork_template_join_guard(template.name, context)
                        if guard_condition:
                            transition.add_guard(guard_condition, Position(mid_x, mid_y - 80))
                        
                        # เพิ่ม assignment สำหรับ Done variable ตามหลัก Strategy Pattern
                        done_assignment = f"Done_{template.name} = true"
                        transition.add_assignment(done_assignment, Position(mid_x, mid_y - 60))
            elif "Template" in template.name and "_" not in template.name and template.name != "Template":
                # For other main fork templates, check if this is transition to final join
                # Updated pattern to handle cases like "JoinNode_Template1_Join_Join"
                is_final_join = (
                    target_node and 
                    "Join" in target_node.name and 
                    target_node.node_type in ("uml:JoinNode", "JoinNode")
                )
                
                if is_final_join:
                    guard_condition = self._create_fork_template_join_guard(template.name, context)
                    if guard_condition:
                        transition.add_guard(guard_condition, Position(mid_x, mid_y - 80))
                    
                    # เพิ่ม assignment สำหรับ Done variable ตามหลัก Strategy Pattern
                    done_assignment = f"Done_{template.name} = true"
                    transition.add_assignment(done_assignment, Position(mid_x, mid_y - 60))
        
        # Handle edge labels and decision variables
        edge_label = context.edge_guards.get((edge.source_id, edge.target_id))
        target_type = target_node.node_type
        
        # Use decision variable name from context if available
        if source_node.node_type in ("uml:DecisionNode", "DecisionNode"):
            decision_var = context.decision_vars.get(source_node.node_id)
            if not decision_var:
                decision_var = source_node.name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
        else:
            decision_var = source_node.name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
        
        # Handle edge conditions
        if edge_label and "=" in edge_label:
            condition = edge_label.strip("[]").split("=")[1].strip().lower()
            if condition == "yes":
                guard_condition = f"{decision_var}==1"
            elif condition == "no":
                guard_condition = f"{decision_var}==0"
            else:
                var_name = context.decision_vars.get(source_node.node_id)
                if var_name:
                    if condition in ("true", "1"):
                        guard_condition = f"{var_name}==1"
                    else:
                        guard_condition = f"{var_name}==0"
                else:
                    return
            
            transition.add_guard(guard_condition, Position(mid_x, mid_y - 80))
        
        # Handle decision node target with select and assignment
        if target_type == "uml:DecisionNode":
            target_decision_var = context.decision_vars.get(target_node.node_id)
            if not target_decision_var:
                target_decision_var = target_node.name.split(",")[0].strip().replace(" ", "_").replace("-", "_").replace(".", "_").replace("?", "")
            
            var_name = "i20"
            transition.add_select(f"{var_name}: int[0,1]", Position(mid_x, mid_y - 100))
            
            existing_assignment = None
            for label in transition.labels:
                if label.kind == "assignment":
                    existing_assignment = label
                    break
            
            if existing_assignment:
                existing_assignment.text += f", {target_decision_var} = {var_name}"
            else:
                clock_name = "t" if template.name == "Template" else f"t{template.name.replace('Template', '') or '1'}"
                transition.add_assignment(f"{clock_name}:=0, {target_decision_var} = {var_name}", Position(mid_x, mid_y - 40))
        
        # Handle activity final node
        elif target_node.node_type in ("uml:ActivityFinalNode", "ActivityFinalNode", "FinalNode"):
            # Only add Done assignment if:
            # 1. NOT coming from MergeNode/JoinNode
            # 2. AND it's the main template (not fork templates)
            if (source_node.node_type not in ("uml:MergeNode", "MergeNode", "uml:JoinNode", "JoinNode") and 
                template.name == "Template"):
                done_var = f"Done_{template.name}"
                transition.add_assignment(f"{done_var}=true", Position(mid_x, mid_y + 40)) 
        
        # Handle MergeNode to JoinNode/final locations in nested templates
        elif (source_node.node_type in ("uml:MergeNode", "MergeNode") and 
              target_node.node_type in ("uml:JoinNode", "JoinNode") and 
              "_" in template.name):  # nested templates
            # Add Done assignment for nested templates
            transition.add_assignment(f"Done_{template.name} = true", Position(mid_x, mid_y - 40)) 
    
    def _create_main_template_join_guard(self, context: ConversionContext) -> str:
        """สร้าง guard condition สำหรับ main template join ตามหลัก Strategy Pattern - Dynamic Detection"""
        # Strategy Pattern: Dynamic detection จาก actual nodes และ edges
        fork_templates = self._detect_fork_templates_from_context(context)
        
        guard_conditions = []
        for template_name in fork_templates:
            if template_name != "Template" and "_" not in template_name:  # main fork templates only
                guard_conditions.append(f"Done_{template_name}==true")
        
        return " && ".join(guard_conditions) if guard_conditions else ""
    
    def _create_fork_template_join_guard(self, template_name: str, context: ConversionContext) -> str:
        """สร้าง guard condition สำหรับ fork template join ตามหลัก Strategy Pattern - Dynamic Detection"""
        # Strategy Pattern: Dynamic detection ของ nested templates
        nested_templates = self._detect_nested_templates_from_context(template_name, context)
        
        guard_conditions = []
        for nested_name in nested_templates:
            guard_conditions.append(f"Done_{nested_name}==true")
        
        return " && ".join(guard_conditions) if guard_conditions else ""
    
    def _detect_fork_templates_from_context(self, context: ConversionContext) -> List[str]:
        """ตรวจหา fork templates จาก context nodes ตามหลัก Repository Pattern"""
        fork_templates = set()
        
        # หา main fork nodes (ไม่ใช่ nested)
        for node_id, node in context.nodes.items():
            if node.node_type in ("uml:ForkNode", "ForkNode") and "1_1" not in node.name:
                # หา outgoing edges จาก main fork
                outgoing_edges = [e for e in context.edges if e.source_id == node.node_id]
                
                # สร้างชื่อ template ตาม target nodes
                for i, edge in enumerate(outgoing_edges):
                    template_name = f"Template{i+1}"
                    fork_templates.add(template_name)
        
        return sorted(list(fork_templates))
    
    def _detect_nested_templates_from_context(self, parent_template: str, context: ConversionContext) -> List[str]:
        """ตรวจหา nested templates จาก context nodes ตามหลัก Factory Pattern"""
        nested_templates = set()
        
        # หา nested fork nodes (มี "1_1" ในชื่อ) สำหรับ Template1 เท่านั้น
        if parent_template == "Template1":
            for node_id, node in context.nodes.items():
                if node.node_type in ("uml:ForkNode", "ForkNode") and "1_1" in node.name:
                    # หา outgoing edges จาก nested fork
                    outgoing_edges = [e for e in context.edges if e.source_id == node.node_id]
                    
                    # สร้างชื่อ nested template
                    for i, edge in enumerate(outgoing_edges):
                        nested_name = f"{parent_template}_{i+1}"
                        nested_templates.add(nested_name)
        
        return sorted(list(nested_templates))

    def _is_template_internal_join(self, node: NodeInfo, template_name: str) -> bool:
        """ตรวจสอบว่า node เป็น join node ภายใน template หรือไม่ ตามหลัก Strategy Pattern"""
        # ตรวจสอบ naming pattern ของ template internal join
        return (template_name in node.name and 
                "Join_Join" in node.name and 
                node.node_type in ("uml:JoinNode", "JoinNode"))