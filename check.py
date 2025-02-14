import os
import base64
import requests
import streamlit as st
from pathlib import Path
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
                
                existing_rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
            
                if room_name in existing_rooms:
                    st.error("Room already exists")
                else:
                    if create_room_folder(room_name):
                        st.success("Room created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create room")


    with tab2:
        rooms = [item['name'] for item in get_github_files(BASE_PATH) if item['type'] == 'dir']
        selected_room = st.selectbox("Select Room", rooms)

        if selected_room:
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

        if selected_room:
        
            files = get_github_files(f"{BASE_PATH}/{selected_room}")
            files = [f for f in files if f['type'] == 'file' and f['name'] != 'info.txt']
            
            if not files:
                st.info("No files to manage in this room")
                return
                
            st.subheader("Manage Files in Selected Room")

            for file in files:
                col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 3])  # Added an extra column for preview
                with col1:
                    # Display file preview
                    file_ext = file['name'].split('.')[-1].lower()
                    if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
                        st.image(file['download_url'], width=100)
                    elif file_ext in ['mp4']:
                        st.video(file['download_url'])
                    else:
                        st.markdown(f"📄 `{file['name']}`")  # Display generic file icon for unknown file types
                
                with col2:
                    st.markdown(f"**File:** `{file['name']}`")
                with col3:
                    new_name = st.text_input(
                        "New name", 
                        value=file['name'],
                        key=f"rename_{file['name']}"
                    )
                with col4:
                    if st.button("🗑️ Delete", key=f"del_{file['name']}"):
                        if delete_file(file['path'], file['sha']):
                            st.success("File deleted!")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to delete file")
                with col5:
                    if st.button("✏️ Rename", key=f"ren_{file['name']}"):
                        if new_name == file['name']:
                            st.warning("Name unchanged")
                        elif not new_name:
                            st.error("Please enter a new name")
                        else:
                            # Check for duplicate names before renaming
                            current_names = [f['name'] for f in files]
                            if new_name in current_names:
                                st.error(f"A file with the name '{new_name}' already exists!")
                            else:
                                if rename_file(file['path'], new_name, file['sha']):
                                    st.success("File renamed!")
                                    st.experimental_rerun()
                                else:
                                    st.error("Failed to rename file")


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
        st.write("Feedback/Contact: [Email](mailto:mitmfirstyearpaper@gmail.com) / [WhatsApp](https://wa.me/9964924820)")


if __name__ == "__main__":
    main()
