#!/usr/bin/env python3
"""
수집된 포커 사이트 데이터 상세 표시
"""
import sys
import os
import logging
from datetime import datetime
import json
from tabulate import tabulate

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def collect_and_display_data():
    """데이터 수집 및 상세 표시"""
    try:
        from github_actions_crawler_firestore import LivePokerScoutCrawler
        
        # 크롤러 인스턴스 생성 및 데이터 수집
        crawler = LivePokerScoutCrawler()
        logger.info("PokerScout.com에서 최신 데이터 수집 중...")
        data = crawler.crawl_pokerscout_data()
        
        if not data:
            logger.error("데이터를 수집할 수 없습니다.")
            return None
        
        # 수집 시간
        collection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n" + "="*100)
        print(f"POKERSCOUT 실시간 데이터 리포트")
        print(f"수집 시간: {collection_time}")
        print("="*100)
        
        # 전체 통계
        total_players = sum(site['players_online'] for site in data)
        total_cash = sum(site['cash_players'] for site in data)
        total_peak = sum(site['peak_24h'] for site in data)
        total_avg = sum(site['seven_day_avg'] for site in data)
        
        print(f"\n[전체 시장 통계]")
        print("-"*50)
        print(f"총 사이트 수: {len(data)}개")
        print(f"전체 온라인 플레이어: {total_players:,}명")
        print(f"전체 캐시 게임 플레이어: {total_cash:,}명")
        print(f"24시간 피크 합계: {total_peak:,}명")
        print(f"7일 평균 합계: {total_avg:,}명")
        
        # 온라인 플레이어 기준 정렬
        data_sorted = sorted(data, key=lambda x: x['players_online'], reverse=True)
        
        # 상위 20개 사이트 상세 정보
        print(f"\n[상위 20개 사이트 상세 정보]")
        print("-"*100)
        
        table_data = []
        for i, site in enumerate(data_sorted[:20], 1):
            # 시장 점유율 계산
            market_share = (site['players_online'] / total_players * 100) if total_players > 0 else 0
            
            table_data.append([
                i,
                site['site_name'][:25],  # 이름이 너무 길면 자르기
                f"{site['players_online']:,}",
                f"{site['cash_players']:,}",
                f"{site['peak_24h']:,}",
                f"{site['seven_day_avg']:,}",
                f"{market_share:.1f}%",
                site['category']
            ])
        
        headers = ["순위", "사이트명", "온라인", "캐시", "24h 피크", "7일 평균", "점유율", "카테고리"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # GG 네트워크 분석
        gg_sites = [s for s in data if s['category'] == 'GG_POKER']
        if gg_sites:
            gg_total = sum(s['players_online'] for s in gg_sites)
            gg_share = (gg_total / total_players * 100) if total_players > 0 else 0
            
            print(f"\n[GG 네트워크 분석]")
            print("-"*50)
            print(f"GG 네트워크 사이트 수: {len(gg_sites)}개")
            print(f"GG 네트워크 총 플레이어: {gg_total:,}명")
            print(f"GG 네트워크 시장 점유율: {gg_share:.1f}%")
            
            for site in gg_sites:
                print(f"  - {site['site_name']}: {site['players_online']:,}명")
        
        # 나머지 모든 사이트 간단히 표시
        if len(data) > 20:
            print(f"\n[나머지 사이트 ({len(data)-20}개)]")
            print("-"*100)
            
            remaining_data = []
            for i, site in enumerate(data_sorted[20:], 21):
                remaining_data.append([
                    i,
                    site['site_name'][:30],
                    f"{site['players_online']:,}",
                    f"{site['cash_players']:,}",
                    f"{site['peak_24h']:,}"
                ])
            
            remaining_headers = ["순위", "사이트명", "온라인", "캐시", "24h 피크"]
            print(tabulate(remaining_data, headers=remaining_headers, tablefmt="simple"))
        
        # 플레이어가 0인 사이트 분석
        zero_players = [s for s in data if s['players_online'] == 0]
        if zero_players:
            print(f"\n[현재 오프라인 사이트 ({len(zero_players)}개)]")
            print("-"*50)
            for site in zero_players:
                peak_info = f"(24h 피크: {site['peak_24h']:,})" if site['peak_24h'] > 0 else ""
                print(f"  - {site['site_name']} {peak_info}")
        
        # JSON 파일로 저장
        output_file = f"poker_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'collection_time': collection_time,
                'total_sites': len(data),
                'total_players': total_players,
                'total_cash_players': total_cash,
                'sites': data_sorted
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n[저장 완료] 전체 데이터가 {output_file}에 저장되었습니다.")
        
        return data
        
    except ImportError:
        logger.error("tabulate 라이브러리가 필요합니다. 설치: pip install tabulate")
        return None
    except Exception as e:
        logger.error(f"데이터 표시 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    collect_and_display_data()