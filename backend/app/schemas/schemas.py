from pydantic import BaseModel
from datetime import datetime
from typing import Union

class SiteBase(BaseModel):
    name: str
    category: str

class SiteCreate(SiteBase):
    pass

class Site(SiteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DailyStatBase(BaseModel):
    players_online: int
    cash_players: int
    peak_24h: int
    seven_day_avg: int

class DailyStatCreate(DailyStatBase):
    site_id: int
    collected_at: datetime

class DailyStat(DailyStatBase):
    id: int
    site_id: int
    collected_at: datetime

    class Config:
        from_attributes = True

class SiteWithLatestStats(SiteBase):
    id: int
    latest_players_online: Union[int, None] = None
    latest_cash_players: Union[int, None] = None
    latest_peak_24h: Union[int, None] = None
    latest_seven_day_avg: Union[int, None] = None

    class Config:
        from_attributes = True
