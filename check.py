import os
import streamlit as st
from pathlib import Path
import time
import streamlit.components.v1 as components
import string
import shutil

# ✅ LOCAL CONFIG — NO GITHUB API NEEDED
LOCAL_REPO_PATH = Path("./locorom")  # Adjust if needed
BASE_PATH = "Rooms"

# ✅ Auto-create repo structure if missing
def ensure_local_structure():
    (LOCAL_REPO_PATH / BASE_PATH).mkdir(parents=True, exist_ok=True)

ensure_local_structure()

# ✅ LOCAL FILESYSTEM HELPER FUNCTIONS — NO GITHUB API

def get_local_files_in_path(relative_path):
    """List files and dirs in a local path (relative to LOCAL_REPO_PATH)"""
    full_path = LOCAL_REPO_PATH / relative_path
    if not full_path.exists() or not full_path.is_dir():
        return []
    items = []
    for item in full_path.iterdir():
        items.append({
            "name": item.name,
            "path": str(item.relative_to(LOCAL_REPO_PATH)),
            "type": "dir" if item.is_dir() else "file",
        })
    return items

def get_all_rooms():
    """Get list of all room folder names under locorom/Rooms/"""
    rooms_path = LOCAL_REPO_PATH / BASE_PATH
    if not rooms_path.exists() or not rooms_path.is_dir():
        return []
    return [item.name for item in rooms_path.iterdir() if item.is_dir()]

def create_local_room_folder(room_name):
    """Create room folder with empty info.txt"""
    room_path = LOCAL_REPO_PATH / BASE_PATH / room_name
    try:
        room_path.mkdir(parents=True, exist_ok=True)
        (room_path / "info.txt").write_text("", encoding="utf-8")
        return True
    except Exception as e:
        st.error(f"Error creating room: {e}")
        return False

def get_local_subfolders(room_name):
    """Get list of subfolder names in a room"""
    room_path = LOCAL_REPO_PATH / BASE_PATH / room_name
    if not room_path.exists() or not room_path.is_dir():
        return []
    return [item.name for item in room_path.iterdir() if item.is_dir()]

def create_local_subfolder(room_name, sub_name, thumbnail_file, info_content):
    """Create subfolder with thumbnail.jpg and info.txt"""
    try:
        sub_path = LOCAL_REPO_PATH / BASE_PATH / room_name / sub_name
        sub_path.mkdir(parents=True, exist_ok=True)
        
        # Save thumbnail
        if thumbnail_file:
            thumbnail_path = sub_path / "thumbnail.jpg"
            with open(thumbnail_path, "wb") as f:
                f.write(thumbnail_file.getvalue())
        
        # Save info
        info_path = sub_path / "info.txt"
        info_path.write_text(info_content, encoding="utf-8")
        
        return True
    except Exception as e:
        st.error(f"Error creating subfolder: {e}")
        return False

def get_subfolder_info(room_name, subfolder):
    """Get info.txt content from a subfolder inside a room (local filesystem version)"""
    info_file_path = LOCAL_REPO_PATH / BASE_PATH / room_name / subfolder / "info.txt"
    if info_file_path.exists() and info_file_path.is_file():
        return info_file_path.read_text(encoding="utf-8").strip()
    return ""

def update_local_subfolder_info(room_name, subfolder, content):
    """Update info.txt in subfolder"""
    info_file_path = LOCAL_REPO_PATH / BASE_PATH / room_name / subfolder / "info.txt"
    try:
        info_file_path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        st.error(f"Error updating info: {e}")
        return False

def delete_local_path(relative_path):
    """Delete folder or file recursively"""
    full_path = LOCAL_REPO_PATH / relative_path
    try:
        if full_path.is_file():
            full_path.unlink()
        elif full_path.is_dir():
            shutil.rmtree(full_path)
        return True
    except Exception as e:
        st.error(f"Error deleting {relative_path}: {e}")
        return False

def next_alphabetical_filename_local(existing_files):
    """Find next available alphabetical filename (a, b, ..., z, aa, ab, ...)"""
    existing_names = [
        f.stem  # stem = filename without extension
        for f in existing_files
        if f.is_file() and f.name not in ['info.txt', 'thumbnail.jpg']
        and all(c in string.ascii_lowercase for c in f.stem)
    ]
    existing_names = sorted(existing_names)
    if not existing_names:
        return 'a'
    last_name = existing_names[-1]
    if last_name == 'z':
        return 'aa'
    elif len(last_name) > 1 and all(c == 'z' for c in last_name):
        return 'a' * (len(last_name) + 1)
    else:
        last_char_list = list(last_name)
        for i in range(len(last_char_list)-1, -1, -1):
            if last_char_list[i] != 'z':
                last_char_list[i] = chr(ord(last_char_list[i]) + 1)
                for j in range(i+1, len(last_char_list)):
                    last_char_list[j] = 'a'
                return ''.join(last_char_list)
            last_char_list[i] = 'a'
        return 'a' * (len(last_char_list) + 1)

