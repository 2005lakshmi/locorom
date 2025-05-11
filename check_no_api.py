import streamlit as st
from pathlib import Path
import streamlit.components.v1 as components

# --- Configuration ---
BASE_PATH = Path("Rooms")  # Local path to the 'Rooms' folder

# --- Helper Functions ---

def get_room_list():
    """List all room directories inside Rooms/."""
    return sorted([f.name for f in BASE_PATH.iterdir() if f.is_dir()])

def get_info_content(path):
    """Read info.txt content if it exists."""
    info_file = path / "info.txt"
    if info_file.exists():
        return info_file.read_text()
    return "No information available"

def list_media_files(path):
    """List image/video files (excluding info.txt and thumbnail.jpg)."""
    return [f for f in path.iterdir()
            if f.is_file() and f.name not in ["info.txt", "thumbnail.jpg"]
            and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".mp4"]]

def display_carousel(files):
    """Display images/videos as a Swiper.js carousel."""
    carousel_items = ""
    for file in files:
        ext = file.suffix.lower()
        file_url = file.as_uri()
        if ext == ".mp4":
            media_html = f"""
                <video controls style="max-height: 400px; width: 100%;">
                    <source src="{file_url}" type="video/mp4">
                </video>
            """
        else:
            media_html = f'''
            <img src="{file_url}" 
                 style="max-height: 400px; width: 100%; object-fit: contain;">
            '''
        carousel_items += f'<div class="swiper-slide">{media_html}</div>'

    if not carousel_items:
        st.info("No media files available.")
        return

    carousel_html = f"""
    <link rel="stylesheet" href="https://unpkg.com/swiper@8/swiper-bundle.min.css">
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

def display_room(room_name):
    room_path = BASE_PATH / room_name
    info_content = get_info_content(room_path)
    main_media = list_media_files(room_path)

    # Main area
    st.markdown(f"<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 3])
    with col1:
        # Show first image if available
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
st.title("Rooms Explorer")

if not BASE_PATH.exists():
    st.error("Rooms folder not found. Please clone the repo locally.")
else:
    # List all rooms
    rooms = [f.name for f in BASE_PATH.iterdir() if f.is_dir()]
    search_term = st.text_input("Search Room Number (or Name)").strip().lower()
    filtered_rooms = [room for room in rooms if search_term in room.lower()] if search_term else []

    if not filtered_rooms:
        st.error("No rooms found" if search_term else "Please enter room number to search..!")
    else:
        selected_room = st.radio("Select Room", filtered_rooms)
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)
        display_room(selected_room)
