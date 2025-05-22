import requests
from bs4 import BeautifulSoup
import os

def scrape_newsletter_links():
    """
    Scrapes links from the most recent newsletter on smol.ai/issues.
    """
    archive_url = "https://news.smol.ai/issues"
    newsletter_links = []

    try:
        # Step 1 & 2: Navigate to archive and find the most recent newsletter URL
        print(f"Navigating to archive page: {archive_url}")
        archive_response = requests.get(archive_url)
        archive_response.raise_for_status() # Raise an exception for bad status codes
        archive_soup = BeautifulSoup(archive_response.content, 'html.parser')

        # Find all links that point to an issue page
        # Select the first 'a' tag that is a direct child of a div with class 'arrow-card' and has an href starting with '/issues/'
        # This assumes the website lists the most recent issue link first.
        issue_links = archive_soup.select('div.arrow-card > a[href^="/issues/"]')

        if not issue_links:
            print("Could not find any potential newsletter links on the archive page.")
            return

        # Assuming the first link in the list is the most recent
        latest_newsletter_link_tag = issue_links[0]

        latest_newsletter_url = latest_newsletter_link_tag['href']
        # Ensure it's an absolute URL
        if not latest_newsletter_url.startswith('http'):
             latest_newsletter_url = f"https://news.smol.ai{latest_newsletter_url}"


        print(f"Found latest newsletter URL: {latest_newsletter_url}")

        # Verify the extracted URL is a specific issue URL
        if latest_newsletter_url == archive_url:
            print("Error: Extracted URL is the archive URL, not a specific issue.")
            return

        # Step 3 & 4: Navigate to the newsletter and scrape links
        print(f"Navigating to newsletter page: {latest_newsletter_url}")
        newsletter_response = requests.get(latest_newsletter_url)
        newsletter_response.raise_for_status() # Raise an exception for bad status codes
        newsletter_soup = BeautifulSoup(newsletter_response.content, 'html.parser')

        # Scrape all href attributes from a tags
        print("Scraping links from the newsletter page...")
        for link in newsletter_soup.find_all('a', href=True):
            href = link['href']
            # Step 5: Handle Twitter/X links (simple extraction for now)
            # The reference to selenium-twitter-scraper is noted but not implemented
            # in this basic version as per instructions.
            newsletter_links.append(href)

        # Filter for full URLs (starting with http:// or https://)
        filtered_links = [link for link in newsletter_links if link.startswith('http://') or link.startswith('https://')]

        # Step 6: Write collected links to a file
        output_filename = "ai_news_links.txt"
        with open(output_filename, 'w') as f:
            for link in filtered_links:
                f.write(f"{link}\n")

        print(f"Successfully wrote {len(filtered_links)} filtered links to {output_filename}")

    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    scrape_newsletter_links()