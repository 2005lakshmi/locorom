import streamlit as st
import os

# Set title
st.title("📁 My Repository Files")

# Get the folder where this script is
folder = os.path.dirname(__file__)
print(folder)

# List all files in this folder and subfolders
for root, dirs, files in os.walk(folder):
    # Skip hidden folders like __pycache__, .git, etc.
    if '/.' in root or '\\.' in root:
        continue

    # Remove hidden folders from listing
    dirs[:] = [d for d in dirs if not d.startswith(".")]

    # Show current folder
    relative_path = os.path.relpath(root, folder)
    if relative_path == ".":
        st.subheader("Root")
    else:
        st.subheader(f"Folder: {relative_path}")

    # Show files
    for file in files:
        if file.startswith("."):
            continue  # Skip hidden files

        # Make a button for each file
        if st.button(f"📄 {file}", key=file):
            try:
                # Read and show file content
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                st.text_area("Content:", content, height=300)
            except Exception as e:
                st.error(f"Could not read file: {e}")
