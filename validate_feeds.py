#!/usr/bin/env python3
"""
RSS Feed Validation Script for Metro Timings
Validates RSS feed structure, content, and accessibility
"""

import xml.etree.ElementTree as ET
import requests
import sys
import os
import logging
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def validate_rss_structure(file_path):
    """Validate the basic RSS structure and required elements."""
    print(f"\n🔍 Validating RSS structure for: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Check root element
        if root.tag != 'rss':
            print(f"❌ Invalid root element: expected 'rss', got '{root.tag}'")
            return False
        
        # Check RSS version
        version = root.get('version')
        if version != '2.0':
            print(f"⚠️  RSS version is '{version}', expected '2.0'")
        
        # Check channel
        channel = root.find('channel')
        if channel is None:
            print("❌ No channel element found")
            return False
        
        # Validate required channel elements
        required_elements = ['title', 'link', 'description']
        for element in required_elements:
            elem = channel.find(element)
            if elem is None or not elem.text:
                print(f"❌ Missing or empty required channel element: {element}")
                return False
        
        # Check items
        items = channel.findall('item')
        print(f"📊 Found {len(items)} items in feed")
        
        if len(items) == 0:
            print("⚠️  No items found in feed")
            return True  # Empty feed is valid but worth noting
        
        # Validate item structure
        valid_items = 0
        invalid_items = 0
        
        for i, item in enumerate(items):
            item_valid = True
            
            # Check required item elements
            title = item.find('title')
            link = item.find('link')
            guid = item.find('guid')
            
            if title is None or not title.text:
                print(f"❌ Item {i+1}: Missing or empty title")
                item_valid = False
            
            if link is None or not link.text:
                print(f"❌ Item {i+1}: Missing or empty link")
                item_valid = False
            
            if guid is None or not guid.text:
                print(f"❌ Item {i+1}: Missing or empty GUID")
                item_valid = False
            
            # Check optional but recommended elements
            pub_date = item.find('pubDate')
            description = item.find('description')
            
            if pub_date is None:
                print(f"⚠️  Item {i+1}: Missing pubDate")
            
            if description is None:
                print(f"⚠️  Item {i+1}: Missing description")
            
            if item_valid:
                valid_items += 1
            else:
                invalid_items += 1
        
        print(f"✅ Valid items: {valid_items}")
        if invalid_items > 0:
            print(f"❌ Invalid items: {invalid_items}")
            return False
        
        # Check for duplicate GUIDs
        guids = [item.find('guid').text for item in items if item.find('guid') is not None and item.find('guid').text]
        unique_guids = set(guids)
        
        if len(guids) != len(unique_guids):
            print(f"❌ Found duplicate GUIDs: {len(guids)} total, {len(unique_guids)} unique")
            return False
        
        print("✅ RSS structure validation passed")
        return True
        
    except ET.ParseError as e:
        print(f"❌ XML parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def validate_feed_accessibility(url):
    """Check if the RSS feed is accessible via HTTP."""
    print(f"\n🌐 Checking feed accessibility: {url}")
    
    try:
        headers = {
            'User-Agent': 'RSS-Validator/1.0 (Metro Timings Validation)',
            'Accept': 'application/rss+xml, application/xml, text/xml'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"📡 HTTP Status: {response.status_code}")
        print(f"📏 Content Length: {len(response.content)} bytes")
        print(f"📋 Content Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            # Try to parse the remote content
            try:
                ET.fromstring(response.content)
                print("✅ Remote RSS feed is accessible and valid XML")
                return True
            except ET.ParseError as e:
                print(f"❌ Remote RSS feed is accessible but contains invalid XML: {e}")
                return False
        elif response.status_code == 404:
            print("❌ RSS feed not found (404)")
            return False
        else:
            print(f"⚠️  RSS feed returned status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - feed not accessible")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - feed not accessible")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False

def validate_feed_content(file_path):
    """Validate the content quality and consistency of the RSS feed."""
    print(f"\n📝 Validating feed content quality...")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        channel = root.find('channel')
        items = channel.findall('item')
        
        if len(items) == 0:
            print("⚠️  No items to validate")
            return True
        
        # Check for recent content
        recent_items = 0
        now = datetime.now()
        
        for item in items:
            pub_date = item.find('pubDate')
            if pub_date is not None and pub_date.text:
                try:
                    # Try to parse the date
                    from email.utils import parsedate_to_datetime
                    item_date = parsedate_to_datetime(pub_date.text)
                    days_old = (now - item_date.replace(tzinfo=None)).days
                    
                    if days_old <= 30:  # Consider items from last 30 days as recent
                        recent_items += 1
                except Exception:
                    pass  # Skip date parsing errors
        
        print(f"📅 Recent items (last 30 days): {recent_items}/{len(items)}")
        
        # Check title diversity
        titles = [item.find('title').text for item in items if item.find('title') is not None and item.find('title').text]
        unique_titles = set(titles)
        
        if len(titles) != len(unique_titles):
            duplicate_count = len(titles) - len(unique_titles)
            print(f"⚠️  Found {duplicate_count} duplicate titles")
        else:
            print("✅ All titles are unique")
        
        # Check link validity format
        valid_links = 0
        for item in items:
            link = item.find('link')
            if link is not None and link.text:
                if link.text.startswith(('http://', 'https://')):
                    valid_links += 1
        
        print(f"🔗 Valid HTTP links: {valid_links}/{len(items)}")
        
        print("✅ Content quality validation completed")
        return True
        
    except Exception as e:
        print(f"❌ Content validation error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Validate Metro RSS feeds')
    parser.add_argument('--file', default='metro_feed.xml', help='RSS file to validate')
    parser.add_argument('--url', help='RSS URL to check accessibility')
    parser.add_argument('--skip-remote', action='store_true', help='Skip remote accessibility check')
    
    args = parser.parse_args()
    
    print("🚇 Metro RSS Feed Validator")
    print("=" * 50)
    
    # Default URL if not provided
    if not args.url and not args.skip_remote:
        args.url = "https://owais5514.github.io/Metro-timings/metro_feed.xml"
    
    validation_results = []
    
    # Validate structure
    structure_valid = validate_rss_structure(args.file)
    validation_results.append(('Structure', structure_valid))
    
    # Validate content quality
    content_valid = validate_feed_content(args.file)
    validation_results.append(('Content Quality', content_valid))
    
    # Validate accessibility
    if not args.skip_remote and args.url:
        accessibility_valid = validate_feed_accessibility(args.url)
        validation_results.append(('Accessibility', accessibility_valid))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in validation_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All validations passed!")
        return 0
    else:
        print("\n💥 Some validations failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
