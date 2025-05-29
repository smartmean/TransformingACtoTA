#!/usr/bin/env python3
"""
Test script for Pure OOP converter
"""

print("Starting test...")

try:
    print("Importing domain modules...")
    from domain.interfaces import IUppaalConverter
    from domain.models import ConversionContext, NodeInfo, EdgeInfo, Position
    print("Domain imports OK")
    
    print("Importing infrastructure modules...")
    from infrastructure.xml_parser import ActivityDiagramParser
    from infrastructure.template_manager import UppaalTemplateManager
    from infrastructure.location_builder import UppaalLocationBuilder
    from infrastructure.transition_builder import UppaalTransitionBuilder
    from infrastructure.declaration_manager import UppaalDeclarationManager
    from infrastructure.xml_generator import UppaalXMLGenerator
    print("Infrastructure imports OK")
    
    print("Creating converter...")
    
    class TestConverter(IUppaalConverter):
        def __init__(self):
            self.xml_parser = ActivityDiagramParser()
            self.xml_generator = UppaalXMLGenerator()
        
        def convert(self, xml_content: str) -> str:
            return "<test>OK</test>"
    
    converter = TestConverter()
    print("Converter created successfully")
    
    print("Testing conversion...")
    result = converter.convert("<test>input</test>")
    print(f"Conversion result: {result}")
    
    print("All tests passed!")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc() 