import React from 'react';
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
  ChartOptions
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

  // Sort sites by current metric value and take top 10
  const sortedSites = Object.entries(data)
    .sort(([, a], [, b]) => b.current_stats[metric] - a.current_stats[metric])
    .slice(0, 10);

  // Get all unique dates
  const allDates = new Set<string>();
  sortedSites.forEach(([, siteData]) => {
    siteData.daily_data.forEach(d => {
      allDates.add(new Date(d.date).toLocaleDateString());
    });
  });
  const sortedDates = Array.from(allDates).sort();

  // Calculate total for each date to compute percentages
  const totalsByDate: { [date: string]: number } = {};
  sortedDates.forEach(date => {
    let total = 0;
    sortedSites.forEach(([, siteData]) => {
      const dayData = siteData.daily_data.find(
        d => new Date(d.date).toLocaleDateString() === date
      );
      if (dayData) {
        total += dayData[metric];
      }
    });
    totalsByDate[date] = total;
  });

  // Prepare datasets with percentage values
  const datasets = sortedSites.map(([siteName, siteData], index) => {
    const dataPoints = sortedDates.map(date => {
      const dayData = siteData.daily_data.find(
        d => new Date(d.date).toLocaleDateString() === date
      );
      const value = dayData ? dayData[metric] : 0;
      const total = totalsByDate[date] || 1;
      return (value / total) * 100; // Convert to percentage
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
        mode: 'index',
        intersect: false,
        callbacks: {
          label: function(context) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            
            if (value !== null) {
              return `${label}: ${value.toFixed(2)}%`;
            }
            
            return label;
          },
          afterLabel: function(context) {
            // 실제 플레이어 수도 표시
            const date = sortedDates[context.dataIndex];
            const siteName = context.dataset.label || '';
            const siteData = data[siteName];
            if (siteData) {
              const dayData = siteData.daily_data.find(
                d => new Date(d.date).toLocaleDateString() === date
              );
              if (dayData) {
                return `(${dayData[metric].toLocaleString()} players)`;
              }
            }
            return '';
          }
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
          text: 'Market Share (%)'
        },
        min: 0,
        max: 100,
        ticks: {
          callback: function(value) {
            return value + '%';
          }
        }
      }
    }
  };

  return (
    <div style={{ height: '500px', marginBottom: '2rem' }}>
      <Line data={chartData} options={options} />
    </div>
  );
};

export default MarketShareStackedChart;