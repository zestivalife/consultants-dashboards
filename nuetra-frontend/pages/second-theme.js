import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle, TrendingUp, Heart, Users, Calendar, BarChart3, Play,
  ChevronLeft, ChevronRight, Target, Shield, Clock, ArrowRight, Phone, Mail,
  MapPin, Activity, Zap, Award, Globe, Briefcase
} from "lucide-react";

const textVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: "easeOut" } },
};

const slideIn = {
  hidden: { opacity: 0, x: -50 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.6, ease: "easeOut" } },
};

const staggerContainer = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.2,
    },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 40, scale: 0.95 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.7 } },
  hover: { y: -8, scale: 1.02, transition: { duration: 0.3 } }
};

const testimonials = [
  {
    quote: "Nuetra revolutionized our workplace culture. Employee engagement soared 45% within 6 months, and healthcare costs dropped significantly.",
    author: "Rajesh Mehta",
    position: "Chief People Officer",
    company: "TechForward Solutions • 800+ employees",
    image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&h=120&fit=crop&crop=face",
    metrics: { engagement: "+45%", costs: "-32%" }
  },
  {
    quote: "The comprehensive wellness analytics gave us unprecedented insights. Our productivity metrics improved dramatically across all departments.",
    author: "Priya Sharma",
    position: "VP Human Resources",
    company: "InnovateCorp • 1200+ employees",
    image: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=120&h=120&fit=crop&crop=face",
    metrics: { productivity: "+38%", satisfaction: "+52%" }
  },
  {
    quote: "Implementing Nuetra was transformative. Our team's energy levels, focus, and collaboration reached new heights we never thought possible.",
    author: "Arjun Patel",
    position: "CEO & Founder",
    company: "GrowthLabs India • 600+ employees",
    image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=120&h=120&fit=crop&crop=face",
    metrics: { retention: "+28%", absenteeism: "-65%" }
  }
];

const features = [
  {
    icon: <Users className="h-7 w-7" />,
    title: "Expert Wellness Architects",
    description: "Certified nutritionists and wellness professionals specialized in corporate transformation",
    details: ["Industry-certified professionals", "Corporate psychology expertise", "Personalized intervention strategies"],
    color: "from-emerald-500 to-teal-600"
  },
  {
    icon: <BarChart3 className="h-7 w-7" />,
    title: "Advanced Analytics Suite",
    description: "Real-time insights and predictive analytics for measurable wellness ROI",
    details: ["Comprehensive health dashboards", "Predictive wellness modeling", "ROI tracking & reporting"],
    color: "from-amber-500 to-orange-600"
  },
  {
    icon: <Target className="h-7 w-7" />,
    title: "Strategic Wellness Planning",
    description: "Customized wellness roadmaps aligned with your organizational objectives",
    details: ["Industry-specific wellness strategies", "Goal-oriented program design", "Scalable implementation frameworks"],
    color: "from-emerald-600 to-green-700"
  },
  {
    icon: <Zap className="h-7 w-7" />,
    title: "Flexible Program Delivery",
    description: "Adaptive scheduling and multi-modal delivery to fit your team's workflow",
    details: ["Hybrid delivery models", "Flexible scheduling options", "Multi-language support"],
    color: "from-teal-500 to-cyan-600"
  }
];

const wellnessPrograms = [
  {
    title: "Executive Wellness Strategy",
    description: "Strategic nutrition and stress management for leadership teams",
    duration: "90 mins",
    participants: "5-15 leaders",
    icon: <Briefcase className="h-6 w-6" />,
    color: "bg-gradient-to-r from-emerald-500 to-teal-600"
  },
  {
    title: "Team Performance Optimization",
    description: "Comprehensive wellness programs designed for high-performance teams",
    duration: "60 mins",
    participants: "15-40 employees",
    icon: <TrendingUp className="h-6 w-6" />,
    color: "bg-gradient-to-r from-amber-500 to-orange-500"
  },
  {
    title: "Chronic Condition Management",
    description: "Specialized support for diabetes, hypertension, and metabolic conditions",
    duration: "75 mins",
    participants: "8-25 employees",
    icon: <Heart className="h-6 w-6" />,
    color: "bg-gradient-to-r from-teal-500 to-cyan-600"
  },
  {
    title: "Workplace Energy & Focus",
    description: "Nutrition strategies for sustained energy and cognitive performance",
    duration: "45 mins",
    participants: "20-60 employees",
    icon: <Activity className="h-6 w-6" />,
    color: "bg-gradient-to-r from-emerald-600 to-green-700"
  }
];

