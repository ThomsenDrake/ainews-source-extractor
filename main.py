import requests
from bs4 import BeautifulSoup
import re
import os
from fpdf import FPDF
import time
from twitter_handler import scrape_single_tweet_selenium # Import the new handler

def create_pdf_from_tweet(tweet_url, text_content, image_urls, output_folder="tweet_pdfs"):
    """
    Creates a PDF file from tweet content.

    Args:
        tweet_url: The URL of the tweet (used for naming the PDF).
        text_content: The text content of the tweet.
        image_urls: A list of image URLs from the tweet.
        output_folder: The folder to save the PDF to.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add tweet URL
    pdf.cell(200, 10, txt=f"Source: {tweet_url}", ln=True, link=tweet_url)
    pdf.ln(5)

    # Add tweet text
    # FPDF requires UTF-8 text to be encoded properly
    try:
        pdf.multi_cell(0, 10, text_content.encode('latin-1', 'replace').decode('latin-1'))
    except UnicodeEncodeError:
        # Fallback for characters not in latin-1, though replace should handle most
        cleaned_text = text_content.encode('ascii', 'ignore').decode('ascii')
        pdf.multi_cell(0, 10, cleaned_text)
        pdf.ln(5)
        pdf.multi_cell(0, 10, "[Some characters could not be rendered in PDF]")

    pdf.ln(10)

    # Add images
    for img_url in image_urls:
        try:
            img_response = requests.get(img_url, stream=True, timeout=10)
            img_response.raise_for_status()
            # Save image temporarily to add to PDF
            temp_img_path = os.path.join(output_folder, "temp_image")
            with open(temp_img_path, 'wb') as img_f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    img_f.write(chunk)
            
            # Check image format and add to PDF
            # Basic check, might need more robust image handling
            if img_url.lower().endswith(('.png', '.jpg', '.jpeg')):
                pdf.image(temp_img_path, w=100) # Adjust width as needed
                pdf.ln(5)
            else:
                pdf.cell(200, 10, txt=f"[Unsupported image format: {img_url}]", ln=True)

            os.remove(temp_img_path) # Clean up temp image
        except requests.exceptions.RequestException as e:
            print(f"Error fetching image {img_url}: {e}")
            pdf.cell(200, 10, txt=f"[Could not load image: {img_url}]", ln=True)
        except Exception as e:
            print(f"Error processing image {img_url}: {e}")
            pdf.cell(200, 10, txt=f"[Error processing image: {img_url}]", ln=True)

    # Sanitize filename
    filename_base = tweet_url.split("/")[-1].split("?")[0]
    safe_filename = re.sub(r'[^a-zA-Z0-9_\\[\\]-]', '_', filename_base)
    if not safe_filename:
        safe_filename = f"tweet_{int(time.time())}" # Fallback filename
    pdf_filename = os.path.join(output_folder, f"{safe_filename}.pdf")

    try:
        pdf.output(pdf_filename, "F")
        print(f"Saved PDF: {pdf_filename}")
    except Exception as e:
        print(f"Error saving PDF {pdf_filename}: {e}")

def scrape_links(url):
    """
    Scrapes all unique links from a given URL.

    Args:
        url: The URL to scrape.

    Returns:
        A list of unique links found on the page.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    links = set()
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        # Filter out relative links, fragments, and discord links
        if (link.startswith('http://') or link.startswith('https://')) and 'discord.com' not in link and 'discord.gg' not in link:
            links.add(link)
            
    return list(links)

if __name__ == '__main__':
    target_url = 'https://news.smol.ai/issues/25-05-20-google-io/'
    unique_links = scrape_links(target_url)
    
    tweet_pdf_folder = "tweet_pdfs"
    if not os.path.exists(tweet_pdf_folder):
        os.makedirs(tweet_pdf_folder)

    if unique_links:
        output_filename = "links.txt"
        with open(output_filename, 'w', encoding='utf-8') as f:
            for link in unique_links:
                f.write(link + os.linesep)
                if 'twitter.com' in link or 'x.com' in link:
                    print(f"Processing tweet: {link}")
                    # Use the new Selenium-based scraper
                    tweet_text, image_urls = scrape_single_tweet_selenium(link)
                    
                    if tweet_text is not None: # Check if scraping was successful
                        create_pdf_from_tweet(link, tweet_text, image_urls, output_folder=tweet_pdf_folder)
                    else:
                        print(f"Could not retrieve content for {link} using Selenium scraper.")

        print(f"Found {len(unique_links)} unique links (excluding Discord) on {target_url}. Saved to {output_filename}")
        print(f"Tweet PDFs saved to {tweet_pdf_folder} folder.")
    else:
        print(f"No links found on {target_url}.")

