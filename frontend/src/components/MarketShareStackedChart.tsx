import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions,
  TooltipItem
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler // 필요한 플러그인 추가
);

interface DailyData {
  date: string;
  players_online: number;
  cash_players: number;
  peak_24h: number;
  seven_day_avg: number;
}

interface SiteData {
  current_stats: {
    site_name: string;
    players_online: number;
    cash_players: number;
    peak_24h: number;
    seven_day_avg: number;
  };
  daily_data: DailyData[];
}

interface MarketShareStackedChartProps {
  data: { [key: string]: SiteData };
  metric: 'players_online' | 'cash_players';
  title: string;
}

const MarketShareStackedChart: React.FC<MarketShareStackedChartProps> = ({ data, metric, title }) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  // Generate colors for each site
  const colors = [
    '#FF6384',
    '#36A2EB',
    '#FFCE56',
    '#4BC0C0',
    '#9966FF',
    '#FF9F40',
    '#C9CBCF',
    '#FF6633',
    '#4BC0C0',
    '#00B3E6',
    '#E6B333',
    '#3366E6',
    '#999966',
    '#99FF99',
    '#B34D4D'
  ];

  // Sort all sites by current metric value
  const allSortedSites = Object.entries(data)
    .sort(([, a], [, b]) => b.current_stats[metric] - a.current_stats[metric]);
  
  // Take top 10 for individual display
  const top10Sites = allSortedSites.slice(0, 10);
  // Get the rest for 'etc' grouping
  const etcSites = allSortedSites.slice(10);

  // Get all unique dates from all sites
  const allDates = new Set<string>();
  Object.values(data).forEach(siteData => {
    siteData.daily_data.forEach(d => {
      allDates.add(new Date(d.date).toLocaleDateString());
    });
  });
  const sortedDates = Array.from(allDates).sort();

  // Calculate 'etc' values for each date
  const etcValuesByDate: { [date: string]: number } = {};
  sortedDates.forEach(date => {
    let etcTotal = 0;
    etcSites.forEach(([, siteData]) => {
      const dayData = siteData.daily_data.find(
        d => new Date(d.date).toLocaleDateString() === date
      );
      if (dayData) {
        etcTotal += dayData[metric];
      }
    });
    etcValuesByDate[date] = etcTotal;
  });

  // Prepare datasets with actual values (not percentage)
  const datasets = top10Sites.map(([siteName, siteData], index) => {
    const dataPoints = sortedDates.map(date => {
      const dayData = siteData.daily_data.find(
        d => new Date(d.date).toLocaleDateString() === date
      );
      return dayData ? dayData[metric] : 0; // Use actual values instead of percentage
    });

    return {
      label: siteName,
      data: dataPoints,
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length],
      fill: true,
      tension: 0.3
    };
  });

  // Add 'etc' dataset if there are sites beyond top 10
  if (etcSites.length > 0) {
    const etcDataPoints = sortedDates.map(date => etcValuesByDate[date] || 0);
    datasets.push({
      label: `Others (${etcSites.length} sites)`,
      data: etcDataPoints,
      borderColor: '#808080',
      backgroundColor: '#808080',
      fill: true,
      tension: 0.3
    });
  }

  const chartData = {
    labels: sortedDates,
    datasets: datasets
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          boxWidth: 12,
          font: {
            size: 11
          }
        }
      },
      title: {
        display: true,
        text: title,
        font: {
          size: 16,
          weight: 'bold'
        }
      },
      tooltip: {
        enabled: false, // 기본 툴팁 비활성화
        mode: 'index',
        intersect: false,
        external: function(context) {
          // 툴팁 엘리먼트 가져오기
          const tooltipEl = document.getElementById('chartjs-tooltip');
          
          // 첫 렌더링 시 툴팁 엘리먼트 생성
          if (!tooltipEl) {
            const div = document.createElement('div');
            div.id = 'chartjs-tooltip';
            div.style.position = 'absolute';
            div.style.background = 'rgba(0, 0, 0, 0.9)';
            div.style.borderRadius = '6px';
            div.style.color = 'white';
            div.style.padding = '12px';
            div.style.pointerEvents = 'none';
            div.style.fontSize = '12px';
            div.style.fontFamily = 'Arial, sans-serif';
            div.style.transition = 'all 0.1s ease';
            div.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
            document.body.appendChild(div);
          }
          
          const tooltip = context.tooltip;
          const tooltipDiv = document.getElementById('chartjs-tooltip')!;
          
          // 툴팁 숨기기
          if (tooltip.opacity === 0) {
            tooltipDiv.style.opacity = '0';
            setHoveredIndex(null);
            return;
          }
          
          // 툴팁 내용 구성
          if (tooltip.body) {
            const titleLines = tooltip.title || [];
            const bodyLines = tooltip.body.map((item: any) => item.lines);
            
            let innerHtml = '<div>';
            
            // 제목 추가
            titleLines.forEach((title: string) => {
              innerHtml += `<div style="font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 4px;">${title}</div>`;
            });
            
            // 데이터 추가 (상위 5개만 표시)
            const dataItems = tooltip.dataPoints || [];
            const sortedItems = dataItems
              .filter((item: any) => item.raw > 0)
              .sort((a: any, b: any) => b.raw - a.raw)
              .slice(0, 10); // 상위 10개만 표시
            
            sortedItems.forEach((item: any, index: number) => {
              const color = item.dataset.borderColor;
              const value = item.raw;
              const label = item.dataset.label;
              
              // 천 단위 구분 및 K/M 단위로 축약
              let formattedValue = value.toLocaleString();
              if (value >= 1000000) {
                formattedValue = (value / 1000000).toFixed(1) + 'M';
              } else if (value >= 10000) {
                formattedValue = (value / 1000).toFixed(0) + 'K';
              }
              
              innerHtml += `
                <div style="display: flex; align-items: center; margin: 4px 0;">
                  <div style="width: 12px; height: 12px; background: ${color}; margin-right: 8px; border-radius: 2px;"></div>
                  <div style="flex: 1;">${label}</div>
                  <div style="font-weight: bold; margin-left: 12px;">${formattedValue}</div>
                </div>
              `;
            });
            
            if (dataItems.length > 10) {
              innerHtml += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2); font-style: italic; opacity: 0.7;">...and ${dataItems.length - 10} more</div>`;
            }
            
            innerHtml += '</div>';
            tooltipDiv.innerHTML = innerHtml;
          }
          
          // 위치 계산
          const position = context.chart.canvas.getBoundingClientRect();
          
          // 툴팁 표시
          tooltipDiv.style.opacity = '1';
          
          // 차트 우측에 툴팁 표시
          const tooltipX = position.left + tooltip.caretX + 20;
          const tooltipY = position.top + window.pageYOffset + tooltip.caretY - 50;
          
          // 화면 경계 체크
          const tooltipWidth = tooltipDiv.offsetWidth;
          const tooltipHeight = tooltipDiv.offsetHeight;
          
          // 우측 경계 체크
          if (tooltipX + tooltipWidth > window.innerWidth) {
            tooltipDiv.style.left = (position.left + tooltip.caretX - tooltipWidth - 20) + 'px';
          } else {
            tooltipDiv.style.left = tooltipX + 'px';
          }
          
          // 하단 경계 체크
          if (tooltipY + tooltipHeight > window.innerHeight + window.pageYOffset) {
            tooltipDiv.style.top = (tooltipY - tooltipHeight) + 'px';
          } else {
            tooltipDiv.style.top = tooltipY + 'px';
          }
          
          setHoveredIndex(tooltip.dataPoints?.[0]?.dataIndex ?? null);
        }
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Date'
        }
      },
      y: {
        stacked: true,
        display: true,
        title: {
          display: true,
          text: metric === 'players_online' ? 'Players Online' : 'Cash Players'
        },
        min: 0,
        ticks: {
          callback: function(value) {
            return value.toLocaleString();
          }
        }
      }
    }
  };

  // 컴포넌트 언마운트 시 툴팁 정리
  useEffect(() => {
    return () => {
      const tooltipEl = document.getElementById('chartjs-tooltip');
      if (tooltipEl) {
        tooltipEl.remove();
      }
    };
  }, []);

  return (
    <div style={{ height: '500px', marginBottom: '2rem', position: 'relative' }}>
      <Line data={chartData} options={options} />
    </div>
  );
};

export default MarketShareStackedChart;