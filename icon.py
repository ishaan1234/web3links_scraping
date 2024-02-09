import requests
from bs4 import BeautifulSoup
# from urllib.parse import urljoin
from urllib.parse import urlparse, urljoin
import os
import re

failed_to_download_logos = []
failed_to_fetch = []
timeout_urls = []


def download_logo(url, save_directory):
    try:
        response = requests.get(url, timeout=30)
    
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            logo_tag = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            
            if logo_tag:
                logo_url = logo_tag['href']
                
                if not logo_url.startswith('http'):
                    logo_url = urljoin(url, logo_url)
                
                logo_response = requests.get(logo_url)
                
                if logo_response.status_code == 200:
                    if not os.path.exists(save_directory):
                        os.makedirs(save_directory)
        
                    # parsed_url = urlparse(logo_url)
                    filename = url.split('//')[-1].replace('/', '_') + '.ico'
                    cleaned_filename = re.sub(r'[\\/:"*?<>|]', '', filename)
                    
                    with open(os.path.join(save_directory, cleaned_filename), 'wb') as f:
                        f.write(logo_response.content)
                        
                    print(f"Logo downloaded successfully as '{filename}'")
                else:
                    print("Failed to download logo")
                    failed_to_download_logos.append(url)
            else:
                print("No logo found on the page")
                download_image_2(url)
        else:
            print("Failed to fetch webpage")
            failed_to_fetch.append(url)
    except requests.exceptions.ConnectTimeout:
        print(f"Connection timeout for URL: {url}")
        timeout_urls.append(url)
    except requests.exceptions.ReadTimeout:
        timeout_urls.append(url)
        print("Read timed out.")
        
def download_image_2(url, save_folder="images"):
    # Create folder to save images if it doesn't exist
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Fetch webpage HTML
    response = requests.get(url)
    html = response.text

    # Parse HTML
    soup = BeautifulSoup(html, "html.parser")

    # Find first encountered IMG or SVG tag
    img_tag = soup.find("img")
    svg_tag = soup.find("svg")

    if img_tag:
        img_url = img_tag.get("src")
        if img_url:
            img_url = urljoin(url, img_url)
            download_file_2(img_url, save_folder)
            print("Image downloaded:", img_url)
    elif svg_tag:
        svg_url = urljoin(url, "image.svg")
        with open(os.path.join(save_folder, "image.svg"), "w", encoding="utf-8") as f:
            f.write(svg_tag.prettify())
        print("SVG downloaded:", svg_url)
    else:
        print("No image found on the page.")

def download_file_2(url, save_folder):
    response = requests.get(url)
    filename = os.path.basename(urlparse(url).path)
    cleaned_filename = re.sub(r'[\\/:"*?<>|]', '', filename)
    save_path = os.path.join(save_folder, cleaned_filename)
    with open(save_path, "wb") as f:
        f.write(response.content)

# Example usage:
# url = "https://api3.org/"  # Replace with the URL of the webpage you want to download the logo from
import json

# Load the JSON file
with open('your_file.json', 'r') as f:
    data = json.load(f)

# Function to extract links from a dictionary
def extract_links(data):
    links = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and value.startswith('http'):
                links.append(value)
            else:
                links.extend(extract_links(value))
    elif isinstance(data, list):
        for item in data:
            links.extend(extract_links(item))
    return links

# Extract links from the JSON data
all_links = extract_links(data)

# Remove duplicates
unique_links = list(set(all_links))

# Print the unique links
print(unique_links)


save_directory = "logo_images"    # Directory to save the downloaded logo
for url in unique_links:
    download_logo(url, save_directory)

print("Failed to download logos from the following URLs:", failed_to_download_logos)
print("Failed to fetch the following URLs:", failed_to_fetch)
