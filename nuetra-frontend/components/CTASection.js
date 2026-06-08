import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { Phone, Mail } from 'lucide-react';
import { trackEvent, trackSectionView } from '../utils/analytics';

/**
 * CTASection Component
 * Conversion-focused Call-to-Action section with animations
 */
const CTASection = () => {
  const [companyCount, setCompanyCount] = useState(0);
  const [hasAnimated, setHasAnimated] = useState(false);
  const sectionRef = useRef(null);

  useEffect(() => {
    if (!sectionRef.current) return;

    trackSectionView('cta_section', sectionRef.current, () => {
      if (!hasAnimated) {
        setHasAnimated(true);
        animateCounter();
      }
    });
  }, [hasAnimated]);

  const animateCounter = () => {
    const target = 500;
    const duration = 2000; // 2 seconds
    const steps = 50;
    const increment = target / steps;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      const newValue = Math.min(Math.round(increment * currentStep), target);
      setCompanyCount(newValue);

      if (currentStep >= steps) {
        clearInterval(timer);
        setCompanyCount(target);
      }
    }, duration / steps);

    return () => clearInterval(timer);
  };

  const handleDemoClick = () => {
    trackEvent('cta_demo_click', { location: 'cta_section' });
  };

  const handleBrochureClick = () => {
    trackEvent('cta_brochure_click', { location: 'cta_section' });
  };

  const textVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
  };

  return (
    <section
      ref={sectionRef}
      className="py-24 bg-[#64ae00] hover:bg-[#579700] text-white relative overflow-hidden transition-colors duration-500 animate-gradient-shift"
      style={{
        background: 'linear-gradient(135deg, #64ae00 0%, #579700 50%, #64ae00 100%)',
        backgroundSize: '200% 200%'
      }}
    >
      {/* Background overlay */}
      <div className="absolute inset-0 bg-black/10"></div>

      {/* Animated background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-10 left-10 w-32 h-32 bg-white rounded-full blur-3xl animate-float"></div>
        <div className="absolute bottom-10 right-10 w-40 h-40 bg-white rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/3 w-24 h-24 bg-white rounded-full blur-3xl animate-float" style={{ animationDelay: '0.5s' }}></div>
      </div>

      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.5 }}
        variants={textVariants}
        className="max-w-4xl mx-auto px-6 text-center relative z-10"
      >
        <motion.h2
          variants={textVariants}
          className="text-4xl md:text-5xl font-bold mb-6"
        >
          Ready to Transform Your Workplace Wellness?
        </motion.h2>
        
        <motion.p
          variants={textVariants}
          className="text-xl mb-2 opacity-90 leading-relaxed"
        >
          Join <span className="font-bold text-2xl" aria-live="polite">{hasAnimated ? companyCount : 500}+</span> Indian companies using Nuetra to build healthier, more productive teams.
        </motion.p>
        
        <motion.p
          variants={textVariants}
          className="text-lg mb-8 opacity-80"
        >
          Get started with a free consultation today.
        </motion.p>

        <motion.div
          variants={textVariants}
          className="flex flex-col sm:flex-row gap-4 justify-center mb-8"
        >
          <Link href="/register" passHref>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleDemoClick}
              className="px-8 py-4 bg-white text-[#64ae00] rounded-full font-bold text-lg shadow-xl hover:bg-gray-100 transition-all hover-glow min-w-[200px] focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-[#64ae00]"
              aria-label="Schedule a free demo"
            >
              Schedule Free Demo
            </motion.button>
          </Link>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleBrochureClick}
            className="px-8 py-4 border-2 border-white rounded-full text-white font-bold text-lg hover:bg-white/10 transition-all min-w-[200px] focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-[#64ae00]"
            aria-label="Download company brochure"
          >
            Download Brochure
          </motion.button>
        </motion.div>

        <motion.div
          variants={textVariants}
          className="flex flex-col sm:flex-row justify-center items-center gap-4 sm:gap-8 text-sm opacity-75"
        >
          <a
            href="tel:+91-XXXX-XXXX"
            className="flex items-center hover:opacity-100 transition-opacity focus:outline-none focus:ring-2 focus:ring-white rounded px-2 py-1"
            aria-label="Call us"
          >
            <Phone className="h-4 w-4 mr-2" />
            +91-XXXX-XXXX
          </a>
          <a
            href="mailto:hello@nuetra.in"
            className="flex items-center hover:opacity-100 transition-opacity focus:outline-none focus:ring-2 focus:ring-white rounded px-2 py-1"
            aria-label="Email us"
          >
            <Mail className="h-4 w-4 mr-2" />
            hello@nuetra.in
          </a>
        </motion.div>

        {/* Trust indicators */}
        <motion.div
          variants={textVariants}
          className="mt-8 text-sm opacity-75"
        >
          <p>✓ No credit card required &nbsp;•&nbsp; ✓ Cancel anytime &nbsp;•&nbsp; ✓ 30-day money-back guarantee</p>
        </motion.div>
      </motion.div>
    </section>
  );
};

export default CTASection;

