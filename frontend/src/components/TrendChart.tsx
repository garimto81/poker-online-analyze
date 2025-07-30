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
  Legend
);

interface DailyData {
  date: string;
  players_online: number;
  cash_players: number;
  peak_24h: number;
  seven_day_avg: number;
  market_share?: number;
}

interface SiteData {
  current_stats: {
    site_name: string;
    players_online: number;
    cash_players: number;
    peak_24h: number;
    seven_day_avg: number;
  };
  market_share: number;
  daily_data: DailyData[];
}

interface TrendChartProps {
  data: { [key: string]: SiteData };
  metric: 'players_online' | 'cash_players' | 'peak_24h' | 'seven_day_avg';
  title: string;
}

const TrendChart: React.FC<TrendChartProps> = ({ data, metric, title }) => {
  // Generate colors for each site
  const colors = [
    '#FF6384',
    '#36A2EB',
    '#FFCE56',
    '#4BC0C0',
    '#9966FF',
    '#FF9F40',
    '#FF6384',
    '#C9CBCF',
    '#4BC0C0',
    '#36A2EB'
  ];

  // Get all unique dates
  const allDates = new Set<string>();
  Object.values(data).forEach(siteData => {
    siteData.daily_data.forEach(d => {
      allDates.add(new Date(d.date).toLocaleDateString());
    });
  });
  const sortedDates = Array.from(allDates).sort();

  // Prepare datasets
  const datasets = Object.entries(data).map(([siteName, siteData], index) => {
    const dataPoints = sortedDates.map(date => {
      const dayData = siteData.daily_data.find(
        d => new Date(d.date).toLocaleDateString() === date
      );
      return dayData ? dayData[metric] : null;
    });

    // Store market share data for tooltip
    const marketShareData = sortedDates.map(date => {
      const dayData = siteData.daily_data.find(
        d => new Date(d.date).toLocaleDateString() === date
      );
      return dayData ? dayData.market_share : null;
    });

    return {
      label: `${siteName} (현재: ${siteData.market_share}%)`,
      data: dataPoints,
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length] + '20',
      tension: 0.1,
      pointRadius: 3,
      pointHoverRadius: 5,
      marketShareData: marketShareData
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
        position: 'top' as const,
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
            let label = context.dataset.label || '';
            const value = context.parsed.y;
            const marketShare = (context.dataset as any).marketShareData?.[context.dataIndex];
            
            if (value !== null) {
              const siteName = label.split(' (')[0];
              label = `${siteName}: ${value.toLocaleString()}`;
              
              if (marketShare !== null && marketShare !== undefined) {
                label += ` (${marketShare}%)`;
              }
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
        display: true,
        title: {
          display: true,
          text: metric === 'players_online' ? 'Players' : 
                 metric === 'cash_players' ? 'Cash Players' :
                 metric === 'peak_24h' ? '24h Peak' : '7-Day Average'
        },
        ticks: {
          callback: function(value) {
            return value.toLocaleString();
          }
        }
      }
    }
  };

  return (
    <div style={{ height: '400px', marginBottom: '2rem' }}>
      <Line data={chartData} options={options} />
    </div>
  );
};

export default TrendChart;