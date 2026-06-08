// apps/web/frontend/pages/terms-of-service.js
import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useAuth } from '../context/AuthContext';
import { getDashboardPathForRole } from '../lib/roleRoutes';
import { ArrowLeft, FileText, Scale } from 'lucide-react';

export default function TermsOfServicePage() {
  const { user: authUser } = useAuth();

  // Get the correct dashboard path based on user role
  const getDashboardPath = () => {
    if (!authUser) {
      return '/'; // Redirect to home if user is not authenticated
    }
    return getDashboardPathForRole(authUser.role, '/dashboard/team-member');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <Link href={getDashboardPath()} className="inline-flex items-center text-sm text-gray-600 hover:text-[#64ae00] mb-8">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 md:p-12"
        >
          <div className="flex items-center space-x-3 mb-8">
            <div className="p-3 bg-[#64ae00]/10 rounded-lg">
              <Scale className="h-8 w-8 text-[#64ae00]" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Terms of Service</h1>
              <p className="text-gray-600 mt-1">Last updated: {new Date().toLocaleDateString()}</p>
            </div>
          </div>

          <div className="prose prose-lg max-w-none">
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Acceptance of Terms</h2>
              <p className="text-gray-700 leading-relaxed">
                By accessing and using the Nuetra Wellness Platform, you accept and agree to be bound by these Terms of Service. If you do not agree, please do not use our platform.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Description of Service</h2>
              <p className="text-gray-700 leading-relaxed">
                Nuetra provides a corporate wellness platform that enables organizations to manage wellness programs, schedule sessions, track metrics, and connect employees with wellness resources.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. User Accounts</h2>
              <ul className="list-disc pl-6 text-gray-700 space-y-2">
                <li>You must provide accurate and complete information when creating an account</li>
                <li>You are responsible for maintaining the security of your account</li>
                <li>You must notify us immediately of any unauthorized access</li>
                <li>You are responsible for all activities under your account</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Acceptable Use</h2>
              <p className="text-gray-700 leading-relaxed mb-4">You agree not to:</p>
              <ul className="list-disc pl-6 text-gray-700 space-y-2">
                <li>Use the platform for any illegal or unauthorized purpose</li>
                <li>Violate any applicable laws or regulations</li>
                <li>Interfere with or disrupt the platform or servers</li>
                <li>Attempt to gain unauthorized access to any part of the platform</li>
                <li>Upload malicious code or viruses</li>
                <li>Harass, abuse, or harm other users</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Intellectual Property</h2>
              <p className="text-gray-700 leading-relaxed">
                All content, features, and functionality of the platform are owned by Nuetra and are protected by copyright, trademark, and other intellectual property laws. You may not reproduce, distribute, or create derivative works without our written permission.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. User Content</h2>
              <p className="text-gray-700 leading-relaxed">
                You retain ownership of content you upload to the platform. By uploading content, you grant us a license to use, store, and display that content as necessary to provide our services.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Payment Terms</h2>
              <p className="text-gray-700 leading-relaxed">
                Corporate clients agree to pay subscription fees as outlined in their service agreement. Payments are due according to the billing cycle specified in your plan.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Termination</h2>
              <p className="text-gray-700 leading-relaxed">
                We may terminate or suspend your account immediately, without prior notice, for conduct that we believe violates these Terms or is harmful to other users, us, or third parties.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Disclaimer of Warranties</h2>
              <p className="text-gray-700 leading-relaxed">
                The platform is provided "as is" without warranties of any kind. We do not guarantee that the platform will be uninterrupted, secure, or error-free.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Limitation of Liability</h2>
              <p className="text-gray-700 leading-relaxed">
                To the maximum extent permitted by law, Nuetra shall not be liable for any indirect, incidental, special, or consequential damages arising from your use of the platform.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Governing Law</h2>
              <p className="text-gray-700 leading-relaxed">
                These Terms shall be governed by and construed in accordance with the laws of India, without regard to its conflict of law provisions.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Changes to Terms</h2>
              <p className="text-gray-700 leading-relaxed">
                We reserve the right to modify these Terms at any time. We will notify users of significant changes via email or platform notification.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">13. Contact Information</h2>
              <p className="text-gray-700 leading-relaxed">
                For questions about these Terms, please contact us at:
              </p>
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-700"><strong>Email:</strong> legal@nuetra.in</p>
                <p className="text-gray-700"><strong>Address:</strong> Nuetra Wellness Platform</p>
              </div>
            </section>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

