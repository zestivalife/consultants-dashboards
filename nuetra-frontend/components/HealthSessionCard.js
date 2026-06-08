import React from 'react';
import { motion } from 'framer-motion';
import { Clock, Users, Activity, ArrowRight } from 'lucide-react';
import { trackEvent } from '../utils/analytics';

/**
 * HealthSessionCard Component
 * Displays health session information with interactive animations
 */
const HealthSessionCard = ({ session, index }) => {
  const handleClick = () => {
    trackEvent('session_card_click', { 
      session: session.title,
      index 
    });
  };

  const handleLearnMore = (e) => {
    e.stopPropagation();
    trackEvent('session_learn_more', { 
      session: session.title 
    });
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
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      variants={cardVariants}
      whileHover={{ y: -8, transition: { duration: 0.3 } }}
      onClick={handleClick}
      className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all group cursor-pointer"
      role="article"
      aria-label={`${session.title}: ${session.description}`}
    >
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-xl font-semibold group-hover:text-[#64ae00] transition-colors flex-1">
          {session.title}
        </h3>
        <motion.div
          whileHover={{ rotate: 360 }}
          transition={{ duration: 0.6 }}
          className="p-2 bg-[#64ae00] rounded-lg group-hover:bg-[#579700] transition-colors flex-shrink-0"
        >
          <Activity className="h-6 w-6 text-white" />
        </motion.div>
      </div>
      <p className="text-gray-600 mb-4">{session.description}</p>
      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
        <div className="flex items-center">
          <Clock className="h-4 w-4 mr-2" />
          {session.duration}
        </div>
        <div className="flex items-center">
          <Users className="h-4 w-4 mr-2" />
          {session.participants}
        </div>
      </div>
      <motion.button
        onClick={handleLearnMore}
        whileHover={{ x: 4 }}
        whileTap={{ scale: 0.95 }}
        className="mt-4 w-full py-2 border border-[#64ae00] text-[#64ae00] rounded-lg bg-[#64ae00]/15 hover:bg-[#64ae00]/25 transition-colors font-medium flex items-center justify-center group/button focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:ring-offset-2"
        aria-label={`Learn more about ${session.title}`}
      >
        Learn More
        <motion.span
          initial={{ x: 0 }}
          className="ml-2 inline-block"
        >
          <ArrowRight className="h-4 w-4 group-hover/button:translate-x-1 transition-transform" />
        </motion.span>
      </motion.button>
    </motion.div>
  );
};

export default HealthSessionCard;

