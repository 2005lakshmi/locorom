import os
import streamlit as st
from pathlib import Path
import streamlit.components.v1 as components
import string

# Configuration
BASE_PATH = Path("Rooms")

# Helper functions

def get_local_files(path):
    """Return a list of dicts for files and folders in the given local path."""
    p = Path(path)
    if not p.exists():
        return []
    items = []
    for f in p.iterdir():
        if f.is_file():
            items.append({'type': 'file', 'name': f.name, 'path': str(f), 'object': f})
        elif f.is_dir():
            items.append({'type': 'dir', 'name': f.name, 'path': str(f), 'object': f})
    return items

def get_subfolders(room_name):
    """Return subfolder names for a room."""
    items = get_local_files(BASE_PATH / room_name)
    return [item['name'] for item in items if item['type'] == 'dir']

def get_room_info(room_name):
    """Get room information from info.txt"""
    info_path = BASE_PATH / room_name / "info.txt"
    if info_path.exists():
        return info_path.read_text()
    return "No information available"

def get_subfolder_info(room_name, subfolder):
    info_path = BASE_PATH / room_name / subfolder / "info.txt"
    if info_path.exists():
        return info_path.read_text()
    return ""

def list_media_files(path):
    """List image/video files (excluding info.txt and thumbnail.jpg)."""
    p = Path(path)
    return [f for f in p.iterdir()
            if f.is_file() and f.name not in ["info.txt", "thumbnail.jpg"]
            and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".mp4"]]

def display_carousel(files, zoom=False):
    """Display media files in a carousel with zoom capability"""
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
            zoom_class = "swiper-zoom-container" if zoom else ""
            media_html = f'''
            <div class="{zoom_class}">
                <img src="{file_url}" 
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

def display_main_content(room_name):
    """Display main content for a room with subfolders"""
    info_content = get_room_info(room_name)
    main_media = list_media_files(BASE_PATH / room_name)

    # Show thumbnail and info in row
    if main_media:
        st.markdown("<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 3])
        with col1:
            st.image(main_media[0], width=200)
        with col2:
            st.markdown("<h5 style='color:#0D92F4;'>Location Info :</h5>", unsafe_allow_html=True)
            st.markdown(f"###### {info_content}")

        st.markdown("##### Photos ")
        st.write("Path through Photos")
        display_carousel(main_media, zoom=True)
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)

    # Subfolders Section
    subfolders = get_subfolders(room_name)
    for sub in subfolders:
        st.markdown("<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)
        sub_path = BASE_PATH / room_name / sub
        sub_media = list_media_files(sub_path)
        col1, col2 = st.columns([2, 3])
        with col1:
            thumb_file = sub_path / "thumbnail.jpg"
            if thumb_file.exists():
                st.image(thumb_file, width=200)
            else:
                st.info("No thumbnail.jpg found")
        with col2:
            sub_info = get_subfolder_info(room_name, sub)
            st.markdown("<h5 style='color:#0D92F4;'>Location Info :</h5>", unsafe_allow_html=True)
            st.markdown(f"###### {sub_info}")

        if sub_media:
            st.markdown("##### Photos")
            display_carousel(sub_media, zoom=True)
        else:
            st.info(f"No media available in {sub}")
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)

# --- Streamlit Page ---
st.set_page_config(page_title="Rooms Explorer", page_icon=":door:")
st.title("Rooms Explorer")

if not BASE_PATH.exists():
    st.error("Rooms folder not found. Please clone the repo locally.")
else:
    # List all rooms
    rooms = [f.name for f in BASE_PATH.iterdir() if f.is_dir()]
    search = st.text_input("Search Rooms")
    if search:
        rooms = [r for r in rooms if search.lower() in r.lower()]
    if not rooms:
        st.info("No rooms found.")
    else:
        selected_room = st.radio("Select a room", rooms)
        display_main_content(selected_room)
