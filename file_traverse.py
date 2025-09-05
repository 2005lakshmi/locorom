import streamlit as st
import os

st.title("📁 My Repository Files")

# 🔍 Show current working directory
st.write("### 📂 Current Working Directory")
cwd = os.getcwd()
st.write(f"`{cwd}`")

# 🔍 List all files in the entire repo
st.write("### 📄 All Files in Repository")
all_files = []

for root, dirs, files in os.walk(cwd):
    # Skip hidden folders like .git, __pycache__, etc.
    dirs[:] = [d for d in dirs if not d.startswith(".")]
    for file in files:
        if file.startswith("."):
            continue  # Skip hidden files
        full_path = os.path.join(root, file)
        rel_path = os.path.relpath(full_path, cwd)
        all_files.append(rel_path)

# Sort files for clean display
all_files.sort()

st.write(f"Found {len(all_files)} files:")

if not all_files:
    st.error("No files found! Something is wrong with the file system.")
else:
        for rel_path in all_files:
            if st.button(f"📄 {rel_path}", key=rel_path):
                file_path = os.path.join(cwd, rel_path)
            
                # Check file extension
                ext = rel_path.lower().split(".")[-1]
            
                if ext in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
                    # It's an image → display it
                    try:
                        st.subheader(f"🖼️ Image: {rel_path}")
                        st.image(file_path)
                    except Exception as e:
                        st.error(f"Could not display image: {e}")
            
                elif ext in ["py", "txt", "md", "csv", "json", "yaml", "yml", "html", "css", "js"]:
                    # It's a text file → read and show content
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        st.subheader(f"📄 Text File: {rel_path}")
                        st.code(content, language=ext)
                    except Exception as e:
                        st.error(f"Could not read file: {e}")
            
                else:
                    # Other files (binary, unknown)
                    st.warning(f"📁 Cannot display `{rel_path}` (unsupported format).")
