import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { toast } from 'react-toastify';
import { motion, AnimatePresence } from 'framer-motion';
import Image from "next/image";
import Link from "next/link";
import { useRouter } from 'next/router';
import {
  Users, Building2, Calendar, TrendingUp, Shield, Settings,
  UserPlus, Eye, BarChart3, Activity, AlertTriangle, CheckCircle,
  Filter, Search, Download, RefreshCw, Bell, Plus, ChevronDown,
  Clock, Zap, Target, Award, Database, Server, Mail, Globe,
  DollarSign, Heart, Brain, Coffee, Dumbbell, Home, ArrowUp, ArrowDown, X,
  BriefcaseBusiness, KeyRound, BadgeCheck, LayoutGrid, ListFilter, Sparkles, UserCog
} from 'lucide-react';
import LogoutButton from '../../components/LogoutButton';
import DashboardHeader from '../../components/DashboardHeader';
import SessionRequestsManager from '../../components/SessionRequestsManager';
import { apiRequest } from '../../lib/api';
import withAuth from '../../hocs/withAuth';
import { TopNavTabs } from '../../components/dashboard';
import { useAuth } from '../../context/AuthContext';
// Icon mapping for activity types
const activityIconMap = {
  company_registered: Building2,
  session_completed: Calendar,
  alert: Server,
  admin_created: UserPlus,
  payment_success: DollarSign,
  user_created: UserPlus
};

// Icon and color mapping for user distribution
const userDistributionConfig = {
  'Corporate Clients': { icon: Building2, color: 'from-blue-500 to-blue-600' },
  'Team Members': { icon: Users, color: 'from-green-500 to-green-600' },
  'Admins': { icon: Shield, color: 'from-purple-500 to-purple-600' },
  'Team Leads': { icon: Target, color: 'from-orange-500 to-orange-600' }
};

// Icon and color mapping for wellness metrics
const wellnessIconMap = {
  'Mindfulness': { icon: Brain, color: 'from-purple-500 to-purple-600' },
  'Physical Wellness': { icon: Dumbbell, color: 'from-green-500 to-green-600' },
  'Mental Health': { icon: Heart, color: 'from-red-500 to-red-600' },
  'Nutrition': { icon: Coffee, color: 'from-orange-500 to-orange-600' }
};

const ROLE_PRESENTATION = {
  superuser: {
    label: 'Platform Owner',
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
    icon: Shield,
  },
  super_admin: {
    label: 'Platform Owner',
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
    icon: Shield,
  },
  admin: {
    label: 'Admin',
    badge: 'bg-violet-50 text-violet-700 border-violet-200',
    icon: UserCog,
  },
  team_lead: {
    label: 'Mentor',
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
    icon: Target,
  },
  provider: {
    label: 'Consultant',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    icon: BriefcaseBusiness,
  },
  dietician: {
    label: 'Senior Consultant',
    badge: 'bg-teal-50 text-teal-700 border-teal-200',
    icon: BriefcaseBusiness,
  },
  corporate_admin: {
    label: 'Organization Admin',
    badge: 'bg-slate-100 text-slate-700 border-slate-200',
    icon: Building2,
  },
  corporate_client: {
    label: 'Corporate Client',
    badge: 'bg-slate-100 text-slate-700 border-slate-200',
    icon: Building2,
  },
};

const ROLE_AUTHORITY_PRESETS = {
  superuser: ['All organizations', 'Access control', 'Invite leaders', 'Billing oversight'],
  super_admin: ['All organizations', 'Access control', 'Invite leaders', 'Billing oversight'],
  admin: ['Manage admins', 'Review operations', 'Monitor reports', 'Escalate issues'],
  team_lead: ['Mentor roster', 'Care oversight', 'Program reviews', 'Support escalation'],
  provider: ['Client plans', 'Consultations', 'Biomarker review', 'Follow-up workflows'],
  dietician: ['Client plans', 'Nutrition plans', 'Consultations', 'Outcome tracking'],
  corporate_admin: ['Employee oversight', 'Package usage', 'Organization analytics'],
  corporate_client: ['Program visibility', 'Usage review'],
};

const PEOPLE_FILTERS = [
  { key: 'all', label: 'All People' },
  { key: 'admins', label: 'Admins' },
  { key: 'mentors', label: 'Mentors' },
  { key: 'consultants', label: 'Consultants' },
  { key: 'organizations', label: 'Org Admins' },
];

// Animation variants
const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

const staggerContainer = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1 }
  }
};