def upload_local_room_file(room, uploaded_file, file_type, subfolder=None):
    """Upload file to room or subfolder with alphabetical filenames"""
    try:
        ext = file_type.split('/')[-1].lower()
        if ext == 'jpeg':
            ext = 'jpg'
        
        base_path = LOCAL_REPO_PATH / BASE_PATH / room
        if subfolder:
            base_path = base_path / subfolder
        
        # Get next available alphabetical filename
        existing_files = [
            item for item in base_path.iterdir()
            if item.is_file() and item.name not in ['info.txt', 'thumbnail.jpg']
        ]
        next_filename = next_alphabetical_filename_local(existing_files)
        file_path = base_path / f"{next_filename}.{ext}"
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        return True
    except Exception as e:
        st.error(f"Upload error: {e}")
        return False

def get_room_info(room_name):
    """Get room information from info.txt (local filesystem version)"""
    if not room_name:
        return "Room name not specified"
    info_file_path = LOCAL_REPO_PATH / BASE_PATH / room_name / "info.txt"
    if info_file_path.exists() and info_file_path.is_file():
        return info_file_path.read_text(encoding="utf-8").strip()
    return "No information available"

def rename_local_file(old_relative_path, new_name):
    """Rename a local file"""
    try:
        old_path = LOCAL_REPO_PATH / old_relative_path
        if not old_path.exists():
            st.error("File not found")
            return False
        new_path = old_path.parent / new_name
        if new_path.exists():
            st.error("A file with this name already exists")
            return False
        old_path.rename(new_path)
        return True
    except Exception as e:
        st.error(f"Error during renaming: {e}")
        return False

def update_local_subfolder_thumbnail(room_name, subfolder_name, new_thumbnail):
    """Replace thumbnail.jpg in subfolder"""
    try:
        thumbnail_path = LOCAL_REPO_PATH / BASE_PATH / room_name / subfolder_name / "thumbnail.jpg"
        # Write new thumbnail
        with open(thumbnail_path, "wb") as f:
            f.write(new_thumbnail.getvalue())
        return True
    except Exception as e:
        st.error(f"Thumbnail update error: {e}")
        return False

# ✅ DISPLAY FUNCTIONS (Updated to use local paths)

