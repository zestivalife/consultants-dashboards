import React from 'react';
import DashboardHeader from '../components/DashboardHeader';
import { Coffee, PlusCircle, CheckCircle, Info } from 'lucide-react';
import withAuth from '../hocs/withAuth';

function DietPlanPage() {
  return (
    <div className="min-h-screen bg-[#f4faff]">
      <DashboardHeader />
      <div className="max-w-[1200px] mx-auto px-8 py-12">
        <div className="bg-white rounded-3xl p-10 shadow-xl border border-gray-100">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-4 bg-blue-50 rounded-2xl text-[#08f]">
              <Coffee className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold font-heading text-gray-900">Personalized Diet Plan</h1>
              <p className="text-gray-500">Get a tailored nutritional guidance based on your biofeedback</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div className="bg-gray-50 p-6 rounded-2xl border border-dashed border-gray-200 text-center py-12">
                <Info className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 font-medium font-sans">Dietary recommendation service is currently being synchronized with our nutrition engine.</p>
                <p className="text-sm text-gray-400 max-w-xs mx-auto mt-2">Expect updates shortly as we fine-tune your caloric intake model.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default withAuth(DietPlanPage);
