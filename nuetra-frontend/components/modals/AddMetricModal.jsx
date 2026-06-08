import React, { useState } from 'react';
import { X, Activity, Heart, Zap, Moon, Droplet, Brain, TrendingUp } from 'lucide-react';

const metricTypes = [
  { id: 'mood', label: 'Mood', icon: Heart, color: '#ec4899', unit: '/10' },
  { id: 'energy', label: 'Energy', icon: Zap, color: '#f59e0b', unit: '/10' },
  { id: 'sleep', label: 'Sleep', icon: Moon, color: '#3b82f6', unit: 'hours' },
  { id: 'stress', label: 'Stress', icon: Brain, color: '#ef4444', unit: '/10' },
  { id: 'hydration', label: 'Hydration', icon: Droplet, color: '#06b6d4', unit: 'glasses' },
  { id: 'exercise', label: 'Exercise', icon: Activity, color: '#22c55e', unit: 'minutes' },
];

const AddMetricModal = ({ isOpen, onClose, onSave }) => {
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [value, setValue] = useState('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedMetric || !value) return;

    setIsSubmitting(true);
    try {
      await onSave({
        type: selectedMetric.id,
        value: parseFloat(value),
        notes,
        timestamp: new Date().toISOString(),
      });
      
      // Reset form
      setSelectedMetric(null);
      setValue('');
      setNotes('');
      onClose();
    } catch (error) {
      console.error('Failed to save metric:', error);
      alert('Failed to save metric. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedMetricData = metricTypes.find(m => m.id === selectedMetric?.id);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-hidden animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Log Wellness Metric</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Metric Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Select Metric Type
            </label>
            <div className="grid grid-cols-3 gap-3">
              {metricTypes.map((metric) => {
                const Icon = metric.icon;
                const isSelected = selectedMetric?.id === metric.id;
                
                return (
                  <button
                    key={metric.id}
                    type="button"
                    onClick={() => setSelectedMetric(metric)}
                    className={`p-3 rounded-xl border-2 transition-all ${
                      isSelected
                        ? 'border-[#64ae00] bg-green-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Icon 
                      className="w-6 h-6 mx-auto mb-1" 
                      style={{ color: metric.color }}
                    />
                    <p className="text-xs font-medium text-gray-900">{metric.label}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Value Input */}
          {selectedMetric && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Value {selectedMetricData?.unit && `(${selectedMetricData.unit})`}
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max={selectedMetric.id === 'mood' || selectedMetric.id === 'energy' || selectedMetric.id === 'stress' ? '10' : undefined}
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  placeholder="Enter value"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notes (Optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add any notes..."
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:border-transparent resize-none"
                />
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-gray-100 text-gray-700 font-semibold rounded-lg hover:bg-gray-200 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedMetric || !value || isSubmitting}
              className="flex-1 px-4 py-3 bg-[#64ae00] text-white font-semibold rounded-lg hover:bg-[#589900] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Saving...' : 'Save Metric'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddMetricModal;

