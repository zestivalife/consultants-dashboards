import React, { useState, useEffect } from 'react';
import { 
  Calendar, Clock, Users, Building2, CheckCircle, XCircle, 
  Loader2, AlertCircle, Eye, Video, MapPin, FileText, User
} from 'lucide-react';
import { apiRequest } from '../lib/api';

const SESSION_TYPE_ICONS = {
  MINDFULNESS: '🧘',
  PHYSICAL_WELLNESS: '💪',
  MENTAL_HEALTH: '🧠',
  NUTRITION: '🥗',
  STRESS_MANAGEMENT: '😌',
  TEAM_BUILDING: '🤝',
  WORKSHOP: '📚',
  ONE_ON_ONE: '👤'
};

export default function SessionRequestsManager() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState('REQUESTED');
  
  const [approvalData, setApprovalData] = useState({
    location: '',
    meetingLink: '',
    externalInstructor: '',
    maxParticipants: '',
    materials: '',
    notes: ''
  });

  useEffect(() => {
    fetchRequests();
  }, [filterStatus]);

  const fetchRequests = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiRequest(
        `/admin/session-requests?status=${filterStatus}&limit=50`
      );
      setRequests(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error('Error fetching session requests:', err);
      setError(err?.data?.message || err.message || 'Failed to load session requests');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = (request) => {
    setSelectedRequest(request);
    setApprovalData({
      location: '',
      meetingLink: '',
      externalInstructor: '',
      maxParticipants: request.maxParticipants || '',
      materials: '',
      notes: ''
    });
    setShowApprovalModal(true);
  };

  const handleDecline = async (request) => {
    if (!window.confirm(`Are you sure you want to decline the session request "${request.title}"?`)) {
      return;
    }

    const notes = window.prompt('Please provide a reason for declining (optional):');
    
    setActionLoading(true);
    try {
      await apiRequest(`/admin/session-requests/${request.id}`, {
        method: 'PATCH',
        body: { action: 'decline', notes }
      });

      alert('Session request declined successfully');
      fetchRequests();
    } catch (err) {
      console.error('Error declining request:', err);
      alert(err?.data?.message || 'Failed to decline request');
    } finally {
      setActionLoading(false);
    }
  };

  const submitApproval = async () => {
    if (!approvalData.meetingLink && !approvalData.location) {
      alert('Please provide either a meeting link or location');
      return;
    }

    setActionLoading(true);
    try {
      await apiRequest(`/admin/session-requests/${selectedRequest.id}`, {
        method: 'PATCH',
        body: {
          action: 'approve',
          location: approvalData.location || null,
          meetingLink: approvalData.meetingLink || null,
          externalInstructor: approvalData.externalInstructor || null,
          maxParticipants: approvalData.maxParticipants ? parseInt(approvalData.maxParticipants) : null,
          materials: approvalData.materials ? [approvalData.materials] : null
        }
      });

      alert('Session request approved and scheduled successfully!');
      setShowApprovalModal(false);
      setSelectedRequest(null);
      fetchRequests();
    } catch (err) {
      console.error('Error approving request:', err);
      alert(err?.data?.message || 'Failed to approve request');
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-[#64ae00]" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with filters */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Session Requests</h2>
          <p className="text-gray-600 mt-1">Review and approve corporate wellness session requests</p>
        </div>
        
        <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
          {['REQUESTED', 'SCHEDULED', 'REJECTED'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                filterStatus === status
                  ? 'bg-white shadow-sm text-[#64ae00]'
                  : 'text-gray-600 hover:text-[#64ae00]'
              }`}
            >
              {status === 'REQUESTED' ? 'Pending' : status.charAt(0) + status.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {/* Requests list */}
      {requests.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center border border-gray-200">
          <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No {filterStatus.toLowerCase()} session requests</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {requests.map((request) => (
            <div
              key={request.id}
              className="bg-white rounded-xl p-6 border border-gray-200 hover:border-[#64ae00] hover:shadow-lg transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <span className="text-3xl">
                      {SESSION_TYPE_ICONS[request.type] || '📅'}
                    </span>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900">{request.title}</h3>
                      <p className="text-sm text-gray-600">
                        {request.type.replace('_', ' ')}
                      </p>
                    </div>
                  </div>

                  {request.description && (
                    <p className="text-gray-700 mb-4">{request.description}</p>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <Building2 className="h-4 w-4" />
                      <span>{request.company?.name || 'Unknown'}</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <Calendar className="h-4 w-4" />
                      <span>{formatDate(request.scheduledAt)}</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <Clock className="h-4 w-4" />
                      <span>{request.duration} minutes</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <Users className="h-4 w-4" />
                      <span>
                        {request.targetAudience === 'ALL_EMPLOYEES' 
                          ? 'All Employees' 
                          : request.team?.name || 'Specific Team'}
                      </span>
                    </div>
                  </div>

                  {request.requestNotes && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">
                        <FileText className="inline h-4 w-4 mr-1" />
                        <strong>Notes:</strong> {request.requestNotes}
                      </p>
                    </div>
                  )}
                </div>

                {request.status === 'REQUESTED' && (
                  <div className="flex flex-col space-y-2 ml-4">
                    <button
                      onClick={() => handleApprove(request)}
                      disabled={actionLoading}
                      className="px-4 py-2 bg-[#64ae00] text-white rounded-lg hover:bg-[#579700] transition-all flex items-center space-x-2 disabled:opacity-50"
                    >
                      <CheckCircle className="h-4 w-4" />
                      <span>Approve</span>
                    </button>
                    <button
                      onClick={() => handleDecline(request)}
                      disabled={actionLoading}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all flex items-center space-x-2 disabled:opacity-50"
                    >
                      <XCircle className="h-4 w-4" />
                      <span>Decline</span>
                    </button>
                  </div>
                )}

                {request.status === 'SCHEDULED' && (
                  <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                    Approved
                  </span>
                )}

                {request.status === 'REJECTED' && (
                  <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                    Declined
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Approval Modal */}
      {showApprovalModal && selectedRequest && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Approve Session: {selectedRequest.title}
            </h3>
            
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Video className="inline h-4 w-4 mr-1" />
                  Meeting Link *
                </label>
                <input
                  type="url"
                  value={approvalData.meetingLink}
                  onChange={(e) => setApprovalData(prev => ({ ...prev, meetingLink: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
                  placeholder="https://zoom.us/j/..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <MapPin className="inline h-4 w-4 mr-1" />
                  Location (optional)
                </label>
                <input
                  type="text"
                  value={approvalData.location}
                  onChange={(e) => setApprovalData(prev => ({ ...prev, location: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
                  placeholder="Conference Room A"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <User className="inline h-4 w-4 mr-1" />
                  Instructor Name
                </label>
                <input
                  type="text"
                  value={approvalData.externalInstructor}
                  onChange={(e) => setApprovalData(prev => ({ ...prev, externalInstructor: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
                  placeholder="Dr. Sarah Chen"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Users className="inline h-4 w-4 mr-1" />
                  Max Participants (optional)
                </label>
                <input
                  type="number"
                  value={approvalData.maxParticipants}
                  onChange={(e) => setApprovalData(prev => ({ ...prev, maxParticipants: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
                  placeholder="Unlimited"
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <FileText className="inline h-4 w-4 mr-1" />
                  Materials/Resources (optional)
                </label>
                <input
                  type="text"
                  value={approvalData.materials}
                  onChange={(e) => setApprovalData(prev => ({ ...prev, materials: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
                  placeholder="https://docs.google.com/..."
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowApprovalModal(false);
                  setSelectedRequest(null);
                }}
                disabled={actionLoading}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={submitApproval}
                disabled={actionLoading}
                className="px-6 py-2 bg-[#64ae00] text-white rounded-lg hover:bg-[#579700] transition-all flex items-center space-x-2 disabled:opacity-50"
              >
                {actionLoading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Approving...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-5 w-5" />
                    <span>Approve & Schedule</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

