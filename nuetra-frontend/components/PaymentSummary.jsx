import React, { useState, useEffect } from 'react';
import { DollarSign, Calendar, AlertCircle, Loader, Shield, CheckCircle } from 'lucide-react';
import { appointmentAPI } from '../utils/api';
import { getCurrentUser } from '../lib/auth';

const PaymentSummary = ({ dietPlan, appointment, onComplete, isLoading, setIsLoading }) => {
  const [errors, setErrors] = useState({});
  const [razorpayLoaded, setRazorpayLoaded] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  // Calculate pricing based on diet plan details
  const calculatePricing = () => {
    const basePrice = 150; // Base consultation fee
    const planPrice = 100; // Standard diet plan price (budgetRange field removed)
    
    const durationMultiplier = appointment?.duration > 30 ? 1.5 : 1;
    const consultationFee = Math.round(basePrice * durationMultiplier);
    
    const subtotal = planPrice + consultationFee;
    const tax = Math.round(subtotal * 0.08); // 8% tax
    const total = subtotal + tax;

    return {
      planPrice,
      consultationFee,
      subtotal,
      tax,
      total
    };
  };

  const pricing = calculatePricing();

  // Load Razorpay script
  useEffect(() => {
    // Get current user
    const user = getCurrentUser();
    setCurrentUser(user);

    // Load Razorpay script if not already loaded
    if (typeof window !== 'undefined' && !window.Razorpay) {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.async = true;
      script.onload = () => {
        setRazorpayLoaded(true);
      };
      script.onerror = () => {
        setErrors({ submit: 'Failed to load Razorpay. Please refresh the page.' });
      };
      document.body.appendChild(script);

      return () => {
        // Cleanup: remove script if component unmounts
        const existingScript = document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
        if (existingScript) {
          document.body.removeChild(existingScript);
        }
      };
    } else if (window.Razorpay) {
      setRazorpayLoaded(true);
    }
  }, []);

  const handleSkipPayment = async () => {
    // Skip payment for testing purposes with dummy data
    if (!appointment?.id) {
      setErrors({ submit: 'Appointment information is missing' });
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      // Create dummy payment data for testing
      const dummyPaymentData = {
        paymentStatus: 'COMPLETED',
        paymentMethod: 'CREDIT_CARD',
        paymentAmount: pricing.total,
        transactionId: `test_txn_${Date.now()}`,
        orderId: `test_order_${Date.now()}`,
        paymentId: `test_payment_${Date.now()}`
      };

      // Update appointment with dummy payment status via backend
      // Note: This is for testing only - in production, payment must be verified
      try {
        const result = await appointmentAPI.updatePaymentStatus(appointment.id, {
          ...dummyPaymentData,
          skipVerification: true // Flag to indicate this is a test skip
        });

        // Proceed to completion step
        onComplete({
          payment: {
            status: 'COMPLETED',
            amount: pricing.total,
            transactionId: dummyPaymentData.transactionId,
            orderId: dummyPaymentData.orderId,
            method: 'CREDIT_CARD',
            skipped: true // Flag to indicate payment was skipped
          },
          appointment: {
            ...appointment,
            ...dummyPaymentData
          },
          message: 'Payment skipped for testing - flow completed'
        });
      } catch (updateError) {
        // If backend update fails, still proceed with dummy data for testing
        console.warn('Could not update appointment payment status, but continuing with test flow:', updateError);
        onComplete({
          payment: {
            status: 'COMPLETED',
            amount: pricing.total,
            transactionId: dummyPaymentData.transactionId,
            orderId: dummyPaymentData.orderId,
            method: 'CREDIT_CARD',
            skipped: true
          },
          appointment: {
            ...appointment,
            ...dummyPaymentData
          },
          message: 'Payment skipped for testing - flow completed'
        });
      }
    } catch (error) {
      console.error('Skip payment error:', error);
      setErrors({ submit: error.message || 'Failed to skip payment. Please try again.' });
      setIsLoading(false);
    }
  };

  const handlePayment = async (e) => {
    e.preventDefault();
    
    if (!appointment?.id) {
      setErrors({ submit: 'Appointment information is missing' });
      return;
    }

    if (!razorpayLoaded) {
      setErrors({ submit: 'Razorpay is still loading. Please wait...' });
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      // Step 1: Create Razorpay order via backend
      const orderResponse = await appointmentAPI.createRazorpayOrder(appointment.id, pricing.total);
      
      if (!orderResponse.success || !orderResponse.data) {
        throw new Error(orderResponse.message || 'Failed to create payment order');
      }

      const { orderId, amount, currency, keyId } = orderResponse.data;

      // Step 2: Open Razorpay Checkout
      const options = {
        key: keyId,
        amount: amount, // Amount in paise
        currency: currency || 'INR',
        name: 'Diet Plan Consultation',
        description: `Appointment with ${appointment?.provider?.name || 'Dietitian'}`,
        order_id: orderId,
        handler: async function (response) {
          // Step 3: Verify payment with backend
          try {
            setIsLoading(true);
            const verifyResponse = await appointmentAPI.verifyRazorpayPayment(
              appointment.id,
              response.razorpay_payment_id,
              response.razorpay_order_id,
              response.razorpay_signature
            );

            if (verifyResponse.success) {
              // Payment verified successfully
              onComplete({
                payment: {
                  status: 'COMPLETED',
                  amount: pricing.total,
                  transactionId: response.razorpay_payment_id,
                  orderId: response.razorpay_order_id,
                  method: verifyResponse.data?.paymentMethod || 'CREDIT_CARD'
                },
                appointment: verifyResponse.data,
                message: 'Payment processed successfully'
              });
            } else {
              throw new Error(verifyResponse.message || 'Payment verification failed');
            }
          } catch (verifyError) {
            console.error('Payment verification error:', verifyError);
            setErrors({ submit: verifyError.message || 'Payment verification failed. Please contact support.' });
            setIsLoading(false);
          }
        },
        prefill: {
          name: currentUser ? `${currentUser.firstName || ''} ${currentUser.lastName || ''}`.trim() : '',
          email: currentUser?.email || '',
          contact: currentUser?.phone || ''
        },
        theme: {
          color: '#059669' // green-600
        },
        modal: {
          ondismiss: function() {
            // User closed the payment modal
            setIsLoading(false);
            setErrors({ submit: 'Payment was cancelled' });
          }
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.on('payment.failed', function (response) {
        console.error('Payment failed:', response);
        setIsLoading(false);
        setErrors({ 
          submit: response.error?.description || 'Payment failed. Please try again.' 
        });
      });

      razorpay.open();
      // Note: Don't set isLoading(false) here as Razorpay modal is now open
      // Loading will be handled in the handler callback or on modal dismissal

    } catch (error) {
      console.error('Payment error:', error);
      setErrors({ submit: error.message || 'Failed to initiate payment. Please try again.' });
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <DollarSign className="h-8 w-8 text-green-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Payment Summary</h3>
        </div>
        <p className="text-sm text-gray-600">
          Complete your payment to finalize your diet plan and appointment booking
        </p>
      </div>

      {/* Order Summary */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h4 className="text-lg font-medium text-gray-900 mb-4">Order Summary</h4>
        
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Diet Plan</span>
            <span className="text-gray-900">{formatCurrency(pricing.planPrice)}</span>
          </div>
          
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">
              Consultation ({appointment?.duration || 15} minutes)
            </span>
            <span className="text-gray-900">{formatCurrency(pricing.consultationFee)}</span>
          </div>
          
          <div className="border-t border-gray-200 pt-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Subtotal</span>
              <span className="text-gray-900">{formatCurrency(pricing.subtotal)}</span>
            </div>
            
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Tax</span>
              <span className="text-gray-900">{formatCurrency(pricing.tax)}</span>
            </div>
          </div>
          
          <div className="border-t border-gray-200 pt-3">
            <div className="flex justify-between text-lg font-semibold">
              <span className="text-gray-900">Total</span>
              <span className="text-gray-900">{formatCurrency(pricing.total)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Appointment Details */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-800 mb-2 flex items-center">
          <Calendar className="h-4 w-4 mr-2" />
          Appointment Details
        </h4>
        <div className="text-sm text-blue-700 space-y-1">
          <p><strong>Date:</strong> {new Date(appointment?.startAt).toLocaleDateString()}</p>
          <p><strong>Time:</strong> {new Date(appointment?.startAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
          <p><strong>Duration:</strong> {appointment?.duration} minutes</p>
          <p><strong>Provider:</strong> {appointment?.provider?.name}</p>
        </div>
      </div>

      {/* Payment Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <Shield className="h-5 w-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Secure Payment via Razorpay</p>
            <p className="text-xs">
              You will be redirected to Razorpay's secure payment gateway. 
              All major payment methods are accepted including Credit/Debit Cards, UPI, Net Banking, and Wallets.
            </p>
          </div>
        </div>
      </div>

      {/* Testing Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="h-5 w-5 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-yellow-800">
            <p className="font-medium mb-1">Testing Mode</p>
            <p className="text-xs">
              For testing purposes, you can skip the payment step using the "Skip (Testing)" button below. 
              This will use dummy payment data to complete the flow.
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handlePayment} className="space-y-6">

        {/* Submit Error */}
        {errors.submit && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-red-700">{errors.submit}</p>
          </div>
        )}

        {/* Submit Buttons */}
        <div className="flex justify-between items-center">
          {/* Skip Button (for testing) */}
          <button
            type="button"
            onClick={handleSkipPayment}
            disabled={isLoading}
            className="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center text-sm font-medium"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            Skip (Testing)
          </button>
          
          {/* Pay Button */}
          <button
            type="submit"
            disabled={isLoading || !razorpayLoaded}
            className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center text-lg font-medium"
          >
            {isLoading && <Loader className="h-5 w-5 mr-2 animate-spin" />}
            Pay {formatCurrency(pricing.total)}
          </button>
        </div>
      </form>

      {/* Security Notice */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-start">
          <Shield className="h-5 w-5 text-gray-600 mr-2 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-gray-600">
            <p className="font-medium mb-1">Secure Payment</p>
            <p>Your payment information is encrypted and secure. We never store your card details.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentSummary;