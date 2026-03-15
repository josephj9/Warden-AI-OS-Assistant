import os
import shutil
import time
from pathlib import Path
from tools.tools import TOOL_REGISTRY

# Test Environment Setup
TEST_DIR = Path("test_env_tools")
if TEST_DIR.exists():
    shutil.rmtree(TEST_DIR)

TEST_DIR.mkdir()

# Dummy files
files_to_create = [
    ("test1.txt", "Hello world, this is a test text file."),
    ("test2.py", "print('Hello World')"),
    ("test3.html", "<html><body>Hello</body></html>"),
]

for name, content in files_to_create:
    with open(TEST_DIR / name, "w") as f:
        f.write(content)

# We will test each tool and write results to a log file
def run_tests():
    results = []
    
    def log(tool_name, req, res):
        results.append(f"--- {tool_name} ---")
        results.append(f"Request: {req}")
        results.append(f"Response: {res}")
        results.append("\n")

    # 1. organize_folder
    # We will organize the TEST_DIR
    res = TOOL_REGISTRY["organize_folder"](str(TEST_DIR))
    log("organize_folder", str(TEST_DIR), res)
    
    # 2. summarize_file
    # The organize_folder should have moved test1.txt to test_env_tools/txt/test1.txt
    txt_file = TEST_DIR / "txt" / "test1.txt"
    if txt_file.exists():
        res = TOOL_REGISTRY["summarize_file"](str(txt_file))
        log("summarize_file", str(txt_file), res)
    else:
        log("summarize_file", str(txt_file), "File not found (organize_folder might have failed)")
    
    # 3. move_file
    py_file = TEST_DIR / "py" / "test2.py"
    html_dir = TEST_DIR / "html"
    if py_file.exists() and html_dir.exists():
        res = TOOL_REGISTRY["move_file"](str(py_file), str(html_dir))
        log("move_file", {"src": str(py_file), "dst": str(html_dir)}, res)
    else:
        log("move_file", "py_file or html_dir", "File/Dir not found")
        
    # 4. list_files_by_date
    res = TOOL_REGISTRY["list_files_by_date"](str(TEST_DIR / "html"))
    log("list_files_by_date", str(TEST_DIR / "html"), res)
    
    # 5. start_folder_monitor
    res = TOOL_REGISTRY["start_folder_monitor"](str(TEST_DIR), [])
    log("start_folder_monitor", str(TEST_DIR), res)
    
    # 6. time_travel_search
    # Search for something we just summarized to ensure it's in memory
    res = TOOL_REGISTRY["time_travel_search"]("test text file")
    log("time_travel_search", "test text file", res)
    
    # 7. explain_folder
    res = TOOL_REGISTRY["explain_folder"](str(TEST_DIR))
    log("explain_folder", str(TEST_DIR), res)
    
    # 8. edit_file_nl
    if html_dir.exists() and (html_dir / "test2.py").exists():
        file_to_edit = str(html_dir / "test2.py")
        res = TOOL_REGISTRY["edit_file_nl"](file_to_edit, "Change the print statement to print Goodbye World")
        log("edit_file_nl", {"file": file_to_edit, "req": "Change print"}, res)
    else:
        log("edit_file_nl", "test2.py", "File not found")
        
    # 9. work_history_summary
    res = TOOL_REGISTRY["work_history_summary"](1)
    log("work_history_summary", "1 day", res)
    
    # 10. proactive_suggestions
    res = TOOL_REGISTRY["proactive_suggestions"](str(TEST_DIR))
    log("proactive_suggestions", str(TEST_DIR), res)
    
    # 11. explain_computer
    res = TOOL_REGISTRY["explain_computer"]([str(TEST_DIR)], 2)
    log("explain_computer", [str(TEST_DIR)], res)
    
    # 12. generate_file_graph
    res = TOOL_REGISTRY["generate_file_graph"](str(TEST_DIR))
    log("generate_file_graph", str(TEST_DIR), res)

    # Note about the "helloword" folder
    helloword_path = "helloword"
    res = TOOL_REGISTRY["organize_folder"](helloword_path)
    log("User Issue Check (organize_folder helloword)", helloword_path, res)
    
    # Same with absolute path
    test_hello = Path("helloword_test").absolute()
    res = TOOL_REGISTRY["organize_folder"](str(test_hello))
    log("User Issue Check (absolute path)", str(test_hello), res)

    with open("test_results.txt", "w") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    run_tests()
    print("Tests complete. Results in test_results.txt")
