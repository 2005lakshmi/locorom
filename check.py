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

# Helper functions
def get_github_files(path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []

def create_room_folder(room_name):
    folder_path = f"{BASE_PATH}/{room_name}"
    info_file_path = f"{folder_path}/info.txt"
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

def get_subfolders(room_name):
    contents = get_github_files(f"{BASE_PATH}/{room_name}")
    return [item['name'] for item in contents if item['type'] == 'dir']

def create_subfolder(room_name, sub_name, thumbnail_file, info_content):
    try:
        sub_path = f"{BASE_PATH}/{room_name}/{sub_name}"
        
        # Create thumbnail
        thumbnail_path = f"{sub_path}/thumbnail.jpg"
        content = base64.b64encode(thumbnail_file.getvalue()).decode()
        data = {
            "message": f"Create subfolder {sub_name} in {room_name}",
            "content": content
        }
        response = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{thumbnail_path}",
            json=data,
            headers=HEADERS
        )
        if response.status_code != 201:
            return False

        # Create info file
        info_path = f"{sub_path}/info.txt"
        encoded_info = base64.b64encode(info_content.encode()).decode()
        data_info = {
            "message": f"Add info for subfolder {sub_name}",
            "content": encoded_info
        }
        response_info = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{info_path}",
            json=data_info,
            headers=HEADERS
        )
        return response_info.status_code == 201
    except Exception as e:
        st.error(f"Error creating subfolder: {str(e)}")
        return False

def get_subfolder_info(room_name, subfolder):
    info_path = f"{BASE_PATH}/{room_name}/{subfolder}/info.txt"
    response = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{info_path}",
        headers=HEADERS
    )
    if response.status_code == 200:
        return base64.b64decode(response.json()['content']).decode()
    return ""

def update_subfolder_info(room_name, subfolder, content):
    info_path = f"{BASE_PATH}/{room_name}/{subfolder}/info.txt"
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

def delete_subfolder(subfolder_path):
    """Delete a subfolder and its contents recursively"""
    try:
        contents = get_github_files(subfolder_path)
        success = True
        for item in contents:
            if item['type'] == 'file':
                if not delete_file(item['path'], item['sha']):
                    success = False
            elif item['type'] == 'dir':
                if not delete_subfolder(f"{subfolder_path}/{item['name']}"):
                    success = False
        return success
    except Exception as e:
        st.error(f"Error deleting subfolder: {str(e)}")
        return False

def delete_room(room_name):
    """Delete a room and all its contents"""
    try:
        contents = get_github_files(f"{BASE_PATH}/{room_name}")
        success = True
        for item in contents:
            if item['type'] == 'file':
                if not delete_file(item['path'], item['sha']):
                    success = False
            elif item['type'] == 'dir':
                if not delete_subfolder(f"{BASE_PATH}/{room_name}/{item['name']}"):
                    success = False
        return success
    except Exception as e:
        st.error(f"Error deleting room: {str(e)}")
        return False
        
def get_next_file_number(room_name, subfolder=None):
    path = f"{BASE_PATH}/{room_name}" + (f"/{subfolder}" if subfolder else "")
    files = get_github_files(path)
    numbers = []
    for file in files:
        if file['name'] not in ['info.txt', 'thumbnail.jpg'] and file['type'] == 'file':
            try:
                numbers.append(int(Path(file['name']).stem))
            except ValueError:
                continue
    return max(numbers) + 1 if numbers else 1

def upload_room_file(room, uploaded_file, file_type, subfolder=None):
    """Upload file to room or subfolder"""
    try:
        ext = file_type.split('/')[-1].lower()
        if ext == 'jpeg':
            ext = 'jpg'
            
        base_path = f"{BASE_PATH}/{room}"
        if subfolder:
            base_path += f"/{subfolder}"
            
        # Get next file number with proper list comprehension
        files = get_github_files(base_path)
        numbers = [
            int(Path(f['name']).stem)  # Convert filename stem to integer
            for f in files
            if (
                f['type'] == 'file' 
                and Path(f['name']).stem.isdigit()  # Verify numeric filename
            )
        ]
        next_num = max(numbers) + 1 if numbers else 1

        file_path = f"{base_path}/{next_num}.{ext}"
        content = base64.b64encode(uploaded_file.read()).decode()
        
        data = {
            "message": f"Add file {next_num}.{ext} to {base_path}",
            "content": content
        }
        
        response = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}",
            json=data,
            headers=HEADERS
        )
        return response.status_code == 201
        
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return False

        
def get_room_info(room_name):
    """Get room information from info.txt"""
    info_path = f"{BASE_PATH}/{room_name}/info.txt"
    try:
        response = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{info_path}",
            headers=HEADERS
        )
        if response.status_code == 200:
            content = base64.b64decode(response.json()['content']).decode()
            return content
        return "No information available"
    except Exception as e:
        st.error(f"Error fetching room info: {str(e)}")
        return "Information unavailable"

