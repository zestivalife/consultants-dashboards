// src/components/InviteEmployeeForm.js
import React, { useState } from 'react';
import * as XLSX from 'xlsx';
import { UploadCloud, CheckCircle, AlertCircle } from 'lucide-react';

export default function InviteEmployeeForm({ onClose, onSubmit }) {
  const [activeTab, setActiveTab] = useState('single');
  const [formData, setFormData] = useState({
    email: '',
    firstName: '',
    lastName: '',
    phone: '',
    role: 'TEAM_MEMBER'
  });
  const [bulkFile, setBulkFile] = useState(null);
  const [bulkEmployees, setBulkEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setError('');
    setBulkFile(file);

    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const bstr = evt.target.result;
        const wb = XLSX.read(bstr, { type: 'binary' });
        const wsname = wb.SheetNames[0];
        const ws = wb.Sheets[wsname];
        const data = XLSX.utils.sheet_to_json(ws);
        
        if (data.length === 0) {
          setError("File is empty or badly formatted. Make sure it has 'First Name', 'Last Name', 'Email', and 'Role' headers.");
          setBulkEmployees([]);
          return;
        }

        const parsedEmp = data.map((row, index) => {
          const fn = row['First Name'] || row['firstName'] || row['firstname'] || '';
          const ln = row['Last Name'] || row['lastName'] || row['lastname'] || '';
          const email = row['Email'] || row['email'] || '';
          const role = (row['Role'] || row['role'] || 'TEAM_MEMBER').toUpperCase();
          const phone = row['Phone'] || row['phone'] || '';
          
          return { firstName: fn, lastName: ln, email, role, phone };
        });

        // Validation
        const missingEmails = parsedEmp.filter(e => !e.email);
        if (missingEmails.length > 0) {
          setError(`Found ${missingEmails.length} rows without an Email. Emails are required.`);
        }
        
        setBulkEmployees(parsedEmp.filter(e => e.email));
      } catch (err) {
        setError('Failed to parse file. Ensure it is a valid CSV or XLSX.');
      }
    };
    reader.readAsBinaryString(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      if (activeTab === 'single') {
        if (!formData.email) throw new Error('Email is required');
        if (!formData.firstName || !formData.lastName) throw new Error('First name and last name are required');
        await onSubmit(formData, 'single');
      } else {
        if (bulkEmployees.length === 0) throw new Error('Please upload a valid file with employee rows first.');
        await onSubmit(bulkEmployees, 'bulk');
      }
      // Success is normally handled by the parent modal closing, but we can set state
    } catch (err) {
      console.error('Invite error:', err);
      setError(err?.data?.message || err.message || 'Failed to send invitation(s)');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          className={`pb-2 px-4 text-sm font-medium ${activeTab === 'single' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => { setActiveTab('single'); setError(''); }}
        >
          Single Invite
        </button>
        <button
          className={`pb-2 px-4 text-sm font-medium ${activeTab === 'bulk' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => { setActiveTab('bulk'); setError(''); }}
        >
          Bulk Invite (Upload)
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex gap-2">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Single Invite View */}
        {activeTab === 'single' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">First Name *</label>
                <input type="text" name="firstName" required value={formData.firstName} onChange={handleChange} disabled={loading} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100" placeholder="John" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Last Name *</label>
                <input type="text" name="lastName" required value={formData.lastName} onChange={handleChange} disabled={loading} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100" placeholder="Doe" />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
              <input type="email" name="email" required value={formData.email} onChange={handleChange} disabled={loading} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100" placeholder="employee@company.com" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Phone (Optional)</label>
                <input type="tel" name="phone" value={formData.phone} onChange={handleChange} disabled={loading} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100" placeholder="+91 98765 43210" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Role *</label>
                <select name="role" value={formData.role} onChange={handleChange} disabled={loading} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100">
                  <option value="TEAM_MEMBER">Team Member</option>
                  <option value="TEAM_LEAD">Team Lead</option>
                </select>
              </div>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> An invitation email will be sent with temporary login credentials.
              </p>
            </div>
          </div>
        )}

        {/* Bulk Invite View */}
        {activeTab === 'bulk' && (
          <div className="space-y-4">
            <div className="border border-dashed border-gray-300 rounded-xl p-8 text-center bg-gray-50 flex flex-col items-center justify-center">
              <UploadCloud className="w-8 h-8 text-gray-400 mb-2" />
              <p className="text-sm text-gray-600 mb-4">Upload an Excel (.xlsx, .xls) or CSV file containing.</p>
              <input type="file" id="bulkUpload" accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel" className="hidden" onChange={handleFileUpload} />
              <label htmlFor="bulkUpload" className="px-5 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-100 shadow-sm transition-all">
                Choose File
              </label>
            </div>

            {bulkEmployees.length > 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex gap-2">
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                <p className="text-sm text-green-800">Ready to invite <strong>{bulkEmployees.length}</strong> employees.</p>
              </div>
            )}

            <div className="text-xs text-gray-500">
              <p className="font-semibold mb-1">Expected format headers:</p>
              <ul className="list-disc ml-4">
                <li><code>Email</code> (Required)</li>
                <li><code>First Name</code></li>
                <li><code>Last Name</code></li>
                <li><code>Role</code> (Optional, defaults to TEAM_MEMBER, can be TEAM_LEAD)</li>
                <li><code>Phone</code> (Optional)</li>
              </ul>
            </div>
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-100">
          <button type="button" onClick={onClose} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="px-6 py-2 bg-[#08f] text-white rounded-lg hover:bg-[#0077e6] transition-all disabled:opacity-50 flex items-center">
            {loading ? 'Sending...' : (activeTab === 'single' ? 'Send Invitation' : `Invite ${bulkEmployees.length || 0} Employees`)}
          </button>
        </div>
      </form>
    </div>
  );
}