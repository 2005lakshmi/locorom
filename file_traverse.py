import streamlit as st
import os

# Show title
st.title("📁 My Repository Files")

# 👉 Step 1: Show where we are (for debugging)
st.write("### 🔍 Debug Info")
folder = os.path.dirname(__file__) if __file__ else "."
st.write(f"Script folder: `{folder}`")

# List all files in the current directory and below
found_files = []

for root, dirs, files in os.walk(folder):
    # 👉 Skip hidden folders (.git, __pycache__, etc.)
    dirs[:] = [d for d in dirs if not d.startswith(".")]
    
    for file in files:
        # 👉 Skip hidden/system files (optional)
        if file.startswith("."):
            continue
        # Build relative path
        rel_path = os.path.relpath(os.path.join(root, file), folder)
        found_files.append(rel_path)

# 👉 Step 2: Show what we found
st.write(f"Found {len(found_files)} visible files:")

if not found_files:
    st.warning("No files found! Maybe everything is hidden or path is wrong.")
else:
    # Sort files to show root ones first
    found_files.sort()

    for rel_path in found_files:
        # Button to show content
        if st.button(f"📄 {rel_path}", key=rel_path):
            try:
                full_path = os.path.join(folder, rel_path)
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                st.text_area("File Content", content, height=300)
            except Exception as e:
                st.error(f"Error reading {rel_path}: {e}")