def delete_file(file_path, sha):
    """Delete a file from GitHub repository"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
        data = {
            "message": f"Delete file {Path(file_path).name}",
            "sha": sha
        }
        response = requests.delete(url, json=data, headers=HEADERS)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Delete failed: {str(e)}")
        return False



def display_main_content(room_name):
    """Display main content for a room with subfolders"""
    # Get room info
    info_content = get_room_info(room_name)
    
    # Main Area Section
    #st.markdown("### From Point:")
    main_files = get_github_files(f"{BASE_PATH}/{room_name}")
    
    # Filter out info.txt and include only media files
    main_media = [f for f in main_files 
                 if f['name'] != 'info.txt' 
                 and f['name'].split('.')[-1].lower() in ['jpg', 'jpeg', 'png', 'gif', 'mp4']]
    
    # Show thumbnail and info in row
    if main_media:
        st.markdown("<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 3])
        with col1:
            first_file = main_media[0]
            st.image(first_file['download_url'], width=200)
        with col2:
            st.markdown("<h5 style='color:#0D92F4;'>Location Info :</h5>", unsafe_allow_html=True)

            st.markdown(f"###### {info_content}")
            
        # Main Area Carousel
        st.markdown("##### Photos ")
        st.write("Path through Photos")
        display_carousel(main_media, zoom=True)
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)

    #else:
    #   st.info("No media available in main area")

    # Subfolders Section
    subfolders = get_subfolders(room_name)
    for sub in subfolders:
        st.markdown("<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)

        sub_path = f"{BASE_PATH}/{room_name}/{sub}"
        sub_files = get_github_files(sub_path)
        
        # Filter subfolder files
        sub_media = [f for f in sub_files 
                    if f['name'] not in ['info.txt', 'thumbnail.jpg'] 
                    and f['name'].split('.')[-1].lower() in ['jpg', 'jpeg', 'png', 'gif', 'mp4']]
        
        # Subfolder thumbnail and info
        col1, col2 = st.columns([2, 3])
        with col1:
            thumbnail_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{sub_path}/thumbnail.jpg"
            st.image(thumbnail_url, width=200)
            

        with col2:
            sub_info = get_subfolder_info(room_name, sub)
            st.markdown("<h5 style='color:#0D92F4;'>Location Info :</h5>", unsafe_allow_html=True)
            st.markdown(f"###### {sub_info}")
        
        # Subfolder media carousel
        if sub_media:
            st.markdown("##### Photos")
            display_carousel(sub_media, zoom=True)
        else:
            st.info(f"No media available in {sub}")
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)


def display_carousel(files, zoom=False):
    """Display media files in a carousel with zoom capability"""
    carousel_items = ""
    for file in files:
        ext = file['name'].split('.')[-1].lower()
        if ext == "mp4":
            media_html = f"""
                <video controls style="max-height: 400px; width: 100%;">
                    <source src="{file['download_url']}" type="video/mp4">
                </video>
            """
        else:
            zoom_class = "swiper-zoom-container" if zoom else ""
            media_html = f'''
            <div class="{zoom_class}">
                <img src="{file['download_url']}" 
                     style="max-height: 400px; width: 100%; object-fit: contain;">
            </div>
            '''
        carousel_items += f'<div class="swiper-slide">{media_html}</div>'

    carousel_html = f"""
    <link rel="stylesheet" href="https://unpkg.com/swiper@8/swiper-bundle.min.css">
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
        .swiper-zoom-container {{
            cursor: zoom-in;
        }}
        .swiper-slide-zoomed .swiper-zoom-container {{
            cursor: move;
        }}
        @media screen and (max-width: 600px) {{
            .swiper-slide img, .swiper-slide video {{
                max-height: 300px;
            }}
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
    
    <script src="https://unpkg.com/swiper@8/swiper-bundle.min.js"></script>
    <script>
        const swiper = new Swiper('.mySwiper', {{
            loop: true,
            zoom: {'true' if zoom else 'false'},
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



def display_subfolder_content(room_name, subfolder):
    info = get_subfolder_info(room_name, subfolder)
    st.markdown(f"### {subfolder}")
    st.markdown(f"*Location Details:*\n\n{info}")
    
    path = f"{BASE_PATH}/{room_name}/{subfolder}"
    files = get_github_files(path)
    media_files = [f for f in files if f['name'] not in ['info.txt', 'thumbnail.jpg']]
    
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
                media_html = f'<img src="{file["download_url"]}" style="max-height: 400px; width: 100%; object-fit: contain;">'
            carousel_items += f'<div class="swiper-slide">{media_html}</div>'

        components.html(f"""
        <link rel="stylesheet" href="https://unpkg.com/swiper@8/swiper-bundle.min.css">
        <div class="swiper">
            <div class="swiper-wrapper">
                {carousel_items}
            </div>
        </div>
        <script src="https://unpkg.com/swiper@8/swiper-bundle.min.js"></script>
        """, height=500)
    else:
        st.info("No media files available for this access point")



def display_subfolder_content(room, subfolder):
    st.markdown(f"### {subfolder}")
    info = get_subfolder_info(room, subfolder)
    st.markdown(f"*Location Details:*\n\n{info}")
    
    path = f"{BASE_PATH}/{room}/{subfolder}"
    files = get_github_files(path)
    media_files = [f for f in files if f['name'] not in ['info.txt', 'thumbnail.jpg']]
    
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
                media_html = f'<img src="{file["download_url"]}" style="max-height: 400px; width: 100%; object-fit: contain;">'
            carousel_items += f'<div class="swiper-slide">{media_html}</div>'

        components.html(f"""
        <!-- Swiper carousel implementation -->
        {carousel_items}
        """, height=500)
    else:
        st.info("No media files available for this access point")


def rename_file(old_path, new_name):
    """Rename a file in the GitHub repository"""
    try:
        # Validate inputs
        if not old_path or not new_name:
            st.error("Invalid file paths provided")
            return False

        # Get file details from GitHub
        file_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{old_path}"
        response = requests.get(file_url, headers=HEADERS)
        
        if response.status_code != 200:
            st.error(f"Failed to fetch file details (HTTP {response.status_code})")
            return False

        file_data = response.json()
        
        # Validate required fields
        required_keys = ['sha', 'content', 'download_url', 'path']
        if not all(key in file_data for key in required_keys):
            st.error("Missing required file metadata from GitHub")
            return False

        # Get file content
        file_content = file_data['content']
        if not file_content:
            # Fallback to direct download
            download_response = requests.get(file_data['download_url'])
            if download_response.status_code == 200:
                file_content = base64.b64encode(download_response.content).decode()
            else:
                st.error("Failed to retrieve file content")
                return False

        # Construct new path
        new_path = str(Path(old_path).parent / new_name)
        
        # Check if new path already exists
        existing_files = get_github_files(str(Path(new_path).parent))
        if any(f['name'] == new_name for f in existing_files):
            st.error("A file with this name already exists")
            return False

        # Create new file
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

        # Delete old file
        delete_response = requests.delete(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{old_path}",
            headers=HEADERS,
            json={
                "message": f"Delete original file after rename",
                "sha": file_data['sha'],
                "branch": "main"
            }
        )

        if delete_response.status_code != 200:
            # Rollback creation
            requests.delete(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/{new_path}",
                headers=HEADERS,
                json={
                    "message": "Rollback failed rename",
                    "sha": create_response.json()['content']['sha']
                }
            )
            st.error("Failed to complete rename operation - rolled back changes")
            return False

        return True

    except Exception as e:
        st.error(f"Error during renaming: {str(e)}")
        return False

def update_subfolder_thumbnail(room_name, subfolder_name, new_thumbnail):
    """Replace existing thumbnail in a subfolder"""
    try:
        # Define thumbnail path
        thumbnail_path = f"{BASE_PATH}/{room_name}/{subfolder_name}/thumbnail.jpg"
        
        # Delete existing thumbnail if exists
        existing_thumb = get_github_files(f"{BASE_PATH}/{room_name}/{subfolder_name}")
        for item in existing_thumb:
            if item['name'].lower() == "thumbnail.jpg":
                if not delete_file(item['path'], item['sha']):
                    return False
        
        # Upload new thumbnail
        content = base64.b64encode(new_thumbnail.read()).decode()
        data = {
            "message": f"Update thumbnail for {subfolder_name}",
            "content": content
        }
        response = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{thumbnail_path}",
            headers=HEADERS,
            json=data
        )
        
        return response.status_code == 201
        
    except Exception as e:
        st.error(f"Thumbnail update error: {str(e)}")
        return False




# Admin Page
def admin_page():
    st.title("Admin Panel")
    tab1, tab2, tab3, tab4, tab5 , tab6= st.tabs(["Create Room", "Add Content", "Manage Subfolders", "Manage Files", "🚮 Delete Rooms","📷 Change Subfolder Thumbnail"])


    # Create Room Tab (Tab1)
    with tab1:
        with st.form(key="create_room_form"):
            room_name = st.text_input("Room Name", key="room_name_input")
            submit_button = st.form_submit_button("Create Room")
            if submit_button:
                existing_rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
                if room_name in existing_rooms:
                    st.error("Room already exists")
                else:
                    if create_room_folder(room_name):
                        st.success(f"Room **{room_name}** created successfully!")
                    else:
                        st.error("Failed to create room")

                        
    if 'upload_counter' not in st.session_state:
        st.session_state.upload_counter = 0
    
    with tab2:
        st.header("📤 Add Content")
        search_term = st.text_input("Search rooms by name", key="content_search").lower()
        
        all_rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
        filtered_rooms = [room for room in all_rooms if search_term in room.lower()]
        
        if not filtered_rooms:
            st.info("No rooms found matching your search")
            return

        for room in filtered_rooms:
            with st.expander(f"Room: **{room}**", expanded=False):
                subfolders = get_subfolders(room)
                selected_sub = st.selectbox(
                    "Select Subfolder", 
                    ["Main"] + subfolders,
                    key=f"sub_{room}"
                )
                
                uploaded_file = st.file_uploader(
                    "Choose file",
                    type=['jpg', 'jpeg', 'png', 'gif', 'mp4'],
                    key=f"upload_{room}_{st.session_state.upload_counter}"
                )
                
                if uploaded_file:
                    success = upload_room_file(
                        room=room,
                        uploaded_file=uploaded_file,
                        file_type=uploaded_file.type,
                        subfolder=selected_sub if selected_sub != "Main" else None
                    )
                    if success:
                        st.success("file uploaded")
                        # Safe counter increment
                        st.session_state.upload_counter += 1
                        st.rerun()


    with tab3:
        st.header("📂 Manage Subfolders")
        room = st.selectbox("Select Room", [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir'])
        
        with st.form(key=f"create_subfolder_{room}"):
            st.subheader("Create New Access Point")
            col1, col2 = st.columns(2)
            with col1:
                sub_name = st.text_input("Access Point Name")
                thumbnail = st.file_uploader("Thumbnail Image", type=['jpg', 'jpeg', 'png'])
            with col2:
                sub_info = st.text_area("Access Point Information", height=200)
            if st.form_submit_button("Create Access Point"):
                if sub_name and thumbnail and sub_info:
                    if create_subfolder(room, sub_name, thumbnail, sub_info):
                        st.success("Access point created!")
                        st.rerun()
                    else:
                        st.error("Creation failed")
                else:
                    st.warning("Please fill all fields")

        st.subheader("Existing Access Points")
        subfolders = get_subfolders(room)
        for sub in subfolders:
            with st.expander(f"Access Point: {sub}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    thumbnail_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{BASE_PATH}/{room}/{sub}/thumbnail.jpg"
                    st.image(thumbnail_url, width=200)
                    current_info = get_subfolder_info(room, sub)
                    new_info = st.text_area("Edit information", value=current_info, key=f"info_{sub}")
                    if st.button(f"Update Info for {sub}"):
                        if update_subfolder_info(room, sub, new_info):
                            st.success("Info updated!")
                        else:
                            st.error("Update failed")
                with col2:
                    if st.button(f"🗑️ Delete {sub}", key=f"del_{sub}"):
                        if delete_subfolder(room, sub):
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error("Deletion failed")

    # Remaining tabs (Manage Files, Delete Rooms) remain similar to previous implementation




    with tab4:
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
                # Add subfolder selection
                subfolders = get_subfolders(room)
                selected_sub = st.selectbox(
                    "Select Location",
                    ["Main Area"] + subfolders,
                    key=f"sub_select_{room}"
                )
                
                # Determine the path
                path = f"{BASE_PATH}/{room}"
                if selected_sub != "Main Area":
                    path += f"/{selected_sub}"
                
                # File management section
                files = get_github_files(path)
                files = [f for f in files if f['type'] == 'file' and f['name'] not in ['info.txt', 'thumbnail.jpg']]
                
                if not files:
                    st.info("No files to manage in this location")
                else:
                    st.subheader(f"Files in {selected_sub}")
                    
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
    
                # Carousel preview
                st.markdown("---")
                st.subheader("Current Media Preview")
                if files:
                    display_carousel(files)
                else:
                    st.info("No media files available in this location")
                
    # Delete Rooms Tab (Tab5)
    with tab5:
        st.header("🚮 Delete Content")
        search_term = st.text_input("Search rooms by name", key="delete_search").lower()
        
        all_rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
        filtered_rooms = [room for room in all_rooms if search_term in room.lower()]
        
        if not filtered_rooms:
            st.info("No rooms found matching your search")
           
    
        for room in filtered_rooms:
            with st.expander(f"Room: **{room}**", expanded=False):
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.subheader("Delete Subfolder")
                    subfolders = get_subfolders(room)
                    if subfolders:
                        selected_sub = st.selectbox(
                            "Select subfolder to delete",
                            subfolders,
                            key=f"sub_del_{room}"
                        )
                        if st.button(f"🗑️ Delete Subfolder", key=f"sub_del_btn_{room}"):
                            if delete_subfolder(f"{BASE_PATH}/{room}/{selected_sub}"):
                                st.success(f"Subfolder '{selected_sub}' deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete subfolder")
                    else:
                        st.info("No subfolders in this room")
    
                with col2:
                    st.subheader("Delete Entire Room")
                    if st.button("⚠️ Delete Entire Room", key=f"room_del_{room}"):
                        if delete_room(room):
                            st.success("Room deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete room")
    
        
    with tab6:
        st.header("📷 Change Subfolder Thumbnail")
        
        # Room selection
        rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
        selected_room = st.selectbox("Select Room", rooms, key="thumb_room_select")
        
        if selected_room:
            # Subfolder selection with thumbnail preview
            subfolders = get_subfolders(selected_room)
            if not subfolders:
                st.info("This room has no subfolders")
                return
            
            # Create columns for dropdown and preview
            col1, col2 = st.columns([3, 2])
            
            with col1:
                selected_sub = st.selectbox("Select Subfolder", subfolders, key="thumb_sub_select")
            
            with col2:
                # Display current thumbnail
                thumbnail_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{BASE_PATH}/{selected_room}/{selected_sub}/thumbnail.jpg"
                st.image(thumbnail_url, 
                        width=150,  # Set fixed small size
                        caption="Current Thumbnail",
                        use_column_width=False)
            
            # Thumbnail upload section
            new_thumbnail = st.file_uploader("Upload New Thumbnail", 
                                           type=['jpg', 'jpeg', 'png'], 
                                           key="thumb_upload")
            
            # Preview new thumbnail before upload
            if new_thumbnail:
                st.image(new_thumbnail, 
                        width=150,
                        caption="New Thumbnail Preview",
                        use_column_width=False)
                
                if st.button("Update Thumbnail", key="thumb_update_btn"):
                    if update_subfolder_thumbnail(selected_room, selected_sub, new_thumbnail):
                        st.success("Thumbnail updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update thumbnail")







def default_page():
    #st.markdown("""<h1>🔍 Room <span style="color: green;font-size: 15px;">[MITM]</span></h1>""", unsafe_allow_html=True)
    st.markdown("""
    <style>
        .header-container {
            display: flex;
            align-items: center;
            justify-content: center; /* Center the whole header */
        }
        .room-title {
            font-size: 24px;
            font-weight: bold;
            margin-right: 8px; /* Small space between text and logo */
        }
        .room-code {
            color: green;
            font-size: 15px;
        }
        .logo img {
            width: 24px;  /* Match header text size */
            height: auto;
        }
    </style>

    <div class="header-container">
        <h1 class="room-title">🔍 Room <span class="room-code">[MITM]</span></h1>
        <img class="logo" src="https://raw.githubusercontent.com/2005lakshmi/locorom/main/logo_locorom.png" alt="Logo">
    </div>
    """, unsafe_allow_html=True)



    
    st.markdown("<hr style='border: 1px solid gray; margin: 5px 0;'>", unsafe_allow_html=True)

    # Search for rooms
    search_term = st.text_input("**Search Room**", "", placeholder="example., 415B").strip().lower()
    
    # Check for admin password
    if search_term == st.secrets["general"]["password"]:
        st.session_state.page = "Admin Page"
        st.rerun()
        return

    # Get filtered rooms
    rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
    filtered_rooms = [room for room in rooms if search_term in room.lower()]

    if not filtered_rooms:
        st.error("No rooms found" if search_term else "Please enter room number to search..!")
        return

    # Select room
    selected_room = st.radio("Select Room", filtered_rooms)
    st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)

    st.header(f"Room: :red[{selected_room}]")

    # Display main content
    display_main_content(selected_room)
        

# Main app execution
def main():
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "Default Page"

    # Check current page state
    if st.session_state.page == "Admin Page":
        admin_page()
    else:
        default_page()
        # Footer content



if __name__ == "__main__":
    main()
