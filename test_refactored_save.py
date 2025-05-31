#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import os
import traceback
from datetime import datetime

def test_refactored_converter():
    """ทดสอบ Main_Beyone_Refactored.py และบันทึกผลลัพธ์ที่โฟลเดอร์ Result"""
    
    print("🚀 TESTING Main_Beyone_Refactored.py")
    print("=" * 60)
    
    # Import converter
    try:
        from Main_Beyone_Refactored import xmlConverter
        print("✅ Successfully imported xmlConverter from Main_Beyone_Refactored.py")
    except Exception as e:
        print(f"❌ Failed to import xmlConverter: {e}")
        traceback.print_exc()
        return False
    
    # Test file
    test_file = "Example_XML/Full_node_simple.xml"
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📁 Using test file: {test_file}")
    
    try:
        # Read and parse XML
        print("\n📖 Reading XML file...")
        with open(test_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        root = ET.fromstring(xml_content)
        print(f"✅ XML parsed successfully")
        
        # Find activity element
        print("🔍 Finding activity element...")
        activity = None
        for elem in root.findall(".//*"):
            xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
            if xmi_type == 'uml:Activity':
                activity = elem
                print(f"✅ Found Activity: {elem.get('name', 'unnamed')}")
                break
        
        if activity is None:
            activity = root
            print("⚠️ Using root element as activity")
        
        # Show basic statistics
        nodes = activity.findall('.//node')
        edges = activity.findall('.//edge')
        print(f"📊 Found {len(nodes)} nodes and {len(edges)} edges")
        
        # Create converter
        print("\n🔧 Creating xmlConverter...")
        converter = xmlConverter()
        print("✅ Converter created")
        
        # Set activity root
        print("🔗 Setting activity root...")
        converter.set_activity_root(activity)
        print("✅ Activity root set")
        
        # Process nodes
        print("\n⚙️ Processing nodes...")
        main_template = converter.process_nodes()
        
        if main_template:
            print("✅ Main template created successfully")
            locations = main_template["element"].findall(".//location")
            transitions = main_template["element"].findall(".//transition")
            print(f"📊 Main template: {len(locations)} locations, {len(transitions)} transitions")
        else:
            print("❌ Failed to create main template")
            return False
        
        # Generate XML
        print("\n🎯 Generating UPPAAL XML...")
        result_xml = converter.generate_xml()
        
        if not result_xml or result_xml.strip() == "":
            print("❌ Failed to generate XML - empty result")
            return False
        
        print(f"✅ XML generated successfully ({len(result_xml):,} characters)")
        
        # Analyze result
        print("\n📊 Analyzing result...")
        root_result = ET.fromstring(result_xml)
        all_locations = root_result.findall(".//location")
        all_transitions = root_result.findall(".//transition")
        all_templates = root_result.findall(".//template")
        
        fork_templates = []
        for template in all_templates:
            name_elem = template.find("name")
            if name_elem is not None and name_elem.text != "Template":
                fork_templates.append(name_elem.text)
        
        print(f"📈 RESULT STATISTICS:")
        print(f"   • Total locations: {len(all_locations)}")
        print(f"   • Total transitions: {len(all_transitions)}")
        print(f"   • Total templates: {len(all_templates)}")
        print(f"   • Fork templates: {len(fork_templates)}")
        print(f"   • XML length: {len(result_xml):,} characters")
        
        if fork_templates:
            print(f"   • Fork template names: {fork_templates}")
        
        # Save to Result folder
        print("\n💾 Saving results...")
        os.makedirs("Result", exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"Result/refactored_test_result_{timestamp}.xml"
        
        # Save XML result
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(result_xml)
        
        print(f"✅ Result saved to: {output_filename}")
        
        # Also save a comparison-ready file
        comparison_filename = "Result/refactored_test_result.xml"
        with open(comparison_filename, "w", encoding="utf-8") as f:
            f.write(result_xml)
        
        print(f"✅ Comparison file saved to: {comparison_filename}")
        
        # Create summary file
        summary_filename = f"Result/test_summary_{timestamp}.txt"
        with open(summary_filename, "w", encoding="utf-8") as f:
            f.write(f"REFACTORED CONVERTER TEST RESULTS\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=" * 50 + "\n\n")
            f.write(f"Input file: {test_file}\n")
            f.write(f"Output file: {output_filename}\n\n")
            f.write(f"STATISTICS:\n")
            f.write(f"  - Input nodes: {len(nodes)}\n")
            f.write(f"  - Input edges: {len(edges)}\n")
            f.write(f"  - Output locations: {len(all_locations)}\n")
            f.write(f"  - Output transitions: {len(all_transitions)}\n")
            f.write(f"  - Output templates: {len(all_templates)}\n")
            f.write(f"  - Fork templates: {len(fork_templates)}\n")
            f.write(f"  - XML length: {len(result_xml):,} characters\n\n")
            
            if fork_templates:
                f.write(f"FORK TEMPLATES:\n")
                for i, template_name in enumerate(fork_templates, 1):
                    f.write(f"  {i}. {template_name}\n")
        
        print(f"✅ Summary saved to: {summary_filename}")
        
        print(f"\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print(f"📂 Check Result folder for output files")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = test_refactored_converter()
    if success:
        print(f"\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed!")
    
    return success

if __name__ == "__main__":
    main() 