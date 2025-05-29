print("Hello World")
print("Python is working")

try:
    import os
    print("OS module imported")
    
    print("Current directory:", os.getcwd())
    print("Files in current directory:")
    for f in os.listdir('.'):
        if f.endswith('.py'):
            print(f"  {f}")
            
except Exception as e:
    print(f"Error: {e}") 