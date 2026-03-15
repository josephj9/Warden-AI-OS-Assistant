from tools.utils import resolve_path
import os
from pathlib import Path

def test_resolve():
    print("Testing path resolution...")
    # Create a test file on Desktop
    desktop = Path.home() / "Desktop"
    test_file = desktop / "resolver_test_file.txt"
    
    with open(test_file, "w") as f:
        f.write("test")
        
    resolved = resolve_path("resolver_test_file.txt")
    print(f"Original: resolver_test_file.txt -> Resolved: {resolved}")
    
    assert str(test_file) == resolved, f"Resolution failed! Expected {test_file}, got {resolved}"
    print("Test passed successfully!")
    
    if test_file.exists():
        test_file.unlink()

if __name__ == "__main__":
    test_resolve()
