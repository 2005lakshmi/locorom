import os
import base64
import requests
import streamlit as st
from pathlib import Path
import time
import streamlit.components.v1 as components




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


def rename_file(old_path, new_name):
    try:
        # Validate inputs
        if not old_path or not new_name:
            st.error("Invalid file paths provided")
            return False

        # Get file details
        file_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{old_path}"
        response = requests.get(file_url, headers=HEADERS)
        
        if response.status_code != 200:
            st.error(f"Failed to fetch file details (HTTP {response.status_code})")
            return False

        file_data = response.json()
        
        # Validate response data
        required_keys = ['sha', 'download_url', 'path', 'name']
        if not all(key in file_data for key in required_keys):
            st.error("Missing critical file metadata from GitHub")
            return False

        # Get file content with fallback
        file_content = file_data.get('content')
        if not file_content:
            download_response = requests.get(file_data['download_url'])
            if download_response.status_code == 200:
                file_content = base64.b64encode(download_response.content).decode('utf-8')
            else:
                st.error("Failed to fetch file content")
                return False

        # Construct new path and verify not existing
        new_path = str(Path(old_path).parent / new_name)
        if get_github_files(new_path):
            st.error("A file with the new name already exists")
            return False

        # Create new file with retry logic
        create_response = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{new_path}",
            headers=HEADERS,
            json={
                "message": f"Rename {Path(old_path).name} to {new_name}",
                "content": file_content,
                "branch": "main"
            }
        )

        if create_response.status_code not in [200, 201]:
            st.error(f"Failed to create new file (HTTP {create_response.status_code})")
            return False

        # Delete old file with verification
        delete_response = requests.delete(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{old_path}",
            headers=HEADERS,
            json={
                "message": f"Delete original file after renaming to {new_name}",
                "sha": file_data['sha'],
                "branch": "main"
            }
        )

        if delete_response.status_code != 200:
            # Attempt to rollback new file creation
            requests.delete(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/{new_path}",
                headers=HEADERS,
                json={
                    "message": "Rollback failed rename",
                    "sha": create_response.json()['content']['sha']
                }
            )
            st.error("Failed to delete original file - rolled back changes")
            return False

        st.success("File renamed successfully! ✅")
        return True

    except Exception as e:
        st.error(f"Critical error during renaming: {str(e)}")
        return False
def delete_room(room_name):
    """Delete a room and all its contents"""
    files = get_github_files(f"{BASE_PATH}/{room_name}")
    success = True
    for file in files:
        if file['type'] == 'file':
            if not delete_file(file['path'], file['sha']):
                success = False
    return success




