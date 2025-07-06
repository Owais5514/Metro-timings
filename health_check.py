#!/usr/bin/env python3
"""
Health Check Script for Metro RSS Feed System
Monitors the RSS generation system and reports status
"""

import requests
import xml.etree.ElementTree as ET
import json
import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
RSS_URL = "https://owais5514.github.io/Metro-timings/metro_feed.xml"
RSS_FILE = "metro_feed.xml"
CACHE_FILE = "metro_cache.json"
LOG_FILE = "metro_rss_generator.log"
HEALTH_REPORT_FILE = "health_report.json"

def check_local_files():
    """Check if required local files exist and are readable."""
    print("🔍 Checking local files...")
    
    status = {
        'rss_file_exists': os.path.exists(RSS_FILE),
        'cache_file_exists': os.path.exists(CACHE_FILE),
        'log_file_exists': os.path.exists(LOG_FILE),
        'script_file_exists': os.path.exists('generate_metro_rss.py')
    }
    
    for file_type, exists in status.items():
        file_name = file_type.replace('_exists', '').replace('_', ' ').title()
        status_icon = "✅" if exists else "❌"
        print(f"  {status_icon} {file_name}")
    
    # Check file sizes and modification times
    if status['rss_file_exists']:
        rss_stat = os.stat(RSS_FILE)
        rss_size = rss_stat.st_size
        rss_modified = datetime.fromtimestamp(rss_stat.st_mtime)
        print(f"     RSS file size: {rss_size} bytes")
        print(f"     RSS last modified: {rss_modified}")
        status['rss_file_size'] = rss_size
        status['rss_last_modified'] = rss_modified.isoformat()
    
    if status['log_file_exists']:
        log_stat = os.stat(LOG_FILE)
        log_size = log_stat.st_size
        log_modified = datetime.fromtimestamp(log_stat.st_mtime)
        print(f"     Log file size: {log_size} bytes")
        print(f"     Log last modified: {log_modified}")
        status['log_file_size'] = log_size
        status['log_last_modified'] = log_modified.isoformat()
    
    return status

def check_rss_feed_health():
    """Check the health of the RSS feed content."""
    print("\n📰 Checking RSS feed health...")
    
    if not os.path.exists(RSS_FILE):
        print("❌ RSS file not found locally")
        return {'healthy': False, 'error': 'RSS file not found'}
    
    try:
        tree = ET.parse(RSS_FILE)
        root = tree.getroot()
        channel = root.find('channel')
        
        if channel is None:
            print("❌ Invalid RSS structure - no channel")
            return {'healthy': False, 'error': 'Invalid RSS structure'}
        
        items = channel.findall('item')
        item_count = len(items)
        
        print(f"📊 Feed contains {item_count} items")
        
        # Check last build date
        last_build_date = channel.find('lastBuildDate')
        if last_build_date is not None and last_build_date.text:
            try:
                build_date = parsedate_to_datetime(last_build_date.text)
                hours_since_build = (datetime.now(timezone.utc) - build_date).total_seconds() / 3600
                print(f"🕐 Last build: {build_date} ({hours_since_build:.1f} hours ago)")
                
                if hours_since_build > 24:
                    print("⚠️  Feed hasn't been updated in over 24 hours")
                elif hours_since_build > 12:
                    print("⚠️  Feed hasn't been updated in over 12 hours")
                else:
                    print("✅ Feed was recently updated")
                    
            except Exception as e:
                print(f"⚠️  Could not parse build date: {e}")
        
        # Check item freshness
        if item_count > 0:
            recent_items = 0
            now = datetime.now(timezone.utc)
            
            for item in items:
                pub_date = item.find('pubDate')
                if pub_date is not None and pub_date.text:
                    try:
                        item_date = parsedate_to_datetime(pub_date.text)
                        days_old = (now - item_date).days
                        
                        if days_old <= 7:  # Items from last 7 days
                            recent_items += 1
                    except Exception:
                        pass
            
            print(f"📅 Recent items (last 7 days): {recent_items}/{item_count}")
        
        # Validate basic RSS structure
        title = channel.find('title')
        link = channel.find('link')
        description = channel.find('description')
        
        if not all([title is not None and title.text,
                   link is not None and link.text,
                   description is not None and description.text]):
            print("❌ Missing required RSS channel elements")
            return {'healthy': False, 'error': 'Missing required RSS elements'}
        
        print("✅ RSS feed structure is healthy")
        
        return {
            'healthy': True,
            'item_count': item_count,
            'recent_items': recent_items if 'recent_items' in locals() else 0,
            'last_build': last_build_date.text if last_build_date is not None else None,
            'hours_since_build': hours_since_build if 'hours_since_build' in locals() else None
        }
        
    except ET.ParseError as e:
        print(f"❌ RSS XML parsing error: {e}")
        return {'healthy': False, 'error': f'XML parsing error: {e}'}
    except Exception as e:
        print(f"❌ RSS health check error: {e}")
        return {'healthy': False, 'error': f'Health check error: {e}'}