// Enhanced Stat Card Component
function StatCard({ icon: Icon, title, value, subtitle, change, gradient = "from-blue-500 to-blue-600", badge }) {
  return (
    <motion.div
      variants={cardVariants}
      whileHover={{ scale: 1.02, y: -5 }}
      className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-2xl transition-all border border-gray-100 group relative overflow-hidden"
    >
      {/* Background gradient effect */}
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${gradient} opacity-5 rounded-full -mr-16 -mt-16 group-hover:opacity-10 transition-opacity`}></div>
      
      <div className="relative">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-xl bg-gradient-to-r ${gradient} text-white group-hover:scale-110 transition-transform shadow-md`}>
            <Icon className="h-6 w-6" />
          </div>
          {badge && (
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
              {badge}
            </span>
          )}
        </div>
        
        <div>
          <p className="text-gray-600 text-sm font-medium mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mb-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mb-2">{subtitle}</p>}
          {change && (
            <div className="flex items-center space-x-1">
              {change.startsWith('+') ? (
                <ArrowUp className="h-4 w-4 text-green-600" />
              ) : (
                <ArrowDown className="h-4 w-4 text-red-600" />
              )}
              <span className={`text-sm font-semibold ${change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                {change}
              </span>
              <span className="text-xs text-gray-500">vs last month</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// Enhanced Activity Item Component
function ActivityItem({ activity }) {
  const getSeverityStyles = () => {
    switch (activity.severity) {
      case 'success': 
        return { 
          bg: 'bg-green-50', 
          border: 'border-green-100', 
          iconBg: 'bg-green-100', 
          iconColor: 'text-green-600' 
        };
      case 'warning': 
        return { 
          bg: 'bg-yellow-50', 
          border: 'border-yellow-100', 
          iconBg: 'bg-yellow-100', 
          iconColor: 'text-yellow-600' 
        };
      case 'error': 
        return { 
          bg: 'bg-red-50', 
          border: 'border-red-100', 
          iconBg: 'bg-red-100', 
          iconColor: 'text-red-600' 
        };
      default: 
        return { 
          bg: 'bg-blue-50', 
          border: 'border-blue-100', 
          iconBg: 'bg-blue-100', 
          iconColor: 'text-blue-600' 
        };
    }
  };

  const styles = getSeverityStyles();
  const IconComponent = activityIconMap[activity.type] || Activity;

  return (
    <motion.div 
      whileHover={{ x: 5 }}
      className={`flex items-start space-x-3 p-4 rounded-xl border ${styles.border} ${styles.bg} hover:shadow-md transition-all cursor-pointer`}
    >
      <div className={`p-2 rounded-lg ${styles.iconBg} ${styles.iconColor} mt-1`}>
        <IconComponent className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 mb-1">{activity.message}</p>
        <div className="flex items-center space-x-3 text-xs text-gray-500">
          <span className="flex items-center space-x-1">
            <Clock className="h-3 w-3" />
            <span>{activity.timestamp}</span>
          </span>
          {activity.company && (
            <span className="flex items-center space-x-1">
              <Building2 className="h-3 w-3" />
              <span>{activity.company}</span>
            </span>
          )}
          {activity.amount && (
            <span className="font-medium text-green-600">{activity.amount}</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// Enhanced User Distribution Component
function UserDistributionChart({ distribution = [], loading = false }) {
  if (loading) {
    return (
      <motion.div 
        variants={cardVariants}
        className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
      >
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div 
      variants={cardVariants}
      className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">User Distribution</h3>
          <p className="text-sm text-gray-600 mt-1">Across all roles</p>
        </div>
        <button className="p-2 text-gray-400 hover:text-[#64ae00] hover:bg-green-50 rounded-lg transition-colors">
          <Eye className="h-5 w-5" />
        </button>
      </div>
      
      <div className="space-y-4">
        {distribution.map((item, index) => {
          const config = userDistributionConfig[item.role] || { icon: Users, color: 'from-gray-500 to-gray-600' };
          const IconComponent = config.icon;
          return (
            <motion.div 
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg bg-gradient-to-r ${config.color} text-white group-hover:scale-110 transition-transform`}>
                    <IconComponent className="h-4 w-4" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">{item.role}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-gray-900">{item.count.toLocaleString()}</p>
                  <p className="text-xs text-green-600 font-medium">{item.growth}</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(item.percentage * 10, 100)}%` }}
                  transition={{ duration: 1, delay: index * 0.1 }}
                  className={`bg-gradient-to-r ${config.color} h-2 rounded-full`}
                ></motion.div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}

// Enhanced Quick Actions Component
function QuickActions() {
  const actions = [
    { icon: UserPlus, label: 'Create Admin', gradient: 'from-blue-500 to-blue-600', action: 'admin' },
    { icon: Building2, label: 'Add Company', gradient: 'from-green-500 to-green-600', action: 'company' },
    { icon: Settings, label: 'System Config', gradient: 'from-purple-500 to-purple-600', action: 'settings' },
    { icon: BarChart3, label: 'Analytics', gradient: 'from-orange-500 to-orange-600', action: 'analytics' },
  ];

  return (
    <motion.div 
      variants={cardVariants}
      className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
          <p className="text-sm text-gray-600 mt-1">Common tasks</p>
        </div>
        <Zap className="h-5 w-5 text-[#64ae00]" />
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        {actions.map((action, index) => (
          <motion.button
            key={index}
            whileHover={{ scale: 1.05, y: -3 }}
            whileTap={{ scale: 0.98 }}
            className="flex flex-col items-center p-4 border-2 border-gray-200 rounded-xl hover:border-[#64ae00] hover:shadow-md transition-all group"
          >
            <div className={`p-3 rounded-xl bg-gradient-to-r ${action.gradient} text-white mb-3 group-hover:scale-110 transition-transform shadow-md`}>
              <action.icon className="h-5 w-5" />
            </div>
            <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900">{action.label}</span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

// Top Companies Component
function TopCompaniesTable({ companies = [], loading = false }) {
  const getPlanBadge = (plan) => {
    const styles = {
      'ENTERPRISE': 'bg-purple-100 text-purple-700 border-purple-200',
      'PREMIUM': 'bg-blue-100 text-blue-700 border-blue-200',
      'BASIC': 'bg-gray-100 text-gray-700 border-gray-200',
    };
    return styles[plan] || styles.BASIC;
  };

  const getStatusBadge = (status) => {
    const styles = {
      'ACTIVE': 'bg-green-100 text-green-700',
      'TRIAL': 'bg-yellow-100 text-yellow-700',
      'SUSPENDED': 'bg-red-100 text-red-700',
    };
    return styles[status] || styles.ACTIVE;
  };

  if (loading) {
    return (
      <motion.div 
        variants={cardVariants}
        className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden"
      >
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div 
      variants={cardVariants}
      className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden"
    >
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Top Companies</h3>
            <p className="text-sm text-gray-600 mt-1">Highest revenue and engagement</p>
          </div>
          <button className="px-4 py-2 text-sm font-medium text-[#64ae00] hover:bg-green-50 rounded-lg transition-colors">
            View All
          </button>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Company</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Employees</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Engagement</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Revenue</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Plan</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {companies.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                  No companies found
                </td>
              </tr>
            ) : (
              companies.map((company) => (
              <motion.tr 
                key={company.id}
                whileHover={{ backgroundColor: '#f9fafb' }}
                className="hover:bg-gray-50 transition-colors cursor-pointer"
              >
                <td className="px-6 py-4">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{company.name}</div>
                    <div className="text-xs text-gray-500">{company.industry}</div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2">
                    <Users className="h-4 w-4 text-gray-400" />
                    <span className="text-sm text-gray-900">{company.employees}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full" 
                        style={{ width: `${company.engagement}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900">{company.engagement}%</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm font-medium text-gray-900">{company.revenue}</span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getPlanBadge(company.plan)}`}>
                    {company.plan}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(company.status)}`}>
                    {company.status}
                  </span>
                </td>
              </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}

