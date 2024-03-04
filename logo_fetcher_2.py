import os
import json
import asyncio
import aiohttp
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import aiofiles

current_directory = os.getcwd()

def write_to_file(content):
    with open("unable_to_open.txt", "a") as file:
        for item in content:
            file.write(item + "\n")


def extract_name(string):
    pattern = r'\.(com|org|net|io|co|uk|us|me|info|biz|tv|edu|gov|mil|name|pro|aero|coop|museum|jobs|mobi|travel|asia|cat|post|tel|xxx|arpa|int|nato|example|invalid|localhost|test|onion|exit|bit|bazar|coin|lib|emc|gnu|ind|lan|local|neo|onl|sdf|geek|guru|ninja|tech|top|zone|club|cool|host|site|wiki|buzz|link|press|red|win|space|store|tube|online|center|direct|place|press|services|systems|today|works|world|zone|email|group|info|life|live|news|shop|store|studio|video|blog|cloud|earth|global|guide|land|live|media|news|site|tech|tips|today|works|world|zone|email|group|info|life|live|news|shop|store|studio|video|blog|cloud|earth|global|guide|land|live|media|news|site|tech|tips|today|works|world|zone|email|group|info|life|live|news|shop|store|studio|video|blog|cloud|earth|global|guide|land|live|media|news|site|tech|tips|today|works|world|zone|email|group|info|life|live|news|shop|store|studio|video|blog|cloud|earth|global|guide|land|live|media|news|site|tech|tips|today|works|world|zone|email|group|info|life|live|news|shop|store|studio|video|blog|cloud|earth|global|guide|land|live|media|news|site|tech|tips|today|works|world|zone|email|group|info|life|live|news|shop|store|studio|video|blog|cloud|earth|global|guide|land|live|media|news|site|tech|tips|today|works|world|zone|email|group|info|life|live|news|shop|store|studio|video|blog|cloud|earth|global|guide|land|live|media|news|site|tech|tips|today|works|world|zone|email|group|info|life|live|news|shop|store|studio|video|blog|cloud|earth|global|guide)'
    rstring = re.sub(pattern, '', string)
    rstring = rstring.replace('www.', '')
    rstring = rstring.replace('.', '_')
    return rstring

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

async def download_logo(session, url, save_directory, failed_to_download_logos, failed_to_fetch, timeout_urls, couldnt_find_logo):
    try:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                logo_tag = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
                if logo_tag:
                    logo_url = logo_tag['href']
                    if not logo_url.startswith('http'):
                        logo_url = urljoin(url, logo_url)
                    async with session.get(logo_url) as logo_response:
                        if logo_response.status == 200:
                            if not os.path.exists(save_directory):
                                os.makedirs(save_directory)
                            filename = url.split('//')[-1].replace('/', '_') 
                            cleaned_filename = re.sub(r'[\\/:"*?<>|]', '', filename)
                            cleaned_filename = extract_name(cleaned_filename) + '.ico'
                            async with aiofiles.open(os.path.join(save_directory, cleaned_filename), 'wb') as f:
                                await f.write(await logo_response.read())
                            print(f"Logo downloaded successfully as '{cleaned_filename}'")
                        else:
                            download_image_2(session, url, failed_to_download_logos)
                else:
                    print("No logo found on the page")
                    couldnt_find_logo.append(url)
            else:
                print("Failed to fetch webpage")
                failed_to_fetch.append(url)
    except asyncio.TimeoutError:
        print(f"Connection timeout for URL: {url}")
        timeout_urls.append(url)
    except Exception as e:
        print(f"Error downloading logo for URL {url}: {e}")

async def download_image_2(session, url, failed_to_download_logos=[], save_folder="images"):
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    try:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            img_tag = soup.find("img")
            svg_tag = soup.find("svg")
            if img_tag:
                img_url = img_tag.get("src")
                if img_url:
                    img_url = urljoin(url, img_url)
                    async with session.get(img_url) as img_response:
                        if img_response.status == 200:
                            with open(os.path.join(save_folder, "image.jpg"), "wb") as f:
                                f.write(await img_response.read())
                            print("Image downloaded:", img_url)
                        else:
                            failed_to_download_logos.append(url)
            elif svg_tag:
                svg_url = urljoin(url, "image.svg")
                with open(os.path.join(save_folder, "image.svg"), "w", encoding="utf-8") as f:
                    f.write(svg_tag.prettify())
                print("SVG downloaded:", svg_url)
            else:
                print("No image found on the page.")
                failed_to_download_logos.append(url)
    except Exception as e:
        print(f"Error downloading image for URL {url}: {e}")
        failed_to_download_logos.append(url)

async def read_json(directory):
    json_files = [file for file in os.listdir(directory) if file.endswith('.json')]
    for json_file in json_files:
        print(f"Processing file: {json_file}")
        failed_to_download_logos = []
        failed_to_fetch = []
        timeout_urls = []  
        couldnt_find_logo = [] 
        other_errors = []
        async with aiohttp.ClientSession() as session:
            with open(json_file, 'r') as f:
                data = json.load(f)

            all_links = extract_links(data)

            base_links = extract_base_links(all_links)
            unique_links = list(set(base_links))
            print(unique_links)
            save_directory = "logo_images"   
            tasks = []
            for url in unique_links:
                tasks.append(download_logo(session, url, save_directory, failed_to_download_logos, failed_to_fetch, timeout_urls, couldnt_find_logo))
            await asyncio.gather(*tasks)

        print("Failed to download logos from the following URLs:", failed_to_download_logos)
        write_to_file(failed_to_download_logos)
        print("Could not find logo for the following URLs:", couldnt_find_logo)
        write_to_file(couldnt_find_logo)
        print("Failed to fetch the following URLs:", failed_to_fetch)
        write_to_file(failed_to_fetch)
        print("Connection timeout for the following URLs:", timeout_urls)
        write_to_file(timeout_urls)
        print("Other errors:", other_errors)
        write_to_file(other_errors)

async def main():
    await read_json(current_directory)

if __name__ == "__main__":
    asyncio.run(main())
