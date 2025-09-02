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
  Filler
);

interface LineChartProps {
  title?: string;
  data: number[];
  labels: string[];
  color?: string;
  gradient?: boolean;
  height?: number;
}

const LineChart: React.FC<LineChartProps> = ({ 
  data, 
  labels, 
  color = '#3B82F6', 
  gradient = true,
  height = 180
}) => {
  const chartRef = React.useRef<ChartJS<'line'>>(null);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Price Trend',
        data,
        borderColor: color,
        backgroundColor: gradient 
          ? (context: any) => {
              const canvas = context.chart.ctx.canvas;
              const ctx = context.chart.ctx;
              const gradientFill = ctx.createLinearGradient(0, 0, 0, canvas.height);
              gradientFill.addColorStop(0, `${color}20`);
              gradientFill.addColorStop(1, `${color}05`);
              return gradientFill;
            }
          : `${color}20`,
        borderWidth: 2,
        fill: gradient,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'white',
        titleColor: '#1f2937',
        bodyColor: '#6b7280',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: false,
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: '#9ca3af',
          font: {
            size: 11,
          },
        },
      },
      y: {
        grid: {
          color: '#f3f4f6',
        },
        ticks: {
          color: '#9ca3af',
          font: {
            size: 11,
          },
          callback: (value: any) => `$${value}k`,
        },
      },
    },
  };

  return (
    <div style={{ height: `${height}px` }}>
      <Line ref={chartRef} data={chartData} options={options} />
    </div>
  );
};

export default LineChart;
