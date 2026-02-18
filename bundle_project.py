import os
import glob

# Configuration
CODE_EXTENSIONS = {'.py', '.sh', '.toml'}
TEXT_EXTENSIONS = {'.md', '.txt', '.jsonl'} # Added jsonl as user might want to see the output examples
IGNORE_DIRS = {'.venv', '__pycache__', '.git', '.pytest_cache', 'egg-info', 'dist', 'build', 'live_test_output', 'live_test_output_2', 'live_test_output_final', 'verification_data', 'final_test_output', 'data', 'output', 'output_test'}
ARTIFACT_DIR = "/Users/adrianaso/.gemini/antigravity/brain/b56559a0-366a-4e44-8856-8ab155431115"

def is_ignored(path):
    parts = path.split(os.sep)
    for part in parts:
        if part in IGNORE_DIRS:
            return True
        if part.endswith('.egg-info'):
            return True
    return False

def bundle_files(output_filename, extensions, check_artifacts=False):
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        # 1. Walk current directory
        for root, dirs, files in os.walk('.'):
            # Filtering ignored dirs in place
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.endswith('.egg-info')]
            
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in extensions:
                    path = os.path.join(root, file)
                    if is_ignored(path):
                        continue
                        
                    # Skip this script itself
                    if file == 'bundle_project.py':
                        continue
                        
                    outfile.write(f"\n\n{'='*20} FILE: {path} {'='*20}\n\n")
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"Error reading file: {e}")

        # 2. Add Artifacts (Only for text bundle)
        if check_artifacts:
            for file in os.listdir(ARTIFACT_DIR):
                if file.endswith('.md'):
                    path = os.path.join(ARTIFACT_DIR, file)
                    outfile.write(f"\n\n{'='*20} ARTIFACT: {file} {'='*20}\n\n")
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"Error reading artifact: {e}")

if __name__ == "__main__":
    print("Bundling code...")
    bundle_files('all_code.txt', CODE_EXTENSIONS, check_artifacts=False)
    
    print("Bundling text and artifacts...")
    # For text, we include .md and .txt from root, AND artifacts
    bundle_files('all_text.txt', TEXT_EXTENSIONS, check_artifacts=True)
    
    print("Done. Created 'all_code.txt' and 'all_text.txt'.")
