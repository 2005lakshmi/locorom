import streamlit as st
import requests
import streamlit.components.v1 as components
import string

# Configuration
GITHUB_REPO = "2005lakshmi/locorom"
BASE_PATH = "Rooms"
BRANCH = "main"

def get_raw_url(*path_parts):
    """Construct raw GitHub URL for a file"""
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{'/'.join(path_parts)}"

def get_rooms():
    """Get list of rooms using GitHub API"""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BASE_PATH}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return [item['name'] for item in response.json() if item['type'] == 'dir']
    return []

def get_room_info(room_name):
    """Fetch room information from info.txt"""
    info_url = get_raw_url(BASE_PATH, room_name, "info.txt")
    response = requests.get(info_url)
    return response.text if response.status_code == 200 else "No information available"

def generate_alphabetical_files(room_name, subfolder=None):
    """Generate possible alphabetical filenames and check existence"""
    base_path = [BASE_PATH, room_name]
    if subfolder:
        base_path.append(subfolder)
    
    files = []
    sequence = ['']
    
    while True:
        current = sequence.pop(0)
        for letter in string.ascii_lowercase:
            candidate = current + letter
            for ext in ['jpg', 'jpeg', 'png', 'gif', 'mp4']:
                url = get_raw_url(*base_path, f"{candidate}.{ext}")
                if requests.head(url).status_code == 200:
                    files.append(url)
            sequence.append(candidate)
        if len(current) > 1:  # Limit depth for practical purposes
            break
    return files

def get_subfolders(room_name):
    """Detect subfolders by checking for thumbnail.jpg"""
    subfolders = []
    for char in string.ascii_lowercase:
        thumb_url = get_raw_url(BASE_PATH, room_name, char, "thumbnail.jpg")
        if requests.head(thumb_url).status_code == 200:
            subfolders.append(char)
    return subfolders

def display_carousel(files, zoom=True):
    """Display media files in a carousel matching original styling"""
    carousel_items = ""
    for file_url in files:
        if file_url.split('.')[-1].lower() in ['mp4', 'webm']:
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
    """Display room content matching original layout"""
    # Main area
    main_files = generate_alphabetical_files(room_name)
    info_content = get_room_info(room_name)
    
    if main_files:
        st.markdown("<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 3])
        with col1:
            st.image(main_files[0], width=200)
        with col2:
            st.markdown("<h5 style='color:#0D92F4;'>Location Info :</h5>", unsafe_allow_html=True)
            st.markdown(f"###### {info_content}")
        
        st.markdown("##### Photos")
        st.write("Path through Photos")
        display_carousel(main_files, zoom=True)
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)

    # Subfolders
    for sub in get_subfolders(room_name):
        st.markdown("<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 3])
        with col1:
            thumb_url = get_raw_url(BASE_PATH, room_name, sub, "thumbnail.jpg")
            st.image(thumb_url, width=200)
        with col2:
            sub_info_url = get_raw_url(BASE_PATH, room_name, sub, "info.txt")
            sub_info = requests.get(sub_info_url).text
            st.markdown("<h5 style='color:#0D92F4;'>Location Info :</h5>", unsafe_allow_html=True)
            st.markdown(f"###### {sub_info}")
        
        sub_files = generate_alphabetical_files(room_name, sub)
        if sub_files:
            st.markdown("##### Photos")
            display_carousel(sub_files, zoom=True)
        else:
            st.info(f"No media available in {sub}")
        st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)

# Streamlit UI
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

# Room search and selection
search_term = st.text_input("**Search Room**", "", placeholder="example., 415B").strip().lower()
all_rooms = get_rooms()
filtered_rooms = [room for room in all_rooms if search_term in room.lower()]

if not filtered_rooms:
    st.error("No rooms found" if search_term else "Please enter room number to search..!")
else:
    selected_room = st.radio("Select Room", filtered_rooms)
    st.markdown("<hr style='border: 1px solid gray; margin: 0px 0;'>", unsafe_allow_html=True)
    st.header(f"Room: :red[{selected_room}]")
    display_main_content(selected_room)
