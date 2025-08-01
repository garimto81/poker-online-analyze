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
        mode: 'index',
        intersect: false,
        callbacks: {
          label: function(context) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            
            if (value !== null) {
              return `${label}: ${value.toLocaleString()} players`;
            }
            
            return label;
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

  return (
    <div style={{ height: '500px', marginBottom: '2rem' }}>
      <Line data={chartData} options={options} />
    </div>
  );
};

export default MarketShareStackedChart;