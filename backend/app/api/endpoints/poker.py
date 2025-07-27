from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database.database import get_db
from ...crud import crud
from ...schemas import schemas
from ...services.poker_crawler import LivePokerScoutCrawler
from datetime import datetime

router = APIRouter()

@router.post("/crawl_and_save_data/")
async def crawl_and_save_data(db: Session = Depends(get_db)):
    crawler = LivePokerScoutCrawler()
    crawled_data = crawler.crawl_pokerscout_data()

    if not crawled_data:
        raise HTTPException(status_code=500, detail="Failed to crawl data from PokerScout.")

    for site_data in crawled_data:
        site = crud.get_site_by_name(db, site_data['site_name'])
        if not site:
            site_create = schemas.SiteCreate(name=site_data['site_name'], category=site_data['category'])
            site = crud.create_site(db, site_create)

        daily_stat_create = schemas.DailyStatCreate(
            site_id=site.id,
            collected_at=datetime.fromisoformat(site_data['collected_at']),
            players_online=site_data['players_online'],
            cash_players=site_data['cash_players'],
            peak_24h=site_data['peak_24h'],
            seven_day_avg=site_data['seven_day_avg']
        )
        crud.create_daily_stat(db, daily_stat_create)

    return {"message": "Data crawled and saved successfully!", "count": len(crawled_data)}

@router.get("/sites/", response_model=list[schemas.Site])
def get_sites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sites = crud.get_all_sites(db, skip=skip, limit=limit)
    return sites

@router.get("/sites_with_latest_stats/", response_model=list[schemas.SiteWithLatestStats])
def get_sites_with_latest_stats(db: Session = Depends(get_db)):
    sites_with_stats = crud.get_sites_with_latest_stats(db)
    return sites_with_stats

@router.get("/sites/{site_id}/stats/", response_model=list[schemas.DailyStat])
def get_site_stats(site_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    stats = crud.get_daily_stats_by_site_id(db, site_id=site_id, skip=skip, limit=limit)
    return stats
