from sqlalchemy.orm import Session
from ..database import models, database
from ..schemas import schemas

def get_site_by_name(db: Session, site_name: str):
    return db.query(models.Site).filter(models.Site.name == site_name).first()

def create_site(db: Session, site: schemas.SiteCreate):
    db_site = models.Site(name=site.name, category=site.category)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site

def create_daily_stat(db: Session, daily_stat: schemas.DailyStatCreate):
    db_daily_stat = models.DailyStat(**daily_stat.dict())
    db.add(db_daily_stat)
    db.commit()
    db.refresh(db_daily_stat)
    return db_daily_stat

def get_daily_stats_by_site_id(db: Session, site_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.DailyStat).filter(models.DailyStat.site_id == site_id).offset(skip).limit(limit).all()

def get_all_sites(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Site).offset(skip).limit(limit).all()

def get_sites_with_latest_stats(db: Session):
    # 각 사이트별 최신 collected_at 값을 가진 daily_stats를 찾기 위한 서브쿼리
    subquery = db.query(
        models.DailyStat.site_id,
        models.DailyStat.collected_at,
        models.DailyStat.players_online,
        models.DailyStat.cash_players,
        models.DailyStat.peak_24h,
        models.DailyStat.seven_day_avg
    ).filter(
        models.DailyStat.collected_at == db.query(
            models.DailyStat.collected_at
        ).filter(
            models.DailyStat.site_id == models.Site.id
        ).order_by(
            models.DailyStat.collected_at.desc()
        ).limit(1).scalar_subquery()
    ).subquery()

    # Site와 최신 daily_stats를 조인하여 결과 반환
    results = db.query(
        models.Site.id,
        models.Site.name,
        models.Site.category,
        subquery.c.players_online,
        subquery.c.cash_players,
        subquery.c.peak_24h,
        subquery.c.seven_day_avg
    ).outerjoin(subquery, models.Site.id == subquery.c.site_id).all()

    # 결과를 SiteWithLatestStats 스키마에 맞게 변환
    formatted_results = []
    for r in results:
        formatted_results.append(schemas.SiteWithLatestStats(
            id=r.id,
            name=r.name,
            category=r.category,
            latest_players_online=r.players_online,
            latest_cash_players=r.cash_players,
            latest_peak_24h=r.peak_24h,
            latest_seven_day_avg=r.seven_day_avg
        ))
    return formatted_results
