import os
import datetime
import subprocess
import logging
import shutil
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_scrape_newsletter():
    """
    Executes scrape_newsletter.py to generate ai_news_links.txt.
    """
    logging.info("Starting newsletter scraping...")
    try:
        result = subprocess.run(
            ["python", "scrape_newsletter.py"],
            check=True,
            capture_output=True,
            text=True
        )
        logging.info("scrape_newsletter.py executed successfully.")
        logging.debug(f"scrape_newsletter.py stdout:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"scrape_newsletter.py stderr:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running scrape_newsletter.py: {e}")
        logging.error(f"Stdout: {e.stdout}")
        logging.error(f"Stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        logging.error("Error: scrape_newsletter.py not found. Ensure it's in the current directory.")
        raise

def read_and_filter_urls(input_filepath='ai_news_links.txt'):
    """
    Reads URLs from the input file, categorizes them, and returns
    lists of non-Twitter/X/Discord links and Twitter/X links.
    """
    logging.info(f"Reading and filtering URLs from {input_filepath}...")
    all_urls = []
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url:
                    all_urls.append(url)
    except FileNotFoundError:
        logging.error(f"Error: Input file {input_filepath} not found.")
        raise
    except Exception as e:
        logging.error(f"Error reading URLs from {input_filepath}: {e}")
        raise

    non_social_urls = []
    twitter_x_urls = []

    for url in all_urls:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        if "twitter.com" in domain or "x.com" in domain:
            twitter_x_urls.append(url)
        elif "discord.com" in domain:
            # Discord links are explicitly excluded from sources.txt as per task
            logging.info(f"Excluding Discord link from sources: {url}")
            pass
        else:
            non_social_urls.append(url)
    
    logging.info(f"Found {len(non_social_urls)} non-social links and {len(twitter_x_urls)} Twitter/X links.")
    return non_social_urls, twitter_x_urls

def write_sources_file(urls, output_filepath):
    """
    Writes a list of URLs to a specified file.
    """
    logging.info(f"Writing non-social URLs to {output_filepath}...")
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
        logging.info(f"Successfully wrote {len(urls)} URLs to {output_filepath}.")
    except Exception as e:
        logging.error(f"Error writing sources file {output_filepath}: {e}")
        raise

def run_tweet_scraper(tweet_urls, output_dir="tweet_markdowns"):
    """
    Executes tweet_scraper.py with the filtered Twitter/X URLs.
    """
    logging.info(f"Starting tweet scraping for {len(tweet_urls)} Twitter/X URLs...")
    try:
        # Call tweet_scraper.py directly with the list of URLs
        # tweet_scraper.py's main function accepts a list of URLs to scrape.
        import tweet_scraper
        tweet_scraper.main(urls_to_scrape=tweet_urls)
        
        logging.info("tweet_scraper.py executed successfully.")
    except ImportError:
        logging.error("Error: tweet_scraper.py could not be imported. Ensure it's in the current directory and valid Python.")
        raise
    except Exception as e:
        logging.error(f"Error running tweet_scraper.py: {e}")
        raise
    finally:
        # No temporary file to clean up in this version
        pass


def create_output_folder():
    """
    Creates a new directory for today's AI News Issue.
    Returns the path to the created folder.
    """
    today_date = datetime.date.today().strftime("%Y-%m-%d")
    output_folder_name = f"{today_date}_AI_News_Issue"
    output_folder_path = os.path.join(os.getcwd(), output_folder_name)

    logging.info(f"Creating output folder: {output_folder_path}...")
    try:
        os.makedirs(output_folder_path, exist_ok=True)
        logging.info(f"Output folder created: {output_folder_path}")
        return output_folder_path
    except Exception as e:
        logging.error(f"Error creating output folder {output_folder_path}: {e}")
        raise

def move_files_to_output_folder(output_folder_path, sources_filepath, tweet_markdowns_dir="tweet_markdowns"):
    """
    Moves generated files (sources.txt, tweet markdowns, and images)
    into the new output folder.
    """
    logging.info(f"Moving generated files to {output_folder_path}...")

    # Move sources.txt
    try:
        if os.path.exists(sources_filepath):
            shutil.move(sources_filepath, os.path.join(output_folder_path, os.path.basename(sources_filepath)))
            logging.info(f"Moved {sources_filepath} to {output_folder_path}")
        else:
            logging.warning(f"sources.txt not found at {sources_filepath}. Skipping move.")
    except Exception as e:
        logging.error(f"Error moving {sources_filepath}: {e}")

    # Move tweet markdowns and images
    try:
        if os.path.exists(tweet_markdowns_dir) and os.path.isdir(tweet_markdowns_dir):
            for item_name in os.listdir(tweet_markdowns_dir):
                item_path = os.path.join(tweet_markdowns_dir, item_name)
                if os.path.isfile(item_path):
                    shutil.move(item_path, os.path.join(output_folder_path, item_name))
                    logging.info(f"Moved {item_name} from {tweet_markdowns_dir} to {output_folder_path}")
            # Clean up the original tweet_markdowns directory if it's empty
            if not os.listdir(tweet_markdowns_dir):
                os.rmdir(tweet_markdowns_dir)
                logging.info(f"Cleaned up empty directory: {tweet_markdowns_dir}")
            else:
                logging.warning(f"Directory {tweet_markdowns_dir} is not empty after moving files. Remaining items: {os.listdir(tweet_markdowns_dir)}")
        else:
            logging.warning(f"Tweet markdowns directory {tweet_markdowns_dir} not found or is not a directory. Skipping move.")
    except Exception as e:
        logging.error(f"Error moving files from {tweet_markdowns_dir}: {e}")

def main():
    """
    Orchestrates the entire process of building the AI News Issue.
    """
    sources_filepath = 'sources.txt'
    ai_news_links_filepath = 'ai_news_links.txt'

    try:
        # Step 1: Run scrape_newsletter.py
        run_scrape_newsletter()

        # Step 2: Read and Filter URLs
        non_social_urls, twitter_x_urls = read_and_filter_urls(ai_news_links_filepath)
        write_sources_file(non_social_urls, sources_filepath)

        # Step 3: Create Output Folder
        output_folder_path = create_output_folder()

        # Step 4: Run tweet_scraper.py and move files
        run_tweet_scraper(twitter_x_urls)
        move_files_to_output_folder(output_folder_path, sources_filepath)

        # Clean up ai_news_links.txt
        if os.path.exists(ai_news_links_filepath):
            os.remove(ai_news_links_filepath)
            logging.info(f"Cleaned up {ai_news_links_filepath}")

        logging.info("AI News Issue build process completed successfully!")

    except Exception as e:
        logging.critical(f"AI News Issue build process failed: {e}")
        # Attempt to clean up any intermediate files in case of failure
        if os.path.exists(sources_filepath):
            os.remove(sources_filepath)
            logging.info(f"Cleaned up {sources_filepath} due to error.")
        if os.path.exists(ai_news_links_filepath):
            os.remove(ai_news_links_filepath)
            logging.info(f"Cleaned up {ai_news_links_filepath} due to error.")
        # Note: tweet_markdowns directory cleanup is handled by move_files_to_output_folder
        # if it successfully moves files, or can be left for manual inspection if partial.

if __name__ == "__main__":
    main()