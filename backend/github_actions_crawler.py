#!/usr/bin/env python3
"""
GitHub Actions용 직접 크롤링 스크립트
서버 없이 직접 Firebase에 데이터를 저장
"""
import sys
import os
import logging
from datetime import datetime

# Add backend to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_github_actions_crawl():
    """GitHub Actions에서 실행되는 직접 크롤링"""
    logger.info("=== GitHub Actions Crawling Start ===")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path[:3]}")
    
    try:
        # Import crawler modules
        logger.info("Importing crawler modules...")
        from app.services.poker_crawler import LivePokerScoutCrawler, upload_to_firestore_efficiently
        logger.info("Import successful!")
        
        # Create crawler instance
        logger.info("Creating crawler instance...")
        crawler = LivePokerScoutCrawler()
        
        # Crawl data
        logger.info("Starting crawl...")
        crawled_data = crawler.crawl_pokerscout_data()
        
        if crawled_data:
            logger.info(f"Crawl success: {len(crawled_data)} sites found")
            
            # Log first few sites for verification
            for i, site in enumerate(crawled_data[:3]):
                logger.info(f"Sample {i+1}: {site.get('name', 'Unknown')} - {site.get('players_online', 0)} players")
            
            # Upload to Firebase
            logger.info("Uploading to Firebase...")
            upload_to_firestore_efficiently(crawled_data)
            logger.info("Firebase upload complete!")
            
            # Calculate totals
            total_players = sum(site.get('players_online', 0) for site in crawled_data)
            logger.info(f"Total players online across all sites: {total_players:,}")
            
            return True
        else:
            logger.error("ERROR: No data crawled")
            return False
            
    except ImportError as e:
        logger.error(f"Import Error: {e}")
        logger.error("Directory contents:")
        
        # List directory structure for debugging
        for root, dirs, files in os.walk('.'):
            level = root.replace('.', '').count(os.sep)
            indent = ' ' * 2 * level
            logger.error(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # Limit to 5 files per dir
                logger.error(f"{subindent}{file}")
        
        return False
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_github_actions_crawl()
    logger.info("=== Crawling Complete ===")
    sys.exit(0 if success else 1)