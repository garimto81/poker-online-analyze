import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

interface MarketShareData {
  current_stats: {
    site_name: string;
    players_online: number;
  };
  market_share: number;
}

interface MarketShareChartProps {
  data: { [key: string]: MarketShareData };
  totalPlayers: number;
}

const MarketShareChart: React.FC<MarketShareChartProps> = ({ data, totalPlayers }) => {
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

  // Calculate "Others" percentage
  const top10Total = Object.values(data).reduce(
    (sum, site) => sum + site.current_stats.players_online, 
    0
  );
  const othersPercentage = ((totalPlayers - top10Total) / totalPlayers * 100).toFixed(2);

  const chartData = {
    labels: [...Object.keys(data), 'Others'],
    datasets: [
      {
        data: [
          ...Object.values(data).map(site => site.market_share),
          parseFloat(othersPercentage)
        ],
        backgroundColor: [...colors, '#E0E0E0'],
        borderColor: [...colors.map(c => c + 'FF'), '#CCCCCCFF'],
        borderWidth: 2,
        hoverOffset: 4
      }
    ]
  };

  const options: ChartOptions<'pie'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          padding: 15,
          font: {
            size: 12
          },
          generateLabels: function(chart) {
            const chartData = chart.data;
            if (chartData.labels && chartData.datasets.length) {
              return chartData.labels.map((label, i) => {
                const dataset = chartData.datasets[0];
                const value = dataset.data[i] as number;
                const siteData = Object.values(data);
                const playerCount = i < siteData.length 
                  ? siteData[i].current_stats.players_online
                  : totalPlayers - top10Total;
                
                return {
                  text: `${label}: ${value}% (${playerCount.toLocaleString()})`,
                  fillStyle: dataset.backgroundColor ? 
                    (Array.isArray(dataset.backgroundColor) ? dataset.backgroundColor[i] : dataset.backgroundColor) : '',
                  strokeStyle: dataset.borderColor ? 
                    (Array.isArray(dataset.borderColor) ? dataset.borderColor[i] : dataset.borderColor) : '',
                  lineWidth: dataset.borderWidth as number,
                  hidden: false,
                  index: i
                };
              });
            }
            return [];
          }
        }
      },
      title: {
        display: true,
        text: 'Market Share by Online Players',
        font: {
          size: 16,
          weight: 'bold'
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed || 0;
            const index = context.dataIndex;
            const siteData = Object.values(data);
            const playerCount = index < siteData.length 
              ? siteData[index].current_stats.players_online
              : totalPlayers - top10Total;
            
            return `${label}: ${value}% (${playerCount.toLocaleString()} players)`;
          }
        }
      }
    }
  };

  return (
    <div style={{ height: '400px', marginBottom: '2rem' }}>
      <Pie data={chartData} options={options} />
    </div>
  );
};

export default MarketShareChart;