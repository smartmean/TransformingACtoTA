#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import os
import traceback
from datetime import datetime

def analyze_xml_result(xml_content, name):
    """วิเคราะห์ผลลัพธ์ XML"""
    if not xml_content or xml_content.strip() == "":
        return {'name': name, 'error': 'Empty XML', 'locations': 0, 'transitions': 0, 'templates': 0, 'xml_length': 0}
    
    try:
        root = ET.fromstring(xml_content)
        
        # นับ elements
        locations = root.findall(".//location")
        transitions = root.findall(".//transition") 
        templates = root.findall(".//template")
        
        # แยก main template กับ fork templates
        main_template_locations = 0
        main_template_transitions = 0
        fork_templates = []
        
        for template in templates:
            name_elem = template.find("name")
            template_name = name_elem.text if name_elem is not None else "Unknown"
            
            template_locations = template.findall(".//location")
            template_transitions = template.findall(".//transition")
            
            if template_name == "Template":
                main_template_locations = len(template_locations)
                main_template_transitions = len(template_transitions)
            else:
                fork_templates.append({
                    'name': template_name,
                    'locations': len(template_locations),
                    'transitions': len(template_transitions)
                })
        
        return {
            'name': name,
            'error': None,
            'total_locations': len(locations),
            'total_transitions': len(transitions),
            'total_templates': len(templates),
            'main_template_locations': main_template_locations,
            'main_template_transitions': main_template_transitions,
            'fork_templates_count': len(fork_templates),
            'fork_templates': fork_templates,
            'xml_length': len(xml_content)
        }
    except Exception as e:
        return {'name': name, 'error': str(e), 'locations': 0, 'transitions': 0, 'templates': 0, 'xml_length': len(xml_content)}

