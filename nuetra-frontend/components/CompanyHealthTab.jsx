import React from 'react';
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
  ArcElement,
  Filler
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import { TrendUp, TrendDown, ClipboardList, Heart } from 'lucide-react'; // Example icons, adjust logic as needed
// Assuming lucide-react has similar icons, I'll use standard ones.
import { ArrowUpRight, TrendingDown } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function CompanyHealthTab() {
  // Chart Data Configurations

  const roiChartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Oct', 'Nov', 'Dec'],
    datasets: [
      {
        type: 'line',
        label: 'Program Participation Rate',
        data: [35, 38, 41, 46, 52, 55, 54, 58, 72, 76, 78],
        borderColor: '#8b5cf6',
        backgroundColor: '#8b5cf6',
        borderWidth: 3,
        tension: 0.4,
        yAxisID: 'y1',
        pointRadius: 0,
        pointHoverRadius: 5
      },
      {
        type: 'bar',
        label: 'Absenteeism Reduction',
        data: [45, 48, 50, 54, 57, 59, 62, 64, 66, 68, 70],
        backgroundColor: '#3b82f6',
        borderRadius: 4,
        barPercentage: 0.5,
        yAxisID: 'y'
      }
    ]
  };

  const roiChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false }
    },
    scales: {
      x: { grid: { display: false } },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: { display: true, text: 'Program Participation Rate (%)', font: { size: 10 } },
        min: 0,
        max: 80,
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: { display: true, text: 'Absenteeism Reduction', font: { size: 10 } },
        min: 0,
        max: 100,
        grid: { drawOnChartArea: false },
        ticks: { callback: (value) => value + '%' }
      }
    }
  };

  // Sparklines Data
  const createSparkline = (color, data) => ({
    labels: [1,2,3,4,5,6,7],
    datasets: [{
      data,
      borderColor: color,
      borderWidth: 2,
      tension: 0.4,
      pointRadius: 0
    }]
  });

  const sparklineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    scales: { x: { display: false }, y: { display: false } }
  };

  const topTrendsData = {
    labels: ['Stress Management', 'Weight Management', 'Sleep Improvement', 'Fitness Goals'],
    datasets: [{
      data: [40, 30, 20, 10],
      backgroundColor: [
        '#6366f1', // Indigo
        '#0ea5e9', // Sky blue
        '#84cc16', // Lime green
        '#f59e0b'  // Amber
      ],
      borderRadius: 10,
      barThickness: 16
    }]
  };

  const topTrendsOptions = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { display: false, max: 50 },
      y: { grid: { display: false }, border: { display: false } }
    }
  };

  const donutData = {
    labels: ['Achieved', 'Remaining'],
    datasets: [{
      data: [73, 27],
      backgroundColor: ['#22c55e', '#f1f5f9'],
      borderWidth: 0,
      cutout: '80%'
    }]
  };

  return (
    <div className="w-full flex flex-col gap-6 font-sans">
      
      {/* SECTION 1: ROI Tracker */}
      <div>
        <h3 className="text-lg font-bold text-gray-900 mb-3 px-1">ROI Tracker</h3>
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-[3] bg-white rounded-2xl p-6 shadow-sm border border-gray-100 relative">
            <h4 className="font-semibold text-gray-900 mb-4">Wellness ROI Tracker & Absenteeism Impact</h4>
            <div className="h-64 w-full">
              <Bar data={roiChartData} options={roiChartOptions} />
            </div>
            <div className="text-center mt-2 text-xs text-gray-400">Company Aggregate - HIPAA Compliant</div>
          </div>
          <div className="flex-1 flex flex-col gap-4">
            <div className="flex-1 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-6 text-white shadow-lg flex flex-col justify-center relative overflow-hidden">
              <div className="z-10">
                <h2 className="text-4xl font-extrabold mb-1">-23%</h2>
                <p className="text-blue-100 font-medium">Sick Days</p>
              </div>
              <div className="absolute right-6 top-1/2 -translate-y-1/2 bg-white/20 p-3 rounded-xl backdrop-blur-sm">
                 <ArrowUpRight className="text-white h-6 w-6" />
              </div>
            </div>
            <div className="flex-1 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg flex flex-col justify-center relative overflow-hidden">
              <div className="z-10">
                <h2 className="text-4xl font-extrabold mb-1">+45%</h2>
                <p className="text-purple-100 font-medium">Engagement</p>
              </div>
              <div className="absolute right-6 top-1/2 -translate-y-1/2 bg-white/20 p-3 rounded-xl backdrop-blur-sm">
                 <ArrowUpRight className="text-white h-6 w-6" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 2: Wellness Impact */}
      <div>
        <h3 className="text-lg font-bold text-gray-900 mb-3 px-1">Wellness Impact</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Mental Health Score</p>
              <h3 className="text-2xl font-bold text-gray-900">+18%</h3>
            </div>
            <div className="w-24 h-12">
              <Line data={createSparkline('#3b82f6', [10, 15, 12, 18, 14, 20, 22])} options={sparklineOptions} />
            </div>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Physical Activity</p>
              <h3 className="text-2xl font-bold text-gray-900">+32%</h3>
            </div>
            <div className="w-24 h-12">
              <Line data={createSparkline('#22c55e', [5, 10, 12, 11, 15, 18, 22])} options={sparklineOptions} />
            </div>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Stress Levels</p>
              <h3 className="text-2xl font-bold text-gray-900">-27%</h3>
            </div>
            <div className="w-24 h-12">
              <Line data={createSparkline('#f59e0b', [25, 22, 24, 18, 15, 12, 8])} options={sparklineOptions} />
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 3: Bottom Row */}
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-[2]">
          <h3 className="text-lg font-bold text-gray-900 mb-3 px-1">Top Health Trends</h3>
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between h-72">
            <div className="flex-1 relative w-full pt-4 pr-12">
               <Bar data={topTrendsData} options={topTrendsOptions} />
               <div className="absolute right-0 top-0 bottom-0 flex flex-col justify-between py-10 font-bold text-gray-700 text-sm">
                 <div>40%</div>
                 <div>30%</div>
                 <div>20%</div>
                 <div>10%</div>
               </div>
            </div>
            <div className="text-center mt-2 text-xs text-gray-400">Company Aggregate - HIPAA Compliant</div>
          </div>
        </div>

        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-900 mb-3 px-1">Dietitian Program Results</h3>
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex flex-col h-72 justify-between">
            <div className="flex justify-center items-center relative flex-1">
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="text-3xl font-extrabold text-gray-900">73%</span>
                <span className="text-xs text-gray-500 font-medium">Goal<br/>Achievement</span>
              </div>
              <div className="h-36 w-36">
                <Doughnut data={donutData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, cutout: '75%' }} />
              </div>
            </div>
            
            <div className="flex items-center justify-between pt-6 border-t border-gray-50 mt-2">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-50 text-blue-500 rounded-lg">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-900">245</div>
                  <div className="text-[10px] text-gray-500 font-medium tracking-wide uppercase">Active Plans</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="p-2 bg-orange-50 text-orange-400 rounded-lg">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-900">89%</div>
                  <div className="text-[10px] text-gray-500 font-medium tracking-wide uppercase">Satisfaction Rate</div>
                </div>
              </div>
            </div>
            <div className="text-center mt-4 text-[10px] text-gray-400">Company Aggregate - HIPAA Compliant</div>
          </div>
        </div>
      </div>
      
    </div>
  );
}
