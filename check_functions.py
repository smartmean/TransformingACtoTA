import ast
import inspect
from typing import Dict, List, Set

def extract_functions_from_file(filename: str) -> Dict[str, str]:
    """แยกฟังก์ชันออกจากไฟล์ Python"""
    functions = {}
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function name
                func_name = node.name
                
                # Get function source (approximate)
                func_lines = []
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    lines = content.split('\n')
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if node.end_lineno else len(lines)
                    func_lines = lines[start_line:end_line]
                
                # Clean function source
                func_source = '\n'.join(func_lines)
                functions[func_name] = func_source
                
            elif isinstance(node, ast.ClassDef):
                # Extract methods from classes
                class_name = node.name
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_name = f"{class_name}.{item.name}"
                        
                        # Get method source
                        if hasattr(item, 'lineno') and hasattr(item, 'end_lineno'):
                            lines = content.split('\n')
                            start_line = item.lineno - 1
                            end_line = item.end_lineno if item.end_lineno else len(lines)
                            method_lines = lines[start_line:end_line]
                            method_source = '\n'.join(method_lines)
                            functions[method_name] = method_source
    
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        
    return functions

def normalize_function_signature(func_source: str) -> str:
    """ทำให้ function signature เป็นมาตรฐาน"""
    lines = func_source.split('\n')
    
    # Remove comments and docstrings
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip comments
        if stripped.startswith('#'):
            continue
        # Skip empty lines
        if not stripped:
            continue
        # Keep the line
        cleaned_lines.append(line.rstrip())
    
    return '\n'.join(cleaned_lines)

def compare_functions(file1: str, file2: str):
    """เปรียบเทียบฟังก์ชันระหว่าง 2 ไฟล์"""
    print("🔍 ตรวจสอบและเปรียบเทียบฟังก์ชัน")
    print("=" * 80)
    
    # Extract functions
    print(f"📂 อ่านฟังก์ชันจาก {file1}...")
    functions1 = extract_functions_from_file(file1)
    
    print(f"📂 อ่านฟังก์ชันจาก {file2}...")
    functions2 = extract_functions_from_file(file2)
    
    print(f"\n📊 ผลการวิเคราะห์:")
    print(f"   {file1}: {len(functions1)} ฟังก์ชัน/เมธอด")
    print(f"   {file2}: {len(functions2)} ฟังก์ชัน/เมธอด")
    
    # Compare function names
    names1 = set(functions1.keys())
    names2 = set(functions2.keys())
    
    common_names = names1.intersection(names2)
    only_in_1 = names1 - names2
    only_in_2 = names2 - names1
    
    print(f"\n🔄 เปรียบเทียบชื่อฟังก์ชัน:")
    print(f"   ฟังก์ชันร่วม: {len(common_names)}")
    print(f"   มีเฉพาะใน {file1}: {len(only_in_1)}")
    print(f"   มีเฉพาะใน {file2}: {len(only_in_2)}")
    
    if only_in_1:
        print(f"\n❌ ฟังก์ชันที่มีเฉพาะใน {file1}:")
        for name in sorted(only_in_1):
            print(f"   • {name}")
    
    if only_in_2:
        print(f"\n✅ ฟังก์ชันที่มีเฉพาะใน {file2}:")
        for name in sorted(only_in_2):
            print(f"   • {name}")
    
    # Compare common functions
    print(f"\n🔬 เปรียบเทียบฟังก์ชันร่วม:")
    identical_count = 0
    different_count = 0
    
    for name in sorted(common_names):
        func1 = normalize_function_signature(functions1[name])
        func2 = normalize_function_signature(functions2[name])
        
        if func1 == func2:
            print(f"   ✅ {name}: เหมือนกัน")
            identical_count += 1
        else:
            print(f"   ❌ {name}: แตกต่างกัน")
            different_count += 1
            
            # Show differences in detail
            print(f"      📁 {file1}:")
            newline = '\n'
            print(f"         บรรทัด: {len(func1.split(newline))}")
            print(f"      📁 {file2}:")
            print(f"         บรรทัด: {len(func2.split(newline))}")
    
    print(f"\n📈 สรุปผลการเปรียบเทียบ:")
    print(f"   ฟังก์ชันเหมือนกัน: {identical_count}")
    print(f"   ฟังก์ชันแตกต่าง: {different_count}")
    print(f"   เปรียบเทียบได้: {len(common_names)} จาก {len(names1.union(names2))} ฟังก์ชัน")
    
    # Calculate similarity percentage
    if common_names:
        similarity = (identical_count / len(common_names)) * 100
        print(f"   🎯 ความเหมือน: {similarity:.1f}%")
    
    return {
        'common_names': common_names,
        'only_in_1': only_in_1,
        'only_in_2': only_in_2,
        'identical_count': identical_count,
        'different_count': different_count,
        'functions1': functions1,
        'functions2': functions2
    }

def analyze_specific_functions(comparison_result: dict, function_names: List[str]):
    """วิเคราะห์ฟังก์ชันเฉพาะที่สนใจ"""
    print(f"\n🔍 วิเคราะห์ฟังก์ชันเฉพาะ:")
    print("-" * 60)
    
    functions1 = comparison_result['functions1']
    functions2 = comparison_result['functions2']
    
    for func_name in function_names:
        print(f"\n📋 ฟังก์ชัน: {func_name}")
        
        # Check if function exists in both files
        in_file1 = func_name in functions1
        in_file2 = func_name in functions2
        
        print(f"   📁 Main_Beyone_final.py: {'✅ มี' if in_file1 else '❌ ไม่มี'}")
        print(f"   📁 Main_Beyone_Refactored.py: {'✅ มี' if in_file2 else '❌ ไม่มี'}")
        
        if in_file1 and in_file2:
            func1 = normalize_function_signature(functions1[func_name])
            func2 = normalize_function_signature(functions2[func_name])
            
            if func1 == func2:
                print(f"   🎯 สถานะ: เหมือนกันทุกประการ")
            else:
                print(f"   ⚠️ สถานะ: แตกต่างกัน")
                newline = '\n'
                print(f"      - บรรทัดใน final: {len(func1.split(newline))}")
                print(f"      - บรรทัดใน refactored: {len(func2.split(newline))}")

if __name__ == "__main__":
    # เปรียบเทียบฟังก์ชันระหว่าง 2 ไฟล์
    result = compare_functions("Main_Beyone_final.py", "Main_Beyone_Refactored.py")
    
    # วิเคราะห์ฟังก์ชันสำคัญ
    important_functions = [
        "UppaalConverter.convert_xmi_to_uppaal",
        "UppaalConverter.process_nodes",
        "UppaalConverter.add_location",
        "UppaalConverter.add_transition",
        "UppaalConverter.generate_xml",
        "ActivityDiagramToXML.convert_to_uppaal",
        "ActivityDiagramToXML.process_nodes",
        "LocationBuilder.add_location", 
        "TransitionBuilder.add_transition",
        "XMLGenerator.generate_xml"
    ]
    
    analyze_specific_functions(result, important_functions) 