def test_final_converter(test_file):
    """ทดสอบ Main_Beyone_final.py"""
    print("🟢 Testing Main_Beyone_final.py (UppaalConverter)")
    print("-" * 60)
    
    try:
        from Main_Beyone_final import UppaalConverter
        
        with open(test_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        root = ET.fromstring(xml_content)
        
        # Find activity element
        activity = None
        for elem in root.findall(".//*"):
            xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
            if xmi_type == 'uml:Activity':
                activity = elem
                break
        if activity is None:
            activity = root
        
        # Create and run converter
        converter = UppaalConverter()
        converter.set_activity_root(activity)
        main_template = converter.process_nodes()
        
        # Validate and fix transitions
        converter.validate_main_template_transitions()
        
        # Generate XML
        result_xml = converter.generate_xml()
        
        # Save result
        os.makedirs("Result", exist_ok=True)
        with open("Result/final_test_result.xml", "w", encoding="utf-8") as f:
            f.write(result_xml)
        
        print("✅ UppaalConverter completed successfully")
        return result_xml, None
        
    except Exception as e:
        error_msg = f"UppaalConverter failed: {e}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return "", error_msg

def test_refactored_converter(test_file):
    """ทดสอบ Main_Beyone_Refactored.py"""
    print("\n🔵 Testing Main_Beyone_Refactored.py (xmlConverter)")
    print("-" * 60)
    
    try:
        from Main_Beyone_Refactored import xmlConverter
        
        with open(test_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        root = ET.fromstring(xml_content)
        
        # Find activity element
        activity = None
        for elem in root.findall(".//*"):
            xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
            if xmi_type == 'uml:Activity':
                activity = elem
                break
        if activity is None:
            activity = root
        
        # Create and run converter
        converter = xmlConverter()
        converter.set_activity_root(activity)
        main_template = converter.process_nodes()
        
        # Generate XML
        result_xml = converter.generate_xml()
        
        # Save result
        os.makedirs("Result", exist_ok=True)
        with open("Result/refactored_test_result.xml", "w", encoding="utf-8") as f:
            f.write(result_xml)
        
        print("✅ xmlConverter completed successfully")
        return result_xml, None
        
    except Exception as e:
        error_msg = f"xmlConverter failed: {e}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return "", error_msg

def compare_results(result1, result2, analysis1, analysis2):
    """เปรียบเทียบผลลัพธ์"""
    print("\n" + "="*80)
    print("📊 COMPARISON RESULTS")
    print("="*80)
    
    print(f"\n[1] UppaalConverter (Main_Beyone_final.py):")
    if analysis1['error']:
        print(f"   ❌ Error: {analysis1['error']}")
    else:
        print(f"   ✅ Main template locations: {analysis1['main_template_locations']}")
        print(f"   ✅ Main template transitions: {analysis1['main_template_transitions']}")
        print(f"   ✅ Total templates: {analysis1['total_templates']}")
        print(f"   ✅ Fork templates: {analysis1['fork_templates_count']}")
        print(f"   ✅ Total locations: {analysis1['total_locations']}")
        print(f"   ✅ Total transitions: {analysis1['total_transitions']}")
        print(f"   ✅ XML length: {analysis1['xml_length']:,} characters")
        
        if analysis1['fork_templates']:
            print(f"   📋 Fork template details:")
            for ft in analysis1['fork_templates']:
                print(f"      • {ft['name']}: {ft['locations']} locations, {ft['transitions']} transitions")
    
    print(f"\n[2] xmlConverter (Main_Beyone_Refactored.py):")
    if analysis2['error']:
        print(f"   ❌ Error: {analysis2['error']}")
    else:
        print(f"   ✅ Main template locations: {analysis2['main_template_locations']}")
        print(f"   ✅ Main template transitions: {analysis2['main_template_transitions']}")
        print(f"   ✅ Total templates: {analysis2['total_templates']}")
        print(f"   ✅ Fork templates: {analysis2['fork_templates_count']}")
        print(f"   ✅ Total locations: {analysis2['total_locations']}")
        print(f"   ✅ Total transitions: {analysis2['total_transitions']}")
        print(f"   ✅ XML length: {analysis2['xml_length']:,} characters")
        
        if analysis2['fork_templates']:
            print(f"   📋 Fork template details:")
            for ft in analysis2['fork_templates']:
                print(f"      • {ft['name']}: {ft['locations']} locations, {ft['transitions']} transitions")
    
    # Calculate differences
    if not analysis1['error'] and not analysis2['error']:
        print(f"\n📈 DIFFERENCES:")
        print("-" * 40)
        
        diff_main_locations = analysis2['main_template_locations'] - analysis1['main_template_locations']
        diff_main_transitions = analysis2['main_template_transitions'] - analysis1['main_template_transitions']
        diff_total_templates = analysis2['total_templates'] - analysis1['total_templates']
        diff_fork_templates = analysis2['fork_templates_count'] - analysis1['fork_templates_count']
        diff_total_locations = analysis2['total_locations'] - analysis1['total_locations']
        diff_total_transitions = analysis2['total_transitions'] - analysis1['total_transitions']
        diff_xml_length = analysis2['xml_length'] - analysis1['xml_length']
        
        print(f"   Main template locations: {diff_main_locations:+d} ({analysis1['main_template_locations']} → {analysis2['main_template_locations']})")
        print(f"   Main template transitions: {diff_main_transitions:+d} ({analysis1['main_template_transitions']} → {analysis2['main_template_transitions']})")
        print(f"   Total templates: {diff_total_templates:+d} ({analysis1['total_templates']} → {analysis2['total_templates']})")
        print(f"   Fork templates: {diff_fork_templates:+d} ({analysis1['fork_templates_count']} → {analysis2['fork_templates_count']})")
        print(f"   Total locations: {diff_total_locations:+d} ({analysis1['total_locations']} → {analysis2['total_locations']})")
        print(f"   Total transitions: {diff_total_transitions:+d} ({analysis1['total_transitions']} → {analysis2['total_transitions']})")
        print(f"   XML length: {diff_xml_length:+,d} chars ({analysis1['xml_length']:,} → {analysis2['xml_length']:,})")
        
        if analysis1['xml_length'] > 0:
            percent_diff = (diff_xml_length / analysis1['xml_length']) * 100
            print(f"   XML Change: {percent_diff:+.1f}%")
        
        # Check if results are identical
        if (diff_main_locations == 0 and diff_main_transitions == 0 and 
            diff_total_templates == 0 and diff_fork_templates == 0 and
            diff_total_locations == 0 and diff_total_transitions == 0 and
            diff_xml_length == 0):
            print(f"\n🎉 *** RESULTS ARE IDENTICAL! ***")
            print("✅ Refactoring SUCCESS - 100% match achieved!")
        else:
            print(f"\n⚠️  Results differ - refactoring needs adjustments")
            
            # Identify major differences
            major_diffs = []
            if abs(diff_main_locations) > 0:
                major_diffs.append(f"Main template locations ({diff_main_locations:+d})")
            if abs(diff_main_transitions) > 0:
                major_diffs.append(f"Main template transitions ({diff_main_transitions:+d})")
            if abs(diff_fork_templates) > 0:
                major_diffs.append(f"Fork templates ({diff_fork_templates:+d})")
            
            if major_diffs:
                print(f"🔧 Major differences: {', '.join(major_diffs)}")
    
    print("="*80)

def main():
    """Main comparison function"""
    test_file = "Example_XML/Full_node_simple.xml"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"🚀 TESTING BOTH CONVERTERS WITH: {test_file}")
    print("="*80)
    
    # Test both converters
    result1, error1 = test_final_converter(test_file)
    result2, error2 = test_refactored_converter(test_file)
    
    # Analyze results
    analysis1 = analyze_xml_result(result1, "UppaalConverter")
    analysis2 = analyze_xml_result(result2, "xmlConverter")
    
    # Compare results
    compare_results(result1, result2, analysis1, analysis2)
    
    # Create detailed comparison report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"Result/comparison_report_{timestamp}.txt"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write("CONVERTER COMPARISON REPORT\n")
        f.write("="*50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Test file: {test_file}\n\n")
        
        f.write("RESULTS SUMMARY:\n")
        f.write("-"*30 + "\n")
        f.write(f"UppaalConverter:\n")
        if analysis1['error']:
            f.write(f"  Error: {analysis1['error']}\n")
        else:
            f.write(f"  Main template: {analysis1['main_template_locations']} locations, {analysis1['main_template_transitions']} transitions\n")
            f.write(f"  Fork templates: {analysis1['fork_templates_count']}\n")
            f.write(f"  Total: {analysis1['total_locations']} locations, {analysis1['total_transitions']} transitions\n")
            f.write(f"  XML length: {analysis1['xml_length']:,} characters\n")
        
        f.write(f"\nxmlConverter:\n")
        if analysis2['error']:
            f.write(f"  Error: {analysis2['error']}\n")
        else:
            f.write(f"  Main template: {analysis2['main_template_locations']} locations, {analysis2['main_template_transitions']} transitions\n")
            f.write(f"  Fork templates: {analysis2['fork_templates_count']}\n")
            f.write(f"  Total: {analysis2['total_locations']} locations, {analysis2['total_transitions']} transitions\n")
            f.write(f"  XML length: {analysis2['xml_length']:,} characters\n")
    
    print(f"\n📋 Detailed report saved to: {report_filename}")
    
    return not analysis1['error'] and not analysis2['error']

if __name__ == "__main__":
    main() 