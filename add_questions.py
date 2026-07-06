import json
import re
import os
import sys

def validate_question(q, index):
    required_keys = {"id", "src", "lec", "cat", "diff", "type", "q", "opts", "a", "expl"}
    missing = required_keys - set(q.keys())
    if missing:
        print(f"Error: Question at index {index} is missing keys: {missing}")
        return False
    if not isinstance(q["opts"], list) or len(q["opts"]) != 4:
        print(f"Error: Question {q['id']} 'opts' must be a list of 4 options.")
        return False
    if not isinstance(q["a"], int) or not (0 <= q["a"] <= 3):
        print(f"Error: Question {q['id']} 'a' (correct index) must be an integer between 0 and 3.")
        return False
    return True

def main():
    html_file = "AI챔피언_1차역량평가_문제은행 Ver 1.9.html"
    
    # Check if a custom json file is provided as argument
    json_file = "new_questions.json"
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        
    if not os.path.exists(json_file):
        print(f"Usage: python add_questions.py [your_questions.json]")
        print(f"Error: Input JSON file '{json_file}' not found.")
        print("Please create a JSON file with the questions you want to add, formatted as a JSON array.")
        return

    if not os.path.exists(html_file):
        print(f"Error: HTML file '{html_file}' not found in the current directory.")
        return

    print(f"Reading new questions from {json_file}...")
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            new_qs = json.load(f)
    except Exception as e:
        print(f"Error reading/parsing JSON file: {e}")
        return

    if not isinstance(new_qs, list):
        # If it's a single question object, wrap it in a list
        if isinstance(new_qs, dict):
            new_qs = [new_qs]
        else:
            print("Error: JSON content must be a list of question objects or a single question object.")
            return

    # Validate questions
    valid_questions = []
    for idx, q in enumerate(new_qs):
        if validate_question(q, idx):
            valid_questions.append(q)
            
    if not valid_questions:
        print("No valid questions found to add.")
        return

    print(f"Reading HTML file...")
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Find QUESTIONS array
    match = re.search(r'const\s+QUESTIONS\s*=\s*(\[.*?\]);?\s*$', content, re.MULTILINE)
    if not match:
        print("Error: Could not find QUESTIONS array in HTML file.")
        return

    array_str = match.group(1)
    try:
        existing_qs = json.loads(array_str)
    except Exception as e:
        print(f"Error parsing existing QUESTIONS from HTML: {e}")
        return

    # Check for duplicate IDs
    existing_ids = {q["id"] for q in existing_qs}
    questions_to_add = []
    for q in valid_questions:
        if q["id"] in existing_ids:
            print(f"Skipping duplicate question ID: {q['id']}")
        else:
            questions_to_add.append(q)

    if not questions_to_add:
        print("No new questions to add (all were duplicate IDs).")
        return

    # Backup the HTML file first
    backup_file = html_file.replace(".html", ".bak.html")
    print(f"Creating backup file: {backup_file}...")
    shutil_copy_success = False
    try:
        import shutil
        shutil.copy(html_file, backup_file)
        shutil_copy_success = True
    except Exception as e:
        print(f"Warning: Backup creation failed ({e}). Proceeding carefully...")

    # Merge questions
    existing_qs.extend(questions_to_add)
    
    # Serialize back to JSON in a single line
    new_array_str = json.dumps(existing_qs, ensure_ascii=False)
    new_declaration = f"const QUESTIONS = {new_array_str};"
    
    # Replace in content
    new_content = content[:match.start()] + new_declaration + content[match.end():]
    
    print("Writing updated content to HTML file...")
    try:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Successfully added {len(questions_to_add)} questions!")
        print(f"Total questions inside the HTML file: {len(existing_qs)}")
    except Exception as e:
        print(f"Error writing to HTML file: {e}")
        if shutil_copy_success:
            print("Restoring backup...")
            shutil.copy(backup_file, html_file)

if __name__ == "__main__":
    main()
