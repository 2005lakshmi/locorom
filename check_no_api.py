import streamlit as st
import requests
import streamlit.components.v1 as components
import string

# Configuration
GITHUB_REPO = "2005lakshmi/locorom"
BASE_PATH = "Rooms"
BRANCH = "main"

def get_raw_url(*path_parts):
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{'/'.join(path_parts)}"

def get_rooms():
    """Get list of rooms using GitHub API without authentication"""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BASE_PATH}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return [item['name'] for item in response.json() if item['type'] == 'dir']
    return []

def get_room_info(room_name):
    info_url = get_raw_url(BASE_PATH, room_name, "info.txt")
    response = requests.get(info_url)
    return response.text if response.status_code == 200 else "No information available"

def generate_alphabetical_files(room_name, subfolder=None):
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
        if len(current) > 1:
            break
    return files

def get_subfolders(room_name):
    subfolders = []
    for char in string.ascii_lowercase:
        thumb_url = get_raw_url(BASE_PATH, room_name, char, "thumbnail.jpg")
        if requests.head(thumb_url).status_code == 200:
            subfolders.append(char)
    return subfolders

def display_carousel(files, zoom=True):
    # Keep the exact same carousel implementation as before
    # ... [same carousel code as previous answer] ...

def display_main_content(room_name):
    # Keep the exact same content display implementation
    # ... [same display code as previous answer] ...

# Streamlit UI with radio button selection
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