const impactMetrics = [
  { number: "32%", label: "Healthcare Cost Reduction", icon: <Shield className="h-6 w-6" />, color: "text-emerald-600" },
  { number: "52%", label: "Employee Satisfaction Increase", icon: <Heart className="h-6 w-6" />, color: "text-amber-600" },
  { number: "38%", label: "Productivity Enhancement", icon: <TrendingUp className="h-6 w-6" />, color: "text-teal-600" },
  { number: "65%", label: "Absenteeism Decrease", icon: <Clock className="h-6 w-6" />, color: "text-green-700" }
];

export default function WellnessHorizonNuetra() {
  const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const [activeFeature, setActiveFeature] = useState(0);
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  const nextTestimonial = () => setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
  const prevTestimonial = () => setCurrentTestimonial((prev) => (prev - 1 + testimonials.length) % testimonials.length);

  return (
    <div className="min-h-screen bg-stone-50 text-slate-900 overflow-hidden relative">
      {/* Header with refined typography and spacing */}
      <header className="fixed top-0 left-0 w-full px-8 py-6 flex justify-between items-center z-50 bg-white/95 backdrop-blur-md shadow-sm border-b border-stone-100">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-gradient-to-r from-emerald-600 to-teal-700 rounded-lg flex items-center justify-center shadow-lg">
            <span className="text-white font-bold text-xl tracking-tight">N</span>
          </div>
          <span className="text-2xl font-bold tracking-tight bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
            Nuetra
          </span>
        </div>
        
        <nav className="hidden lg:flex space-x-10">
          <a href="#solutions" className="text-slate-600 hover:text-emerald-600 transition-colors font-medium tracking-wide">Solutions</a>
          <a href="#impact" className="text-slate-600 hover:text-emerald-600 transition-colors font-medium tracking-wide">Impact</a>
          <a href="#success-stories" className="text-slate-600 hover:text-emerald-600 transition-colors font-medium tracking-wide">Success Stories</a>
          <a href="#insights" className="text-slate-600 hover:text-emerald-600 transition-colors font-medium tracking-wide">Insights</a>
        </nav>
        
        <div className="flex items-center space-x-4">
          <motion.button
            whileHover={{ scale: 1.05 }}
            className="text-slate-600 hover:text-emerald-600 transition-colors font-medium tracking-wide"
          >
            Partner With Us
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05, boxShadow: "0 8px 25px rgba(5, 150, 105, 0.3)" }}
            className="px-7 py-3 rounded-lg text-white bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-700 hover:to-teal-800 transition-all font-semibold shadow-lg tracking-wide"
          >
            Get Started
          </motion.button>
        </div>
      </header>

      {/* Hero Section with enhanced visual hierarchy */}
      <section className="min-h-screen pt-40 pb-24 flex items-center justify-center bg-gradient-to-br from-white via-emerald-50/30 to-stone-100/50 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-20 right-20 w-96 h-96 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 left-20 w-96 h-96 bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-full blur-3xl"></div>
        </div>
        
        <motion.div
          initial="hidden"
          animate="visible"
          variants={staggerContainer}
          className="flex flex-col items-center max-w-7xl mx-auto px-8 relative z-10"
        >
          <motion.div
            variants={textVariants}
            className="mb-8 px-6 py-3 bg-gradient-to-r from-emerald-100 to-teal-100 text-emerald-800 rounded-full font-semibold border border-emerald-200/50 shadow-sm"
          >
            🏢 Trusted by 500+ Enterprise Organizations Across India
          </motion.div>

          <motion.h1
            className="text-5xl sm:text-6xl lg:text-7xl font-bold text-slate-900 leading-tight mb-8 text-center tracking-tight"
            variants={textVariants}
          >
            Transform Your Corporate Culture with <br />
            <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-700 bg-clip-text text-transparent">
              Strategic Wellness Solutions
            </span>
          </motion.h1>

          <motion.p
            className="text-xl sm:text-2xl text-slate-600 max-w-4xl mx-auto mb-12 leading-relaxed text-center font-light"
            variants={textVariants}
          >
            Drive measurable results with evidence-based wellness programs. Increase productivity by 38%, reduce healthcare costs by 32%, and build a thriving organizational culture.
          </motion.p>

          <motion.div
            variants={textVariants}
            className="flex flex-col sm:flex-row gap-6 mb-16"
          >
            <motion.button
              whileHover={{ scale: 1.05, boxShadow: "0 12px 35px rgba(5, 150, 105, 0.4)" }}
              className="px-10 py-5 bg-gradient-to-r from-emerald-600 to-teal-700 rounded-lg text-white font-bold text-lg shadow-xl hover:from-emerald-700 hover:to-teal-800 transition-all transform"
            >
              Schedule Strategic Consultation
              <ArrowRight className="inline ml-3 h-5 w-5" />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              onClick={() => setIsVideoModalOpen(true)}
              className="px-10 py-5 border-2 border-emerald-600 rounded-lg text-emerald-700 font-bold text-lg hover:bg-emerald-50 transition-all transform flex items-center justify-center"
            >
              <Play className="mr-3 h-5 w-5" />
              Watch Success Stories
            </motion.button>
          </motion.div>

          {/* Enhanced Hero Visual */}
          <motion.div
            variants={textVariants}
            className="w-full max-w-5xl mx-auto relative"
          >
            <div className="absolute inset-0 bg-gradient-to-t from-emerald-500/20 to-transparent rounded-2xl"></div>
            <img
              src="https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=1400&h=700&fit=crop"
              alt="Modern Indian corporate team collaborating in wellness-focused office environment"
              className="rounded-2xl shadow-2xl w-full border border-stone-200/50"
            />
            <div className="absolute -bottom-6 -right-6 bg-white p-6 rounded-xl shadow-xl border border-stone-200/50">
              <div className="text-2xl font-bold text-emerald-600">500+</div>
              <div className="text-sm text-slate-600 font-medium">Companies Transformed</div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Solutions Section with improved visual design */}
      <section id="solutions" className="py-32 bg-white">
        <div className="max-w-7xl mx-auto px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={textVariants}
            className="text-center mb-20"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-slate-900 mb-6 tracking-tight">
              Comprehensive Wellness Solutions
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto font-light leading-relaxed">
              Our integrated approach combines expert guidance, advanced analytics, and strategic planning to deliver measurable wellness outcomes.
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  variants={cardVariants}
                  whileHover="hover"
                  className={`p-8 rounded-xl border-2 transition-all cursor-pointer ${
                    activeFeature === index
                      ? "border-emerald-500 bg-gradient-to-r from-emerald-50 to-teal-50 shadow-xl"
                      : "border-stone-200 hover:border-emerald-300 hover:bg-stone-50/50"
                  }`}
                  onClick={() => setActiveFeature(index)}
                >
                  <div className="flex items-start space-x-6">
                    <div className={`p-4 rounded-xl bg-gradient-to-r ${feature.color} text-white shadow-lg`}>
                      {feature.icon}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold mb-3 text-slate-900 tracking-tight">{feature.title}</h3>
                      <p className="text-slate-600 mb-4 leading-relaxed">{feature.description}</p>
                      <AnimatePresence>
                        {activeFeature === index && (
                          <motion.ul
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.3 }}
                            className="space-y-3"
                          >
                            {feature.details.map((detail, i) => (
                              <li key={i} className="flex items-center text-emerald-700 font-medium">
                                <CheckCircle className="h-5 w-5 mr-3 flex-shrink-0" />
                                {detail}
                              </li>
                            ))}
                          </motion.ul>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
            
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 rounded-2xl transform rotate-3"></div>
              <img
                src="https://images.unsplash.com/photo-1551434678-e076c223a692?w=700&h=600&fit=crop"
                alt="Professional team analyzing wellness metrics on modern dashboard"
                className="rounded-2xl shadow-2xl relative z-10 border border-stone-200/50"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Wellness Programs with refined card design */}
      <section className="py-32 bg-gradient-to-br from-stone-50 to-emerald-50/30">
        <div className="max-w-7xl mx-auto px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={textVariants}
            className="text-center mb-20"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-slate-900 mb-6 tracking-tight">
              Strategic Wellness Programs
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto font-light leading-relaxed">
              Tailored interventions designed to address specific organizational challenges and drive measurable wellness outcomes.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8">
            {wellnessPrograms.map((program, index) => (
              <motion.div
                key={index}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={cardVariants}
                whileHover="hover"
                className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-all group border border-stone-200/50"
              >
                <div className="flex items-start justify-between mb-6">
                  <h3 className="text-xl font-bold group-hover:text-emerald-600 transition-colors tracking-tight">
                    {program.title}
                  </h3>
                  <div className={`p-3 rounded-xl text-white shadow-lg ${program.color}`}>
                    {program.icon}
                  </div>
                </div>
                <p className="text-slate-600 mb-6 leading-relaxed">{program.description}</p>
                <div className="flex items-center justify-between text-sm text-slate-500 mb-6">
                  <div className="flex items-center bg-stone-100 px-3 py-2 rounded-lg">
                    <Clock className="h-4 w-4 mr-2" />
                    {program.duration}
                  </div>
                  <div className="flex items-center bg-stone-100 px-3 py-2 rounded-lg">
                    <Users className="h-4 w-4 mr-2" />
                    {program.participants}
                  </div>
                </div>
                <button className="w-full py-3 border-2 border-emerald-500 text-emerald-600 rounded-lg hover:bg-emerald-50 transition-colors font-semibold">
                  Learn More
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Impact Metrics with enhanced visual treatment */}
      <section id="impact" className="py-32 bg-white">
        <div className="max-w-7xl mx-auto px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={textVariants}
            className="text-center mb-20"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-slate-900 mb-6 tracking-tight">
              Proven Impact Across Organizations
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto font-light leading-relaxed">
              Data-driven results that demonstrate the transformative power of strategic wellness investments.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {impactMetrics.map((stat, index) => (
              <motion.div
                key={index}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={cardVariants}
                whileHover="hover"
                className="text-center p-8 rounded-xl bg-gradient-to-br from-white to-stone-50/50 hover:from-emerald-50/50 hover:to-teal-50/50 transition-all border border-stone-200/50 shadow-lg"
              >
                <div className="flex justify-center mb-6">
                  <div className={`p-5 rounded-xl ${stat.color} bg-gradient-to-br from-emerald-100 to-teal-100 shadow-lg`}>
                    {stat.icon}
                  </div>
                </div>
                <div className="text-5xl font-bold text-slate-900 mb-3 tracking-tight">{stat.number}</div>
                <div className="text-slate-600 font-medium leading-relaxed">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Enhanced Testimonials */}
      <section id="success-stories" className="py-32 bg-gradient-to-br from-stone-50 to-white">
        <div className="max-w-6xl mx-auto px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={textVariants}
            className="text-center mb-20"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-slate-900 mb-6 tracking-tight">
              Success Stories from Industry Leaders
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto font-light leading-relaxed">
              Discover how forward-thinking organizations are transforming their workplace culture with Nuetra.
            </p>
          </motion.div>

          <div className="relative bg-white rounded-2xl shadow-2xl p-12 md:p-16 border border-stone-200/50">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentTestimonial}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{ duration: 0.6 }}
                className="text-center"
              >
                <img
                  src={testimonials[currentTestimonial].image}
                  alt={testimonials[currentTestimonial].author}
                  className="w-24 h-24 rounded-full mx-auto mb-8 border-4 border-emerald-100 shadow-lg"
                />
                <blockquote className="text-2xl lg:text-3xl text-slate-700 mb-8 leading-relaxed font-light italic">
                  "{testimonials[currentTestimonial].quote}"
                </blockquote>
                <div className="text-slate-900 font-bold text-xl mb-2 tracking-tight">
                  {testimonials[currentTestimonial].author}
                </div>
                <div className="text-emerald-600 font-semibold mb-2">
                  {testimonials[currentTestimonial].position}
                </div>
                <div className="text-slate-500 mb-6">
                  {testimonials[currentTestimonial].company}
                </div>
                
                {/* Metrics Display */}
                <div className="flex justify-center space-x-8 mt-8">
                  {Object.entries(testimonials[currentTestimonial].metrics).map(([key, value]) => (
                    <div key={key} className="text-center">
                      <div className="text-2xl font-bold text-emerald-600">{value}</div>
                      <div className="text-sm text-slate-500 capitalize">{key}</div>
                    </div>
                  ))}
                </div>
              </motion.div>
            </AnimatePresence>

            <div className="flex justify-between items-center mt-12">
              <button
                onClick={prevTestimonial}
                className="p-3 rounded-full border-2 border-stone-300 hover:border-emerald-500 hover:bg-emerald-50 transition-all"
              >
                <ChevronLeft className="h-6 w-6 text-slate-600 hover:text-emerald-600" />
              </button>

              <div className="flex space-x-3">
                {testimonials.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentTestimonial(index)}
                    className={`w-3 h-3 rounded-full transition-all ${
                      index === currentTestimonial
                        ? "bg-emerald-500"
                        : "bg-stone-300 hover:bg-stone-400"
                    }`}
                  />
                ))}
              </div>

              <button
                onClick={nextTestimonial}
                className="p-3 rounded-full border-2 border-stone-300 hover:border-emerald-500 hover:bg-emerald-50 transition-all"
              >
                <ChevronRight className="h-6 w-6 text-slate-600 hover:text-emerald-600" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section with refined styling */}
      <section className="py-32 bg-gradient-to-r from-emerald-600 via-teal-700 to-green-800 text-white relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-10 right-10 w-96 h-96 bg-white/5 rounded-full blur-3xl"></div>
          <div className="absolute bottom-10 left-10 w-96 h-96 bg-amber-400/10 rounded-full blur-3xl"></div>
        </div>
        
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
          variants={textVariants}
          className="max-w-5xl mx-auto px-8 text-center relative z-10"
        >
          <h2 className="text-4xl lg:text-6xl font-bold mb-8 tracking-tight">
            Ready to Transform Your Organization?
          </h2>
          <p className="text-xl lg:text-2xl mb-12 opacity-90 leading-relaxed font-light max-w-3xl mx-auto">
            Join 500+ forward-thinking companies using Nuetra to build healthier, more productive, and engaged teams.
          </p>

          <div className="flex flex-col sm:flex-row gap-6 justify-center mb-12">
            <motion.button
              whileHover={{ scale: 1.05, boxShadow: "0 12px 35px rgba(255, 255, 255, 0.2)" }}
              className="px-10 py-5 bg-white text-emerald-700 rounded-lg font-bold text-lg shadow-xl hover:bg-stone-50 transition-all transform"
            >
              Schedule Strategic Consultation
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              className="px-10 py-5 border-2 border-white/80 rounded-lg text-white font-bold text-lg hover:bg-white/10 transition-all"
            >
              Download Success Framework
            </motion.button>
          </div>

          <div className="flex justify-center items-center space-x-12 text-sm opacity-75">
            <div className="flex items-center">
              <Phone className="h-5 w-5 mr-3" />
              +91-XXXX-XXXX
            </div>
            <div className="flex items-center">
              <Mail className="h-5 w-5 mr-3" />
              partnerships@nuetra.in
            </div>
          </div>
        </motion.div>
      </section>

      {/* Footer with improved typography */}
      <footer className="bg-slate-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center shadow-lg">
                  <span className="text-white font-bold text-lg">N</span>
                </div>
                <span className="text-2xl font-bold tracking-tight">Nuetra</span>
              </div>
              <p className="text-slate-400 mb-6 leading-relaxed">
                Transforming corporate wellness across India with strategic, evidence-based solutions.
              </p>
              <div className="flex space-x-4">
                <Globe className="h-5 w-5 text-slate-500" />
                <Award className="h-5 w-5 text-slate-500" />
              </div>
            </div>
            
            <div>
              <h4 className="font-bold mb-6 text-lg tracking-tight">Solutions</h4>
              <ul className="space-y-3 text-slate-400">
                <li><a href="#" className="hover:text-emerald-400 transition-colors">Corporate Wellness</a></li>
                <li><a href="#" className="hover:text-emerald-400 transition-colors">Strategic Planning</a></li>
                <li><a href="#" className="hover:text-emerald-400 transition-colors">Analytics Suite</a></li>
                <li><a href="#" className="hover:text-emerald-400 transition-colors">Executive Programs</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-bold mb-6 text-lg tracking-tight">Company</h4>
              <ul className="space-y-3 text-slate-400">
                <li><a href="#" className="hover:text-emerald-400 transition-colors">About Nuetra</a></li>
                <li><a href="#" className="hover:text-emerald-400 transition-colors">Success Stories</a></li>
                <li><a href="#" className="hover:text-emerald-400 transition-colors">Research & Insights</a></li>
                <li><a href="#" className="hover:text-emerald-400 transition-colors">Careers</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-bold mb-6 text-lg tracking-tight">Connect</h4>
              <div className="space-y-4 text-slate-400">
                <div className="flex items-center">
                  <MapPin className="h-5 w-5 mr-3 flex-shrink-0" />
                  Mumbai & Delhi, India
                </div>
                <div className="flex items-center">
                  <Mail className="h-5 w-5 mr-3 flex-shrink-0" />
                  partnerships@nuetra.in
                </div>
                <div className="flex items-center">
                  <Phone className="h-5 w-5 mr-3 flex-shrink-0" />
                  +91-XXXX-XXXX
                </div>
              </div>
            </div>
          </div>
          
          <div className="border-t border-slate-800 mt-12 pt-8 text-center text-slate-400">
            <p className="font-light">
              &copy; 2024 Nuetra. All rights reserved. | Strategic Wellness Solutions for Modern Organizations
            </p>
          </div>
        </div>
      </footer>

      {/* Video Modal */}
      <AnimatePresence>
        {isVideoModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            onClick={() => setIsVideoModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.8 }}
              className="bg-white rounded-2xl p-8 max-w-4xl w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-2xl font-bold tracking-tight">Success Stories & Platform Demo</h3>
                <button
                  onClick={() => setIsVideoModalOpen(false)}
                  className="p-2 hover:bg-stone-100 rounded-full transition-colors"
                >
                  ✕
                </button>
              </div>
              <div className="aspect-video bg-stone-100 rounded-xl flex items-center justify-center">
                <div className="text-center">
                  <Play className="h-20 w-20 text-emerald-600 mx-auto mb-4" />
                  <p className="text-slate-700 text-lg font-semibold">Platform Demo & Success Stories</p>
                  <p className="text-slate-500 mt-2">
                    See how Nuetra transforms organizational wellness culture
                  </p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}