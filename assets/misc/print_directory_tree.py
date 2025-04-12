import os

# 🔧 Change this path to point to the folder you want to visualize
ROOT_DIR = r"C:\Users\lester\MeDocuments\Research\MadhavLab\CodeBase\omniroute_analysis"

def print_tree(root, prefix=""):
    """Recursively build a tree string."""
    entries = sorted(os.listdir(root))
    entries = [e for e in entries if not e.startswith('__pycache__') and not e.endswith('.pyc')]
    lines = []
    pointers = ["├── "] * (len(entries) - 1) + ["└── "]
    for pointer, entry in zip(pointers, entries):
        path = os.path.join(root, entry)
        lines.append(prefix + pointer + entry)
        if os.path.isdir(path):
            extension = "│   " if pointer == "├── " else "    "
            lines.extend(print_tree(path, prefix + extension))
    return lines

if __name__ == "__main__":
    root_name = os.path.basename(os.path.abspath(ROOT_DIR))
    tree_lines = [root_name + "/"] + print_tree(ROOT_DIR)

    # Save output
    output_path = os.path.join(ROOT_DIR, "directory_tree.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tree_lines))

    print(f"[✓] Directory tree saved to: {output_path}")
