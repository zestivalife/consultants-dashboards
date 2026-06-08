// pages/register.js
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Building2, Users, Briefcase, Mail, Lock, Eye, EyeOff, AlertCircle, CheckCircle, Loader2, ArrowRight, MapPin } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';

import { authAPI } from '../lib/api';

function RegisterPage() {

    const [formData, setFormData] = useState({
        companyName: '',
        companyEmail: '',
        password: '',
        confirmPassword: '',
        employees: '',
        industry: '',
        location: ''
    });
    const [showPassword, setShowPassword] = useState(false);
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const auth = useAuth();
    const router = useRouter();

    // prefer flags from auth context if present
    const authIsLoading = auth?.isLoading;
    const registering = submitting || authIsLoading;

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const industries = [
        "Technology", "Healthcare", "Finance", "Education", "Retail", "Manufacturing", "Other"
    ];

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        // basic validation
        if (Object.values(formData).some(val => val === '')) {
            setError('Please fill all fields.');
            return;
        }
        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        setSubmitting(true);

        const payload = {
            email: formData.companyEmail,
            password: formData.password,
            companyName: formData.companyName,
            location: formData.location,
            employees: Number(formData.employees),
            industry: formData.industry,
            role: 'corporate_client',
        };

        try {
            if (auth && typeof auth.register === 'function') {
                // AuthContext.register handles the API call + OTP redirect
                const res = await auth.register(payload);
                if (res && res.error) {
                    throw new Error(res.error);
                }
                // Auth context will redirect to /verify-otp automatically
                setSuccess('Registration successful! Check your email for the OTP.');
            } else {
                // Fallback: direct API call if auth context not available
                await authAPI.register(payload);
                setSuccess('Registration successful! Check your email for the OTP.');
                setTimeout(() => router.push(`/verify-otp?email=${encodeURIComponent(formData.companyEmail)}`), 1200);
            }
        } catch (err) {
            console.error('Registration error:', err);
            setError(err.message || 'Network error during registration');
        } finally {
            setSubmitting(false);
        }
    };

    // small animation variants (unchanged)
    const pageVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.6 } },
    };

    const formVariants = {
        hidden: { opacity: 0, x: -20 },
        visible: { opacity: 1, x: 0, transition: { duration: 0.5, delay: 0.2 } },
    };

    return (
        <div className="min-h-screen relative overflow-hidden font-sans">
          {/* Background - same as login / team-member dashboard */}
          <div className="absolute inset-0 bg-[#f4faff]">
            <div
              className="absolute -left-[400px] -top-[400px] w-[1000px] h-[1000px] rounded-full"
              style={{
                background: 'radial-gradient(circle, rgba(255, 208, 208, 0.8) 0%, rgba(255, 220, 220, 0.4) 40%, transparent 70%)',
                filter: 'blur(80px)'
              }}
            />
            <div
              className="absolute -right-[100px] top-[50px] w-[800px] h-[800px] rounded-full"
              style={{
                background: 'radial-gradient(circle, rgba(255, 208, 208, 0.7) 0%, rgba(255, 200, 200, 0.3) 50%, transparent 70%)',
                filter: 'blur(60px)'
              }}
            />
            <div
              className="absolute right-[-300px] bottom-[-200px] w-[900px] h-[900px] rounded-full"
              style={{
                background: 'radial-gradient(circle, rgba(255, 208, 208, 0.6) 0%, rgba(255, 220, 220, 0.3) 50%, transparent 70%)',
                filter: 'blur(80px)'
              }}
            />
            <div className="absolute left-[50%] top-[-50px] w-[1000px] h-[900px] flex items-center justify-center pointer-events-none">
              <img src="/dna-helix.svg" alt="" className="w-[900px] h-[600px] opacity-[0.08] rotate-[27deg] object-contain" />
            </div>
          </div>

          <div className="relative z-10 flex min-h-screen items-center justify-center p-8">
            <motion.div variants={pageVariants} initial="hidden" animate="visible" className="w-full max-w-md">
              {/* Logo - same as login / dashboard */}
              <div className="flex justify-center mb-8">
                <Link href="/" className="flex items-center">
                  <Image src="/nuetra-logo-new.svg" alt="Nuetra Logo" width={200} height={38} className="object-contain" />
                </Link>
              </div>

              {/* White card container */}
              <div className="bg-white border border-[#f2f2f7] rounded-2xl p-6 sm:p-8 shadow-[0px_4px_4px_-1px_rgba(12,12,13,0.1),0px_4px_4px_-1px_rgba(12,12,13,0.05)] space-y-6">
                    <motion.div variants={formVariants} className="text-center">
                        <h2 className="text-3xl font-bold text-gray-900 mb-2">Register Your Company</h2>
                        <p className="text-gray-600">Join our wellness platform and empower your team.</p>
                    </motion.div>

                    <AnimatePresence>
                        {(error || success) && (
                            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className={`rounded-lg p-4 flex items-center space-x-2 ${error ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'}`}>
                                {error && <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />}
                                {success && <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />}
                                <span className={`text-sm ${error ? 'text-red-700' : 'text-green-700'}`}>{error || success}</span>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <motion.form variants={formVariants} onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 mb-2">Company Name</label>
                            <div className="relative">
                                <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                <input id="companyName" name="companyName" type="text" required value={formData.companyName} onChange={handleInputChange} className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#237afc] focus:border-transparent transition-all" placeholder="Enter company name" />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                            <div className="relative">
                                <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                <input id="location" name="location" type="text" required value={formData.location} onChange={handleInputChange} className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#237afc] focus:border-transparent transition-all" placeholder="Enter company location" />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="employees" className="block text-sm font-medium text-gray-700 mb-2">No. of Employees</label>
                                <div className="relative">
                                    <Users className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                    <input id="employees" name="employees" type="number" required value={formData.employees} onChange={handleInputChange} className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#237afc] focus:border-transparent transition-all" placeholder="e.g., 50" />
                                </div>
                            </div>
                            <div>
                                <label htmlFor="industry" className="block text-sm font-medium text-gray-700 mb-2">Industry</label>
                                <div className="relative">
                                    <Briefcase className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                    <select id="industry" name="industry" required value={formData.industry} onChange={handleInputChange} className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#237afc] focus:border-transparent transition-all appearance-none cursor-pointer">
                                        <option value="" disabled>Select industry</option>
                                        {industries.map(ind => <option key={ind} value={ind}>{ind}</option>)}
                                    </select>
                                    <svg className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                                </div>
                            </div>
                        </div>

                        <div>
                            <label htmlFor="companyEmail" className="block text-sm font-medium text-gray-700 mb-2">Company Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                <input id="companyEmail" name="companyEmail" type="email" required value={formData.companyEmail} onChange={handleInputChange} className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#237afc] focus:border-transparent transition-all" placeholder="Enter company email" />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                <input id="password" name="password" type={showPassword ? 'text' : 'password'} required value={formData.password} onChange={handleInputChange} className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#237afc] focus:border-transparent transition-all" placeholder="Create a password" />
                                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
                                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                                </button>
                            </div>
                        </div>

                        <div>
                            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">Confirm Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                <input id="confirmPassword" name="confirmPassword" type={showPassword ? 'text' : 'password'} required value={formData.confirmPassword} onChange={handleInputChange} className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#237afc] focus:border-transparent transition-all" placeholder="Re-enter your password" />
                                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
                                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                                </button>
                            </div>
                        </div>

                        <motion.button
  whileHover={{ scale: 1.02 }}
  whileTap={{ scale: 0.98 }}
  type="submit"
  disabled={registering}
  className="w-full bg-[#08f] hover:bg-[#0077e6] text-white font-bold py-3 px-4 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
>
                            {registering ? (<Loader2 className="h-5 w-5 animate-spin" />) : (<><span>Register</span><ArrowRight className="h-5 w-5" /></>)}
                        </motion.button>
                    </motion.form>

                <p className="text-gray-600 text-center pt-2">
                    Already have an account?{' '}
                    <Link href="/login" className="text-[#237afc] hover:text-[#1a5fc7] font-medium">Sign In</Link>
                </p>
              </div>

              <div className="text-center pt-6">
                <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">← Back to Homepage</Link>
              </div>
            </motion.div>
          </div>
        </div>
    );
}

export default RegisterPage;