import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle } from 'lucide-react';
import { trackEvent } from '../utils/analytics';

/**
 * FeatureCard Component
 * Interactive feature card with hover effects and progressive disclosure
 */
const FeatureCard = ({ feature, index, isActive, onClick }) => {
  const [ripples, setRipples] = useState([]);
  const cardRef = useRef(null);

  const handleClick = (e) => {
    // Create ripple effect
    const card = cardRef.current;
    if (card) {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const newRipple = {
        x,
        y,
        id: Date.now()
      };
      
      setRipples(prev => [...prev, newRipple]);
      
      // Remove ripple after animation
      setTimeout(() => {
        setRipples(prev => prev.filter(r => r.id !== newRipple.id));
      }, 600);
    }

    // Track analytics
    trackEvent('feature_card_click', { 
      feature: feature.title,
      index 
    });

    if (!isActive) {
      trackEvent('feature_details_expand', { feature: feature.title });
    }

    onClick();
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.6,
        delay: index * 0.1 
      }
    }
  };

  return (
    <motion.div
      ref={cardRef}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      variants={cardVariants}
      whileHover={{ y: -4 }}
      className={`relative overflow-hidden p-6 rounded-xl border-2 transition-all cursor-pointer ${
        isActive
          ? "border-[#64ae00] bg-[#64ae00]/15 shadow-lg"
          : "border-gray-100 hover:border-[#64ae00] hover:bg-gray-50"
      }`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-expanded={isActive}
      aria-label={`${feature.title}: ${feature.description}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick(e);
        }
      }}
    >
      {/* Ripple effects */}
      {ripples.map((ripple) => (
        <span
          key={ripple.id}
          className="absolute bg-[#64ae00]/30 rounded-full pointer-events-none"
          style={{
            left: ripple.x,
            top: ripple.y,
            width: 10,
            height: 10,
            marginLeft: -5,
            marginTop: -5,
            animation: 'ripple 0.6s ease-out'
          }}
        />
      ))}

      <div className="flex items-start space-x-4">
        <motion.div
          whileHover={{ rotate: 5, scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          transition={{ type: 'spring', stiffness: 300 }}
          className={`p-3 rounded-lg transition-all ${
            isActive
              ? "bg-[#64ae00] text-white"
              : "bg-gray-100 text-gray-600"
          }`}
        >
          {feature.icon}
        </motion.div>
        <div className="flex-1">
          <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
          <p className="text-gray-600 mb-3">{feature.description}</p>
          <AnimatePresence>
            {isActive && (
              <motion.ul
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="space-y-2"
              >
                {feature.details.map((detail, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-center text-sm text-green-700"
                  >
                    <CheckCircle className="h-4 w-4 mr-2 flex-shrink-0" />
                    {detail}
                  </motion.li>
                ))}
              </motion.ul>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};

export default FeatureCard;