// Wellness Metrics Component
function WellnessMetricsGrid({ metrics = [], loading = false }) {
  if (loading) {
    return (
      <motion.div 
        variants={cardVariants}
        className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
      >
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div 
      variants={cardVariants}
      className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Wellness Programs</h3>
          <p className="text-sm text-gray-600 mt-1">Performance across categories</p>
        </div>
        <Activity className="h-5 w-5 text-[#64ae00]" />
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {metrics.length === 0 ? (
          <div className="col-span-2 text-center text-gray-500 py-8">
            No wellness metrics available
          </div>
        ) : (
          metrics.map((metric, index) => {
            const config = wellnessIconMap[metric.category] || { icon: Activity, color: 'from-gray-500 to-gray-600' };
            const IconComponent = config.icon;
            return (
            <motion.div
              key={index}
              whileHover={{ scale: 1.03 }}
              className="p-4 border-2 border-gray-100 rounded-xl hover:border-gray-200 hover:shadow-md transition-all group"
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`p-2 rounded-lg bg-gradient-to-r ${config.color} text-white group-hover:scale-110 transition-transform`}>
                  <IconComponent className="h-5 w-5" />
                </div>
                <span className="text-xs font-medium text-green-600">{metric.growth}</span>
              </div>
              
              <h4 className="font-semibold text-gray-900 mb-2">{metric.category}</h4>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Sessions</span>
                  <span className="font-medium text-gray-900">{metric.sessions}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Participants</span>
                  <span className="font-medium text-gray-900">{metric.participants}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Avg Rating</span>
                  <div className="flex items-center space-x-1">
                    <Award className="h-4 w-4 text-yellow-500" />
                    <span className="font-medium text-gray-900">{metric.avgRating}</span>
                  </div>
                </div>
              </div>
            </motion.div>
            );
          })
        )}
      </div>
    </motion.div>
  );
}

// System Health Component
function SystemHealthMetrics({ metrics = [], loading = false }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'excellent': return 'text-green-600';
      case 'good': return 'text-blue-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <motion.div 
        variants={cardVariants}
        className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
      >
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div 
      variants={cardVariants}
      className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
          <div className="flex items-center space-x-2 mt-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-green-600 font-medium">All Systems Operational</span>
          </div>
        </div>
        <Server className="h-5 w-5 text-[#64ae00]" />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        {metrics.length === 0 ? (
          <div className="col-span-2 text-center text-gray-500 py-8">
            No system metrics available
          </div>
        ) : (
          metrics.map((metric, index) => (
          <div
            key={index}
            className="p-3 border border-gray-100 rounded-lg hover:border-gray-200 hover:shadow-sm transition-all"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-600">{metric.name}</span>
              {metric.trend === 'up' ? (
                <ArrowUp className={`h-3 w-3 ${getStatusColor(metric.status)}`} />
              ) : (
                <ArrowDown className={`h-3 w-3 ${getStatusColor(metric.status)}`} />
              )}
            </div>
            <div className="flex items-center justify-between">
              <span className={`text-lg font-bold ${getStatusColor(metric.status)}`}>
                {metric.value}
              </span>
              <span className="text-xs text-gray-500">{metric.change}</span>
            </div>
          </div>
          ))
        )}
      </div>
    </motion.div>
  );
}

