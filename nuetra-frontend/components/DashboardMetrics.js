const React = require('react');
const { Users, Calendar, TrendingUp, Clock } = require('lucide-react');
const { useDashboard } = require('../contexts/DashboardContext');

const DashboardMetrics = () => {
  const { state, isConnected } = useDashboard();

  const MetricCard = ({ title, value, subtitle, icon: Icon, trend, color = "blue" }) => {
    const colorClasses = {
      blue: "bg-blue-50 text-blue-600",
      green: "bg-green-50 text-green-600",
      purple: "bg-purple-50 text-purple-600",
      orange: "bg-orange-50 text-orange-600"
    };

    return React.createElement('div', {
      className: "bg-white p-6 rounded-lg shadow-sm border border-gray-200"
    },
      React.createElement('div', { className: "flex items-center justify-between mb-4" },
        React.createElement('div', {
          className: `p-3 rounded-lg ${colorClasses[color]}`
        }, React.createElement(Icon, { className: "h-6 w-6" })),
        trend && React.createElement('span', {
          className: `text-sm font-medium ${trend > 0 ? 'text-green-600' : 'text-red-600'}`
        }, `${trend > 0 ? '+' : ''}${trend}%`)
      ),
      React.createElement('div', null,
        React.createElement('h3', { className: "text-2xl font-bold text-gray-900 mb-1" }, value),
        React.createElement('p', { className: "text-sm text-gray-600" }, title),
        subtitle && React.createElement('p', { className: "text-xs text-gray-400 mt-1" }, subtitle)
      )
    );
  };

  if (state.loading) {
    return React.createElement('div', { className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" },
      Array(4).fill(0).map((_, i) => 
        React.createElement('div', { 
          key: i,
          className: "bg-white p-6 rounded-lg shadow-sm border border-gray-200 animate-pulse" 
        },
          React.createElement('div', { className: "h-12 w-12 bg-gray-200 rounded-lg mb-4" }),
          React.createElement('div', { className: "h-8 bg-gray-200 rounded mb-2" }),
          React.createElement('div', { className: "h-4 bg-gray-200 rounded w-3/4" })
        )
      )
    );
  }

  return React.createElement('div', { className: "space-y-6" },
    // Connection Status
    React.createElement('div', { className: "flex items-center gap-2 text-sm" },
      React.createElement('div', {
        className: `w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`
      }),
      React.createElement('span', {
        className: isConnected ? 'text-green-600' : 'text-red-600'
      }, isConnected ? 'Real-time updates active' : 'Connection lost - retrying...')
    ),

    // Metrics Grid
    React.createElement('div', { className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" },
      React.createElement(MetricCard, {
        title: "Total Employees",
        value: state.totalEmployees,
        subtitle: `${state.activeEmployees} active this month`,
        icon: Users,
        trend: 8,
        color: "blue"
      }),
      React.createElement(MetricCard, {
        title: "Sessions This Month", 
        value: state.sessionsThisMonth,
        subtitle: `${state.completedSessions} completed`,
        icon: Calendar,
        trend: 15,
        color: "green"
      }),
      React.createElement(MetricCard, {
        title: "Average Engagement",
        value: `${state.averageEngagement}%`,
        subtitle: "Across all programs",
        icon: TrendingUp,
        trend: 5,
        color: "purple"
      }),
      React.createElement(MetricCard, {
        title: "Upcoming Sessions",
        value: state.upcomingSessions,
        subtitle: "Next 7 days",
        icon: Clock,
        color: "orange"
      })
    )
  );
};

module.exports = DashboardMetrics;