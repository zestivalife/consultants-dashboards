// apps/web/frontend/components/dashboard/SessionsTab.jsx
import React, { useState } from 'react';
import { 
  Mic, MicOff, Volume2, VolumeX, Maximize2, 
  Calendar, Clock, Plus, ChevronRight, Play, 
  Video, VideoOff, Phone, PhoneOff, MessageSquare
} from 'lucide-react';

// No static mock sessions anymore. We will use dynamic data.

// Video Player Component
function VideoPlayer({ session, onNextSession }) {
  const [isMuted, setIsMuted] = useState(false);
  const [isMicOn, setIsMicOn] = useState(true);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [elapsedTime, setElapsedTime] = useState('04:45');

  return (
    <div className="relative rounded-2xl overflow-hidden bg-gray-900" style={{ height: 400 }}>
      {/* Video/Thumbnail */}
      <img 
        src={session?.thumbnail || 'https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=600&h=400&fit=crop'}
        alt="Session"
        className="w-full h-full object-cover"
      />
      
      {/* Overlay gradient */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
      
      {/* Live indicator */}
      {session?.status === 'live' && (
        <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/50 backdrop-blur-sm px-4 py-2 rounded-full">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
          <span className="text-white font-medium">{elapsedTime}</span>
        </div>
      )}
      
      {/* Session info overlay */}
      {session?.status !== 'live' && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/40">
          <button className="w-20 h-20 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 transition-colors">
            <Play className="w-10 h-10 text-white fill-white ml-1" />
          </button>
        </div>
      )}
      
      {/* Controls */}
      <div className="absolute bottom-0 left-0 right-0 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Mic */}
          <button 
            onClick={() => setIsMicOn(!isMicOn)}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
              isMicOn ? 'bg-white/20 backdrop-blur-sm hover:bg-white/30' : 'bg-red-500 hover:bg-red-600'
            }`}
          >
            {isMicOn ? <Mic className="w-5 h-5 text-white" /> : <MicOff className="w-5 h-5 text-white" />}
          </button>
          
          {/* Volume */}
          <button 
            onClick={() => setIsMuted(!isMuted)}
            className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 transition-colors"
          >
            {isMuted ? <VolumeX className="w-5 h-5 text-white" /> : <Volume2 className="w-5 h-5 text-white" />}
          </button>
          
          {/* Fullscreen */}
          <button 
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 transition-colors"
          >
            <Maximize2 className="w-5 h-5 text-white" />
          </button>
        </div>
        
        {/* Next Session Button */}
        <button 
          onClick={onNextSession}
          className="px-6 py-3 bg-[#237afc] text-white rounded-lg font-medium hover:bg-[#1a5fc7] transition-colors shadow-lg"
        >
          Next Session
        </button>
      </div>
    </div>
  );
}

// Session Card Component
function SessionCard({ session, isActive, onClick }) {
  const statusColors = {
    live: 'bg-red-100 text-red-600 border-red-200',
    upcoming: 'bg-blue-100 text-blue-600 border-blue-200',
    completed: 'bg-green-100 text-green-600 border-green-200',
  };

  return (
    <button
      onClick={onClick}
      className={`w-full p-4 rounded-xl text-left transition-all ${
        isActive 
          ? 'bg-blue-50 border-2 border-blue-200' 
          : 'bg-white hover:bg-gray-50 border border-gray-100'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-semibold text-gray-800">{session.title}</h4>
            {session.status === 'live' && (
              <span className="px-2 py-0.5 bg-red-100 text-red-600 text-xs font-medium rounded-full animate-pulse">
                LIVE
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mb-3">{session.specialist}</p>
          
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              <span>{session.date}</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              <span>{session.time}</span>
            </div>
          </div>
        </div>
        
        <img 
          src={session.specialistAvatar}
          alt={session.specialistName}
          className="w-12 h-12 rounded-full object-cover border-2 border-white shadow-sm"
        />
      </div>
    </button>
  );
}

export default function SessionsTab() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [requestForm, setRequestForm] = useState({
    title: 'Wellness Session',
    type: 'Mental Wellness',
    scheduledAt: '',
    time: '09:00 AM',
    duration: 60,
    mode: 'ONLINE',
    targetAudience: 'ALL_EMPLOYEES',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    requestNotes: ''
  });
  
  const currentMonth = new Date().toLocaleString('default', { month: 'long', year: 'numeric' });
  
  React.useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const { teamMemberAPI } = await import('../../lib/api');
      const res = await teamMemberAPI.getSessions();
      
      const mappedSessions = res.map(s => ({
        ...s,
        specialist: s.specialistRole || 'Pending Assignment',
        specialistName: s.specialistName || 'TBD',
        specialistAvatar: s.specialistAvatar || 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=100&h=100&fit=crop&crop=face',
        date: new Date(s.scheduledAt).toLocaleDateString(),
        time: new Date(s.scheduledAt).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
        thumbnail: s.thumbnailUrl || 'https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=600&h=400&fit=crop',
        status: s.status.toLowerCase()
      }));
      
      setSessions(mappedSessions);
      if (mappedSessions.length > 0) {
        setActiveSession(mappedSessions[0]);
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  };

  const handleNextSession = () => {
    if (!sessions.length || !activeSession) return;
    const currentIndex = sessions.findIndex(s => s.id === activeSession.id);
    const nextIndex = (currentIndex + 1) % sessions.length;
    setActiveSession(sessions[nextIndex]);
  };

  const handleSubmitRequest = async () => {
    if (!requestForm.scheduledAt || !requestForm.time) {
      alert("Please select a valid date and time");
      return;
    }

    try {
      setIsSubmitting(true);
      const { teamMemberAPI } = await import('../../lib/api');
      
      // Combine date and time to ISO
      const [hours, minutes, period] = requestForm.time.split(/[: ]/);
      let hour24 = parseInt(hours, 10);
      if (period === 'PM' && hour24 < 12) hour24 += 12;
      if (period === 'AM' && hour24 === 12) hour24 = 0;
      
      const dt = new Date(requestForm.scheduledAt);
      dt.setHours(hour24, parseInt(minutes, 10), 0);
      
      const payload = {
        title: `${requestForm.type} Session`,
        type: requestForm.type.toUpperCase().replace(' ', '_'),
        scheduledAt: dt.toISOString(),
        duration: requestForm.duration,
        mode: requestForm.mode,
        targetAudience: requestForm.targetAudience,
        timezone: requestForm.timezone,
        requestNotes: requestForm.requestNotes
      };

      await teamMemberAPI.requestSession(payload);
      setShowRequestModal(false);
      alert('Session request submitted successfully! Your Department Lead and HR will be notified.');
      fetchSessions();
    } catch (error) {
      console.error(error);
      alert('Failed to request session. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const upcomingSessions = sessions.filter(s => s.status === 'upcoming' || s.status === 'live' || s.status === 'scheduled');
  const pastSessions = sessions.filter(s => s.status === 'completed');
  const missedSessions = sessions.filter(s => s.status === 'missed');

  return (
    <div className="flex gap-6">
      {/* Left - Video Player */}
      <div className="flex-1" style={{ maxWidth: 560 }}>
        <VideoPlayer 
          session={activeSession} 
          onNextSession={handleNextSession}
        />
        
        {/* Current Session Info */}
        {activeSession && (
          <div className="mt-4 p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-800">{activeSession.title}</h3>
                <p className="text-sm text-gray-500">with {activeSession.specialistName}</p>
              </div>
              <div className="flex gap-2">
                <button className="p-2 bg-white rounded-lg border border-gray-200 hover:bg-gray-50">
                  <MessageSquare className="w-5 h-5 text-gray-600" />
                </button>
                <button className="p-2 bg-red-500 rounded-lg hover:bg-red-600">
                  <PhoneOff className="w-5 h-5 text-white" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Middle - Sessions Overview */}
      <div className="w-[320px] shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-800">Sessions Overview</h2>
            <p className="text-sm text-gray-500">{currentMonth}</p>
          </div>
          <button 
            onClick={() => setShowRequestModal(true)}
            className="w-10 h-10 bg-[#237afc] rounded-full flex items-center justify-center hover:bg-[#1a5fc7] transition-colors shadow-lg shadow-blue-500/30"
          >
            <Plus className="w-5 h-5 text-white" />
          </button>
        </div>
        
        {/* Sessions List */}
        <div className="space-y-3 max-h-[450px] overflow-y-auto pr-2">
          {upcomingSessions.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              isActive={activeSession?.id === session.id}
              onClick={() => setActiveSession(session)}
            />
          ))}
          
          {pastSessions.length > 0 && (
            <>
              <div className="py-2">
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Past Sessions</span>
              </div>
              {pastSessions.map((session) => (
                <SessionCard
                  key={session.id}
                  session={session}
                  isActive={activeSession?.id === session.id}
                  onClick={() => setActiveSession(session)}
                />
              ))}
            </>
          )}
        </div>
      </div>

      {/* Right - Info Panel */}
      <div className="w-[200px] shrink-0">
        {/* Ads Section */}
        <div className="p-4 bg-white rounded-xl border border-gray-100 mb-4">
          <p className="text-sm font-semibold text-gray-700 mb-3">Partner Apps</p>
          <div className="space-y-2">
            <a href="#" className="block text-sm text-blue-600 hover:underline">Fiteatsy Ads</a>
            <a href="#" className="block text-sm text-blue-600 hover:underline">Humjoli Ads</a>
          </div>
        </div>
        
        {/* Info Box */}
        <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
          <p className="text-sm text-blue-800">
            <span className="font-semibold">Request a Session</span> will go to Department Lead and HR
          </p>
        </div>
        
        {/* Quick Stats */}
        <div className="mt-4 p-4 bg-white rounded-xl border border-gray-100">
          <p className="text-sm font-semibold text-gray-700 mb-3">This Month</p>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">Attended</span>
              <span className="text-sm font-bold text-green-600">{pastSessions.length}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">Upcoming</span>
              <span className="text-sm font-bold text-blue-600">{upcomingSessions.length}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">Missed</span>
              <span className="text-sm font-bold text-red-600">{missedSessions.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Request Session Modal */}
      {showRequestModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Request a Session</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Session Type</label>
                <select 
                  value={requestForm.type}
                  onChange={e => setRequestForm({...requestForm, type: e.target.value})}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option>Dental Health</option>
                  <option>Mental Wellness</option>
                  <option>Nutrition Counseling</option>
                  <option>Stress Management</option>
                  <option>Physical Therapy</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Date</label>
                <input 
                  type="date" 
                  value={requestForm.scheduledAt}
                  onChange={e => setRequestForm({...requestForm, scheduledAt: e.target.value})}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Time</label>
                <select 
                  value={requestForm.time}
                  onChange={e => setRequestForm({...requestForm, time: e.target.value})}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option>09:00 AM</option>
                  <option>10:00 AM</option>
                  <option>11:00 AM</option>
                  <option>12:00 PM</option>
                  <option>01:00 PM</option>
                  <option>02:00 PM</option>
                  <option>03:00 PM</option>
                  <option>04:00 PM</option>
                  <option>05:00 PM</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes (Optional)</label>
                <textarea 
                  value={requestForm.requestNotes}
                  onChange={e => setRequestForm({...requestForm, requestNotes: e.target.value})}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows={3}
                  placeholder="Any specific concerns or topics you'd like to discuss..."
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button 
                onClick={() => setShowRequestModal(false)}
                disabled={isSubmitting}
                className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
              >
                Cancel
              </button>
              <button 
                onClick={handleSubmitRequest}
                disabled={isSubmitting}
                className="flex-1 px-4 py-2.5 bg-[#237afc] text-white rounded-lg hover:bg-[#1a5fc7] font-medium disabled:opacity-70"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Request'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