def check_remote_accessibility():
    """Check if the RSS feed is accessible remotely."""
    print("\n🌐 Checking remote accessibility...")
    
    try:
        headers = {
            'User-Agent': 'Metro-RSS-HealthCheck/1.0',
            'Accept': 'application/rss+xml, application/xml, text/xml'
        }
        
        response = requests.get(RSS_URL, headers=headers, timeout=15)
        
        print(f"📡 HTTP Status: {response.status_code}")
        print(f"📏 Content Length: {len(response.content)} bytes")
        print(f"📋 Content Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            # Try to parse remote content
            try:
                remote_root = ET.fromstring(response.content)
                remote_channel = remote_root.find('channel')
                
                if remote_channel is not None:
                    remote_items = remote_channel.findall('item')
                    print(f"📊 Remote feed has {len(remote_items)} items")
                    
                    # Compare with local if available
                    if os.path.exists(RSS_FILE):
                        local_tree = ET.parse(RSS_FILE)
                        local_channel = local_tree.getroot().find('channel')
                        local_items = local_channel.findall('item')
                        
                        if len(remote_items) == len(local_items):
                            print("✅ Remote and local feeds have same item count")
                        else:
                            print(f"⚠️  Item count mismatch: remote={len(remote_items)}, local={len(local_items)}")
                
                print("✅ Remote RSS feed is accessible and valid")
                return {
                    'accessible': True,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'remote_item_count': len(remote_items) if 'remote_items' in locals() else 0
                }
                
            except ET.ParseError as e:
                print(f"❌ Remote feed has invalid XML: {e}")
                return {'accessible': False, 'error': f'Invalid XML: {e}'}
                
        else:
            print(f"❌ Remote feed returned status {response.status_code}")
            return {'accessible': False, 'status_code': response.status_code}
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - remote feed not accessible")
        return {'accessible': False, 'error': 'Timeout'}
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - remote feed not accessible")
        return {'accessible': False, 'error': 'Connection error'}
    except Exception as e:
        print(f"❌ Remote accessibility check error: {e}")
        return {'accessible': False, 'error': str(e)}

def check_cache_status():
    """Check the status of the cache file and recent processing."""
    print("\n💾 Checking cache status...")
    
    if not os.path.exists(CACHE_FILE):
        print("⚠️  Cache file not found - this is normal for first run")
        return {'cache_exists': False}
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        print("✅ Cache file loaded successfully")
        
        if 'last_check' in cache_data:
            last_check = datetime.fromisoformat(cache_data['last_check'])
            hours_since_check = (datetime.now(timezone.utc) - last_check).total_seconds() / 3600
            print(f"🕐 Last check: {last_check} ({hours_since_check:.1f} hours ago)")
        
        if 'content_hash' in cache_data:
            print(f"🔑 Content hash: {cache_data['content_hash'][:8]}...")
        
        return {
            'cache_exists': True,
            'last_check': cache_data.get('last_check'),
            'hours_since_check': hours_since_check if 'hours_since_check' in locals() else None,
            'has_content_hash': 'content_hash' in cache_data
        }
        
    except json.JSONDecodeError as e:
        print(f"❌ Cache file has invalid JSON: {e}")
        return {'cache_exists': True, 'error': f'Invalid JSON: {e}'}
    except Exception as e:
        print(f"❌ Cache check error: {e}")
        return {'cache_exists': True, 'error': str(e)}

def check_recent_logs():
    """Check recent log entries for errors or issues."""
    print("\n📋 Checking recent logs...")
    
    if not os.path.exists(LOG_FILE):
        print("⚠️  Log file not found")
        return {'log_exists': False}
    
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            print("⚠️  Log file is empty")
            return {'log_exists': True, 'empty': True}
        
        print(f"📄 Log file has {len(lines)} lines")
        
        # Check last few lines for recent activity
        recent_lines = lines[-20:] if len(lines) > 20 else lines
        
        error_count = 0
        warning_count = 0
        info_count = 0
        
        for line in recent_lines:
            if ' - ERROR - ' in line:
                error_count += 1
            elif ' - WARNING - ' in line:
                warning_count += 1
            elif ' - INFO - ' in line:
                info_count += 1
        
        print(f"📊 Recent log entries: {error_count} errors, {warning_count} warnings, {info_count} info")
        
        if error_count > 0:
            print("❌ Recent errors found in logs")
            # Show last error
            for line in reversed(recent_lines):
                if ' - ERROR - ' in line:
                    print(f"   Last error: {line.strip()}")
                    break
        elif warning_count > 0:
            print("⚠️  Recent warnings found in logs")
        else:
            print("✅ No recent errors or warnings")
        
        return {
            'log_exists': True,
            'line_count': len(lines),
            'recent_errors': error_count,
            'recent_warnings': warning_count,
            'recent_info': info_count
        }
        
    except Exception as e:
        print(f"❌ Log check error: {e}")
        return {'log_exists': True, 'error': str(e)}

def generate_health_report():
    """Generate a comprehensive health report."""
    print("\n🏥 Generating comprehensive health report...")
    
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'overall_health': 'unknown',
        'checks': {}
    }
    
    # Run all health checks
    report['checks']['local_files'] = check_local_files()
    report['checks']['rss_health'] = check_rss_feed_health()
    report['checks']['remote_access'] = check_remote_accessibility()
    report['checks']['cache_status'] = check_cache_status()
    report['checks']['recent_logs'] = check_recent_logs()
    
    # Determine overall health
    critical_issues = 0
    warnings = 0
    
    # Check for critical issues
    if not report['checks']['local_files'].get('rss_file_exists', False):
        critical_issues += 1
    
    if not report['checks']['rss_health'].get('healthy', False):
        critical_issues += 1
    
    if not report['checks']['remote_access'].get('accessible', False):
        warnings += 1  # Remote access issues are warnings, not critical
    
    if report['checks']['recent_logs'].get('recent_errors', 0) > 0:
        critical_issues += 1
    
    # Determine overall status
    if critical_issues == 0:
        if warnings == 0:
            report['overall_health'] = 'healthy'
        else:
            report['overall_health'] = 'healthy_with_warnings'
    else:
        report['overall_health'] = 'unhealthy'
    
    # Save report
    try:
        with open(HEALTH_REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"💾 Health report saved to {HEALTH_REPORT_FILE}")
    except Exception as e:
        print(f"⚠️  Could not save health report: {e}")
    
    return report

