#!/usr/bin/env python3
"""
Test Enhanced Refactored Version - Function Comparison Only
เปรียบเทียบฟังก์ชันการทำงานระหว่าง Main_Beyone_final.py และ Main_Beyone_Refactored.py
"""

import xml.etree.ElementTree as ET
import sys
import traceback
from pathlib import Path
import inspect

def load_test_file():
    """โหลดไฟล์ทดสอบ"""
    test_file = "Example_XML/Demo_Final.xml"
    if not Path(test_file).exists():
        print(f"❌ Test file {test_file} not found!")
        return None
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        root = ET.fromstring(content)
        
        # หา activity element
        activity = None
        namespaces = {
            'uml': 'http://www.eclipse.org/uml2/5.0.0/UML',
            'xmi': 'http://www.omg.org/spec/XMI/20131001'
        }
        
        for elem in root.findall(".//packagedElement", namespaces):
            xmi_type = elem.get('{http://www.omg.org/spec/XMI/20131001}type') or elem.get('xmi:type')
            if xmi_type == 'uml:Activity':
                activity = elem
                break
        
        if activity is None:
            activity = root.find(".//*[@xmi:type='uml:Activity']", namespaces)
        if activity is None:
            activity = root
        
        return activity
        
    except Exception as e:
        print(f"❌ Error loading test file: {e}")
        return None

def test_main_beyone_final():
    """ทดสอบ Main_Beyone_final.py"""
    print("\n" + "="*100)
    print("🧪 TESTING Main_Beyone_final.py")
    print("="*100)
    
    try:
        from Main_Beyone_final import UppaalConverter
        
        activity = load_test_file()
        if not activity:
            return None
        
        print("✅ Loaded test file successfully")
        
        # สร้าง converter และทดสอบ
        converter = UppaalConverter()
        converter.set_activity_root(activity)
        
        print("✅ Created UppaalConverter and set activity root")
        
        # ประมวลผล nodes
        main_template = converter.process_nodes()
        
        print("✅ Processed nodes successfully")
        print(f"📊 Main template locations: {len(main_template['state_map']) if main_template else 0}")
        print(f"📊 Fork templates created: {len(converter.fork_templates)}")
        
        # สร้าง XML
        xml_result = converter.generate_xml()
        
        print("✅ Generated XML successfully")
        print(f"📊 XML length: {len(xml_result)} characters")
        
        # บันทึกผลลัพธ์
        with open("Result/final_test_result.xml", "w", encoding="utf-8") as f:
            f.write(xml_result)
        
        print("✅ Saved result to Result/final_test_result.xml")
        
        return {
            'status': 'success',
            'main_template_locations': len(main_template['state_map']) if main_template else 0,
            'fork_templates': len(converter.fork_templates),
            'xml_length': len(xml_result),
            'xml_content': xml_result,
            'converter': converter
        }
        
    except Exception as e:
        print(f"❌ Error in Main_Beyone_final.py: {e}")
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e)
        }

def test_main_beyone_refactored():
    """ทดสอบ Main_Beyone_Refactored.py"""
    print("\n" + "="*100)
    print("🧪 TESTING Main_Beyone_Refactored.py")
    print("="*100)
    
    try:
        from Main_Beyone_Refactored import ActivityDiagramToXML
        
        activity = load_test_file()
        if not activity:
            return None
        
        print("✅ Loaded test file successfully")
        
        # สร้าง converter และทดสอบ
        converter = ActivityDiagramToXML()
        
        print("✅ Created ActivityDiagramToXML converter")
        
        # ประมวลผลการแปลง
        xml_result = converter.convert_xmi_to_uppaal(activity)
        
        print("✅ Converted XMI to UPPAAL successfully")
        print(f"📊 Main template locations: {len(converter.template_manager.main_template['state_map']) if converter.template_manager.main_template else 0}")
        print(f"📊 Fork templates created: {len(converter.template_manager.fork_templates)}")
        print(f"📊 XML length: {len(xml_result)} characters")
        
        # บันทึกผลลัพธ์
        with open("Result/refactored_test_result.xml", "w", encoding="utf-8") as f:
            f.write(xml_result)
        
        print("✅ Saved result to Result/refactored_test_result.xml")
        
        return {
            'status': 'success',
            'main_template_locations': len(converter.template_manager.main_template['state_map']) if converter.template_manager.main_template else 0,
            'fork_templates': len(converter.template_manager.fork_templates),
            'xml_length': len(xml_result),
            'xml_content': xml_result,
            'converter': converter
        }
        
    except Exception as e:
        print(f"❌ Error in Main_Beyone_Refactored.py: {e}")
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e)
        }

