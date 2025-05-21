import os
import sys
from time import sleep
from dotenv import load_dotenv # Added import

# Load environment variables from .env file
load_dotenv()

# Add selenium-twitter-scraper to sys.path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'selenium-twitter-scraper'))

from scraper.twitter_scraper import Twitter_Scraper
from scraper.tweet import Tweet # Assuming Tweet class handles individual tweet data

# Environment variables for Twitter credentials (ensure these are set)
# TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME")
# TWITTER_PASSWORD = os.environ.get("TWITTER_PASSWORD")
# TWITTER_EMAIL = os.environ.get("TWITTER_EMAIL") # The scraper might need email for login

# --- Helper function to extract tweet data (to be refined) ---
def extract_data_from_tweet_object(tweet_obj):
    """
    Extracts text and image URLs from the scraper's tweet object.
    This will need to be adjusted based on the actual structure of the Tweet class
    from the selenium-twitter-scraper.
    """
    text_content = ""
    image_urls = []

    if hasattr(tweet_obj, 'content'):
        text_content = tweet_obj.content
    else:
        text_content = "Could not extract tweet text." # Fallback

    # Placeholder for image extraction - this needs to be accurate
    # based on how the selenium scraper stores image information.
    # For example, if tweet_obj.photos is a list of image URLs:
    if hasattr(tweet_obj, 'photos') and isinstance(tweet_obj.photos, list):
        image_urls.extend(tweet_obj.photos)
    # Or if there's another attribute for media:
    # if hasattr(tweet_obj, 'media_urls') and isinstance(tweet_obj.media_urls, list):
    #     image_urls.extend(tweet_obj.media_urls)

    # The selenium scraper's Tweet class has card.find_elements("xpath", './/div[@data-testid="tweetPhoto"]//img')
    # We need to see how to access this after the scrape.
    # For now, this is a placeholder.
    if hasattr(tweet_obj, 'card'):
        try:
            # This is a guess based on typical tweet structures, might need adjustment
            # to match what selenium-twitter-scraper's Tweet class actually finds.
            img_elements = tweet_obj.card.find_elements("xpath", './/div[@data-testid="tweetPhoto"]//img[@src]')
            for img_el in img_elements:
                src = img_el.get_attribute('src')
                if src and ('twimg.com' in src or 'pbs.twimg.com' in src): # Check for Twitter image URLs
                    image_urls.append(src)
        except Exception as e:
            print(f"Error extracting images from tweet card: {e}")


    return text_content, list(set(image_urls)) # Return unique image URLs

# --- Main function to scrape a single tweet ---
def scrape_single_tweet_selenium(tweet_url: str):
    """
    Scrapes a single tweet using the selenium-twitter-scraper.
    Args:
        tweet_url: The full URL of the tweet.
    Returns:
        A tuple (text_content, image_urls) or (None, None) if scraping fails.
    """
    print(f"Selenium: Attempting to scrape tweet: {tweet_url}")

    # Credentials - consider a more secure way to handle these if deploying
    # For now, relying on environment variables as suggested by the scraper's README
    twitter_email = os.environ.get("TWITTER_EMAIL") # Scraper seems to use 'mail'
    twitter_username = os.environ.get("TWITTER_USERNAME") # Scraper uses 'username' for handle like @user
    twitter_password = os.environ.get("TWITTER_PASSWORD")

    if not all([twitter_email, twitter_username, twitter_password]):
        print("Error: Twitter credentials (TWITTER_EMAIL, TWITTER_USERNAME, TWITTER_PASSWORD) not found in environment variables.")
        print("Please set them to use the Selenium scraper.")
        return None, None

    try:
        # The scraper is designed to scrape based on query, username, hashtag etc.
        # We need to adapt it for a single tweet URL.
        # One approach: use the search functionality with the tweet URL.
        # The `scrape_query` parameter in Twitter_Scraper seems relevant.
        
        # Initialize the scraper
        # headlessState='yes' for no browser window, 'no' to see the browser
        scraper_instance = Twitter_Scraper(
            mail=twitter_email,
            username=twitter_username, # This is the @handle for login
            password=twitter_password,
            headlessState='no', # Changed to 'no' for debugging
            max_tweets=1, # We only want one tweet
            scrape_query=tweet_url, # Use the tweet URL as a search query
            scrape_latest=True # Try to get the latest, should be the tweet itself
        )

        # Login
        if not scraper_instance.login():
            print(f"Selenium: Login failed for {twitter_username}")
            scraper_instance.driver.quit()
            return None, None
        
        print("Selenium: Login successful.")

        # The scraper's main logic is in `scrape()`.
        # We need to see how it returns data or how to access the scraped tweet.
        # The `scrape()` method in the provided `twitter_scraper.py` seems to collect
        # tweets into `self.data`. We need to inspect this.

        scraper_instance.scrape() # This will run the configured scraping task

        if scraper_instance.interrupted:
            print("Selenium: Scraping was interrupted.")
            if hasattr(scraper_instance, 'driver'):
                scraper_instance.driver.quit()
            return None, None # Or handle as appropriate

        # After scraping, the data should be in scraper_instance.data
        # This list likely contains Tweet objects or dictionaries.
        if scraper_instance.data:
            raw_tweet_data = scraper_instance.data[0] # Assuming the first item is our tweet
            print("---------- RAW TWEET DATA ----------")
            print(raw_tweet_data)
            print(type(raw_tweet_data))
            # Try to print attributes if it's an object
            if hasattr(raw_tweet_data, '__dict__'):
                print("---------- RAW TWEET DATA (ATTRIBUTES) ----------")
                for attr, value in raw_tweet_data.__dict__.items():
                    print(f"{attr}: {value}")
            print("------------------------------------")
            raise SystemExit("Stopping for inspection of raw_tweet_data.") # Stop execution here
            # ... rest of the logic will be skipped for now
        else:
            print("Selenium: No data scraped.")
            if hasattr(scraper_instance, 'driver'):
                scraper_instance.driver.quit()
            return None, None

    except SystemExit as e: # Catch the SystemExit to allow clean script termination for inspection
        print(e)
        if 'scraper_instance' in locals() and hasattr(scraper_instance, 'driver'):
            scraper_instance.driver.quit()
        return None, None # Indicate that normal processing didn't complete
    except Exception as e:
        print(f"Selenium: An error occurred while scraping {tweet_url}: {e}")
        if 'scraper_instance' in locals() and hasattr(scraper_instance, 'driver'):
            scraper_instance.driver.quit()
        return None, None

if __name__ == '__main__':
    # Example usage (for testing this module directly)
    # Make sure to set your TWITTER_EMAIL, TWITTER_USERNAME, TWITTER_PASSWORD env vars
    test_tweet_url = "https://twitter.com/elonmusk/status/1793364230056202389" # Replace with a valid, recent tweet URL
    
    print(f"Testing direct scrape of: {test_tweet_url}")
    content, images = scrape_single_tweet_selenium(test_tweet_url)

    if content:
        print("\\n--- Tweet Text ---")
        print(content)
        if images:
            print("\\n--- Images ---")
            for img_url in images:
                print(img_url)
        else:
            print("\\nNo images found.")
    else:
        print("\\nFailed to retrieve tweet content.")