def rename_room(old_name, new_name):
    try:

        dummy_content = base64.b64encode(b"Initial file").decode('utf-8')  # <-- FIX HERE
    
        # Existing logic
        # Replace requests calls with:
        create_response = github_api_call(
            'PUT', 
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BASE_PATH}/{new_name}/dummy.txt",
            json={"message": f"Create new room {new_name}", "content": dummy_content}
        )
        
        # And similarly for other operations
        github_api_call(
            'DELETE',
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file['path']}",
            json={"message": f"Delete during rename", "sha": file['sha']}
        )
            
    except requests.exceptions.HTTPError as e:
        response = e.response
        error_message = "An error occurred during the operation"
        
        try:
            # Try to get GitHub's error message
            error_data = response.json()
            error_message = error_data.get("message", error_message)
            details = error_data.get("errors", "")
        except ValueError:
            details = response.text
    
        # Handle specific status codes
        if response.status_code == 401:
            st.error("🔐 Authentication failed: Check your GitHub token")
        elif response.status_code == 403:
            reset_time = datetime.fromtimestamp(
                int(response.headers.get('X-RateLimit-Reset', time.time() + 3600)))
            st.error(f"⏳ Rate limited: Try again after {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        elif response.status_code == 404:
            st.error("🔍 Resource not found: The room or file may have been deleted")
        elif response.status_code == 422:
            st.error(f"📄 Validation error: {details}")
        else:
            st.error(f"🚨 Unexpected error ({response.status_code}): {error_message}")
    
        # Log technical details for debugging
        st.markdown(f"```\nTechnical details: {error_message}\n{details}\n```")
        
        return False, error_message

def admin_page():
    st.title("Admin Panel")
    tab1, tab2, tab3, tab4= st.tabs(["Create Room", "Add Content", "Manage Files", "Delete Rooms"])
    
                
    with tab1:
        with st.form("create_room"):
            room_name = st.text_input("Room Name")
            if st.form_submit_button("Create Room"):
                existing_rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
                
                if room_name in existing_rooms:
                    st.error("Room already exists")
                else:
                    if create_room_folder(room_name):
                        st.success(f"Room **{room_name}** created successfully!")
                        
                    else:
                        st.error("Failed to create room")
    
        # Modified search section with unique key
        st.markdown("---")
        st.subheader("Search Existing Rooms")
        search_term = st.text_input("Enter room number to search:", 
                                  key="tab1_room_search").strip()  # Unique key
        
        if search_term:
            existing_rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
            filtered_rooms = [room for room in existing_rooms if search_term.lower() in room.lower()]
            
            if filtered_rooms:
                st.write("Matching rooms:")
                for room in filtered_rooms:
                    st.markdown(f"- `{room}`")
            else:
                st.info("No rooms found matching your search")
        
    with tab2:
        st.header("📤 Add/Edit Room Content")
        search_term = st.text_input("Search rooms by name", key="content_search").lower()

        if 'upload_counter' not in st.session_state:
            st.session_state.upload_counter = 0
        
        # Get all rooms and filter
        all_rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
        filtered_rooms = [room for room in all_rooms if search_term in room.lower()]
        
        if not filtered_rooms:
            st.info("No rooms found matching your search")
            return
    
        for room in filtered_rooms:
            with st.expander(f"Room: **{room}**", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Display current content
                    files = get_github_files(f"{BASE_PATH}/{room}")
                    media_files = [f for f in files if f['name'] != 'info.txt']
                    
                    if media_files:
                        st.markdown("### Existing Media")
                        carousel_items = ""
                        for file in media_files:
                            ext = file['name'].split('.')[-1].lower()
                            if ext == "mp4":
                                media_html = f"""
                                    <video controls style="max-height: 400px; width: 100%;">
                                        <source src="{file['download_url']}" type="video/mp4">
                                    </video>
                                """
                            else:
                                media_html = (
                                    f'<div class="swiper-zoom-container">'
                                    f'<img src="{file["download_url"]}" '
                                    f'style="max-height: 400px; width: 100%; object-fit: contain;" />'
                                    f'</div>'
                                )
                            carousel_items += f'<div class="swiper-slide">{media_html}</div>'
    
                        carousel_html = f"""
                        <link rel="stylesheet" href="https://unpkg.com/swiper@8.0.7/swiper-bundle.min.css">
                        <style>
                            /* Same carousel styles as before */
                            .swiper {{
                                width: 100%;
                                height: auto;
                            }}
                            .swiper-slide {{
                                text-align: center;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                            }}
                            .swiper-slide img, .swiper-slide video {{
                                max-height: 400px;
                                width: 100%;
                                border-radius: 10px;
                                box-shadow: 0px 5px 15px rgba(0,0,0,0.2);
                                object-fit: contain;
                            }}
                            .swiper-pagination-fraction {{
                                font-size: 18px;
                                font-weight: bold;
                                color: white;
                                text-shadow: 0 0 5px rgba(0,0,0,0.5);
                            }}
                            .swiper-button-next,
                            .swiper-button-prev {{
                                width: 30px;
                                height: 30px;
                                background-color: rgba(0, 0, 0, 0.4);
                                border-radius: 50%;
                            }}
                            .swiper-button-next:after,
                            .swiper-button-prev:after {{
                                font-size: 20px;
                                color: white;
                            }}
                        </style>
                        <div class="swiper mySwiper">
                            <div class="swiper-wrapper">
                                {carousel_items}
                            </div>
                            <div class="swiper-pagination"></div>
                            <div class="swiper-button-next"></div>
                            <div class="swiper-button-prev"></div>
                        </div>
                        <script src="https://unpkg.com/swiper@8.0.7/swiper-bundle.min.js"></script>
                        <script>
                            var swiper = new Swiper('.mySwiper', {{
                                loop: true,
                                zoom: true,
                                pagination: {{
                                    el: '.swiper-pagination',
                                    type: 'fraction',
                                }},
                                navigation: {{
                                    nextEl: '.swiper-button-next',
                                    prevEl: '.swiper-button-prev',
                                }},
                            }});
                        </script>
                        """
                        components.html(carousel_html, height=500)
                    else:
                        st.info("No photos or videos available in this room")
    
                with col2:
                    # Room info editor
                    st.markdown("### Room Info")
                    info_content = get_room_info(room)
                    new_content = st.text_area(
                        "Edit description:",
                        value=info_content,
                        height=200,
                        key=f"info_edit_{room}"
                    )
                    if st.button("💾 Save Info", key=f"save_{room}"):
                        if update_room_info(room, new_content):
                            st.success("Info updated!")
                        else:
                            st.error("Update failed")
    
                    # File uploader with state management
                    st.markdown("### Upload Media")
                    uploaded_file = st.file_uploader(
                        "Choose file",
                        type=['jpg', 'jpeg', 'png', 'gif', 'mp4'],
                        key=f"upload_{room}_{st.session_state.upload_counter}"
                    )
                    
                    if uploaded_file:
                        if upload_room_file(room, uploaded_file, uploaded_file.type):
                            st.success("Upload successful!")
                            # Increment counter to reset uploader
                            st.session_state.upload_counter += 1
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Upload failed")
                
                        
    with tab3:
        st.header("🗂 Manage Files")
        search_term = st.text_input("Search rooms by name", key="manage_search").lower()
        
        # Get all rooms
        all_rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
        filtered_rooms = [room for room in all_rooms if search_term in room.lower()]
        
        if not filtered_rooms:
            st.info("No rooms found matching your search")
            return
    
        for room in filtered_rooms:
            with st.expander(f"Room: **{room}**", expanded=False):
                # File management section
                files = get_github_files(f"{BASE_PATH}/{room}")
                files = [f for f in files if f['type'] == 'file' and f['name'] != 'info.txt']
                
                if not files:
                    st.info("No files to manage in this room")
                else:
                    st.subheader(f"Files in {room}")
                    
                    for file in files:
                        col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
                        with col1:
                            # File preview
                            file_ext = file['name'].split('.')[-1].lower()
                            if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
                                st.image(file['download_url'], width=100)
                            elif file_ext in ['mp4']:
                                st.video(file['download_url'])
                            else:
                                st.markdown(f"📄 `{file['name']}`")
                        
                        with col2:
                            st.markdown(f"**File:** `{file['name']}`")
                        
                        with col3:
                            # Rename functionality
                            new_name = st.text_input(
                                "New name",
                                value=file['name'],
                                key=f"rename_{room}_{file['name']}"
                            )
                        
                        with col4:
                            # Delete button
                            if st.button("🗑️ Delete", key=f"del_{room}_{file['name']}"):
                                if delete_file(file['path'], file['sha']):
                                    st.success("File deleted!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete file")
                            
                            # Rename button
                            if st.button("✏️ Rename", key=f"ren_{room}_{file['name']}"):
                                if new_name.strip() == file['name']:
                                    st.warning("Name unchanged")
                                elif not new_name.strip():
                                    st.error("Please enter a new name")
                                else:
                                    if rename_file(file['path'], new_name.strip()):
                                        st.success("File renamed!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to rename file")
    
                # Carousel preview at the bottom
                st.markdown("---")
                st.subheader("Current Media Preview")
                media_files = get_github_files(f"{BASE_PATH}/{room}")
                media_files = [f for f in media_files if f['name'] != 'info.txt']
                
                if media_files:
                    carousel_items = ""
                    for file in media_files:
                        ext = file['name'].split('.')[-1].lower()
                        if ext == "mp4":
                            media_html = f"""
                                <video controls style="max-height: 400px; width: 100%;">
                                    <source src="{file['download_url']}" type="video/mp4">
                                </video>
                            """
                        else:
                            media_html = (
                                f'<div class="swiper-zoom-container">'
                                f'<img src="{file["download_url"]}" '
                                f'style="max-height: 400px; width: 100%; object-fit: contain;" />'
                                f'</div>'
                            )
                        carousel_items += f'<div class="swiper-slide">{media_html}</div>'
    
                    carousel_html = f"""
                    <link rel="stylesheet" href="https://unpkg.com/swiper@8.0.7/swiper-bundle.min.css">
                    <style>
                        .swiper {{
                            width: 100%;
                            height: auto;
                        }}
                        .swiper-slide {{
                            text-align: center;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                        }}
                        .swiper-slide img, .swiper-slide video {{
                            max-height: 400px;
                            width: 100%;
                            border-radius: 10px;
                            box-shadow: 0px 5px 15px rgba(0,0,0,0.2);
                            object-fit: contain;
                        }}
                        .swiper-pagination-fraction {{
                            font-size: 18px;
                            font-weight: bold;
                            color: white;
                            text-shadow: 0 0 5px rgba(0,0,0,0.5);
                        }}
                        .swiper-button-next,
                        .swiper-button-prev {{
                            width: 30px;
                            height: 30px;
                            background-color: rgba(0, 0, 0, 0.4);
                            border-radius: 50%;
                        }}
                        .swiper-button-next:after,
                        .swiper-button-prev:after {{
                            font-size: 20px;
                            color: white;
                        }}
                    </style>
                    <div class="swiper mySwiper">
                        <div class="swiper-wrapper">
                            {carousel_items}
                        </div>
                        <div class="swiper-pagination"></div>
                        <div class="swiper-button-next"></div>
                        <div class="swiper-button-prev"></div>
                    </div>
                    <script src="https://unpkg.com/swiper@8.0.7/swiper-bundle.min.js"></script>
                    <script>
                        var swiper = new Swiper('.mySwiper', {{
                            loop: true,
                            zoom: true,
                            pagination: {{
                                el: '.swiper-pagination',
                                type: 'fraction',
                            }},
                            navigation: {{
                                nextEl: '.swiper-button-next',
                                prevEl: '.swiper-button-prev',
                            }},
                        }});
                    </script>
                    """
                    components.html(carousel_html, height=500)
                else:
                    st.info("No media files available in this room")
        


    with tab4:
        st.header("🚮 Delete/Rename Rooms")
        search_term = st.text_input("Search rooms by name", key="delete_search").lower()
        
        all_rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
        filtered_rooms = [room for room in all_rooms if search_term in room.lower()]
        
        if not filtered_rooms:
            st.info("No rooms found matching your search")
            return

        for room in filtered_rooms:
            with st.expander(f"Room: **{room}**", expanded=False):
                col1, col2 = st.columns([4, 2])
                with col1:
                    # Rename section
                    new_name = st.text_input(
                        "New room name",
                        value=room,
                        key=f"rename_{room}"
                    )
                    if st.button("✏️ Rename Room", key=f"ren_btn_{room}"):
                        st.error("Rename not available do it manually")
                        '''if new_name.strip() == room:
                            st.warning("Name unchanged")
                        elif not new_name.strip():
                            st.error("Please enter a new name")
                        else:
                            success, message = rename_room(room, new_name.strip())
                            if success:
                                st.success(f"Renamed to {new_name}!")
                                st.rerun()
                            else:
                                st.error(f"Rename failed: {message}")'''
                
                with col2:
                    # Delete section
                    if st.button("🗑️ Delete Room", key=f"del_{room}"):
                        if delete_room(room):
                            st.success("Room deleted!")
                            st.rerun()
                        else:
                            st.error("Delete failed")

               
                files = get_github_files(f"{BASE_PATH}/{room}")
                media_files = [f for f in files if f['name'] != 'info.txt']
                
                if media_files:
                    st.markdown(f"media files exists, {media_files}")
                    #Add your carousel implementation here
                else:
                    st.info("No media files in this room")



    
def default_page():
    #st.header("🔍 Room")
    st.markdown("""
    <h1>
    🔍 Room <span style="color: green;font-size: 15px;">[MITM]</span>
    </h1>
    """, unsafe_allow_html=True)

    # Fetch room names from GitHub (only directories)
    rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']

    #selected_room = st.selectbox("Select from below dropdown menu", rooms)
    
    search_term = st.text_input("**Search Room**", "",placeholder="example., 415B").lower()
    filtered_rooms = [room for room in rooms if search_term in room.lower()]

    if search_term == st.secrets["general"]["password"]:
        st.session_state.page = "Admin Page"
        st.success("Password correct! Redirecting to Admin Page...")
        st.rerun()

    

    if not filtered_rooms:
        if search_term == "":
            st.error("enter room number to find..!")
        else:
            st.error(f"No rooms found with the search {search_term}..!")
        return
    


    if filtered_rooms or selected_room:
        st.write("***Select Room***")
        selected_room = st.radio("Select from below dropdown menu", filtered_rooms)  
        st.subheader(f"Room : {selected_room}")

        # Display room info from info.txt
        info_content = get_room_info(selected_room)
        st.markdown(f"*Room Info/Location:*\n\n <b>{info_content}</b>",unsafe_allow_html = True)

        # Fetch media files for the selected room (ignoring info.txt)
        files = get_github_files(f"{BASE_PATH}/{selected_room}")
        media_files = [f for f in files if f['name'] != 'info.txt']



        if media_files:
            st.markdown("### Photos")

            # Build carousel items. Wrap images in a zoom container for pinch-to-zoom.
            carousel_items = ""
            for file in media_files:
                ext = file['name'].split('.')[-1].lower()
                if ext == "mp4":
                    media_html = f"""
                        <video controls style="max-height: 400px; width: 100%;">
                            <source src="{file['download_url']}" type="video/mp4">
                        </video>
                    """
                else:
                    media_html = (
                        f'<div class="swiper-zoom-container">'
                        f'<img src="{file["download_url"]}" '
                        f'style="max-height: 400px; width: 100%; object-fit: contain;" />'
                        f'</div>'
                    )
                carousel_items += f'<div class="swiper-slide">{media_html}</div>'

            # Combine CSS, HTML, and JS (with zoom and custom navigation) in one block.
            carousel_html = f"""
            <link rel="stylesheet" href="https://unpkg.com/swiper@8.0.7/swiper-bundle.min.css">
            <style>
                .swiper {{
                    width: 100%;
                    height: auto;
                }}
                .swiper-slide {{
                    text-align: center;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                .swiper-slide img, .swiper-slide video {{
                    max-height: 400px;
                    width: 100%;
                    border-radius: 10px;
                    box-shadow: 0px 5px 15px rgba(0,0,0,0.2);
                    object-fit: contain;
                }}
                .swiper-pagination-fraction {{
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                    text-shadow: 0 0 5px rgba(0,0,0,0.5);
                }}
                /* Responsive adjustments for mobile screens */
                @media screen and (max-width: 600px) {{
                    .swiper-slide img, .swiper-slide video {{
                        max-height: 300px;
                        width: 100%;
                        object-fit: contain;
                    }}
                }}
                /* Custom navigation arrow styling */
                .swiper-button-next,
                .swiper-button-prev {{
                    width: 30px;
                    height: 30px;
                    background-color: rgba(0, 0, 0, 0.4);
                    border-radius: 50%;
                }}
                .swiper-button-next:after,
                .swiper-button-prev:after {{
                    font-size: 20px;
                    color: white;
                }}
            </style>
            <div class="swiper mySwiper">
                <div class="swiper-wrapper">
                    {carousel_items}
                </div>
                <div class="swiper-pagination"></div>
                <div class="swiper-button-next"></div>
                <div class="swiper-button-prev"></div>
            </div>
            <script src="https://unpkg.com/swiper@8.0.7/swiper-bundle.min.js"></script>
            <script>
                var swiper = new Swiper('.mySwiper', {{
                    loop: true,
                    zoom: true,  // Enable pinch-to-zoom support
                    pagination: {{
                        el: '.swiper-pagination',
                        type: 'fraction',
                    }},
                    navigation: {{
                        nextEl: '.swiper-button-next',
                        prevEl: '.swiper-button-prev',
                    }},
                }});
            </script>
            """

            # Render the carousel
            components.html(carousel_html, height=500)

           
# Main App
def main():
    if 'page' not in st.session_state:
        st.session_state.page = "Default Page"  # Set the default page on first load

    page = st.session_state.page

    if page == "Admin Page":
        admin_page()
    else:
        default_page()
        st.markdown("<hr style = 'border : 1px solid gray;'>", unsafe_allow_html = True)
        st.markdown("<hr style = 'border : 1px solid gray;'>", unsafe_allow_html = True)
        st.write("IA,SEE papers - first year 2023-24: [https://lnjmitmfirstyearpapers.streamlit.app/](https://lnjmitmfirstyearpapers.streamlit.app/)")
        st.write("Made to find Room during Test")
        st.write("Feedback/Contact: [Email](mailto:mitmfirstyearpaper@gmail.com)")


if __name__ == "__main__":
    main()
