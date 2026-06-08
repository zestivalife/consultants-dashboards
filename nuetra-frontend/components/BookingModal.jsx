import React, { useState, useEffect } from 'react';
import { Calendar, Clock, User, AlertCircle, Loader, CheckCircle } from 'lucide-react';
import { appointmentAPI, dietPlanAPI } from '../utils/api';
import { apiRequest } from '../lib/api';

const BookingModal = ({ dietPlanId, onComplete, initialData, isLoading, setIsLoading }) => {
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [duration, setDuration] = useState(15); // Default 15 minutes
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [providers, setProviders] = useState([]);
  const [errors, setErrors] = useState({});
  const [loadingSlots, setLoadingSlots] = useState(false);

  // Initialize with existing data if available
  useEffect(() => {
    if (initialData) {
      const appointmentDate = new Date(initialData.startAt);
      setSelectedDate(appointmentDate.toISOString().split('T')[0]);
      setSelectedTime(appointmentDate.toTimeString().slice(0, 5));
      setDuration(initialData.duration || 15);
      setSelectedProvider(initialData.providerId || '');
    }
  }, [initialData]);

  // Fetch available providers
  useEffect(() => {
    fetchProviders();
  }, []);

  // Fetch available slots when date or provider changes
  useEffect(() => {
    if (selectedDate && selectedProvider) {
      fetchAvailableSlots();
    }
  }, [selectedDate, selectedProvider]);

  const fetchProviders = async () => {
    try {
      const providersData = await apiRequest('/consultations/providers');
      const providers = Array.isArray(providersData) ? providersData : (providersData?.providers || []);
      
      if (!providers.length) {
        setErrors({ providers: 'No dieticians available. Please try again later.' });
        setProviders([]);
        return;
      }
      
      // Map provider data to display format
      const formattedProviders = providers.map(provider => ({
        id: provider.id,
        name: provider.email.split('@')[0], // Use email username as display name
        email: provider.email,
        role: provider.role
      }));
      
      setProviders(formattedProviders);
      
      // Auto-select first provider if only one available
      if (formattedProviders.length === 1) {
        setSelectedProvider(formattedProviders[0].id);
      }
    } catch (error) {
      console.error('Error fetching providers:', error);
      setErrors({ 
        providers: error.message || 'Failed to load available providers. Please try again later.' 
      });
      setProviders([]);
    }
  };

  const fetchAvailableSlots = async () => {
    setLoadingSlots(true);
    try {
      // Try to use diet plan slots endpoint if dietPlanId is available
      if (dietPlanId) {
        try {
          const slotsData = await dietPlanAPI.getConsultationSlots(dietPlanId, selectedDate);
          setAvailableSlots(slotsData.data || slotsData || []);
          return;
        } catch (dietPlanErr) {
          console.warn('Diet plan slots endpoint failed, trying appointments endpoint:', dietPlanErr);
        }
      }
      
      // Fallback to appointments available-slots endpoint
      const slotsData = await appointmentAPI.getAvailableSlots(selectedProvider, selectedDate);
      setAvailableSlots(slotsData.data || slotsData || []);
    } catch (error) {
      console.error('Error fetching available slots:', error);
      // If both fail, generate default slots for testing
      const defaultSlots = [];
      for (let hour = 9; hour <= 17; hour++) {
        for (let minute = 0; minute < 60; minute += 15) {
          defaultSlots.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
        }
      }
      setAvailableSlots(defaultSlots);
    } finally {
      setLoadingSlots(false);
    }
  };

  const getMinDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  const getMaxDate = () => {
    const maxDate = new Date();
    maxDate.setDate(maxDate.getDate() + 90); // 3 months ahead
    return maxDate.toISOString().split('T')[0];
  };

  const validateBooking = () => {
    const newErrors = {};

    if (!selectedDate) {
      newErrors.date = 'Please select a date';
    } else {
      const selectedDateTime = new Date(`${selectedDate}T${selectedTime}`);
      const now = new Date();
      const minBookingTime = new Date(now.getTime() + 24 * 60 * 60 * 1000); // 24 hours from now

      if (selectedDateTime < minBookingTime) {
        newErrors.date = 'Appointments must be booked at least 24 hours in advance';
      }
    }

    if (!selectedTime) {
      newErrors.time = 'Please select a time';
    }

    if (!selectedProvider) {
      newErrors.provider = 'Please select a provider';
    }

    if (!duration || duration < 15) {
      newErrors.duration = 'Minimum duration is 15 minutes';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateBooking()) {
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      const startAt = new Date(`${selectedDate}T${selectedTime}`);
      const endAt = new Date(startAt.getTime() + duration * 60 * 1000);

      const appointmentData = {
        dietPlanId,
        providerId: selectedProvider,
        startAt: startAt.toISOString(),
        durationMinutes: duration // Backend expects durationMinutes
      };

      const result = await appointmentAPI.createAppointment(appointmentData);
      
      onComplete({
        appointment: {
          id: result.data?.appointmentId || result.data?.id || result.appointmentId,
          startAt: startAt.toISOString(),
          endAt: endAt.toISOString(),
          providerId: selectedProvider,
          duration,
          durationMinutes: duration,
          provider: providers.find(p => p.id === selectedProvider)
        },
        message: result.message || 'Appointment booked successfully'
      });
    } catch (error) {
      console.error('Error booking appointment:', error);
      setErrors({ submit: error.message || 'Failed to book appointment. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (timeString) => {
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  const isSlotAvailable = (time) => {
    return availableSlots.includes(time);
  };

  const generateTimeSlots = () => {
    const slots = [];
    for (let hour = 9; hour <= 17; hour++) {
      for (let minute = 0; minute < 60; minute += 30) {
        const timeString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        slots.push(timeString);
      }
    }
    return slots;
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Calendar className="h-8 w-8 text-blue-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Book Your Consultation</h3>
        </div>
        <p className="text-sm text-gray-600">
          Schedule a consultation with a dietician to discuss your personalized diet plan
        </p>
      </div>

      {/* Booking Rules */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="h-5 w-5 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-yellow-800">
            <p className="font-medium mb-1">Booking Requirements:</p>
            <ul className="space-y-1 text-xs">
              <li>• Appointments must be booked at least 24 hours in advance</li>
              <li>• Minimum consultation duration is 15 minutes</li>
              <li>• Available slots are Monday-Friday, 9:00 AM - 5:30 PM</li>
              <li>• You'll receive a confirmation email after booking</li>
            </ul>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Provider Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Dietician *
          </label>
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.provider ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">Choose a dietician</option>
            {providers.map(provider => (
              <option key={provider.id} value={provider.id}>
                {provider.name} - {provider.specialization || 'General Nutrition'}
              </option>
            ))}
          </select>
          {errors.provider && <p className="text-red-500 text-xs mt-1">{errors.provider}</p>}
        </div>

        {/* Date Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Date *
          </label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            min={getMinDate()}
            max={getMaxDate()}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.date ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.date && <p className="text-red-500 text-xs mt-1">{errors.date}</p>}
        </div>

        {/* Time Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Time *
          </label>
          {loadingSlots ? (
            <div className="flex items-center justify-center py-8">
              <Loader className="h-6 w-6 animate-spin text-blue-600" />
              <span className="ml-2 text-sm text-gray-600">Loading available slots...</span>
            </div>
          ) : (
            <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
              {generateTimeSlots().map(time => {
                const available = !selectedDate || !selectedProvider || isSlotAvailable(time);
                return (
                  <button
                    key={time}
                    type="button"
                    onClick={() => setSelectedTime(time)}
                    disabled={!available}
                    className={`p-2 text-sm rounded-lg border transition-colors ${
                      selectedTime === time
                        ? 'bg-blue-600 text-white border-blue-600'
                        : available
                        ? 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                        : 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                    }`}
                  >
                    {formatTime(time)}
                  </button>
                );
              })}
            </div>
          )}
          {errors.time && <p className="text-red-500 text-xs mt-1">{errors.time}</p>}
        </div>

        {/* Duration Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Duration (minutes) *
          </label>
          <select
            value={duration}
            onChange={(e) => setDuration(parseInt(e.target.value))}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.duration ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value={15}>15 minutes</option>
            <option value={30}>30 minutes</option>
            <option value={45}>45 minutes</option>
            <option value={60}>60 minutes</option>
          </select>
          {errors.duration && <p className="text-red-500 text-xs mt-1">{errors.duration}</p>}
        </div>

        {/* Booking Summary */}
        {selectedDate && selectedTime && selectedProvider && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-800 mb-2">Booking Summary</h4>
            <div className="text-sm text-blue-700 space-y-1">
              <p><strong>Date:</strong> {new Date(selectedDate).toLocaleDateString()}</p>
              <p><strong>Time:</strong> {formatTime(selectedTime)}</p>
              <p><strong>Duration:</strong> {duration} minutes</p>
              <p><strong>Dietician:</strong> {providers.find(p => p.id === selectedProvider)?.name}</p>
            </div>
          </div>
        )}

        {/* Submit Error */}
        {errors.submit && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-red-700">{errors.submit}</p>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading || !selectedDate || !selectedTime || !selectedProvider}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            Book Appointment & Continue
          </button>
        </div>
      </form>
    </div>
  );
};

export default BookingModal;