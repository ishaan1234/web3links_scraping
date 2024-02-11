import os
import json
from urllib.parse import urlparse
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin


current_directory = os.getcwd()
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

def extract_base_links(links):
    base_links = []
    for link in links:
        parsed_link = urlparse(link)
        base_link = parsed_link.scheme + "://" + parsed_link.netloc
        if base_link not in base_links:
            base_links.append(base_link)
    return base_links

def download_logo(url, save_directory, failed_to_download_logos, failed_to_fetch, timeout_urls, couldnt_find_logo):
    try:
        # Send a GET request to the URL with a timeout of 10 seconds
        response = requests.get(url, timeout=30)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the logo image tag
            logo_tag = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            
            if logo_tag:
                # Get the URL of the logo image
                logo_url = logo_tag['href']
                
                # Handle relative URLs
                if not logo_url.startswith('http'):
                    # Construct absolute URL
                    logo_url = urljoin(url, logo_url)
                
                # Download the logo image
                logo_response = requests.get(logo_url)
                
                if logo_response.status_code == 200:
                    # Create the save directory if it doesn't exist
                    if not os.path.exists(save_directory):
                        os.makedirs(save_directory)
                    
                    # Extract the filename from the URL
                    # parsed_url = urlparse(logo_url)
                    filename = url.split('//')[-1].replace('/', '_') + '.ico'
                    cleaned_filename = re.sub(r'[\\/:"*?<>|]', '', filename)
                    
                    # Save the logo image to the specified directory
                    with open(os.path.join(save_directory, cleaned_filename), 'wb') as f:
                        f.write(logo_response.content)
                        
                    print(f"Logo downloaded successfully as '{filename}'")
                else:
                    download_image_2(url, failed_to_download_logos)
                    
            else:
                print("No logo found on the page")
                couldnt_find_logo.append(url)
        else:
            print("Failed to fetch webpage")
            failed_to_fetch.append(url)
    except requests.exceptions.ConnectTimeout:
        print(f"Connection timeout for URL: {url}")
        timeout_urls.append(url)
    except requests.exceptions.ReadTimeout:
        timeout_urls.append(url)
        print("Read timed out.")
        
def download_image_2(url, failed_to_download_logos=[] , save_folder="images"):
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
        failed_to_download_logos.append(url)

def download_file_2(url, save_folder):
    response = requests.get(url)
    # filename = os.path.basename(urlparse(url).path)
    filename = url
    match = re.search('//(.*?)/', filename)
    cleaned_filename = match.group(1) 
    save_path = os.path.join(save_folder, cleaned_filename)
    with open(save_path, "wb") as f:
        f.write(response.content)

# loop over json files and run code
def read_json(directory):
    json_files = [file for file in os.listdir(directory) if file.endswith('.json')]
    for json_file in json_files:
        failed_to_download_logos = []
        failed_to_fetch = []
        timeout_urls = []  
        couldnt_find_logo = [] 
        
        with open(json_file, 'r') as f:
            data = json.load(f)

        all_links = extract_links(data)

        base_links = extract_base_links(all_links)
        unique_links = list(set(base_links))
        print(unique_links)
        # Download logos for each unique link
        save_directory = "logo_images"   
        for url in unique_links:
            download_logo(url, save_directory, failed_to_download_logos, failed_to_fetch, timeout_urls, couldnt_find_logo)

        print("Failed to download logos from the following URLs:", failed_to_download_logos)
        print("Could not find logo for the following URLs:", couldnt_find_logo)
        print("Failed to fetch the following URLs:", failed_to_fetch)
        print("Connection timeout for the following URLs:", timeout_urls)
        
    
read_json(current_directory)