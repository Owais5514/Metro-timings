import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone, timedelta
import os
import hashlib
from urllib.parse import urljoin
import sys
import json
import time
import logging

# --- Logging Configuration ---
LOG_FILE = "metro_rss_generator.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Configuration ---
# Metro-related news and updates sources
METRO_SOURCES = [
    {
        'name': 'Dhaka Metro Rail',
        'url': 'https://dmtcl.gov.bd/site/notices',
        'selector': 'div.notice-item',
        'title_selector': 'h4 a, h3 a, .title',
        'summary_selector': '.excerpt, .description, p',
        'link_selector': 'a',
        'date_selector': '.date, .published-date, time'
    },
    {
        'name': 'Bangladesh Railway',
        'url': 'https://railway.gov.bd/site/notices',
        'selector': 'div.notice-item, .news-item',
        'title_selector': 'h4 a, h3 a, .title',
        'summary_selector': '.excerpt, .description, p',
        'link_selector': 'a',
        'date_selector': '.date, .published-date, time'
    }
]

RSS_FILENAME = "metro_feed.xml"
MAX_FEED_ITEMS = 50
FEED_TITLE = "Dhaka Metro & Public Transport Updates"
FEED_LINK = "https://owais5514.github.io/Metro-timings/"
FEED_DESCRIPTION = "Latest updates on Dhaka Metro Rail (MRT), public transport, and transit announcements."

# Define the local timezone (Bangladesh Standard Time = UTC+6)
LOCAL_TIMEZONE = timezone(timedelta(hours=6))

# Cache file for storing the last check's content hash
CACHE_FILE = "metro_cache.json"

