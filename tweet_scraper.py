import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import re
import time # Added for time.sleep
import requests # Added for downloading images
import random # Added for exponential backoff

# Constants for rate limit handling
MAX_RETRIES = 5
INITIAL_WAIT_TIME = 5 # seconds


def read_urls_from_file(filepath):
    urls = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                urls.append(line.strip())
    except FileNotFoundError:
        print(f"Error: The file {filepath} was not found.")
    return urls

def filter_tweet_urls(urls):
    tweet_urls = []
    for url in urls:
        if "twitter.com" in url or "x.com" in url:
            tweet_urls.append(url)
    return tweet_urls

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')  # Run in headless mode, 'new' is preferred for modern Chrome
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3') # Suppress console logs
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36") # Add user-agent
    options.add_argument('--disable-gpu') # Disable GPU hardware acceleration, often problematic in headless
    options.add_argument('--window-size=1920,1080') # Set a consistent window size
    options.add_argument('--disable-extensions') # Disable browser extensions
    options.add_argument('--disable-infobars') # Disable infobars
    options.add_argument('--disable-notifications') # Disable notifications
    options.add_argument('--disable-setuid-sandbox') # Often paired with --no-sandbox
    options.add_argument('--disable-browser-side-navigation') # May help with certain navigation issues
    options.add_argument('--disable-features=VizDisplayCompositor') # Experimental, can improve stability
    try:
        # Attempt to use a pre-installed ChromeDriver or one found in PATH
        driver = webdriver.Chrome(options=options)
        return driver
    except WebDriverException as e:
        print(f"WebDriver error: {e}")
        print("Please ensure ChromeDriver is installed and available in your system's PATH.")
        print("You can download it from: https://chromedriver.chromium.org/downloads")
        return None

def scrape_tweet(driver, url):
    tweet_data = {
        "url": url,
        "text": "N/A",
        "images": []
    }
    
    retries = 0
    while retries < MAX_RETRIES:
        try:
            driver.get(url)
            # Removed time.sleep(5) as it was causing KeyboardInterrupts

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//article[@data-testid='tweet']"))
            )

            # Scroll down to ensure content loads
            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(3): # Scroll a few times
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2) # Wait for content to load
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Extract tweet text - trying more general XPaths
            tweet_text = "N/A"
            try:
                # Common XPaths for tweet text on Twitter/X
                text_elements = driver.find_elements(By.XPATH, "//div[@data-testid='tweetText']//span | //div[contains(@data-testid, 'tweet')]//div[contains(@dir, 'auto')]//span")
                full_text = []
                for el in text_elements:
                    text = el.text.strip()
                    if text and not text.startswith('@') and not text.startswith('#'): # Exclude mentions/hashtags if they are separate spans
                        full_text.append(text)
                if full_text:
                    tweet_text = " ".join(full_text).strip()
                    tweet_data["text"] = tweet_text
                else:
                    print(f"Could not find tweet text for {url} using general XPaths.")
            except NoSuchElementException:
                print(f"Could not find tweet text for {url} (NoSuchElementException).")
            except Exception as e:
                print(f"Error extracting tweet text for {url}: {e}")

            # Extract image URLs and download them
            try:
                image_elements = driver.find_elements(By.XPATH, "//div[@data-testid='tweetPhoto']//img | //div[contains(@data-testid, 'tweet')]//img[contains(@src, 'media')]")
                tweet_id_match = re.search(r'status/(\d+)', url)
                tweet_id = tweet_id_match.group(1) if tweet_id_match else "unknown_tweet"
                
                for i, img in enumerate(image_elements):
                    img_src = img.get_attribute('src')
                    if img_src and "media" in img_src: # Ensure it's a media image
                        local_path = download_image(img_src, tweet_id, i)
                        if local_path:
                            tweet_data["images"].append(local_path)
                if not tweet_data["images"]:
                    print(f"No images found for {url} using general XPaths.")
            except NoSuchElementException:
                print(f"No images found for {url} (NoSuchElementException).")
            except Exception as e:
                print(f"Error extracting images for {url}: {e}")

            if tweet_data["text"] == "N/A" and not tweet_data["images"]:
                print(f"Warning: No tweet content (text or images) found for {url}. This might indicate a scraping issue or a non-tweet page.")

        except (TimeoutException, WebDriverException) as e:
            retries += 1
            wait_time = INITIAL_WAIT_TIME * (2 ** (retries - 1)) + random.uniform(0, 2)
            print(f"Rate limit or WebDriver error while scraping {url}: {e}. Retrying in {wait_time:.2f} seconds (Attempt {retries}/{MAX_RETRIES}).")
            time.sleep(wait_time)
            if retries == MAX_RETRIES:
                print(f"Max retries reached for {url}. Skipping.")
                return tweet_data # Return current data, likely "N/A"
        except Exception as e:
            print(f"An unexpected error occurred while scraping {url}: {e}")
            return tweet_data # Return current data for other unexpected errors
        else:
            break # Break out of retry loop if successful
    return tweet_data

