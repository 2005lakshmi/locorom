import streamlit as st
from pathlib import Path
import streamlit.components.v1 as components

BASE_PATH = Path("Rooms")

def list_media_files(path):
    return [str(f) for f in path.iterdir()
            if f.is_file() and f.name not in ["info.txt", "thumbnail.jpg"]
            and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif"]]

def display_main_content(selected_room):
    room_path = BASE_PATH / selected_room
    images = list_media_files(room_path)
    if images:
        items = [{"img": img, "title": "", "text": ""} for img in images]
        carousel(items=items)
    else:
        st.info("No images found.")


def display_main_content(selected_room):
    room_path = BASE_PATH / selected_room
    info_content = get_info_content(room_path)
    main_media = list_media_files(room_path)

    st.markdown(f"<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 3])
    with col1:
        if main_media:
            st.image(main_media[0], width=200)
    with col2:
        st.markdown("<h5 style='color:#0D92F4;'>Location Info :</h5>", unsafe_allow_html=True)
        st.markdown(f"###### {info_content}")

    if main_media:
        st.markdown("##### Photos")
        display_carousel(main_media)
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)

    # Subfolders (access points)
    for sub in sorted([f for f in room_path.iterdir() if f.is_dir()]):
        st.markdown("<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)
        sub_info = get_info_content(sub)
        col1, col2 = st.columns([2, 3])
        with col1:
            thumb_file = sub / "thumbnail.jpg"
            if thumb_file.exists():
                st.image(thumb_file, width=200)
            else:
                st.info("No thumbnail.jpg found")
        with col2:
            st.markdown("<h5 style='color:#0D92F4;'>Location Info :</h5>", unsafe_allow_html=True)
            st.markdown(f"###### {sub_info}")

        sub_media = list_media_files(sub)
        if sub_media:
            st.markdown("##### Photos")
            display_carousel(sub_media)
        else:
            st.info(f"No media available in {sub.name}")
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)

# --- Streamlit Page ---
st.set_page_config(page_title="Rooms Explorer", page_icon=":door:")

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
    <h1 class="room-title">🔍 Room <span class="room-code">[MITM]</span></h1>
    <div class="logo">
        <img src="https://raw.githubusercontent.com/2005lakshmi/locorom/main/logo_locorom.png" alt="Logo">
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='border: 1px solid gray; margin: 5px 0;'>", unsafe_allow_html=True)

if not BASE_PATH.exists():
    st.error("Rooms folder not found. Please clone the repo locally.")
else:
    # Search for rooms
    search_term = st.text_input("**Search Room**", "", placeholder="example., 415B").strip().lower()
    # Get filtered rooms (local only)
    rooms = [f.name for f in BASE_PATH.iterdir() if f.is_dir()]
    filtered_rooms = [room for room in rooms if search_term in room.lower()] if search_term else []

    if not filtered_rooms:
        st.error("No rooms found" if search_term else "Please enter room number to search..!")
    else:
        selected_room = st.radio("Select Room", filtered_rooms)
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)
        st.header(f"Room: :red[{selected_room}]")
        display_main_content(selected_room)