def main():
    print("🚇 Metro RSS Feed Health Check")
    print("=" * 50)
    
    # Generate comprehensive health report
    health_report = generate_health_report()
    
    # Print summary
    print("\n" + "=" * 50)
    print("🏥 HEALTH CHECK SUMMARY")
    print("=" * 50)
    
    overall_health = health_report['overall_health']
    
    if overall_health == 'healthy':
        print("🎉 System is healthy!")
        exit_code = 0
    elif overall_health == 'healthy_with_warnings':
        print("⚠️  System is healthy but has some warnings")
        exit_code = 0
    else:
        print("💥 System has health issues that need attention")
        exit_code = 1
    
    # Print key metrics
    rss_health = health_report['checks']['rss_health']
    if isinstance(rss_health, dict) and rss_health.get('healthy'):
        print(f"📊 RSS Items: {rss_health.get('item_count', 'Unknown')}")
        if rss_health.get('hours_since_build') is not None:
            print(f"🕐 Last Update: {rss_health['hours_since_build']:.1f} hours ago")
    
    remote_access = health_report['checks']['remote_access']
    if isinstance(remote_access, dict) and remote_access.get('accessible'):
        print("🌐 Remote access: ✅ Available")
    else:
        print("🌐 Remote access: ❌ Issues detected")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
