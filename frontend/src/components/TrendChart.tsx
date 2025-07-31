import React, { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
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
  market_share?: number;
  daily_data: DailyData[];
}

type ChartType = 'line' | 'stacked' | 'bar';

interface TrendChartProps {
  data: { [key: string]: SiteData };
  metric: 'players_online' | 'cash_players' | 'peak_24h' | 'seven_day_avg';
  title: string;
}

const TrendChart: React.FC<TrendChartProps> = ({ data, metric, title }) => {
  const [chartType, setChartType] = useState<ChartType>('stacked');
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

  // Prepare datasets based on chart type
  const datasets = sortedSites.map(([siteName, siteData], index) => {
    const dataPoints = sortedDates.map(date => {
      const dayData = siteData.daily_data.find(
        d => new Date(d.date).toLocaleDateString() === date
      );
      return dayData ? dayData[metric] : null;
    });

    const baseDataset = {
      label: `${siteName} (현재: ${siteData.current_stats[metric].toLocaleString()})`,
      data: dataPoints,
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length] + '40',
      borderWidth: 1
    };

    // Configure dataset based on chart type
    switch (chartType) {
      case 'stacked':
        return {
          ...baseDataset,
          fill: index === 0 ? 'origin' : '-1',
          tension: 0.1,
          pointRadius: 2,
          pointHoverRadius: 4
        };
      case 'line':
        return {
          ...baseDataset,
          fill: false,
          tension: 0.1,
          pointRadius: 3,
          pointHoverRadius: 5,
          backgroundColor: colors[index % colors.length] + '20'
        };
      case 'bar':
        return {
          ...baseDataset,
          backgroundColor: colors[index % colors.length] + '80',
          borderWidth: 0
        };
      default:
        return baseDataset;
    }
  });

  const chartData = {
    labels: sortedDates,
    datasets: datasets
  };

  const getChartOptions = (): ChartOptions<'line' | 'bar'> => {
    return {
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
            
            if (value !== null) {
              const siteName = label.split(' (')[0];
              label = `${siteName}: ${value.toLocaleString()}`;
            }
            
            return label;
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        stacked: chartType === 'stacked' || chartType === 'bar',
        title: {
          display: true,
          text: 'Date'
        }
      },
      y: {
        display: true,
        stacked: chartType === 'stacked' || chartType === 'bar',
        beginAtZero: true,
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
  };

  const renderChart = () => {
    const options = getChartOptions();
    
    if (chartType === 'bar') {
      return <Bar data={chartData} options={options as ChartOptions<'bar'>} />;
    } else {
      return <Line data={chartData} options={options as ChartOptions<'line'>} />;
    }
  };

  return (
    <div style={{ marginBottom: '2rem' }}>
      {/* Chart Type Selection Buttons */}
      <div style={{ 
        display: 'flex', 
        gap: '10px', 
        marginBottom: '15px',
        justifyContent: 'center',
        flexWrap: 'wrap'
      }}>
        <button
          onClick={() => setChartType('line')}
          style={{
            padding: '8px 16px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            backgroundColor: chartType === 'line' ? '#007bff' : '#fff',
            color: chartType === 'line' ? '#fff' : '#333',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: chartType === 'line' ? 'bold' : 'normal'
          }}
        >
          📈 선형 차트
        </button>
        <button
          onClick={() => setChartType('stacked')}
          style={{
            padding: '8px 16px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            backgroundColor: chartType === 'stacked' ? '#007bff' : '#fff',
            color: chartType === 'stacked' ? '#fff' : '#333',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: chartType === 'stacked' ? 'bold' : 'normal'
          }}
        >
          📊 누적 차트
        </button>
        <button
          onClick={() => setChartType('bar')}
          style={{
            padding: '8px 16px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            backgroundColor: chartType === 'bar' ? '#007bff' : '#fff',
            color: chartType === 'bar' ? '#fff' : '#333',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: chartType === 'bar' ? 'bold' : 'normal'
          }}
        >
          📊 막대 차트
        </button>
      </div>
      
      {/* Chart Container */}
      <div style={{ height: '400px' }}>
        {renderChart()}
      </div>
    </div>
  );
};

export default TrendChart;