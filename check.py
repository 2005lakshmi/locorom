import os
import base64
import requests
import streamlit as st
from pathlib import Path

# Configuration
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = "2005lakshmi/locorom"
BASE_PATH = "Rooms"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

def get_github_files(path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []

def create_room_folder(room_name):
    folder_path = f"{BASE_PATH}/{room_name}"
    info_file_path = f"{folder_path}/info.txt"
    
    # Create info.txt file
    content = base64.b64encode("".encode()).decode()
    data = {
        "message": f"Create room {room_name}",
        "content": content
    }
    response = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{info_file_path}",
        json=data,
        headers=HEADERS
    )
    return response.status_code == 201

def get_next_file_number(room_name):
    files = get_github_files(f"{BASE_PATH}/{room_name}")
    numbers = []
    for file in files:
        if file['name'] != 'info.txt' and file['type'] == 'file':
            try:
                numbers.append(int(Path(file['name']).stem))
            except ValueError:
                continue
    return max(numbers) + 1 if numbers else 1

def upload_room_file(room_name, file_data, file_type):
    try:
        ext = file_type.split('/')[-1]
        if ext == 'jpeg':
            ext = 'jpg'
            
        next_num = get_next_file_number(room_name)
        file_path = f"{BASE_PATH}/{room_name}/{next_num}.{ext}"
        
        content = base64.b64encode(file_data.read()).decode()
        data = {
            "message": f"Add file {next_num}.{ext} to {room_name}",
            "content": content
        }
        response = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}",
            json=data,
            headers=HEADERS
        )
        return response.status_code == 201
    except Exception as e:
        st.error(f"Error uploading file: {str(e)}")
        return False

def get_room_info(room_name):
    info_path = f"{BASE_PATH}/{room_name}/info.txt"
    response = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{info_path}",
        headers=HEADERS
    )
    if response.status_code == 200:
        return base64.b64decode(response.json()['content']).decode()
    return ""

def update_room_info(room_name, content):
    info_path = f"{BASE_PATH}/{room_name}/info.txt"
    current_content = get_github_files(info_path)
    sha = current_content['sha'] if 'sha' in current_content else None
    
    encoded = base64.b64encode(content.encode()).decode()
    data = {
        "message": "Update info.txt",
        "content": encoded,
        "sha": sha
    }
    response = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{info_path}",
        json=data,
        headers=HEADERS
    )
    return response.status_code == 200


def delete_file(file_path, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    data = {
        "message": f"Delete file {Path(file_path).name}",
        "sha": sha
    }
    response = requests.delete(url, json=data, headers=HEADERS)
    return response.status_code == 200

def rename_file(old_path, new_name, sha):
    # Get file content
    content = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{old_path}",
        headers=HEADERS
    ).json()
    
    # Create new file
    new_path = str(Path(old_path).parent / new_name)
    data = {
        "message": f"Rename {Path(old_path).name} to {new_name}",
        "content": content['content']
    }
    create_response = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{new_path}",
        json=data,
        headers=HEADERS
    )
    # Delete old file if creation succeeded
    if create_response.status_code == 201:
        delete_file(old_path, sha)
        return True
    return False


def admin_page():
    st.title("Admin Panel")
    tab1, tab2, tab3 = st.tabs(["Create Room", "Add Content", "Manage Files"])
    
    # ... [Keep previous tab1 and tab2 content] ...
    with tab1:
        with st.form("create_room"):
            room_name = st.text_input("Room Name")
            if st.form_submit_button("Create Room"):
                if create_room_folder(room_name):
                    st.success("Room created successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to create room")


    with tab2:
        rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
        selected_room = st.selectbox("Select Room", rooms)
        
        # File Upload
        uploaded_file = st.file_uploader("Upload Media", type=['jpg', 'jpeg', 'png', 'gif', 'mp4'])
        if uploaded_file:
            if upload_room_file(selected_room, uploaded_file, uploaded_file.type):
                st.success("File uploaded successfully!")
            else:
                st.error("Failed to upload file")
        
        # Info.txt Editor
        info_content = get_room_info(selected_room)
        new_content = st.text_area("Edit Room Info", value=info_content, height=200)
        if st.button("Save Info"):
            if update_room_info(selected_room, new_content):
                st.success("Info updated!")
            else:
                st.error("Failed to update info")


    
    with tab3:
        rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
        selected_room = st.selectbox("Select Room to Manage", rooms)
        
        files = get_github_files(f"{BASE_PATH}/{selected_room}")
        files = [f for f in files if f['type'] == 'file' and f['name'] != 'info.txt']
        
        if not files:
            st.info("No files to manage in this room")
            return
            
        st.subheader("Manage Files in Selected Room")
        for file in files:
            col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
            with col1:
                st.markdown(f"**File:** `{file['name']}`")
                
            with col2:
                new_name = st.text_input(
                    "New name", 
                    value=file['name'],
                    key=f"rename_{file['name']}"
                )

            with col3:
                if st.button("🗑️ Delete", key=f"del_{file['name']}"):
                    if delete_file(file['path'], file['sha']):
                        st.success("File deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete file")
                        
            with col4:
                if st.button("✏️ Rename", key=f"ren_{file['name']}"):
                    if new_name == file['name']:
                        st.warning("Name unchanged")
                    elif not new_name:
                        st.error("Please enter a new name")
                    else:
                        if rename_file(file['path'], new_name, file['sha']):
                            st.success("File renamed!")
                            st.rerun()
                        else:
                            st.error("Failed to rename file")





# Default Page
def default_page():
    st.markdown("<h1 style='text-align: center; color: #4B0082; font-family: Arial;'>🔍 Search Room</h1>", 
                unsafe_allow_html=True)
    
    rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
    search_term = st.text_input("Search Rooms", "").lower()
    filtered_rooms = [room for room in rooms if search_term in room.lower()]
    
    if filtered_rooms:
        selected_room = st.selectbox("Select a Room", filtered_rooms)
        st.subheader(selected_room)
        
        # Display info.txt
        info_content = get_room_info(selected_room)
        st.markdown(f"**Room Information:**\n{info_content}")
        
        # Display media files
        files = get_github_files(f"{BASE_PATH}/{selected_room}")
        media_files = [f for f in files if f['name'] != 'info.txt']
        
        if media_files:
            st.markdown("### Media Files")
            cols = st.columns(len(media_files))
            for idx, col in enumerate(cols):
                with col:
                    file_url = media_files[idx]['download_url']
                    if media_files[idx]['name'].split('.')[-1] in ['mp4']:
                        st.video(file_url)
                    else:
                        st.image(file_url, use_column_width=True)

# Main App
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Search Rooms", "Admin Panel"])
    
    if page == "Admin Panel":
        password = st.sidebar.text_input("Password", type="password")
        if password == st.secrets["general"]["password"]:
            admin_page()
        else:
            st.error("Incorrect Password")
    else:
        default_page()

if __name__ == "__main__":
    main()