def get_all_functions(module_or_class):
    """ดึงฟังก์ชันทั้งหมดจาก module หรือ class"""
    functions = []
    
    if hasattr(module_or_class, '__dict__'):
        for name, obj in module_or_class.__dict__.items():
            if callable(obj) and not name.startswith('_'):
                # ถ้าเป็น method ให้ได้ signature
                try:
                    sig = inspect.signature(obj)
                    functions.append({
                        'name': name,
                        'signature': str(sig),
                        'callable': obj
                    })
                except:
                    functions.append({
                        'name': name,
                        'signature': 'unknown',
                        'callable': obj
                    })
    
    return functions

def compare_function_signatures(final_result, refactored_result):
    """เปรียบเทียบ function signatures"""
    print("\n" + "="*100)
    print("🔍 FUNCTION SIGNATURE COMPARISON")
    print("="*100)
    
    if not final_result or not refactored_result:
        print("❌ Cannot compare - missing converter objects")
        return
    
    # ดึง converter objects
    final_converter = final_result.get('converter')
    refactored_converter = refactored_result.get('converter')
    
    if not final_converter or not refactored_converter:
        print("❌ Cannot compare - converter objects not available")
        return
    
    # ดึงฟังก์ชันจาก final converter (UppaalConverter)
    final_functions = get_all_functions(final_converter)
    
    # ดึงฟังก์ชันจาก refactored converter และ components ต่างๆ
    refactored_functions = get_all_functions(refactored_converter)
    
    # รวมฟังก์ชันจาก components ใน refactored version
    if hasattr(refactored_converter, 'declaration_manager'):
        refactored_functions.extend(get_all_functions(refactored_converter.declaration_manager))
    if hasattr(refactored_converter, 'template_manager'):
        refactored_functions.extend(get_all_functions(refactored_converter.template_manager))
    if hasattr(refactored_converter, 'transition_builder'):
        refactored_functions.extend(get_all_functions(refactored_converter.transition_builder))
    if hasattr(refactored_converter, 'fork_template_builder'):
        refactored_functions.extend(get_all_functions(refactored_converter.fork_template_builder))
    
    print(f"\n📊 FUNCTION COUNT COMPARISON:")
    print("-" * 80)
    print(f"Final version functions: {len(final_functions)}")
    print(f"Refactored version functions: {len(refactored_functions)}")
    
    # แสดงฟังก์ชันที่สำคัญๆ
    print(f"\n📋 KEY FUNCTIONS IN FINAL VERSION:")
    print("-" * 80)
    key_functions = ['process_nodes', 'generate_xml', 'add_location', 'add_transition', 'create_template']
    
    for func_info in final_functions:
        if any(key in func_info['name'].lower() for key in key_functions):
            print(f"• {func_info['name']}{func_info['signature']}")
    
    print(f"\n📋 KEY FUNCTIONS IN REFACTORED VERSION:")
    print("-" * 80)
    
    for func_info in refactored_functions:
        if any(key in func_info['name'].lower() for key in key_functions):
            print(f"• {func_info['name']}{func_info['signature']}")
    
    # ตรวจสอบฟังก์ชันหลักๆ ที่ควรมี
    print(f"\n✅ CORE FUNCTIONALITY CHECK:")
    print("-" * 80)
    
    core_functions = [
        'process_nodes', 'generate_xml', 'add_location', 'add_transition', 
        'create_template', 'set_activity_root'
    ]
    
    final_func_names = [f['name'].lower() for f in final_functions]
    refactored_func_names = [f['name'].lower() for f in refactored_functions]
    
    for core_func in core_functions:
        final_has = any(core_func in name for name in final_func_names)
        refactored_has = any(core_func in name for name in refactored_func_names)
        
        status = "✅" if final_has and refactored_has else "⚠️" if final_has or refactored_has else "❌"
        print(f"{status} {core_func:<20} | Final: {'✅' if final_has else '❌'} | Refactored: {'✅' if refactored_has else '❌'}")

