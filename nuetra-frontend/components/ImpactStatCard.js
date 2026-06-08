import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { trackEvent } from '../utils/analytics';

/**
 * ImpactStatCard Component
 * Displays a statistic with animated counter and icon
 */
const ImpactStatCard = ({ number, label, icon, index = 0 }) => {
  const [count, setCount] = useState(0);
  const [hasAnimated, setHasAnimated] = useState(false);
  const cardRef = useRef(null);

  // Extract numeric value from the number prop (e.g., "30%" -> 30)
  const targetValue = parseInt(number.replace(/[^0-9]/g, ''), 10) || 0;
  const suffix = number.replace(/[0-9]/g, '');

  useEffect(() => {
    if (!cardRef.current) return;
    
    let hasTracked = false; // Local flag to prevent multiple tracking calls

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasTracked) {
            hasTracked = true;
            setHasAnimated(true);
            animateCounter();
            trackEvent('impact_stat_view', { stat: label });
          }
        });
      },
      { threshold: 0.5 }
    );

    const currentRef = cardRef.current;
    observer.observe(currentRef);

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, []); // Empty dependency array - only run once on mount

  const animateCounter = () => {
    const duration = 1500; // 1.5 seconds
    const steps = 60;
    const increment = targetValue / steps;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      const newValue = Math.min(Math.round(increment * currentStep), targetValue);
      setCount(newValue);

      if (currentStep >= steps) {
        clearInterval(timer);
        setCount(targetValue);
      }
    }, duration / steps);

    return () => clearInterval(timer);
  };

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay: index * 0.1 }}
      whileHover={{ scale: 1.05 }}
      className="text-center p-8 rounded-2xl bg-[#64ae00]/15 hover:bg-[#64ae00]/25 transition-all duration-300 text-gray-900 hover-glow cursor-default"
      role="article"
      aria-label={`${number} ${label}`}
    >
      <div className="flex justify-center mb-4">
        <motion.div
          initial={{ scale: 0.3, opacity: 0 }}
          whileInView={{ scale: 1, opacity: 1 }}
          viewport={{ once: true }}
          transition={{
            duration: 0.6,
            delay: index * 0.1 + 0.2,
            type: 'spring',
            stiffness: 200,
            damping: 10
          }}
          className="p-4 bg-[#64ae00] rounded-full text-white"
        >
          {icon}
        </motion.div>
      </div>
      <div className="text-4xl font-bold text-gray-900 mb-2" aria-live="polite">
        {hasAnimated ? count : 0}{suffix}
      </div>
      <div className="text-gray-600 font-medium">{label}</div>
    </motion.div>
  );
};

export default ImpactStatCard;

