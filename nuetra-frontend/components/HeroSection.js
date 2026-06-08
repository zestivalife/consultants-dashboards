import React, { useState } from 'react';
import { motion } from 'framer-motion';
import Image from 'next/image';
import Link from 'next/link';
import { Play, ArrowRight, ChevronDown } from 'lucide-react';
import { trackEvent } from '../utils/analytics';

/**
 * HeroSection Component
 * Enhanced hero with animations, CTAs, and scroll indicator
 */
const HeroSection = ({ onVideoClick }) => {
  const handleCTAClick = (ctaName) => {
    trackEvent('hero_cta_click', { cta: ctaName });
  };

  const handleScroll = () => {
    trackEvent('hero_scroll', { action: 'click_indicator' });
    const featuresSection = document.getElementById('features');
    if (featuresSection) {
      featuresSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const textVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
  };

  const staggerContainer = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: 0.15
      }
    }
  };

  return (
    <section className="min-h-screen pt-32 pb-16 flex items-center justify-center text-center relative overflow-hidden">
      {/* Animated background */}
      <div 
        className="absolute inset-0 animate-gradient-shift"
        style={{
          background: 'linear-gradient(135deg, #ffffff 0%, rgba(100, 174, 0, 0.05) 25%, rgba(59, 130, 246, 0.05) 50%, rgba(100, 174, 0, 0.05) 75%, #ffffff 100%)',
          backgroundSize: '400% 400%'
        }}
      ></div>

      {/* Floating background shapes */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-[#64ae00]/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }}></div>
      </div>

      <motion.div
        initial="hidden"
        animate="visible"
        variants={staggerContainer}
        className="flex flex-col items-center max-w-6xl mx-auto px-4 relative z-10"
      >
        {/* Trust Badge */}
        <motion.div
          variants={textVariants}
          className="mb-6 px-4 py-2 bg-[#64ae00]/5 text-green-800 rounded-full font-medium inline-flex items-center"
          role="status"
          aria-label="Trusted by over 500 Indian companies"
        >
          🏢 Trusted by 500+ Indian Companies
        </motion.div>

        {/* Headline */}
        <motion.h1
          className="text-4xl sm:text-5xl lg:text-7xl font-extrabold text-gray-900 leading-tight mb-6"
          variants={textVariants}
        >
          Transform Your Corporate Culture with <br />
          <span className="text-[#64ae00] hover:text-[#4f9600] transition-colors">
            Expert Wellness Solutions
          </span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          className="text-xl sm:text-2xl text-gray-600 max-w-3xl mx-auto mb-8 leading-relaxed"
          variants={textVariants}
        >
          Boost productivity by 25%, reduce healthcare costs by 30%, and enhance employee satisfaction with personalized nutrition and wellness programs.
        </motion.p>

        {/* CTAs */}
        <motion.div
          variants={textVariants}
          className="flex flex-col sm:flex-row gap-4 mb-12"
        >
          <Link href="/register" passHref>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleCTAClick('request_demo')}
              className="px-8 py-4 bg-[#64ae00] rounded-full text-white font-bold text-lg shadow-xl hover:bg-[#579700] transition-all animate-pulse-glow hover-glow min-w-[220px] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#64ae00]"
              aria-label="Request a demo of Nuetra platform"
            >
              Request a Demo
              <ArrowRight className="inline ml-2 h-5 w-5" />
            </motion.button>
          </Link>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              handleCTAClick('watch_demo');
              onVideoClick();
            }}
            className="px-8 py-4 border-2 border-[#64ae00] rounded-full text-[#64ae00] font-bold text-lg hover:bg-[#f3fbde] transition-all flex items-center justify-center min-w-[220px] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#64ae00]"
            aria-label="Watch platform demo video"
          >
            <Play className="mr-2 h-5 w-5" />
            Watch Platform Demo
          </motion.button>
        </motion.div>

        {/* Hero Image */}
        <motion.div
          variants={textVariants}
          className="w-full max-w-4xl mx-auto relative"
        >
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ 
              duration: 3, 
              repeat: Infinity, 
              ease: "easeInOut" 
            }}
          >
            <img
              src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=1200&h=600&fit=crop"
              alt="Indian corporate team in modern office discussing wellness"
              className="rounded-2xl shadow-2xl w-full"
              loading="eager"
            />
          </motion.div>
          
          {/* Trust Badges / Company Logos Placeholder */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.6 }}
            className="mt-8 flex flex-wrap justify-center items-center gap-6 opacity-50"
          >
            <div className="text-sm text-gray-500 font-medium">Trusted by leading companies:</div>
            <div className="flex gap-6 flex-wrap justify-center">
              {['TCS', 'Infosys', 'Wipro', 'HCL', 'Tech Mahindra'].map((company, idx) => (
                <div 
                  key={idx}
                  className="px-4 py-2 bg-white rounded-lg shadow-sm text-gray-600 font-semibold"
                >
                  {company}
                </div>
              ))}
            </div>
          </motion.div>
        </motion.div>

        {/* Scroll Indicator */}
        <motion.button
          onClick={handleScroll}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, y: [0, 10, 0] }}
          transition={{
            opacity: { delay: 1, duration: 0.5 },
            y: { 
              duration: 1.5, 
              repeat: Infinity, 
              ease: "easeInOut" 
            }
          }}
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2 text-[#64ae00] hover:text-[#579700] transition-colors focus:outline-none focus:ring-2 focus:ring-[#64ae00] rounded-full p-2"
          aria-label="Scroll down to features"
        >
          <ChevronDown className="h-8 w-8" />
        </motion.button>
      </motion.div>
    </section>
  );
};

export default HeroSection;