// Main Superuser Dashboard Component
function SuperuserDashboard() {
  const router = useRouter();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedTimeframe, setSelectedTimeframe] = useState('30d');
  const [showSystemHealth, setShowSystemHealth] = useState(true);
  const [peopleFilter, setPeopleFilter] = useState('all');
  const [peopleSearch, setPeopleSearch] = useState('');
  const [peopleView, setPeopleView] = useState('cards');

  const adminTabs = [
    { key: 'dashboard', label: 'Command Center' },
    { key: 'companies', label: 'Organizations' },
    { key: 'users', label: 'People & Access' },
    { key: 'providers', label: 'Practitioners' },
    { key: 'system', label: 'Platform Health' },
  ];
  
  // Data state
  const [stats, setStats] = useState(null);
  const [userDistribution, setUserDistribution] = useState([]);
  const [topCompanies, setTopCompanies] = useState([]);
  const [wellnessMetrics, setWellnessMetrics] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState([]);
  const [recentActivities, setRecentActivities] = useState([]);
  
  // Provider management state
  const [providers, setProviders] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteForm, setInviteForm] = useState({ email: '', firstName: '', lastName: '', role: 'provider', message: '' });
  const [inviting, setInviting] = useState(false);
  const [providerLoading, setProviderLoading] = useState(true);
  const [userLoading, setUserLoading] = useState(true);

  // Loading states
  const [loading, setLoading] = useState({
    stats: true,
    userDistribution: true,
    topCompanies: true,
    wellnessMetrics: true,
    systemMetrics: true,
    recentActivities: true
  });

  const timeframeOptions = [
    { key: '7d', label: 'Last 7 Days' },
    { key: '30d', label: 'Last 30 Days' },
    { key: '90d', label: 'Last 90 Days' },
    { key: '1y', label: 'This Year' },
  ];

  const ownerName = useMemo(() => {
    const firstName = user?.first_name || user?.firstName;
    const lastName = user?.last_name || user?.lastName;
    if (firstName || lastName) {
      return [firstName, lastName].filter(Boolean).join(' ');
    }
    if ((user?.email || '').toLowerCase() === 'lalitppaunikar26@gmail.com') {
      return 'Lalit Paunikar';
    }
    if ((user?.email || '').toLowerCase() === 'zestivapriyanshi@gmail.com') {
      return 'Priyanshi';
    }
    return user?.name || 'Platform Owner';
  }, [user]);

  // Fetch all dashboard data
  const fetchDashboardData = async () => {
    try {
      setLoading({
        stats: true,
        userDistribution: true,
        topCompanies: true,
        wellnessMetrics: true,
        systemMetrics: true,
        recentActivities: true
      });

      // Fetch all data in parallel
      const [
        statsData,
        userDistributionData,
        topCompaniesData,
        wellnessMetricsData,
        systemMetricsData,
        recentActivitiesData
      ] = await Promise.all([
        apiRequest(`/superuser/dashboard/stats?timeframe=${selectedTimeframe}`),
        apiRequest(`/superuser/dashboard/user-distribution?timeframe=${selectedTimeframe}`),
        apiRequest('/superuser/dashboard/top-companies?limit=10'),
        apiRequest(`/superuser/dashboard/wellness-metrics?timeframe=${selectedTimeframe}`),
        apiRequest('/superuser/system/metrics'),
        apiRequest('/superuser/dashboard/recent-activities?limit=20')
      ]);

      setStats(statsData);
      setUserDistribution(userDistributionData?.distribution || []);
      setTopCompanies(topCompaniesData?.companies || []);
      setWellnessMetrics(wellnessMetricsData?.metrics || []);
      setSystemMetrics(systemMetricsData?.metrics || []);
      setRecentActivities(recentActivitiesData?.activities || []);

      // Update loading states
      setLoading({
        stats: false,
        userDistribution: false,
        topCompanies: false,
        wellnessMetrics: false,
        systemMetrics: false,
        recentActivities: false
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Set loading to false even on error
      setLoading({
        stats: false,
        userDistribution: false,
        topCompanies: false,
        wellnessMetrics: false,
        systemMetrics: false,
        recentActivities: false
      });
    }
  };

  const fetchProviderData = useCallback(async () => {
    setProviderLoading(true);
    try {
      const [provData, invData] = await Promise.all([
        apiRequest('/superuser/providers'),
        apiRequest('/superuser/invitations'),
      ]);
      setProviders(Array.isArray(provData) ? provData : []);
      setInvitations(Array.isArray(invData) ? invData : []);
    } catch (e) { console.error('Provider fetch error:', e); }
    finally { setProviderLoading(false); }
  }, []);

  const fetchAllUsers = useCallback(async () => {
    setUserLoading(true);
    try {
      const [userData, invData] = await Promise.all([
        apiRequest('/superuser/users?limit=200&offset=0'),
        apiRequest('/superuser/invitations'),
      ]);
      setAllUsers(Array.isArray(userData?.users) ? userData.users : []);
      setInvitations(Array.isArray(invData) ? invData : []);
    } catch (error) {
      console.error('User fetch error:', error);
      setAllUsers([]);
    } finally {
      setUserLoading(false);
    }
  }, []);

  const matchesPeopleFilter = useCallback((role, filterKey) => {
    const normalizedRole = (role || '').toLowerCase();
    if (filterKey === 'all') return true;
    if (filterKey === 'admins') return ['superuser', 'super_admin', 'admin'].includes(normalizedRole);
    if (filterKey === 'mentors') return normalizedRole === 'team_lead';
    if (filterKey === 'consultants') return ['provider', 'dietician'].includes(normalizedRole);
    if (filterKey === 'organizations') return ['corporate_admin', 'corporate_client'].includes(normalizedRole);
    return true;
  }, []);

  const filteredUsers = useMemo(() => {
    const query = peopleSearch.trim().toLowerCase();
    return allUsers.filter((person) => {
      const roleMatch = matchesPeopleFilter(person.role, peopleFilter);
      const haystack = [
        person.firstName,
        person.lastName,
        person.email,
        person.companyName,
        ROLE_PRESENTATION[(person.role || '').toLowerCase()]?.label,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      const searchMatch = !query || haystack.includes(query);
      return roleMatch && searchMatch;
    });
  }, [allUsers, matchesPeopleFilter, peopleFilter, peopleSearch]);

  const peopleSummary = useMemo(() => {
    const countRoles = (roles) => allUsers.filter((person) => roles.includes((person.role || '').toLowerCase())).length;
    return {
      total: allUsers.length,
      admins: countRoles(['superuser', 'super_admin', 'admin']),
      mentors: countRoles(['team_lead']),
      consultants: countRoles(['provider', 'dietician']),
      organizations: countRoles(['corporate_admin', 'corporate_client']),
      pendingInvites: invitations.filter((invite) => !invite.isAccepted && !invite.isExpired).length,
    };
  }, [allUsers, invitations]);

  const handleInviteProvider = async (e) => {
    e.preventDefault();
    if (!inviteForm.email) return;
    setInviting(true);
    try {
      const res = await apiRequest('/superuser/providers/invite', {
        method: 'POST',
        body: inviteForm,
      });
      toast.success(`Invitation sent to ${inviteForm.email}`);
      setShowInviteModal(false);
      setInviteForm({ email: '', firstName: '', lastName: '', role: 'provider', message: '' });
      fetchProviderData();
    } catch (err) {
      toast.error(err?.message || 'Failed to send invitation');
    } finally { setInviting(false); }
  };

  useEffect(() => {
    fetchDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTimeframe]);

  useEffect(() => {
    if (activeTab === 'providers') fetchProviderData();
    if (activeTab === 'users') fetchAllUsers();
  }, [activeTab, fetchProviderData, fetchAllUsers]);

  useEffect(() => {
    if (!router.isReady) return;
    const tabFromQuery = typeof router.query.tab === 'string' ? router.query.tab : 'dashboard';
    if (adminTabs.some((tab) => tab.key === tabFromQuery) && tabFromQuery !== activeTab) {
      setActiveTab(tabFromQuery);
    }
  }, [activeTab, adminTabs, router.isReady, router.query.tab]);

  const handleTabChange = useCallback((nextTab) => {
    setActiveTab(nextTab);
    const nextQuery = nextTab === 'dashboard' ? {} : { tab: nextTab };
    router.replace({ pathname: router.pathname, query: nextQuery }, undefined, { shallow: true });
  }, [router]);

  return (
    <div className="min-h-screen relative overflow-hidden font-sans">
      {/* Background Gradient Pack */}
      <div className="absolute inset-0 bg-[#f4faff]">
        <div className="absolute -left-[400px] -top-[400px] w-[1000px] h-[1000px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255, 208, 208, 0.8) 0%, rgba(255, 220, 220, 0.4) 40%, transparent 70%)', filter: 'blur(80px)' }} />
        <div className="absolute -right-[100px] top-[50px] w-[800px] h-[800px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255, 208, 208, 0.7) 0%, rgba(255, 200, 200, 0.3) 50%, transparent 70%)', filter: 'blur(60px)' }} />
        <div className="absolute right-[-300px] bottom-[-200px] w-[900px] h-[900px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255, 208, 208, 0.6) 0%, rgba(255, 220, 220, 0.3) 50%, transparent 70%)', filter: 'blur(80px)' }} />
        <div className="absolute left-[50%] top-[-50px] w-[1000px] h-[900px] flex items-center justify-center pointer-events-none">
          <img src="/dna-helix.svg" alt="" className="w-[900px] h-[600px] opacity-[0.08] rotate-[27deg] object-contain" />
        </div>
      </div>

      <div className="relative z-[100]">
        <DashboardHeader searchPlaceholder="Search companies, users, sessions..." />
      </div>

      <div className="relative z-10 max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-20">
        <TopNavTabs activeTab={activeTab} onTabChange={handleTabChange} tabs={adminTabs} className="mb-2" />

        {activeTab === 'dashboard' && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            {/* Enhanced Welcome Section with Key Metrics */}
            <div className="bg-white border border-[#f2f2f7] rounded-3xl p-8 shadow-[0px_4px_4px_-1px_rgba(12,12,13,0.1),0px_4px_4px_-1px_rgba(12,12,13,0.05)]">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
                <div>
                  <h1 className="text-3xl font-black bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 bg-clip-text text-transparent mb-2 tracking-tighter">
                    Welcome back, {ownerName}
                  </h1>
                  <p className="text-gray-500 font-medium text-sm">
                    Platform owner command center for organizations, access, and recovery operations.
                  </p>
                </div>
                
                {/* Time Filter & Refresh */}
                <div className="flex items-center gap-3">
                  <div className="flex items-center space-x-2 bg-gray-50 rounded-xl p-1 shadow-inner border border-gray-100">
                    {timeframeOptions.map((period) => (
                      <button
                        key={period.key}
                        onClick={() => setSelectedTimeframe(period.key)}
                        className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                          selectedTimeframe === period.key
                            ? 'bg-white text-[#237afc] shadow-sm'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        {period.key}
                      </button>
                    ))}
                  </div>
                  <button 
                    onClick={fetchDashboardData}
                    className="p-2.5 bg-white border border-gray-200 text-gray-600 hover:text-[#237afc] hover:bg-blue-50 rounded-xl transition-all shadow-sm"
                    title="Refresh Dashboard"
                  >
                    <RefreshCw className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* Primary Stats Grid */}
              <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
              >
                <StatCard
                  icon={Users}
                  title="Total Users"
                  value={loading.stats ? '...' : (stats?.totalUsers || 0).toLocaleString()}
                  subtitle="Across all companies"
                  change={stats?.userGrowth || '+0%'}
                  gradient="from-blue-500 to-blue-600"
                />
                <StatCard
                  icon={Building2}
                  title="Active Companies"
                  value={loading.stats ? '...' : (stats?.totalCompanies || 0)}
                  subtitle="Wellness programs"
                  change={stats?.companyGrowth || '+0%'}
                  gradient="from-green-500 to-green-600"
                  badge={stats?.totalCompanies > 0 ? "Growing" : null}
                />
                <StatCard
                  icon={Calendar}
                  title="Sessions Today"
                  value={loading.stats ? '...' : (stats?.completedSessionsToday || 0)}
                  subtitle={loading.stats ? 'Loading...' : `${stats?.activeSessions || 0} in progress`}
                  change="+24%"
                  gradient="from-purple-500 to-purple-600"
                />
                <StatCard
                  icon={Activity}
                  title="Engagement"
                  value={loading.stats ? '...' : `${stats?.avgEngagement || 0}%`}
                  subtitle="Platform-wide"
                  change={"+2.4%"}
                  gradient="from-orange-500 to-orange-600"
                />
              </motion.div>

              {/* Main Dashboard Grid */}
              <div className="grid lg:grid-cols-3 gap-8 mb-8">
                {/* Left Column - User Distribution */}
                <div className="lg:col-span-2">
                  <UserDistributionChart distribution={userDistribution} loading={loading.userDistribution} />
                </div>

                {/* Right Column - Wellness Metrics */}
                <div className="space-y-8">
                  <WellnessMetricsGrid metrics={wellnessMetrics} loading={loading.wellnessMetrics} />
                </div>
              </div>

              {/* Bottom Row */}
              <div className="grid lg:grid-cols-2 gap-8">
                {/* Recent Activity Feed */}
                <motion.div
                  variants={cardVariants}
                  initial="hidden"
                  animate="visible"
                  className="bg-white rounded-2xl shadow-lg border border-gray-100"
                >
                  <div className="p-6 border-b border-gray-100">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
                        <p className="text-sm text-gray-600 mt-1">Platform-wide events</p>
                      </div>
                      <button className="px-3 py-1.5 text-sm font-medium text-[#237afc] hover:bg-blue-50 rounded-lg transition-colors">
                        View All
                      </button>
                    </div>
                  </div>
                  
                  <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
                    {loading.recentActivities ? (
                      <div className="flex items-center justify-center py-8">
                        <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                      </div>
                    ) : recentActivities.length === 0 ? (
                      <div className="text-center text-gray-500 py-8">
                        No recent activities
                      </div>
                    ) : (
                      recentActivities.map((activity) => (
                        <ActivityItem key={activity.id} activity={activity} />
                      ))
                    )}
                  </div>
                </motion.div>

                {/* Quick Actions */}
                <QuickActions />
              </div>
            </div>
          </motion.div>
        )}

        {/* System Health Tab */}
        {activeTab === 'system' && (
           <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
           >
             <div className="bg-white border border-[#f2f2f7] rounded-3xl p-8 shadow-[0px_4px_4px_-1px_rgba(12,12,13,0.1),0px_4px_4px_-1px_rgba(12,12,13,0.05)]">
                <SystemHealthMetrics metrics={systemMetrics} loading={loading.systemMetrics} />
             </div>
           </motion.div>
        )}

        {/* Companies Tab */}
        {activeTab === 'companies' && (
           <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
           >
             <div className="bg-white border border-[#f2f2f7] rounded-3xl p-8 shadow-[0px_4px_4px_-1px_rgba(12,12,13,0.1),0px_4px_4px_-1px_rgba(12,12,13,0.05)]">
                <TopCompaniesTable companies={topCompanies} loading={loading.topCompanies} />
             </div>
           </motion.div>
        )}

        {/* Providers Tab */}
        {activeTab === 'providers' && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div className="bg-white border border-[#f2f2f7] rounded-3xl p-8 shadow-[0px_4px_4px_-1px_rgba(12,12,13,0.1),0px_4px_4px_-1px_rgba(12,12,13,0.05)]">
              {/* Header */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
                <div>
                  <h2 className="text-2xl font-black text-gray-900 tracking-tight">Practitioner workspace</h2>
                  <p className="text-sm text-gray-500 mt-1">{providers.length} active consultants and dieticians · {invitations.filter(i => !i.isAccepted && !i.isExpired).length} pending invitations</p>
                </div>
                <button onClick={() => setShowInviteModal(true)} className="flex items-center gap-2 px-6 py-3 bg-[#237afc] hover:bg-[#1a62d6] text-white font-bold rounded-xl transition-all shadow-md">
                  <Mail className="w-4 h-4" /> Invite practitioner
                </button>
              </div>

              {/* Active Providers */}
              <div className="mb-8">
                <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-4">Active Providers</h3>
                {providerLoading ? (
                  <div className="flex justify-center py-12"><RefreshCw className="w-6 h-6 animate-spin text-gray-400" /></div>
                ) : providers.length === 0 ? (
                    <div className="text-center py-12 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
                      <UserPlus className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 font-medium">No practitioners yet</p>
                    <p className="text-gray-400 text-sm mt-1">Invite your first consultant or dietician to get started</p>
                    <button onClick={() => setShowInviteModal(true)} className="mt-4 text-[#237afc] font-bold text-sm hover:underline">Send Invitation →</button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {providers.map((p) => (
                      <motion.div key={p.id} whileHover={{ y: -4 }} className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all">
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center text-white font-black text-lg">
                            {(p.firstName || p.email)[0].toUpperCase()}
                          </div>
                          <div className="min-w-0">
                            <p className="font-bold text-gray-900 truncate">{p.firstName ? `${p.firstName} ${p.lastName || ''}` : p.email.split('@')[0]}</p>
                            <p className="text-xs text-gray-400 truncate">{p.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold px-2 py-1 rounded-full bg-teal-50 text-teal-700 capitalize">{p.role}</span>
                          <span className={`text-xs font-semibold px-2 py-1 rounded-full ${p.isVerified ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'}`}>{p.isVerified ? 'Verified' : 'Pending'}</span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>

              {/* Invitations */}
              <div>
                <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-4">Invitations History</h3>
                {invitations.length === 0 ? (
                  <p className="text-gray-400 text-sm text-center py-6">No invitations sent yet</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100">
                          {['Email', 'Role', 'Status', 'Sent', 'Expires'].map(h => (
                            <th key={h} className="py-3 px-4 text-left text-xs font-black text-gray-400 uppercase tracking-wider">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {invitations.map(inv => (
                          <tr key={inv.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                            <td className="py-3 px-4">
                              <p className="font-medium text-gray-900">{inv.email}</p>
                              {inv.firstName && <p className="text-xs text-gray-400">{inv.firstName} {inv.lastName}</p>}
                            </td>
                            <td className="py-3 px-4"><span className="capitalize text-gray-600">{inv.role}</span></td>
                            <td className="py-3 px-4">
                              <span className={`text-xs font-semibold px-2 py-1 rounded-full ${inv.isAccepted ? 'bg-green-50 text-green-700' : inv.isExpired ? 'bg-red-50 text-red-600' : 'bg-yellow-50 text-yellow-700'}`}>
                                {inv.isAccepted ? '✓ Accepted' : inv.isExpired ? 'Expired' : '⏳ Pending'}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-gray-500">{new Date(inv.createdAt).toLocaleDateString()}</td>
                            <td className="py-3 px-4 text-gray-500">{new Date(inv.expiresAt).toLocaleDateString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Invite Modal */}
            {showInviteModal && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowInviteModal(false)}>
                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} onClick={e => e.stopPropagation()} className="bg-white rounded-2xl p-8 w-full max-w-lg mx-4 shadow-xl">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">Invite team member</h3>
                    <button onClick={() => setShowInviteModal(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
                  </div>
                  <form onSubmit={handleInviteProvider} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email Address *</label>
                      <input type="email" required value={inviteForm.email} onChange={e => setInviteForm(p => ({...p, email: e.target.value}))} className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#237afc]" placeholder="provider@example.com" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                        <input type="text" value={inviteForm.firstName} onChange={e => setInviteForm(p => ({...p, firstName: e.target.value}))} className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#237afc]" placeholder="John" />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                        <input type="text" value={inviteForm.lastName} onChange={e => setInviteForm(p => ({...p, lastName: e.target.value}))} className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#237afc]" placeholder="Doe" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Role and authority bundle</label>
                      <select value={inviteForm.role} onChange={e => setInviteForm(p => ({...p, role: e.target.value}))} className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#237afc] bg-white">
                        <option value="admin">Admin</option>
                        <option value="team_lead">Mentor</option>
                        <option value="provider">Consultant</option>
                        <option value="dietician">Senior Consultant</option>
                        <option value="corporate_admin">Organization Admin</option>
                      </select>
                      <p className="mt-2 text-xs text-gray-500">
                        Access is assigned through role. Choose the role that best matches the person’s authority level.
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Personal Message (optional)</label>
                      <textarea value={inviteForm.message} onChange={e => setInviteForm(p => ({...p, message: e.target.value}))} rows={3} className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#237afc] resize-none" placeholder="Welcome to the team..." />
                    </div>
                    <button type="submit" disabled={inviting} className="w-full py-3 bg-[#237afc] hover:bg-[#1a62d6] text-white font-bold rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                      {inviting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
                      {inviting ? 'Sending...' : 'Send Invitation'}
                    </button>
                  </form>
                </motion.div>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'users' && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div className="bg-white border border-[#f2f2f7] rounded-3xl p-8 shadow-[0px_4px_4px_-1px_rgba(12,12,13,0.1),0px_4px_4px_-1px_rgba(12,12,13,0.05)]">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-[11px] font-black uppercase tracking-[0.24em] text-[#237afc]">
                    <Shield className="h-3.5 w-3.5" />
                    People and access
                  </div>
                  <h2 className="mt-4 text-3xl font-black tracking-tight text-gray-900">Admins, mentors, consultants, and authority coverage</h2>
                  <p className="mt-2 max-w-3xl text-sm text-gray-500">
                    Invite new team members, review live access, and manage role-based authority from one owner console.
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => fetchAllUsers()}
                    className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-bold text-gray-700 hover:border-[#237afc] hover:text-[#237afc] transition-colors"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Refresh roster
                  </button>
                  <button
                    onClick={() => setShowInviteModal(true)}
                    className="inline-flex items-center gap-2 rounded-xl bg-[#237afc] px-5 py-3 text-sm font-bold text-white shadow-md transition hover:bg-[#1a62d6]"
                  >
                    <UserPlus className="h-4 w-4" />
                    Add admin or consultant
                  </button>
                </div>
              </div>

              <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                {[
                  { label: 'Total roster', value: peopleSummary.total, icon: Users, tone: 'from-slate-900 to-slate-700' },
                  { label: 'Admins', value: peopleSummary.admins, icon: Shield, tone: 'from-blue-600 to-blue-500' },
                  { label: 'Mentors', value: peopleSummary.mentors, icon: Target, tone: 'from-amber-500 to-orange-500' },
                  { label: 'Consultants', value: peopleSummary.consultants, icon: BriefcaseBusiness, tone: 'from-emerald-600 to-teal-500' },
                  { label: 'Pending invites', value: peopleSummary.pendingInvites, icon: Mail, tone: 'from-violet-600 to-fuchsia-500' },
                ].map((metric) => (
                  <div key={metric.label} className="rounded-2xl border border-gray-100 bg-gradient-to-br from-white to-gray-50 p-5 shadow-sm">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">{metric.label}</p>
                        <p className="mt-3 text-3xl font-black tracking-tight text-gray-900">{metric.value}</p>
                      </div>
                      <div className={`rounded-2xl bg-gradient-to-br ${metric.tone} p-3 text-white shadow-sm`}>
                        <metric.icon className="h-5 w-5" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-8 flex flex-col gap-4 rounded-3xl border border-gray-100 bg-gray-50/70 p-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex flex-1 items-center gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-3">
                  <Search className="h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    value={peopleSearch}
                    onChange={(event) => setPeopleSearch(event.target.value)}
                    placeholder="Search by name, email, company, or role..."
                    className="w-full bg-transparent text-sm text-gray-900 outline-none placeholder:text-gray-400"
                  />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {PEOPLE_FILTERS.map((filter) => (
                    <button
                      key={filter.key}
                      onClick={() => setPeopleFilter(filter.key)}
                      className={`rounded-full px-4 py-2 text-sm font-bold transition-colors ${
                        peopleFilter === filter.key
                          ? 'bg-[#237afc] text-white shadow-sm'
                          : 'bg-white text-gray-600 border border-gray-200 hover:border-[#237afc] hover:text-[#237afc]'
                      }`}
                    >
                      {filter.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-8 grid gap-8 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,0.9fr)]">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold text-gray-900">Live access roster</h3>
                      <p className="text-sm text-gray-500">{filteredUsers.length} matching people</p>
                    </div>
                    <div className="inline-flex rounded-xl border border-gray-200 bg-white p-1">
                      <button
                        onClick={() => setPeopleView('cards')}
                        className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold ${
                          peopleView === 'cards' ? 'bg-[#edf4ff] text-[#237afc]' : 'text-gray-500'
                        }`}
                      >
                        <LayoutGrid className="h-4 w-4" />
                        Cards
                      </button>
                      <button
                        onClick={() => setPeopleView('table')}
                        className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold ${
                          peopleView === 'table' ? 'bg-[#edf4ff] text-[#237afc]' : 'text-gray-500'
                        }`}
                      >
                        <ListFilter className="h-4 w-4" />
                        Table
                      </button>
                    </div>
                  </div>

                  {userLoading ? (
                    <div className="flex min-h-[240px] items-center justify-center rounded-3xl border border-gray-100 bg-white">
                      <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                    </div>
                  ) : filteredUsers.length === 0 ? (
                    <div className="rounded-3xl border border-dashed border-gray-200 bg-white px-6 py-16 text-center">
                      <Users className="mx-auto h-10 w-10 text-gray-300" />
                      <h4 className="mt-4 text-lg font-bold text-gray-900">No matching people found</h4>
                      <p className="mt-2 text-sm text-gray-500">Try another filter or invite a new admin, mentor, or consultant.</p>
                    </div>
                  ) : peopleView === 'cards' ? (
                    <div className="grid gap-4 xl:grid-cols-2">
                      {filteredUsers.map((person) => {
                        const roleKey = (person.role || '').toLowerCase();
                        const presentation = ROLE_PRESENTATION[roleKey] || {
                          label: person.role,
                          badge: 'bg-gray-100 text-gray-700 border-gray-200',
                          icon: Users,
                        };
                        const authorityPreview = ROLE_AUTHORITY_PRESETS[roleKey] || ['Standard platform access'];
                        const RoleIcon = presentation.icon;
                        return (
                          <div key={person.id} className="rounded-3xl border border-gray-100 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex items-center gap-4">
                                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#237afc] to-[#53b6ff] text-lg font-black text-white shadow-sm">
                                  {`${person.firstName?.[0] || person.email?.[0] || 'U'}${person.lastName?.[0] || ''}`.toUpperCase()}
                                </div>
                                <div>
                                  <p className="text-base font-black text-gray-900">
                                    {[person.firstName, person.lastName].filter(Boolean).join(' ') || person.email.split('@')[0]}
                                  </p>
                                  <p className="mt-1 text-sm text-gray-500">{person.email}</p>
                                  {person.companyName && (
                                    <p className="mt-1 text-xs font-semibold uppercase tracking-[0.22em] text-gray-400">{person.companyName}</p>
                                  )}
                                </div>
                              </div>
                              <RoleIcon className="h-5 w-5 text-gray-300" />
                            </div>

                            <div className="mt-5 flex flex-wrap items-center gap-2">
                              <span className={`rounded-full border px-3 py-1 text-xs font-bold ${presentation.badge}`}>
                                {presentation.label}
                              </span>
                              <span className={`rounded-full px-3 py-1 text-xs font-bold ${
                                person.isVerified ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'
                              }`}>
                                {person.isVerified ? 'Verified' : 'Pending verification'}
                              </span>
                            </div>

                            <div className="mt-5 rounded-2xl bg-gray-50 p-4">
                              <div className="flex items-center gap-2">
                                <KeyRound className="h-4 w-4 text-[#237afc]" />
                                <p className="text-sm font-bold text-gray-900">Authority bundle</p>
                              </div>
                              <div className="mt-3 flex flex-wrap gap-2">
                                {authorityPreview.map((authority) => (
                                  <span key={authority} className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-gray-600 border border-gray-200">
                                    {authority}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="overflow-hidden rounded-3xl border border-gray-100 bg-white">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            {['Person', 'Role', 'Verification', 'Authority bundle', 'Created'].map((header) => (
                              <th key={header} className="px-5 py-4 text-left text-xs font-black uppercase tracking-[0.24em] text-gray-400">{header}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {filteredUsers.map((person) => {
                            const roleKey = (person.role || '').toLowerCase();
                            const presentation = ROLE_PRESENTATION[roleKey] || {
                              label: person.role,
                              badge: 'bg-gray-100 text-gray-700 border-gray-200',
                            };
                            return (
                              <tr key={person.id} className="hover:bg-gray-50/70">
                                <td className="px-5 py-4">
                                  <p className="font-bold text-gray-900">{[person.firstName, person.lastName].filter(Boolean).join(' ') || person.email.split('@')[0]}</p>
                                  <p className="text-xs text-gray-500">{person.email}</p>
                                </td>
                                <td className="px-5 py-4">
                                  <span className={`rounded-full border px-3 py-1 text-xs font-bold ${presentation.badge}`}>
                                    {presentation.label}
                                  </span>
                                </td>
                                <td className="px-5 py-4 text-sm font-semibold text-gray-700">{person.isVerified ? 'Verified' : 'Pending'}</td>
                                <td className="px-5 py-4 text-sm text-gray-500">{(ROLE_AUTHORITY_PRESETS[roleKey] || ['Standard platform access']).slice(0, 2).join(' • ')}</td>
                                <td className="px-5 py-4 text-sm text-gray-500">{person.createdAt ? new Date(person.createdAt).toLocaleDateString() : '—'}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <div className="rounded-3xl border border-gray-100 bg-gradient-to-br from-[#0f172a] via-[#172554] to-[#1d4ed8] p-6 text-white shadow-lg">
                    <div className="flex items-center gap-3">
                      <Sparkles className="h-5 w-5 text-white/80" />
                      <p className="text-sm font-black uppercase tracking-[0.24em] text-white/70">Authority logic</p>
                    </div>
                    <h3 className="mt-4 text-2xl font-black tracking-tight">Role-based access stays simple</h3>
                    <p className="mt-3 text-sm leading-6 text-white/75">
                      Super admins define authority by assigning the right role. The invitation flow becomes the operational control point for admins, mentors, and consultants.
                    </p>
                    <div className="mt-5 space-y-3">
                      {[
                        'Admins handle organization-level operations and escalations.',
                        'Mentors guide practitioners and monitor care quality.',
                        'Consultants handle plans, biomarkers, and follow-up workflows.',
                      ].map((item) => (
                        <div key={item} className="flex items-start gap-2 text-sm text-white/80">
                          <CheckCircle className="mt-0.5 h-4 w-4 text-white" />
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-sm">
                    <div className="flex items-center gap-3">
                      <Mail className="h-5 w-5 text-[#237afc]" />
                      <div>
                        <h3 className="text-lg font-bold text-gray-900">Pending invitations</h3>
                        <p className="text-sm text-gray-500">Track new people before they activate access.</p>
                      </div>
                    </div>

                    <div className="mt-5 space-y-3">
                      {invitations.filter((invite) => !invite.isAccepted && !invite.isExpired).slice(0, 5).map((invite) => {
                        const roleKey = (invite.role || '').toLowerCase();
                        const presentation = ROLE_PRESENTATION[roleKey] || {
                          label: invite.role,
                          badge: 'bg-gray-100 text-gray-700 border-gray-200',
                        };
                        return (
                          <div key={invite.id} className="rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3">
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <p className="text-sm font-bold text-gray-900">{invite.email}</p>
                                <p className="mt-1 text-xs text-gray-500">Expires {new Date(invite.expiresAt).toLocaleDateString()}</p>
                              </div>
                              <span className={`rounded-full border px-3 py-1 text-[11px] font-bold ${presentation.badge}`}>
                                {presentation.label}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                      {invitations.filter((invite) => !invite.isAccepted && !invite.isExpired).length === 0 && (
                        <div className="rounded-2xl border border-dashed border-gray-200 px-4 py-8 text-center text-sm text-gray-500">
                          No pending invitations right now.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default withAuth(SuperuserDashboard, ['superuser', 'super_admin']);