def compare_results(final_result, refactored_result):
    """เปรียบเทียบผลลัพธ์"""
    print("\n" + "="*100)
    print("📊 FUNCTIONALITY COMPARISON RESULTS")
    print("="*100)
    
    if not final_result or not refactored_result:
        print("❌ Cannot compare - one or both tests failed")
        return
    
    if final_result.get('status') != 'success' or refactored_result.get('status') != 'success':
        print("❌ Cannot compare - one or both tests had errors")
        if final_result.get('status') != 'success':
            print(f"   Final error: {final_result.get('error', 'Unknown')}")
        if refactored_result.get('status') != 'success':
            print(f"   Refactored error: {refactored_result.get('error', 'Unknown')}")
        return
    
    print(f"\n📈 QUANTITATIVE COMPARISON:")
    print("-" * 80)
    print(f"{'Metric':<30} {'Final':<15} {'Refactored':<15} {'Match':<10}")
    print("-" * 80)
    
    # เปรียบเทียบจำนวน locations
    final_locations = final_result.get('main_template_locations', 0)
    refact_locations = refactored_result.get('main_template_locations', 0)
    locations_match = "✅" if final_locations == refact_locations else "❌"
    print(f"{'Main Template Locations':<30} {final_locations:<15} {refact_locations:<15} {locations_match:<10}")
    
    # เปรียบเทียบจำนวน fork templates
    final_forks = final_result.get('fork_templates', 0)
    refact_forks = refactored_result.get('fork_templates', 0)
    forks_match = "✅" if final_forks == refact_forks else "❌"
    print(f"{'Fork Templates':<30} {final_forks:<15} {refact_forks:<15} {forks_match:<10}")
    
    # เปรียบเทียบความยาว XML
    final_xml_len = final_result.get('xml_length', 0)
    refact_xml_len = refactored_result.get('xml_length', 0)
    xml_len_match = "✅" if abs(final_xml_len - refact_xml_len) < 100 else "❌"  # ยอมให้ต่างได้ไม่เกิน 100 ตัวอักษร
    print(f"{'XML Length':<30} {final_xml_len:<15} {refact_xml_len:<15} {xml_len_match:<10}")
    
    print("-" * 80)
    
    # สรุปผลการเปรียบเทียบ
    all_match = locations_match == "✅" and forks_match == "✅" and xml_len_match == "✅"
    
    print(f"\n🎯 FUNCTIONALITY ASSESSMENT:")
    print("-" * 80)
    if all_match:
        print("✅ EXCELLENT! Main_Beyone_Refactored.py produces equivalent functionality to Main_Beyone_final.py")
        print("   All core metrics match perfectly.")
    else:
        print("⚠️ DIFFERENCES DETECTED between Main_Beyone_final.py and Main_Beyone_Refactored.py")
        if locations_match == "❌":
            print(f"   • Main template locations differ: {final_locations} vs {refact_locations}")
        if forks_match == "❌":
            print(f"   • Fork templates differ: {final_forks} vs {refact_forks}")
        if xml_len_match == "❌":
            print(f"   • XML length differs significantly: {final_xml_len} vs {refact_xml_len}")
    
    print("\n📋 DETAILED ANALYSIS:")
    print("-" * 80)
    
    # วิเคราะห์เนื้อหา XML
    final_xml = final_result.get('xml_content', '')
    refact_xml = refactored_result.get('xml_content', '')
    
    # นับจำนวน templates ใน XML
    final_template_count = final_xml.count('<template>')
    refact_template_count = refact_xml.count('<template>')
    
    print(f"Final XML templates: {final_template_count}")
    print(f"Refactored XML templates: {refact_template_count}")
    print(f"Templates match: {'✅' if final_template_count == refact_template_count else '❌'}")
    
    # นับจำนวน locations ใน XML
    final_location_count = final_xml.count('<location')
    refact_location_count = refact_xml.count('<location')
    
    print(f"Final XML locations: {final_location_count}")
    print(f"Refactored XML locations: {refact_location_count}")
    print(f"Locations match: {'✅' if final_location_count == refact_location_count else '❌'}")
    
    # นับจำนวน transitions ใน XML
    final_transition_count = final_xml.count('<transition')
    refact_transition_count = refact_xml.count('<transition')
    
    print(f"Final XML transitions: {final_transition_count}")
    print(f"Refactored XML transitions: {refact_transition_count}")
    print(f"Transitions match: {'✅' if final_transition_count == refact_transition_count else '❌'}")
    
    # เปรียบเทียบฟังก์ชัน
    compare_function_signatures(final_result, refactored_result)

def main():
    """Main test function"""
    print("🚀 Starting Enhanced Refactored Version Test - Function Comparison")
    print("="*100)
    
    # สร้าง Result directory ถ้าไม่มี
    Path("Result").mkdir(exist_ok=True)
    
    # ทดสอบทั้งสองเวอร์ชัน
    final_result = test_main_beyone_final()
    refactored_result = test_main_beyone_refactored()
    
    # เปรียบเทียบผลลัพธ์และฟังก์ชัน
    compare_results(final_result, refactored_result)
    
    print("\n" + "="*100)
    print("✅ FUNCTION COMPARISON TEST COMPLETE")
    print("="*100)

if __name__ == "__main__":
    main() 