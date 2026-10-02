import os
import sys

def inspect_vault(target_dir):
    print(f"Scanning target directory: {target_dir}")
    md_files = []
    
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
                
    print(f"Total Markdown files detected: {len(md_files)}")
    for f in md_files[:10]:  # Show first 10 files as a sample
        print(f" - {f}")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    inspect_vault(path)

