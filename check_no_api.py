import streamlit as st
import base64
import requests
import streamlit.components.v1 as components

# Configuration
GITHUB_REPO = "2005lakshmi/locorom"
BASE_PATH = "Rooms"

def get_room_info(room_name):
    """Fetch room info directly from GitHub raw URL"""
    info_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{BASE_PATH}/{room_name}/info.txt"
    response = requests.get(info_url)
    return response.text if response.status_code == 200 else "No information available"

def display_carousel(files):
    """Display media files in a carousel with zoom capability"""
    carousel_items = ""
    for file_url in files:
        if file_url.split('.')[-1].lower() in ['mp4', 'webm']:
            media_html = f"""
                <video controls style="max-height: 400px; width: 100%;">
                    <source src="{file_url}" type="video/mp4">
                </video>
            """
        else:
            media_html = f'<img src="{file_url}" style="max-height: 400px; width: 100%; object-fit: contain;">'
        
        carousel_items += f'<div class="swiper-slide">{media_html}</div>'

    carousel_html = f"""
    <!-- Swiper CSS -->
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
        }}
        .swiper-pagination-fraction {{
            font-size: 18px;
            font-weight: bold;
            color: white;
            text-shadow: 0 0 5px rgba(0,0,0,0.5);
        }}
        .swiper-button-next,
        .swiper-button-prev {{
            color: white;
            background: rgba(0,0,0,0.5);
            padding: 20px;
            border-radius: 50%;
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

    <!-- Swiper JS -->
    <script src="https://unpkg.com/swiper@8/swiper-bundle.min.js"></script>
    <script>
        new Swiper('.mySwiper', {{
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

def display_main_content(room_name):
    """Display main content for a room with subfolders"""
    # Get room info
    info_content = get_room_info(room_name)
    
    # Main Area Section
    main_media = []
    # Generate possible media URLs (a-z then aa-zz)
    for i in range(26):
        letter = chr(97 + i)
        main_media.append(f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{BASE_PATH}/{room_name}/{letter}.jpg")
    
    # Show thumbnail and info in row
    st.markdown("<h4 style='color: green;'>From Point:</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 3])
    with col1:
        if main_media:
            st.image(main_media[0], width=200)
    with col2:
        st.markdown(f"###### {info_content}")
    
    # Main Area Carousel
    st.markdown("##### Photos")
    st.write("Path through Photos")
    display_carousel([url for url in main_media if requests.head(url).status_code == 200])

def default_page():
    """User-facing interface without admin features"""
    st.markdown("""
    <style>
        .logo-container {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        .logo {{
            width: 83px;
            height: 83px;
            margin-right: 15px;
        }}
        .room-title {{
            font-size: 24px;
            font-weight: bold;
        }}
        .room-code {{
            color: green;
            font-size: 15px;
        }}
    </style>
    <div class="logo-container">
        <h1 class="room-title">🔍 Room <span class="room-code">[MITM]</span></h1>
        <img class="logo" src="https://raw.githubusercontent.com/2005lakshmi/locorom/main/logo_locorom.png">
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border:1px solid gray;margin:5px 0'>", unsafe_allow_html=True)

    # Room search input
    room_name = st.text_input("**Search Room**", "", placeholder="Enter exact room number (e.g. 415B)").strip()

    if not room_name:
        st.info("Please enter a room number to begin")
        return

    # Verify room exists
    info_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{BASE_PATH}/{room_name}/info.txt"
    if requests.head(info_url).status_code != 200:
        st.error("Room not found")
        return

    # Display room content
    st.markdown(f"## Room: :red[{room_name}]")
    display_main_content(room_name)

if __name__ == "__main__":
    default_page()
