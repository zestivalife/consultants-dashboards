const React = require('react');
const { createContext, useContext, useReducer, useEffect } = React;
const { apiRequest } = require('../lib/api');

const DashboardContext = createContext();

const initialState = {
  totalEmployees: 0,
  activeEmployees: 0,
  sessionsThisMonth: 0,
  completedSessions: 0,
  averageEngagement: 0,
  wellnessScore: 0,
  upcomingSessions: 0,
  departments: [],
  recentSessions: [],
  loading: true,
  error: null
};

const dashboardReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'UPDATE_METRIC':
      return { ...state, [action.key]: action.value };
    case 'BULK_UPDATE':
      return { ...state, ...action.payload, loading: false };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
};

const DashboardProvider = ({ children }) => {
  const [state, dispatch] = useReducer(dashboardReducer, initialState);

  const fetchDashboardData = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const data = await apiRequest('/analytics/dashboard/metrics');
      dispatch({ type: 'BULK_UPDATE', payload: data || {} });
    } catch (error) {
      console.error('Dashboard fetch error:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  };

  const updateMetric = (key, value) => {
    dispatch({ type: 'UPDATE_METRIC', key, value });
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const contextValue = {
    state,
    updateMetric,
    fetchDashboardData,
  };

  return React.createElement(
    DashboardContext.Provider,
    { value: contextValue },
    children
  );
};

const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within DashboardProvider');
  }
  return context;
};

module.exports = { DashboardProvider, useDashboard };