def check_for_new_content():
    """Checks if there are new updates by comparing page content hash with previous run.
    Returns True if new content is available or cache doesn't exist, False otherwise."""
    
    # Check if we need to force a refresh (weekly)
    force_refresh = False
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
                if 'last_check' in cache:
                    last_check = datetime.fromisoformat(cache['last_check'])
                    now = datetime.now(timezone.utc)
                    # Force refresh if last check was more than 7 days ago
                    if (now - last_check).days >= 7:
                        logging.info("Performing weekly forced refresh regardless of content change")
                        force_refresh = True
        except (json.JSONDecodeError, IOError, ValueError) as e:
            logging.warning(f"Could not check last refresh time: {e}")
            
    if force_refresh:
        return True
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try to load previously saved hash
        cache = {}
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Could not load cache file: {e}")
        
        # Check each source for changes
        combined_content = ""
        for source in METRO_SOURCES:
            try:
                response = requests.get(source['url'], headers=headers, timeout=15)
                if response.status_code == 200:
                    combined_content += response.text
            except Exception as e:
                logging.warning(f"Could not fetch {source['name']}: {e}")
                continue
        
        if not combined_content:
            logging.warning("No content fetched from any source")
            return True  # Proceed anyway to be safe
            
        content_hash = hashlib.md5(combined_content.encode()).hexdigest()
        
        # If we have a previous hash and it matches, no new content
        if 'content_hash' in cache and cache['content_hash'] == content_hash:
            logging.info("Content hash matches previous check, no new updates")
            return False
            
        # Save new hash for next time
        new_cache = {
            'content_hash': content_hash,
            'last_check': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(new_cache, f)
        except IOError as e:
            logging.warning(f"Could not save cache file: {e}")
            
        logging.info("New content detected, will process updates")
        return True
        
    except Exception as e:
        logging.error(f"Error checking for new content: {e}")
        # If any error occurs, proceed with processing to be safe
        return True

def fetch_metro_updates():
    """Fetches and parses metro updates from various sources."""
    all_updates = []
    
    for source in METRO_SOURCES:
        logging.info(f"Fetching updates from {source['name']}: {source['url']}")
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(source['url'], headers=headers, timeout=30)
                response.raise_for_status()
                logging.info(f"Successfully fetched {source['name']}. Status code: {response.status_code}")
                break
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logging.warning(f"Error fetching {source['url']}: {e}. Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Error fetching {source['url']} after {max_retries} attempts: {e}")
                    continue

        # Parse the content
        try:
            soup = BeautifulSoup(response.content, 'lxml')
            update_elements = soup.select(source['selector'])
            
            if not update_elements:
                logging.warning(f"No update elements found for {source['name']} using selector '{source['selector']}'")
                continue
                
            logging.info(f"Found {len(update_elements)} potential update elements for {source['name']}")
            
            for element in update_elements:
                try:
                    # Extract title
                    title_tag = element.select_one(source['title_selector'])
                    title = title_tag.get_text(strip=True) if title_tag else None
                    
                    if not title:
                        continue
                    
                    # Extract summary
                    summary_tag = element.select_one(source['summary_selector'])
                    summary = summary_tag.get_text(strip=True) if summary_tag else ''
                    
                    # Extract link
                    link_tag = element.select_one(source['link_selector'])
                    link = None
                    if link_tag and link_tag.get('href'):
                        link = link_tag['href']
                        if not link.startswith(('http://', 'https://')):
                            link = urljoin(source['url'], link)
                    else:
                        link = source['url']
                    
                    # Generate GUID
                    if link and link != source['url']:
                        guid = link
                        is_permalink = True
                    else:
                        guid_content = f"{title}-{summary}-{source['name']}"
                        guid = hashlib.sha1(guid_content.encode('utf-8')).hexdigest()
                        is_permalink = False
                    
                    # Extract or generate date
                    pub_date = None
                    date_tag = element.select_one(source['date_selector'])
                    if date_tag:
                        date_text = date_tag.get_text(strip=True)
                        # Try to parse various date formats
                        for date_format in ['%Y-%m-%d', '%d-%m-%Y', '%b %d, %Y', '%B %d, %Y']:
                            try:
                                parsed_date = datetime.strptime(date_text, date_format)
                                now_bd = datetime.now(LOCAL_TIMEZONE)
                                local_dt = parsed_date.replace(hour=now_bd.hour, minute=now_bd.minute, second=now_bd.second)
                                aware_local_dt = local_dt.replace(tzinfo=LOCAL_TIMEZONE)
                                pub_date = aware_local_dt.astimezone(timezone.utc)
                                break
                            except ValueError:
                                continue
                    
                    # Fallback to current time if date parsing failed
                    if pub_date is None:
                        pub_date = datetime.now(timezone.utc)
                    
                    description = summary if summary else title
                    
                    logging.info(f"Found update from {source['name']}: Title='{title}', Link='{link}', Date='{pub_date}'")
                    all_updates.append({
                        'title': f"[{source['name']}] {title}",
                        'link': link,
                        'guid': guid,
                        'is_permalink': is_permalink,
                        'pub_date': pub_date,
                        'description': description,
                        'source': source['name']
                    })
                    
                except Exception as e:
                    logging.warning(f"Error processing update element from {source['name']}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error parsing content from {source['name']}: {e}")
            continue
    
    # Add some default/static content if no updates are found
    if not all_updates:
        logging.info("No updates found from sources, adding default content")
        default_update = {
            'title': 'Dhaka Metro Timetable Available',
            'link': FEED_LINK,
            'guid': 'metro-timings-default',
            'is_permalink': True,
            'pub_date': datetime.now(timezone.utc),
            'description': 'Check the latest Dhaka MRT-6 metro timetable and schedule information.',
            'source': 'Metro Timings'
        }
        all_updates.append(default_update)
    
    logging.info(f"Total updates collected: {len(all_updates)}")
    return all_updates

def load_existing_feed_guids(filename):
    """Loads GUIDs from an existing RSS feed file."""
    existing_guids = set()
    if not os.path.exists(filename):
        logging.info(f"No existing feed file found at {filename}. Starting fresh.")
        return existing_guids

    logging.info(f"Loading existing GUIDs from {filename}...")
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        for item in root.findall('./channel/item'):
            guid = item.find('guid')
            if guid is not None and guid.text:
                existing_guids.add(guid.text)
        logging.info(f"Loaded {len(existing_guids)} existing GUIDs.")
    except ET.ParseError as e:
        logging.warning(f"Could not parse existing feed file {filename}. Error: {e}. Starting fresh.")
    except FileNotFoundError:
        logging.warning(f"File {filename} not found error during parsing. Starting fresh.")
    return existing_guids

def generate_rss_feed(updates, existing_guids, filename):
    """Generates and saves the RSS feed XML file."""
    logging.info("Generating new RSS feed...")
    root = ET.Element("rss", version="2.0", attrib={"xmlns:atom": "http://www.w3.org/2005/Atom"})
    channel = ET.SubElement(root, "channel")

    # GitHub Pages URL for the RSS feed
    gh_pages_url = f"https://owais5514.github.io/Metro-timings/{filename}"
    atom_link = ET.SubElement(channel, "atom:link", href=gh_pages_url, rel="self", type="application/rss+xml")

    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = FEED_LINK
    ET.SubElement(channel, "description").text = FEED_DESCRIPTION
    ET.SubElement(channel, "language").text = "en-US"
    ET.SubElement(channel, "copyright").text = "Metro Timings"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    ET.SubElement(channel, "generator").text = "Metro RSS Generator Script"
    
    # Add a version element that changes with each run
    current_timestamp = datetime.now().strftime("%Y%m%d.%H%M%S")
    ET.SubElement(channel, "version").text = f"1.0.{current_timestamp}"

    combined_items_data = []
    new_items_added = 0

    for update in updates:
        if update['guid'] not in existing_guids:
            combined_items_data.append(update)
            new_items_added += 1

    logging.info(f"Adding {new_items_added} new item(s) based on GUID comparison.")

    # Add old items if we need to fill up to MAX_FEED_ITEMS
    num_old_items_to_add = MAX_FEED_ITEMS - new_items_added
    if num_old_items_to_add > 0 and os.path.exists(filename):
        logging.info(f"Loading max {num_old_items_to_add} old items from existing feed...")
        try:
            tree = ET.parse(filename)
            old_root = tree.getroot()
            loaded_old_items = 0
            for old_item in old_root.findall('./channel/item'):
                guid_elem = old_item.find('guid')
                if guid_elem is not None and guid_elem.text and guid_elem.text not in [item['guid'] for item in combined_items_data]:
                    old_update_data = {
                        'title': old_item.find('title').text if old_item.find('title') is not None else '',
                        'link': old_item.find('link').text if old_item.find('link') is not None else FEED_LINK,
                        'guid': guid_elem.text,
                        'is_permalink': guid_elem.get('isPermaLink', 'false') == 'true',
                        'description': old_item.find('description').text if old_item.find('description') is not None else '',
                        'pub_date': datetime.now(timezone.utc)  # Default/Fallback
                    }
                    pub_date_elem = old_item.find('pubDate')
                    if pub_date_elem is not None and pub_date_elem.text:
                        try:
                            old_update_data['pub_date'] = datetime.strptime(pub_date_elem.text, "%a, %d %b %Y %H:%M:%S %z")
                        except ValueError:
                            try:
                                old_update_data['pub_date'] = datetime.strptime(pub_date_elem.text, "%a, %d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc)
                            except ValueError:
                                logging.warning(f"Could not parse old date '{pub_date_elem.text}' for GUID {guid_elem.text}. Using current time.")
                    combined_items_data.append(old_update_data)
                    loaded_old_items += 1
                    if loaded_old_items >= num_old_items_to_add:
                        break
            logging.info(f"Added {loaded_old_items} old items.")
        except (ET.ParseError, FileNotFoundError) as e:
            logging.warning(f"Could not parse or find old feed to append items. Error: {e}.")

    logging.info(f"Sorting {len(combined_items_data)} combined items by publication date (newest first)...")
    combined_items_data.sort(key=lambda x: x['pub_date'], reverse=True)

    items_added_to_xml = 0
    for item_data in combined_items_data[:MAX_FEED_ITEMS]:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = item_data['title']
        ET.SubElement(item, "link").text = item_data['link']
        ET.SubElement(item, "description").text = item_data['description']
        ET.SubElement(item, "pubDate").text = item_data['pub_date'].strftime("%a, %d %b %Y %H:%M:%S %z")
        ET.SubElement(item, "guid", isPermaLink=str(item_data['is_permalink']).lower()).text = item_data['guid']
        items_added_to_xml += 1

    logging.info(f"Added {items_added_to_xml} total items to the feed XML.")

    xml_str = ET.tostring(root, encoding='utf-8', method='xml')
    try:
        pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding='utf-8')
    except Exception as parse_err:
        logging.warning(f"Could not prettify XML output using minidom. Error: {parse_err}. Saving raw XML.")
        pretty_xml_str = xml_str

    try:
        with open(filename, "wb") as f:
            f.write(pretty_xml_str)
        logging.info(f"RSS feed successfully generated and saved to {filename}")
    except IOError as e:
        logging.error(f"Error writing RSS feed file {filename}: {e}")

if __name__ == "__main__":
    start_time = datetime.now()
    logging.info(f"Starting Metro updates RSS generation process...")
    logging.info(f"Local time: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')} (Timezone Offset: {LOCAL_TIMEZONE})")
    
    try:
        # Check for new content first
        if not check_for_new_content():
            logging.info("No new content detected, skipping RSS generation")
            sys.exit(0)
        
        # Fetch updates
        fetched_updates = fetch_metro_updates()

        # Load existing GUIDs
        current_guids = load_existing_feed_guids(RSS_FILENAME)

        # Determine if there are new updates by comparing fetched GUIDs to existing ones
        new_updates_found = False
        if fetched_updates:
            for update in fetched_updates:
                if update['guid'] not in current_guids:
                    new_updates_found = True
                    logging.info(f"New update found: GUID {update['guid']} Title: {update['title']}")
                    break

        # Generate feed ONLY if new updates were found
        if new_updates_found:
            logging.info("New updates detected based on GUID comparison. Generating updated RSS feed.")
            generate_rss_feed(fetched_updates, current_guids, RSS_FILENAME)
        else:
            if not fetched_updates:
                logging.info("No updates were fetched from any source.")
            else:
                logging.info("No new updates found based on GUID comparison with the existing feed.")
            logging.info("RSS feed generation skipped.")

        end_time = datetime.now()
        logging.info(f"Process finished. Duration: {end_time - start_time}")
    except Exception as e:
        logging.error(f"Unexpected error during execution: {e}", exc_info=True)
        sys.exit(1)
