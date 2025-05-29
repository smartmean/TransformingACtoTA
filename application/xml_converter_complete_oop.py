"""
Complete OOP UPPAAL Converter Application
ใช้ infrastructure components เต็มรูปแบบตาม Clean Architecture principles
"""
from typing import Dict, Any, List
from domain.interfaces import IConverter
from domain.models import ConversionContext, NodeInfo, EdgeInfo, Template

# Import infrastructure components - Complete OOP Architecture
from infrastructure.xml_parser import ActivityDiagramParser
from infrastructure.location_builder import LocationBuilder
from infrastructure.transition_builder import TransitionBuilder
from infrastructure.template_manager import TemplateManager
from infrastructure.declaration_manager import DeclarationManager
from infrastructure.xml_generator import XMLGenerator
from infrastructure.node_processors import NodeProcessorFactory


class CompleteOOPConverter(IConverter):
    """
    Complete OOP Converter ที่ใช้ infrastructure components เต็มรูปแบบ
    ปฏิบัติตาม Clean Architecture และ SOLID principles
    """
    
    def __init__(self):
        """Initialize all infrastructure components with proper dependency injection"""
        # Working context - สร้างก่อนเพื่อ dependency injection
        self.context = ConversionContext()
        
        # Infrastructure Layer Components - ตาม Dependency Injection pattern
        self.declaration_manager = DeclarationManager()
        self.template_manager = TemplateManager(self.context)
        self.xml_parser = ActivityDiagramParser()
        self.location_builder = LocationBuilder(self.context, self.declaration_manager)
        self.transition_builder = TransitionBuilder()
        self.xml_generator = XMLGenerator()
        self.node_processor_factory = NodeProcessorFactory(self.context)
    
    def convert(self, activity_xml: str) -> str:
        """แปลง Activity Diagram XML เป็น UPPAAL XML ด้วย Complete OOP Architecture"""
        try:
            # 1. Parse XML ด้วย Infrastructure Parser
            print("🔍 Parsing XML with ActivityDiagramParser...")
            nodes, edges = self.xml_parser.parse_activity_diagram(activity_xml)
            
            # Update context
            self.context.nodes = {node.node_id: node for node in nodes}
            self.context.edges = edges
            
            print(f"📊 Parsed {len(nodes)} nodes and {len(edges)} edges")
            
            # 2. Process nodes ด้วย Node Processor Factory (Strategy Pattern)
            print("⚙️ Processing nodes with NodeProcessorFactory...")
            processed_nodes = []
            for node in nodes:
                processor = self.node_processor_factory.get_processor(node.node_type)
                if processor:
                    result = processor.process_node(
                        node_id=node.node_id,
                        node_name=node.name,
                        node_type=node.node_type,
                        context={'x_offset': len(processed_nodes) * 300}
                    )
                    processed_nodes.append({
                        'node': node,
                        'result': result
                    })
            
            # 3. Create main template ด้วย Template Manager
            print("🏗️ Creating main template with TemplateManager...")
            main_template = self.template_manager.create_template("Template")
            
            # 4. Build locations ด้วย Location Builder
            print("📍 Building locations with LocationBuilder...")
            for processed in processed_nodes:
                node = processed['node']
                result = processed['result']
                
                self.location_builder.add_location(
                    template=main_template,
                    location_id=node.node_id,
                    node_name=node.name,
                    node_type=node.node_type
                )
                
                # เพิ่ม declarations จาก processed result
                if 'declarations' in result:
                    for decl in result['declarations']:
                        self.declaration_manager.add_declaration(decl)
            
            # 5. Create fork templates ตาม OOP pattern
            print("🔀 Creating fork templates...")
            fork_templates = self._create_fork_templates_oop()
            
            # 6. Build transitions ด้วย Transition Builder
            print("🔗 Building transitions with TransitionBuilder...")
            all_templates = [main_template] + fork_templates
            
            for template in all_templates:
                self._build_transitions_for_template(template)
            
            # 7. Generate final XML ด้วย XML Generator
            print("📄 Generating XML with XMLGenerator...")
            declarations = self.declaration_manager.get_declarations()
            final_xml = self.xml_generator.generate_xml(all_templates, declarations)
            
            print("✅ Complete OOP conversion completed successfully!")
            return final_xml
            
        except Exception as e:
            raise ValueError(f"Complete OOP Conversion failed: {str(e)}")
    
    def _create_fork_templates_oop(self) -> List[Template]:
        """สร้าง fork templates ด้วย OOP approach ที่ถูกต้อง"""
        fork_templates = []
        template_counter = 1
        
        # หา fork nodes และสร้าง templates
        for node_id, node in self.context.nodes.items():
            if node.node_type in ("uml:ForkNode", "ForkNode"):
                # สร้าง templates สำหรับ parallel branches
                outgoing_edges = [e for e in self.context.edges if e.source_id == node_id]
                
                for i, edge in enumerate(outgoing_edges):
                    template_name = f"Template{template_counter}"
                    template_counter += 1
                    
                    fork_template = self.template_manager.create_template(template_name)
                    
                    # สร้าง initial location สำหรับ fork template
                    initial_id = f"fork_{template_name}"
                    self.location_builder.add_location(
                        template=fork_template,
                        location_id=initial_id,
                        node_name=f"InitialNode_{template_name}",
                        node_type="InitialNode"
                    )
                    
                    # เพิ่ม nodes ตาม path
                    self._add_nodes_to_fork_template(fork_template, edge.target_id)
                    
                    fork_templates.append(fork_template)
        
        return fork_templates
    
    def _add_nodes_to_fork_template(self, template: Template, start_node_id: str):
        """เพิ่ม nodes เข้า fork template ตาม path"""
        visited = set()
        current = start_node_id
        
        while current and current not in visited:
            visited.add(current)
            node = self.context.nodes.get(current)
            if not node:
                break
            
            # เพิ่ม location
            self.location_builder.add_location(
                template=template,
                location_id=node.node_id,
                node_name=node.name,
                node_type=node.node_type
            )
            
            # หา edge ถัดไป
            next_edge = None
            for edge in self.context.edges:
                if edge.source_id == current:
                    next_edge = edge
                    break
            
            if not next_edge:
                break
            
            current = next_edge.target_id
            
            # หยุดที่ join node
            next_node = self.context.nodes.get(current)
            if next_node and next_node.node_type in ("uml:JoinNode", "JoinNode"):
                self.location_builder.add_location(
                    template=template,
                    location_id=next_node.node_id,
                    node_name=next_node.name,
                    node_type=next_node.node_type
                )
                break
    
    def _build_transitions_for_template(self, template: Template):
        """สร้าง transitions สำหรับ template แบบ OOP ที่ถูกต้อง"""
        template_node_ids = set(template.locations.keys())
        
        # เพิ่ม initial location สำหรับ fork templates
        if template.name.startswith("Template") and template.name != "Template":
            template_node_ids.add(f"fork_{template.name}")
        
        # สร้าง transitions ตาม edges ที่เกี่ยวข้องกับ template นี้
        for edge in self.context.edges:
            source_node = self.context.nodes.get(edge.source_id)
            target_node = self.context.nodes.get(edge.target_id)
            
            # Check if this edge belongs to this template
            if self._edge_belongs_to_template(edge, template, template_node_ids):
                if source_node and target_node:
                    self.transition_builder.add_transition(
                        template=template,
                        edge=edge,
                        source_node=source_node,
                        target_node=target_node,
                        context=self.context,
                        from_fork_template=(template.name != "Template")
                    )
    
    def _edge_belongs_to_template(self, edge: EdgeInfo, template: Template, template_node_ids: set) -> bool:
        """ตรวจสอบว่า edge นี้เป็นของ template นี้หรือไม่"""
        if template.name == "Template":
            # Main template: รวมทุก edge ยกเว้นที่อยู่ใน fork templates
            return edge.source_id in template_node_ids and edge.target_id in template_node_ids
        else:
            # Fork template: เฉพาะ edge ที่อยู่ใน path ของ template นี้
            # หรือ edge ที่เริ่มจาก initial node ของ template
            return (edge.source_id in template_node_ids and edge.target_id in template_node_ids) or \
                   edge.source_id == f"fork_{template.name}"
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """ดึงสถิติการแปลงแบบ Complete OOP"""
        return {
            "architecture": "Complete OOP with Full Infrastructure Components",
            "design_patterns": [
                "Dependency Injection",
                "Strategy Pattern (NodeProcessorFactory)",
                "Builder Pattern (LocationBuilder, TransitionBuilder)",
                "Factory Pattern (NodeProcessorFactory)",
                "Repository Pattern (TemplateManager, DeclarationManager)"
            ],
            "infrastructure_components": [
                "ActivityDiagramParser",
                "NodeProcessorFactory",
                "LocationBuilder", 
                "TransitionBuilder",
                "TemplateManager", 
                "DeclarationManager",
                "XMLGenerator"
            ],
            "templates": len(self.context.templates) if hasattr(self.context, 'templates') else 0,
            "declarations": len(self.declaration_manager.get_declarations()),
            "nodes_processed": len(self.context.nodes),
            "edges_processed": len(self.context.edges),
            "clean_architecture": True,
            "solid_principles": True
        } 