import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { trackEvent } from '../utils/analytics';

/**
 * TestimonialCarousel Component
 * Interactive carousel with auto-play, keyboard navigation, and swipe support
 */
const TestimonialCarousel = ({ testimonials }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [progress, setProgress] = useState(0);
  const [touchStart, setTouchStart] = useState(0);
  const [touchEnd, setTouchEnd] = useState(0);
  const carouselRef = useRef(null);
  const progressIntervalRef = useRef(null);

  const autoPlayDuration = 5000; // 5 seconds

  useEffect(() => {
    if (!isPaused) {
      // Start progress animation
      const startTime = Date.now();
      
      progressIntervalRef.current = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const newProgress = (elapsed / autoPlayDuration) * 100;
        
        if (newProgress >= 100) {
          handleNext('auto');
        } else {
          setProgress(newProgress);
        }
      }, 50);

      return () => {
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      };
    } else {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    }
  }, [currentIndex, isPaused]);

  const handleNext = (source = 'manual') => {
    setCurrentIndex((prev) => (prev + 1) % testimonials.length);
    setProgress(0);
    
    if (source === 'manual') {
      trackEvent('testimonial_navigate', { 
        direction: 'next',
        testimonial: testimonials[currentIndex].author 
      });
    } else {
      trackEvent('testimonial_auto_advance', { 
        testimonial: testimonials[currentIndex].author 
      });
    }
  };

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
    setProgress(0);
    trackEvent('testimonial_navigate', { 
      direction: 'prev',
      testimonial: testimonials[currentIndex].author 
    });
  };

  const handleDotClick = (index) => {
    setCurrentIndex(index);
    setProgress(0);
    trackEvent('testimonial_navigate', { 
      direction: 'dot',
      testimonial: testimonials[index].author 
    });
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        handlePrev();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        handleNext('manual');
      }
    };

    if (carouselRef.current) {
      carouselRef.current.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      if (carouselRef.current) {
        carouselRef.current.removeEventListener('keydown', handleKeyDown);
      }
    };
  }, [currentIndex]);

  // Touch/swipe support
  const handleTouchStart = (e) => {
    setTouchStart(e.touches[0].clientX);
  };

  const handleTouchMove = (e) => {
    setTouchEnd(e.touches[0].clientX);
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > 50;
    const isRightSwipe = distance < -50;

    if (isLeftSwipe) {
      handleNext('manual');
    } else if (isRightSwipe) {
      handlePrev();
    }

    setTouchStart(0);
    setTouchEnd(0);
  };

  useEffect(() => {
    // Track section view
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            trackEvent('testimonial_section_view', {});
          }
        });
      },
      { threshold: 0.3 }
    );

    if (carouselRef.current) {
      observer.observe(carouselRef.current);
    }

    return () => {
      if (carouselRef.current) {
        observer.unobserve(carouselRef.current);
      }
    };
  }, []);

  const slideVariants = {
    enter: (direction) => ({
      x: direction > 0 ? 20 : -20,
      opacity: 0
    }),
    center: {
      x: 0,
      opacity: 1
    },
    exit: (direction) => ({
      x: direction < 0 ? 20 : -20,
      opacity: 0
    })
  };

  return (
    <div
      ref={carouselRef}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      className="relative bg-white rounded-2xl shadow-xl p-8 md:p-12"
      tabIndex={0}
      role="region"
      aria-label="Customer testimonials carousel"
      aria-live="polite"
    >
      {/* Progress Bar */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gray-200 rounded-t-2xl overflow-hidden">
        <motion.div
          className="h-full bg-[#64ae00]"
          style={{ width: `${progress}%` }}
          initial={{ width: 0 }}
        />
      </div>

      <AnimatePresence mode="wait" custom={1}>
        <motion.div
          key={currentIndex}
          custom={1}
          variants={slideVariants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <motion.img
            src={testimonials[currentIndex].image}
            alt={testimonials[currentIndex].author}
            className="w-20 h-20 rounded-full mx-auto mb-6 border-4 border-green-100"
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5 }}
          />
          <blockquote className="text-2xl text-gray-700 italic mb-6 leading-relaxed">
            "{testimonials[currentIndex].quote}"
          </blockquote>
          <div className="text-gray-900 font-semibold text-lg">
            {testimonials[currentIndex].author}
          </div>
          <div className="text-[#64ae00] font-medium">
            {testimonials[currentIndex].position}
          </div>
          <div className="text-gray-500 text-sm mt-1">
            {testimonials[currentIndex].company}
          </div>
        </motion.div>
      </AnimatePresence>

      <div className="flex justify-between items-center mt-8">
        <button
          onClick={handlePrev}
          className="p-2 rounded-full border border-gray-300 hover:border-[#64ae00] hover:bg-green-50 transition-all focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:ring-offset-2"
          aria-label="Previous testimonial"
        >
          <ChevronLeft className="h-6 w-6 text-gray-600 hover:text-[#64ae00]" />
        </button>

        <div className="flex space-x-2" role="tablist" aria-label="Testimonial indicators">
          {testimonials.map((_, index) => (
            <button
              key={index}
              onClick={() => handleDotClick(index)}
              className={`w-3 h-3 rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:ring-offset-2 ${
                index === currentIndex
                  ? "bg-[#64ae00] scale-125"
                  : "bg-gray-300 hover:bg-gray-400"
              }`}
              aria-label={`Go to testimonial ${index + 1}`}
              role="tab"
              aria-selected={index === currentIndex}
            />
          ))}
        </div>

        <button
          onClick={() => handleNext('manual')}
          className="p-2 rounded-full border border-gray-300 hover:border-[#64ae00] hover:bg-green-50 transition-all focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:ring-offset-2"
          aria-label="Next testimonial"
        >
          <ChevronRight className="h-6 w-6 text-gray-600 hover:text-[#64ae00]" />
        </button>
      </div>

      {/* Pause indicator */}
      {isPaused && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute top-4 right-4 text-xs text-gray-500 bg-white/80 px-2 py-1 rounded"
        >
          Paused
        </motion.div>
      )}
    </div>
  );
};

export default TestimonialCarousel;