def display_main_content(room_name):
    """Display main content for a room with subfolders"""
    if not room_name:
        st.warning("No room selected.")
        return

    # Get room info
    info_content = get_room_info(room_name)
    
    # Main Area Section
    main_files = get_local_files_in_path(f"{BASE_PATH}/{room_name}")
    
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
            img_path = LOCAL_REPO_PATH / first_file['path']
            if img_path.exists():
                st.image(str(img_path), width=200)
        with col2:
            st.markdown("<h5 style='color:#0D92F4;'>Location Info :</h5>", unsafe_allow_html=True)
            st.markdown(f"###### {info_content}")
        
        # Main Area Carousel
        st.markdown("##### Photos ")
        st.write("Path through Photos")
        display_carousel(main_media, zoom=True)
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)

    # Subfolders Section
    subfolders = get_local_subfolders(room_name)
    for sub in subfolders:
        st.markdown("<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)
        sub_path = f"{BASE_PATH}/{room_name}/{sub}"
        sub_files = get_local_files_in_path(sub_path)
        
        # Filter subfolder files
        sub_media = [f for f in sub_files 
                    if f['name'] not in ['info.txt', 'thumbnail.jpg'] 
                    and f['name'].split('.')[-1].lower() in ['jpg', 'jpeg', 'png', 'gif', 'mp4']]

        # Subfolder thumbnail and info
        col1, col2 = st.columns([2, 3])
        with col1:
            thumbnail_path = LOCAL_REPO_PATH / BASE_PATH / room_name / sub / "thumbnail.jpg"
            if thumbnail_path.exists():
                st.image(str(thumbnail_path), width=200)
            else:
                st.image("https://via.placeholder.com/200?text=No+Thumbnail", width=200)
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
    """Display media files in a carousel with zoom capability (using local paths)"""
    carousel_items = ""
    for file in files:
        ext = file['name'].split('.')[-1].lower()
        file_path = LOCAL_REPO_PATH / file['path']
        if not file_path.exists():
            continue
        if ext == "mp4":
            # For video, we can't embed local file directly in Swiper — fallback to st.video
            # But for now, we'll use a placeholder or skip in carousel
            media_html = f"""
                <div style="background:#000; color:#fff; padding:50px; text-align:center;">
                    Video: {file['name']}<br>
                    <small>Click to view below</small>
                </div>
            """
        else:
            # Use file:// protocol doesn't work in browsers — so we serve via Streamlit's static
            # Instead, we'll generate a data URL or just use st.image outside carousel
            # For simplicity, we show placeholder
            media_html = f'''
            <img src="https://via.placeholder.com/400x300?text={file['name']}" 
                 style="max-height: 400px; width: 100%; object-fit: contain; border-radius:10px;">
            '''
        carousel_items += f'<div class="swiper-slide">{media_html}</div>'

    # Note: Swiper can't access local filesystem files directly from browser.
    # For production, consider serving files via Flask or use st.image/video in grid.
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
            background: #f5f5f5;
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

    # Fallback: Show actual media below carousel since Swiper can't load local files
    st.markdown("### Media Gallery (Actual Files)")
    cols = st.columns(3)
    for idx, file in enumerate(files):
        file_path = LOCAL_REPO_PATH / file['path']
        if not file_path.exists():
            continue
        ext = file['name'].split('.')[-1].lower()
        with cols[idx % 3]:
            if ext in ["mp4", "mov", "avi"]:
                st.video(str(file_path))
            else:
                st.image(str(file_path), caption=file['name'], use_column_width=True)

def display_subfolder_content(room, subfolder):
    st.markdown(f"### {subfolder}")
    info = get_subfolder_info(room, subfolder)
    st.markdown(f"*Location Details:*\n{info}")
    path = f"{BASE_PATH}/{room}/{subfolder}"
    files = get_local_files_in_path(path)
    media_files = [f for f in files if f['name'] not in ['info.txt', 'thumbnail.jpg']]
    if media_files:
        st.markdown("### Media Files")
        cols = st.columns(3)
        for idx, file in enumerate(media_files):
            file_path = LOCAL_REPO_PATH / file['path']
            if not file_path.exists():
                continue
            ext = file['name'].split('.')[-1].lower()
            with cols[idx % 3]:
                if ext in ["mp4", "mov", "avi"]:
                    st.video(str(file_path))
                else:
                    st.image(str(file_path), caption=file['name'], use_column_width=True)
    else:
        st.info("No media files available for this access point")

# ✅ ADMIN PAGE (Fully Local)

def admin_page():
    st.title("Admin Panel")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Create Room", "Add Content", "Manage Subfolders", "Manage Files", "🚮 Delete Rooms", "📷 Change Subfolder Thumbnail"])

    # Create Room Tab
    with tab1:
        with st.form(key="create_room_form"):
            room_name = st.text_input("Room Name", key="room_name_input")
            submit_button = st.form_submit_button("Create Room")
            if submit_button:
                existing_rooms = get_all_rooms()
                if room_name in existing_rooms:
                    st.error("Room already exists")
                else:
                    if create_local_room_folder(room_name):
                        st.success(f"Room **{room_name}** created successfully!")
                    else:
                        st.error("Failed to create room")

    if 'upload_counter' not in st.session_state:
        st.session_state.upload_counter = 0

    # Add Content Tab
    with tab2:
        st.header("📤 Add Content")
        search_term = st.text_input("Search rooms by name", key="content_search").lower()
        all_rooms = get_all_rooms()
        filtered_rooms = [room for room in all_rooms if search_term in room.lower()]
        if not filtered_rooms:
            st.info("No rooms found matching your search")
            return

        for room in filtered_rooms:
            with st.expander(f"Room: **{room}**", expanded=False):
                subfolders = get_local_subfolders(room)
                selected_sub = st.selectbox(
                    "Select Subfolder", 
                    ["Main"] + subfolders,
                    key=f"sub_{room}"
                )
                uploaded_files = st.file_uploader(
                    "Choose files (multiple allowed)",
                    type=['jpg', 'jpeg', 'png', 'gif', 'mp4'],
                    key=f"upload_{room}_{st.session_state.upload_counter}",
                    accept_multiple_files=True
                )
                if uploaded_files:
                    for idx, uploaded_file in enumerate(uploaded_files, 1):
                        success = upload_local_room_file(
                            room=room,
                            uploaded_file=uploaded_file,
                            file_type=uploaded_file.type,
                            subfolder=selected_sub if selected_sub != "Main" else None
                        )
                        if success:
                            st.success(f"Uploaded ({idx}/{len(uploaded_files)}) {uploaded_file.name}")
                        else:
                            st.error(f"Failed to upload {uploaded_file.name}")
                    st.session_state.upload_counter += 1
                    st.rerun()

    # Manage Subfolders Tab
    with tab3:
        st.header("🗃 Manage Subfolders")
        room = st.selectbox("Select Room", get_all_rooms())
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
                    if create_local_subfolder(room, sub_name, thumbnail, sub_info):
                        st.success("Access point created!")
                        st.rerun()
                    else:
                        st.error("Creation failed")
                else:
                    st.warning("Please fill all fields")

        st.subheader("Existing Access Points")
        subfolders = get_local_subfolders(room)
        for sub in subfolders:
            with st.expander(f"Access Point: {sub}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    thumbnail_path = LOCAL_REPO_PATH / BASE_PATH / room / sub / "thumbnail.jpg"
                    if thumbnail_path.exists():
                        st.image(str(thumbnail_path), width=200)
                    current_info = get_subfolder_info(room, sub)
                    new_info = st.text_area("Edit information", value=current_info, key=f"info_{sub}")
                    if st.button(f"Update Info for {sub}"):
                        if update_local_subfolder_info(room, sub, new_info):
                            st.success("Info updated!")
                        else:
                            st.error("Update failed")
                with col2:
                    if st.button(f"🗑️ Delete {sub}", key=f"del_{sub}"):
                        if delete_local_path(f"{BASE_PATH}/{room}/{sub}"):
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error("Deletion failed")

    # Manage Files Tab
    with tab4:
        st.header("🗂 Manage Files")
        search_term = st.text_input("Search rooms by name", key="manage_search").lower()
        all_rooms = get_all_rooms()
        filtered_rooms = [room for room in all_rooms if search_term in room.lower()]
        if not filtered_rooms:
            st.info("No rooms found matching your search")
            return

        for room in filtered_rooms:
            with st.expander(f"Room: **{room}**", expanded=False):
                subfolders = get_local_subfolders(room)
                selected_sub = st.selectbox(
                    "Select Location",
                    ["Main Area"] + subfolders,
                    key=f"sub_select_{room}"
                )
                path = f"{BASE_PATH}/{room}"
                if selected_sub != "Main Area":
                    path += f"/{selected_sub}"

                files = get_local_files_in_path(path)
                files = [f for f in files if f['type'] == 'file' and f['name'] not in ['info.txt', 'thumbnail.jpg']]
                if not files:
                    st.info("No files to manage in this location")
                else:
                    st.subheader(f"Files in {selected_sub}")
                    for file in files:
                        col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
                        with col1:
                            file_path = LOCAL_REPO_PATH / file['path']
                            if file_path.exists():
                                ext = file['name'].split('.')[-1].lower()
                                if ext in ['jpg', 'jpeg', 'png', 'gif']:
                                    st.image(str(file_path), width=100)
                                elif ext in ['mp4']:
                                    st.video(str(file_path))
                                else:
                                    st.markdown(f"📄 `{file['name']}`")
                        with col2:
                            st.markdown(f"**File:** `{file['name']}`")
                        with col3:
                            new_name = st.text_input(
                                "New name",
                                value=file['name'],
                                key=f"rename_{room}_{file['name']}"
                            )
                        with col4:
                            if st.button("🗑️ Delete", key=f"del_{room}_{file['name']}"):
                                if delete_local_path(file['path']):
                                    st.success("File deleted!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete file")
                            if st.button("✍️ Rename", key=f"ren_{room}_{file['name']}"):
                                if new_name.strip() == file['name']:
                                    st.warning("Name unchanged")
                                elif not new_name.strip():
                                    st.error("Please enter a new name")
                                else:
                                    if rename_local_file(file['path'], new_name.strip()):
                                        st.success("File renamed!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to rename file")

                st.markdown("---")
                st.subheader("Current Media Preview")
                if files:
                    # Use simple gallery since Swiper can't load local files
                    cols = st.columns(3)
                    for idx, file in enumerate(files):
                        file_path = LOCAL_REPO_PATH / file['path']
                        if file_path.exists():
                            ext = file['name'].split('.')[-1].lower()
                            with cols[idx % 3]:
                                if ext in ['mp4']:
                                    st.video(str(file_path))
                                else:
                                    st.image(str(file_path), caption=file['name'], use_column_width=True)
                else:
                    st.info("No media files available in this location")

    # Delete Rooms Tab
    with tab5:
        st.header("🚮 Delete Content")
        search_term = st.text_input("Search rooms by name", key="delete_search").lower()
        all_rooms = get_all_rooms()
        filtered_rooms = [room for room in all_rooms if search_term in room.lower()]
        if not filtered_rooms:
            st.info("No rooms found matching your search")

        for room in filtered_rooms:
            with st.expander(f"Room: **{room}**", expanded=False):
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.subheader("Delete Subfolder")
                    subfolders = get_local_subfolders(room)
                    if subfolders:
                        selected_sub = st.selectbox(
                            "Select subfolder to delete",
                            subfolders,
                            key=f"sub_del_{room}"
                        )
                        if st.button(f"🗑️ Delete Subfolder", key=f"sub_del_btn_{room}"):
                            if delete_local_path(f"{BASE_PATH}/{room}/{selected_sub}"):
                                st.success(f"Subfolder '{selected_sub}' deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete subfolder")
                    else:
                        st.info("No subfolders in this room")
                with col2:
                    st.subheader("Delete Entire Room")
                    if st.button("⚠️ Delete Entire Room", key=f"room_del_{room}"):
                        if delete_local_path(f"{BASE_PATH}/{room}"):
                            st.success("Room deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete room")

    # Change Thumbnail Tab
    with tab6:
        st.header("📷 Change Subfolder Thumbnail")
        rooms = get_all_rooms()
        selected_room = st.selectbox("Select Room", rooms, key="thumb_room_select")
        if selected_room:
            subfolders = get_local_subfolders(selected_room)
            if not subfolders:
                st.info("This room has no subfolders")
                return

            col1, col2 = st.columns([3, 2])
            with col1:
                selected_sub = st.selectbox("Select Subfolder", subfolders, key="thumb_sub_select")
            with col2:
                thumbnail_path = LOCAL_REPO_PATH / BASE_PATH / selected_room / selected_sub / "thumbnail.jpg"
                if thumbnail_path.exists():
                    st.image(str(thumbnail_path), width=150, caption="Current Thumbnail")
                else:
                    st.image("https://via.placeholder.com/150?text=No+Thumbnail", caption="Current Thumbnail")

            new_thumbnail = st.file_uploader("Upload New Thumbnail", type=['jpg', 'jpeg', 'png'], key="thumb_upload")
            if new_thumbnail:
                st.image(new_thumbnail, width=150, caption="New Thumbnail Preview")
                if st.button("Update Thumbnail", key="thumb_update_btn"):
                    if update_local_subfolder_thumbnail(selected_room, selected_sub, new_thumbnail):
                        st.success("Thumbnail updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update thumbnail")

# ✅ DEFAULT PAGE (Fully Local)

def default_page():
    st.markdown("""
    <style>
        .logo-container {
            display: flex;
            align-items: center;
        }
        .logo {
            width: 83px;
            height: 83px;
            background-color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-right: 10px;
        }
        .logo img {
            width: 68px;
            height: 68px;
        }
        .room-title {
            font-size: 24px;
            font-weight: bold;
        }
        .room-code {
            color: green;
            font-size: 15px;
        }
    </style>
    <div class="logo-container">
        <h1 class="room-title">🔒 Room <span class="room-code">[MITM]</span></h1>
        <div class="logo">
            <img src="https://raw.githubusercontent.com/2005lakshmi/locorom/main/logo_locorom.png" alt="Logo">
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid gray; margin: 5px 0;'>", unsafe_allow_html=True)

    search_term = st.text_input("**Search Room**", "", placeholder="example., 415B").strip().lower()

    # Check for admin password
    if search_term == st.secrets["general"]["password"]:
        st.session_state.page = "Admin Page"
        st.rerun()
        return

    # Get filtered rooms
    rooms = get_all_rooms()
    filtered_rooms = [room for room in rooms if search_term.lower() in room.lower()] if search_term else rooms

    if not filtered_rooms:
        st.info("No rooms found" if search_term else "Please enter room number to search..!")
        return

    selected_room = st.radio("Select Room", filtered_rooms)
    st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)
    st.header(f"Room: :red[{selected_room}]")

    # Display main content
    display_main_content(selected_room)

# ✅ MAIN APP

def main():
    if 'page' not in st.session_state:
        st.session_state.page = "Default Page"

    if st.session_state.page == "Admin Page":
        admin_page()
    else:
        default_page()

if __name__ == "__main__":
    main()
