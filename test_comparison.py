#!/usr/bin/env python3
"""
Simple test script to compare outputs between Main_Beyone.py and Main_Pure_OOP.py
"""

import os
from Main_Pure_OOP import xmlConverter as PureOOPConverter

def test_comparison():
    print("=== Simple Comparison Test ===")
    
    # Test file
    input_file = "Example_XML/AP2.xml"
    
    if not os.path.exists(input_file):
        print(f"Test file {input_file} not found")
        return
    
    # Read input XML
    with open(input_file, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    print("\n=== Testing Pure OOP Main_Pure_OOP.py ===")
    try:
        pure_oop_converter = PureOOPConverter()
        pure_oop_result = pure_oop_converter.convert(xml_content)
        print("✅ Pure OOP converter worked")
        
        # Save Pure OOP result
        os.makedirs("Result", exist_ok=True)
        with open("Result/pure_oop_test_result.xml", "w", encoding='utf-8') as f:
            f.write(pure_oop_result)
        print("Pure OOP result saved to Result/pure_oop_test_result.xml")
        print(f"Result length: {len(pure_oop_result)} characters")
        
        # Show first few lines
        lines = pure_oop_result.split('\n')[:10]
        print("First 10 lines:")
        for i, line in enumerate(lines, 1):
            print(f"{i:2}: {line}")
        
    except Exception as e:
        print(f"❌ Pure OOP converter failed: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    test_comparison() 