def download_image(image_url, tweet_id, image_index, output_dir="tweet_markdowns"):
    """Downloads an image from a URL and returns its local path."""
    
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

            # Extract file extension from URL or default to .jpg
            file_extension = os.path.splitext(image_url.split('?')[0])[1]
            if not file_extension:
                file_extension = ".jpg" # Default if no extension found

            image_filename = f"{tweet_id}_image_{image_index}{file_extension}"
            local_image_path = os.path.join(output_dir, image_filename)

            with open(local_image_path, 'wb') as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    out_file.write(chunk)
            print(f"Downloaded image: {local_image_path}")
            return local_image_path
        except requests.exceptions.RequestException as e:
            retries += 1
            wait_time = INITIAL_WAIT_TIME * (2 ** (retries - 1)) + random.uniform(0, 2)
            print(f"Error downloading image {image_url}: {e}. Retrying in {wait_time:.2f} seconds (Attempt {retries}/{MAX_RETRIES}).")
            time.sleep(wait_time)
            if retries == MAX_RETRIES:
                print(f"Max retries reached for image {image_url}. Skipping.")
                return None
        else:
            break # Break out of retry loop if successful
    return local_image_path if retries < MAX_RETRIES else None

def format_tweet_as_markdown(tweet_data):
    markdown_content = f"## Original Tweet URL: {tweet_data['url']}\n\n"
    markdown_content += f"### Tweet Text:\n{tweet_data['text']}\n\n"
    if tweet_data['images']:
        markdown_content += "### Attached Images:\n"
        for img_path in tweet_data['images']: # Now expects local paths
            # Use relative path for markdown embedding
            relative_img_path = os.path.basename(img_path)
            markdown_content += f"- ![]({relative_img_path})\n"
        markdown_content += "\n"
    markdown_content += "---\n\n" # Separator for tweets
    return markdown_content

# Constant for driver rotation
SCRAPE_BATCH_SIZE = 20 # Restart driver after this many scrapes

def main(urls_to_scrape=None):
    """
    Main function to orchestrate tweet scraping.
    Args:
        urls_to_scrape (list, optional): A list of Twitter/X URLs to scrape.
                                         If None, URLs are read from 'ai_news_links.txt'.
    """
    if urls_to_scrape:
        tweet_urls = urls_to_scrape
    else:
        urls = read_urls_from_file('ai_news_links.txt')
        if not urls:
            print("No URLs found in 'ai_news_links.txt'.")
            return

        tweet_urls = filter_tweet_urls(urls)
        if not tweet_urls:
            print("No Twitter/X URLs found in the provided file or list.")
            return

    driver = None
    scrape_counter = 0

    try:
        for i, url in enumerate(tweet_urls):
            # Driver rotation logic
            if driver is None or scrape_counter >= SCRAPE_BATCH_SIZE:
                if driver:
                    print(f"Restarting ChromeDriver after {scrape_counter} scrapes...")
                    driver.quit()
                driver = setup_driver()
                if not driver:
                    print("Failed to set up ChromeDriver. Exiting.")
                    return
                scrape_counter = 0 # Reset counter after driver restart

            print(f"Scraping ({i+1}/{len(tweet_urls)}): {url}")
            
            tweet_data = None
            try:
                tweet_data = scrape_tweet(driver, url)
            except WebDriverException as e:
                print(f"Fatal WebDriver error during scrape of {url}: {e}. Attempting driver restart.")
                if driver:
                    driver.quit()
                driver = setup_driver()
                if not driver:
                    print("Failed to set up ChromeDriver after error. Exiting.")
                    return
                # Re-attempt scrape with new driver, or just log and continue
                # For simplicity, we'll just log and continue to the next URL
                # A more robust solution might re-add the URL to a retry queue
                tweet_data = {"url": url, "text": "N/A", "images": []} # Mark as failed

            if tweet_data and (tweet_data["text"] != "N/A" or tweet_data["images"]): # Only save if some content was scraped
                markdown_output = format_tweet_as_markdown(tweet_data)
                tweet_id_match = re.search(r'status/(\d+)', tweet_data['url'])
                tweet_id = tweet_id_match.group(1) if tweet_id_match else "unknown_tweet"
                output_filename = os.path.join("tweet_markdowns", f"tweet_{tweet_id}.md")
                
                os.makedirs("tweet_markdowns", exist_ok=True)
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(markdown_output)
                print(f"Generated Markdown: {output_filename}")
            else:
                print(f"Skipping Markdown creation for {url} due to no content scraped.")
            
            scrape_counter += 1
            # Add a small delay between tweet scrapes to reduce rate limit issues
            time.sleep(random.uniform(2, 5)) # Wait between 2 and 5 seconds
    finally:
        if driver:
            driver.quit()
        print("Scraping complete.")

if __name__ == "__main__":
    main()
