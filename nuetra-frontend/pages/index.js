import React, { useState, useEffect, useRef, useCallback } from "react";
import Head from "next/head";
import Image from "next/image";
import Link from "next/link";

// ─── Brand colours ───────────────────────────────────────────────────────────
const C = {
  green:  "#19AA41",
  red:    "#D9251C",
  blue:   "#237AFC",
  yellow: "#FFDE36",
  dark:   "#1a1a1a",
  muted:  "#555555",
};

// ─── Data ─────────────────────────────────────────────────────────────────────
const heroSlides = [
  {
    bg: "https://xcoach-demo.pbminfotech.com/demo1/wp-content/uploads/sites/2/2023/11/demo1-slide1.jpg",
    badge: "TOTAL WELLNESS",
    badgeColor: C.yellow,
    badgeText: C.dark,
    title: <>Nutrition that Fits<br />Your Daily Life.</>,
    desc: "We build personalized nutrition plans designed specifically for your unique body type, lifestyle, and goals.",
    btnText: "Start Your Journey →",
    btnClass: "green",
  },
  {
    bg: "https://xcoach-demo.pbminfotech.com/demo1/wp-content/uploads/sites/2/2023/11/demo1-slide2.jpg",
    badge: "PEAK PERFORMANCE",
    badgeColor: C.blue,
    badgeText: "#fff",
    title: <>Push Limits,<br />Break Barriers.</>,
    desc: "Experience professional coaching and elite guidance to help you reach your peak physical performance.",
    btnText: "Start Your Journey →",
    btnClass: "red",
  },
  {
    bg: "https://xcoach-demo.pbminfotech.com/demo1/wp-content/uploads/sites/2/2023/11/demo1-slide3.jpg",
    badge: "LIFESTYLE MENTORING",
    badgeColor: C.yellow,
    badgeText: C.dark,
    title: <>Work 1-on-1 with<br />Certified Mentors.</>,
    desc: "Build your best routines with Nuetra's structured framework designed to support your physical and mental well-being.",
    btnText: "Start Your Journey →",
    btnClass: "green",
  },
];

const offerCards = [
  {
    img: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600&h=700&fit=crop",
    cat: "Healthy Choices",
    name: "Smart Meal Swaps",
    desc: "Discover healthier alternatives for your cravings without giving up taste.",
    color: C.green,
  },
  {
    img: "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=600&h=700&fit=crop",
    cat: "Performance",
    name: "Nutrition Blueprint",
    desc: "Get a simple, customised plan based on your intense lifestyle and goals.",
    color: C.red,
  },
  {
    img: "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=600&h=700&fit=crop",
    cat: "Consistency",
    name: "Habit Tracking",
    desc: "Daily reminders and small steps that help you stay consistent effortlessly.",
    color: C.blue,
  },
  {
    img: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=600&h=700&fit=crop",
    cat: "Community",
    name: "Expert Guidance",
    desc: "Access nutrition mentors and weekly progress insights anytime.",
    color: "#d4a000",
  },
];

const processCards = [
  {
    step: "Step 01",
    color: C.green,
    title: "Enrol & Onboard",
    desc: "Organizations partner with Nuetra, and employees get seamless access to the platform. Benefits, privacy safeguards, and wellness options are clearly explained to ensure smooth adoption.",
    img: "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=700&h=480&fit=crop",
    alt: "Enrol & Onboard",
  },
  {
    step: "Step 02",
    color: C.red,
    title: "Assess & Understand",
    desc: "Employees request diet plans or health sessions, securely upload health reports, and complete assessments. Our experts review the data to understand individual health needs and goals.",
    img: "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=700&h=480&fit=crop",
    alt: "Assess & Understand",
  },
  {
    step: "Step 03",
    color: C.blue,
    title: "Personalised Expert Care",
    desc: "Employees book one-on-one consultations with clinical experts. Tailored diet plans, lifestyle recommendations, and actionable guidance are shared through secure digital and virtual sessions.",
    img: "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=700&h=480&fit=crop",
    alt: "Personalised Expert Care",
  },
  {
    step: "Step 04",
    color: C.yellow,
    title: "Track, Support & Sustain",
    desc: "Ongoing follow-ups, progress reviews, reminders, and continuous support help employees build better habits—leading to lasting health improvements and sustained workplace performance.",
    img: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=700&h=480&fit=crop",
    alt: "Track, Support & Sustain",
  },
];

const wellnessSteps = [
  { icon: "🤝", label: "Connect", desc: "Start your corporate wellness journey with a personalized consultation.", color: C.green },
  { icon: "📋", label: "Assessment", desc: "We gather health data, dietary preferences, and your specific goals.", color: C.red },
  { icon: "💡", label: "Smart Planning", desc: "Customized nutrition and fitness strategies for your unique workforce.", color: C.blue },
  { icon: "🏆", label: "Perform", desc: "Monitor real-time results and experience a healthier, more active team.", color: C.yellow },
];

// ─── Hero Slider Component ────────────────────────────────────────────────────
function HeroSlider() {
  const [current, setCurrent] = useState(0);
  const [animating, setAnimating] = useState(false);
  const intervalRef = useRef(null);

  const goTo = useCallback((idx) => {
    if (animating) return;
    setAnimating(true);
    setCurrent(idx);
    setTimeout(() => setAnimating(false), 800);
  }, [animating]);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setCurrent(c => (c + 1) % heroSlides.length);
    }, 6000);
    return () => clearInterval(intervalRef.current);
  }, []);

  const slide = heroSlides[current];

  return (
    <div style={{ position: "relative", width: "100%", height: "100vh", minHeight: 560, overflow: "hidden", background: "#000" }}>
      {/* Background images */}
      {heroSlides.map((s, i) => (
        <div
          key={i}
          style={{
            position: "absolute", inset: 0,
            backgroundImage: `url('${s.bg}')`,
            backgroundSize: "cover", backgroundPosition: "center",
            transition: "opacity 1.2s ease, transform 6s ease-in-out",
            opacity: i === current ? 1 : 0,
            transform: i === current ? "scale(1.05)" : "scale(1)",
            zIndex: 0,
          }}
        />
      ))}

      {/* Overlay */}
      <div style={{
        position: "absolute", inset: 0, zIndex: 1,
        background: "linear-gradient(90deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.5) 55%, rgba(0,0,0,0.1) 100%)",
      }} />

      {/* Content */}
      <div style={{
        position: "relative", zIndex: 10,
        maxWidth: 1100, width: "90%", margin: "0 auto",
        height: "100%", display: "flex", alignItems: "center",
        paddingLeft: 20,
      }}>
        <div key={current} style={{ maxWidth: 680, animation: "heroFadeUp 0.8s ease forwards" }}>
          <span style={{
            display: "inline-block",
            background: slide.badgeColor,
            color: slide.badgeText,
            padding: "8px 18px",
            fontWeight: 800, fontSize: 13,
            borderRadius: 4, marginBottom: 24,
            letterSpacing: "1.5px", textTransform: "uppercase",
            boxShadow: `0 4px 15px rgba(255,222,54,0.4)`,
            fontFamily: "'Manrope', sans-serif",
          }}>
            {slide.badge}
          </span>

          <h1 style={{
            color: "#ffffff",
            fontFamily: "'DM Sans', sans-serif",
            fontSize: "clamp(42px, 6vw, 78px)",
            fontWeight: 800, lineHeight: 1.1,
            marginBottom: 24,
            textShadow: "0 2px 10px rgba(0,0,0,0.5)",
          }}>
            {slide.title}
          </h1>

          <p style={{
            color: "#ffffff",
            fontSize: 18, maxWidth: 620, marginBottom: 40,
            lineHeight: 1.7, fontWeight: 500,
            borderLeft: `4px solid ${C.blue}`,
            paddingLeft: 20,
            textShadow: "0 2px 5px rgba(0,0,0,0.5)",
          }}>
            {slide.desc}
          </p>

          <Link href="/register" style={{
            display: "inline-block",
            padding: "18px 45px",
            borderRadius: 50,
            textDecoration: "none",
            fontWeight: 700, fontSize: 16,
            background: slide.btnClass === "green" ? C.green : C.red,
            color: "#ffffff",
            border: `2px solid ${slide.btnClass === "green" ? C.green : C.red}`,
            boxShadow: slide.btnClass === "green"
              ? "0 10px 30px rgba(25,170,65,0.4)"
              : "0 10px 30px rgba(217,37,28,0.4)",
            transition: "all 0.3s ease",
            fontFamily: "'Manrope', sans-serif",
          }}>
            {slide.btnText}
          </Link>
        </div>
      </div>

      {/* Arrows */}
      <button
        onClick={() => goTo((current - 1 + heroSlides.length) % heroSlides.length)}
        aria-label="Previous slide"
        style={arrowStyle("left")}
      >←</button>
      <button
        onClick={() => goTo((current + 1) % heroSlides.length)}
        aria-label="Next slide"
        style={arrowStyle("right")}
      >→</button>

      {/* Dots */}
      <div style={{ position: "absolute", bottom: 30, left: "50%", transform: "translateX(-50%)", display: "flex", gap: 10, zIndex: 10 }}>
        {heroSlides.map((_, i) => (
          <button
            key={i}
            onClick={() => goTo(i)}
            aria-label={`Go to slide ${i + 1}`}
            style={{
              width: i === current ? 28 : 10,
              height: 10, borderRadius: 5,
              background: i === current ? C.green : "rgba(255,255,255,0.5)",
              border: "none", cursor: "pointer",
              transition: "all 0.3s ease", padding: 0,
            }}
          />
        ))}
      </div>
    </div>
  );
}

function arrowStyle(side) {
  return {
    position: "absolute",
    [side]: 24,
    top: "50%", transform: "translateY(-50%)",
    zIndex: 10,
    width: 56, height: 56,
    borderRadius: "50%",
    border: "1px solid rgba(255,255,255,0.3)",
    background: "rgba(255,255,255,0.12)",
    backdropFilter: "blur(5px)",
    color: "#ffffff",
    fontSize: 22, fontWeight: "bold",
    cursor: "pointer",
    display: "flex", alignItems: "center", justifyContent: "center",
    transition: "all 0.3s ease",
  };
}

// ─── Offer Cards Slider ───────────────────────────────────────────────────────
function OfferSlider() {
  const [offset, setOffset] = useState(0);
  const trackRef = useRef(null);

  function slideTo(dir) {
    const track = trackRef.current;
    if (!track) return;
    const cards = track.querySelectorAll("[data-card]");
    if (!cards.length) return;
    const cardW = cards[0].getBoundingClientRect().width + 30;
    const maxOffset = Math.max(0, (offerCards.length - 3) * cardW);
    setOffset(o => Math.max(0, Math.min(o + dir * cardW, maxOffset)));
  }

  return (
    <div style={{ overflow: "hidden", paddingBottom: 50, paddingLeft: 10 }}>
      <div ref={trackRef} style={{
        display: "flex", gap: 30,
        transform: `translateX(-${offset}px)`,
        transition: "transform 0.6s cubic-bezier(0.25,1,0.5,1)",
      }}>
        {offerCards.map((card, i) => (
          <article
            key={i}
            data-card="true"
            style={{
              flex: "0 0 calc((100% - 60px) / 3)",
              minWidth: 280,
              background: "rgba(255,255,255,0.97)",
              borderRadius: 12, overflow: "hidden",
              boxShadow: "0 10px 30px rgba(0,0,0,0.07)",
              borderLeft: `6px solid ${card.color}`,
              transition: "all 0.4s ease",
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-10px)"; e.currentTarget.style.boxShadow = `0 20px 40px rgba(0,0,0,0.12)`; }}
            onMouseLeave={e => { e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = "0 10px 30px rgba(0,0,0,0.07)"; }}
          >
            <div style={{ height: 220, overflow: "hidden" }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={card.img}
                alt={card.name}
                style={{ width: "100%", height: "100%", objectFit: "cover", display: "block", transition: "transform 0.6s ease" }}
                loading="lazy"
                onMouseEnter={e => e.currentTarget.style.transform = "scale(1.1)"}
                onMouseLeave={e => e.currentTarget.style.transform = ""}
              />
            </div>
            <div style={{ padding: 25 }}>
              <div style={{ fontSize: 11, letterSpacing: "2px", textTransform: "uppercase", fontWeight: 700, color: card.color, marginBottom: 10 }}>{card.cat}</div>
              <h3 style={{ fontFamily: "'Manrope', sans-serif", fontSize: 22, fontWeight: 700, color: C.dark, margin: "0 0 10px" }}>{card.name}</h3>
              <p style={{ fontSize: 15, lineHeight: 1.6, color: C.muted, margin: 0 }}>{card.desc}</p>
            </div>
          </article>
        ))}
      </div>
      <div style={{ display: "flex", gap: 15, marginTop: 30 }}>
        <button onClick={() => slideTo(-1)} style={navBtnStyle} aria-label="Previous">←</button>
        <button onClick={() => slideTo(1)} style={navBtnStyle} aria-label="Next">→</button>
      </div>
    </div>
  );
}

const navBtnStyle = {
  border: "1px solid rgba(0,0,0,0.15)",
  background: "rgba(255,255,255,0.8)",
  color: C.dark, cursor: "pointer",
  width: 50, height: 50, borderRadius: "50%",
  display: "flex", alignItems: "center", justifyContent: "center",
  fontSize: 18, transition: "all 0.3s ease",
  boxShadow: "0 5px 15px rgba(0,0,0,0.05)",
};

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function NuetraHome() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeImg, setActiveImg] = useState(1);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <Head>
        <title>Nuetra - Corporate Wellness & Nutrition Platform</title>
        <meta name="description" content="Nuetra brings certified clinical dietitians, personalized nutrition plans, and measurable health tracking directly into your workplace — structured, affordable, and built for Indian organizations." />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />
        <style>{`
          * { margin: 0; padding: 0; box-sizing: border-box; }
          html { scroll-behavior: smooth; }
          body { font-family: 'DM Sans', sans-serif; overflow-x: hidden; background: #fff; }
          @keyframes heroFadeUp {
            from { opacity: 0; transform: translateY(40px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes gradientMove { 0% { transform: scale(1); } 100% { transform: scale(1.2); } }
          @keyframes nsZoom { 0% { transform: scale(1); } 100% { transform: scale(1.15); } }
          @keyframes fadeSlideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
          @keyframes pulseDot { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }
        `}</style>
      </Head>

      <div style={{ minHeight: "100vh", background: "#fff", fontFamily: "'DM Sans', sans-serif" }}>

        {/* ── TOPBAR ── */}
        <div style={{
          background: C.green, color: "#fff",
          fontSize: 13, fontWeight: 600, padding: "10px 20px",
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <span>
            <i className="fa-regular fa-envelope" style={{ marginRight: 8 }} />
            <a href="mailto:info@nuetra.in" style={{ color: "#fff", textDecoration: "none" }}>info@nuetra.in</a>
          </span>
          <div style={{ display: "flex", gap: 15 }}>
            <a href="https://www.linkedin.com/company/nuetra/" target="_blank" rel="noreferrer"
              style={{ color: "#fff", fontSize: 16, textDecoration: "none" }}>
              <i className="fa-brands fa-linkedin-in" />
            </a>
          </div>
        </div>

        {/* ── HEADER ── */}
        <header style={{
          width: "100%",
          background: "#ffffff",
          boxShadow: scrolled ? "0 4px 15px rgba(0,0,0,0.08)" : "0 1px 3px rgba(0,0,0,0.04)",
          position: "sticky", top: 0, zIndex: 999,
          transition: "box-shadow 0.3s ease",
        }}>
          <div style={{ maxWidth: 1400, margin: "0 auto", padding: "12px 20px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>

            {/* Logo */}
            <Link href="/" style={{ display: "flex", alignItems: "center", textDecoration: "none" }}>
              <Image src="/nuetra-logo-new.svg" alt="Nuetra" width={140} height={36} style={{ objectFit: "contain" }} />
            </Link>

            {/* Desktop Nav */}
            <nav style={{ display: "flex", gap: 30, alignItems: "center" }}>
              {[
                ["Home", "/"],
                ["About", "#about"],
                ["Services", "#services"],
                ["How It Works", "#process"],
                ["Contact", "#contact"],
              ].map(([label, href]) => (
                <a key={label} href={href} style={{
                  textDecoration: "none", fontWeight: 700, fontSize: 15,
                  color: C.dark, fontFamily: "'Manrope', sans-serif",
                  transition: "color 0.2s",
                }}
                  onMouseEnter={e => e.currentTarget.style.color = C.green}
                  onMouseLeave={e => e.currentTarget.style.color = C.dark}
                >
                  {label}
                </a>
              ))}
            </nav>

            {/* CTA */}
            <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
              <Link href="/login" style={{
                textDecoration: "none", fontWeight: 700, fontSize: 14,
                color: C.dark, fontFamily: "'Manrope', sans-serif",
              }}>Log In</Link>
              <Link href="/register" style={{
                textDecoration: "none",
                border: `2px solid ${C.green}`,
                padding: "10px 28px",
                borderRadius: 50,
                fontWeight: 700, fontSize: 14,
                color: C.green,
                transition: "all 0.3s ease",
                fontFamily: "'Manrope', sans-serif",
              }}
                onMouseEnter={e => { e.currentTarget.style.background = C.green; e.currentTarget.style.color = "#fff"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = C.green; }}
              >GET STARTED</Link>
            </div>
          </div>
        </header>

        {/* ── HERO SLIDER ── */}
        <HeroSlider />

        {/* ── WHO WE ARE ── */}
        <section id="about" style={{ padding: "100px 20px", background: "#fff" }}>
          <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", gap: 60, alignItems: "center", flexWrap: "wrap" }}>

            <div style={{ flex: 1, minWidth: 300 }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=600&h=700&fit=crop"
                alt="Nuetra Coaching"
                style={{
                  width: "100%", height: "auto", borderRadius: 20, display: "block",
                  objectFit: "cover", boxShadow: "0 20px 40px rgba(0,0,0,0.08)",
                  transition: "transform 0.3s ease"
                }}
                loading="lazy"
                onMouseEnter={e => e.currentTarget.style.transform = "translateY(-5px)"}
                onMouseLeave={e => e.currentTarget.style.transform = ""}
              />
            </div>

            <div style={{ flex: 1.1, minWidth: 300 }}>
              <span style={{
                display: "inline-block",
                padding: "8px 20px",
                background: C.yellow,
                color: C.dark,
                borderRadius: 4, fontSize: 12, fontWeight: 800,
                textTransform: "uppercase", letterSpacing: "1.5px",
                marginBottom: 24,
                boxShadow: "0 4px 15px rgba(255,222,54,0.3)",
                fontFamily: "'Manrope', sans-serif",
              }}>
                Why Choose Nuetra
              </span>

              <h2 style={{
                fontFamily: "'Manrope', sans-serif",
                fontSize: "clamp(34px, 4vw, 50px)",
                fontWeight: 800, color: C.dark,
                lineHeight: 1.15, marginBottom: 24,
              }}>
                Your Employees Deserve More Than a Wellness App.
              </h2>

              <p style={{
                marginBottom: 32, fontSize: 18, color: C.muted,
                borderLeft: `4px solid ${C.red}`, paddingLeft: 20, lineHeight: 1.7,
              }}>
                Nuetra brings certified clinical dietitians, personalized nutrition plans, and measurable health tracking directly into your workplace — structured, affordable, and built for Indian organizations.
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: 20, marginBottom: 40 }}>
                {[
                  ["Clinician-Led, Not AI-Generated", "Every plan designed by a certified clinical dietitian."],
                  ["Measurable HR Health Insights", "Anonymized workforce health data your HR team can actually use."],
                  ["Built for Indian SMEs", "Device-independent. Affordable. Designed for 50–500 employee organizations."],
                ].map(([title, text]) => (
                  <div key={title} style={{ display: "flex", alignItems: "flex-start", gap: 15 }}>
                    <div style={{
                      background: "rgba(25,170,65,0.1)", color: C.green,
                      width: 26, height: 26, borderRadius: "50%",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 14, fontWeight: 800, flexShrink: 0, marginTop: 4,
                    }}>✓</div>
                    <div>
                      <h3 style={{ fontFamily: "'Manrope', sans-serif", fontSize: 18, fontWeight: 700, color: C.dark, margin: "0 0 4px", lineHeight: 1.3 }}>{title}</h3>
                      <p style={{ fontSize: 15, margin: 0, color: C.muted, lineHeight: 1.5 }}>{text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── WHAT WE OFFER ── */}
        <section id="services" style={{ position: "relative", padding: "100px 0", overflow: "hidden" }}>
          {/* Animated gradient bg */}
          <div style={{
            position: "absolute", inset: 0, zIndex: 0,
            backgroundImage: `
              radial-gradient(at 10% 10%, rgba(35,122,252,0.15) 0px, transparent 50%),
              radial-gradient(at 90% 0%, rgba(255,222,54,0.2) 0px, transparent 50%),
              radial-gradient(at 50% 90%, rgba(25,170,65,0.15) 0px, transparent 50%)
            `,
            filter: "blur(80px)",
            animation: "gradientMove 10s ease-in-out infinite alternate",
            backgroundColor: "#f8f9fa",
          }} />

          <div style={{ maxWidth: 1240, margin: "0 auto", padding: "0 20px", position: "relative", zIndex: 2 }}>
            <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 60, flexWrap: "wrap", gap: 20 }}>
              <div>
                <div style={{
                  display: "inline-block", padding: "6px 14px",
                  background: "rgba(255,222,54,0.2)",
                  border: `1px solid ${C.yellow}`,
                  borderRadius: 4, fontSize: 11, letterSpacing: "2px",
                  textTransform: "uppercase", fontWeight: 700, color: "#b38f00",
                  marginBottom: 20,
                }}>
                  What We Offer
                </div>
                <h2 style={{
                  fontFamily: "'Manrope', sans-serif",
                  fontSize: "clamp(30px, 4vw, 46px)",
                  fontWeight: 800, color: C.dark, lineHeight: 1.2,
                }}>
                  Transform Your Daily Eating<br />With Our Personalized Tools
                </h2>
              </div>
            </div>

            <OfferSlider />
          </div>
        </section>

        {/* ── HOW NUETRA HELPS: PROCESS CARDS (dark) ── */}
        <section id="process" style={{
          background: "#050505", padding: "120px 0 80px", color: "#fff",
          fontFamily: "'DM Sans', sans-serif",
        }}>
          <div style={{ maxWidth: 1100, margin: "0 auto", padding: "0 20px" }}>
            <span style={{
              textTransform: "uppercase", letterSpacing: "3px", fontSize: 12,
              fontWeight: 700, color: C.yellow, marginBottom: 15, textAlign: "center", display: "block",
            }}>
              Our Process
            </span>
            <h2 style={{
              fontFamily: "'Manrope', sans-serif",
              fontSize: "clamp(34px, 5vw, 50px)", lineHeight: 1.2, fontWeight: 800,
              marginBottom: 20, textAlign: "center",
              background: "linear-gradient(to right, #fff, #999)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            }}>
              How Nuetra Helps You
            </h2>
            <p style={{
              fontSize: 18, color: "#9ca3af", textAlign: "center",
              maxWidth: 700, margin: "0 auto 80px", lineHeight: 1.7,
            }}>
              Build your best routines with Nuetra's structured framework designed to support your physical and mental well-being.
            </p>

            {processCards.map((card, i) => (
              <div
                key={i}
                style={{
                  display: "flex", background: "#111111",
                  borderRadius: 24, overflow: "hidden",
                  boxShadow: "0 -10px 40px rgba(0,0,0,0.5)",
                  marginBottom: i < processCards.length - 1 ? 30 : 0,
                  border: "1px solid rgba(255,255,255,0.07)",
                  borderTop: `4px solid ${card.color}`,
                  minHeight: 400,
                }}
                onMouseEnter={e => {
                  const img = e.currentTarget.querySelector("img");
                  if (img) img.style.transform = "scale(1.05)";
                }}
                onMouseLeave={e => {
                  const img = e.currentTarget.querySelector("img");
                  if (img) img.style.transform = "";
                }}
              >
                <div style={{
                  flex: 1, padding: 60, display: "flex", flexDirection: "column", justifyContent: "center",
                  background: `radial-gradient(circle at top left, ${card.color}22, transparent 70%)`,
                  position: "relative", zIndex: 2,
                }}>
                  <div style={{
                    fontSize: 13, fontWeight: 800, textTransform: "uppercase",
                    letterSpacing: "2px", marginBottom: 22,
                    display: "inline-block", padding: "6px 14px", borderRadius: 4,
                    background: "rgba(255,255,255,0.05)",
                    color: card.color, border: `1px solid ${card.color}`,
                    alignSelf: "flex-start",
                  }}>
                    {card.step}
                  </div>
                  <h3 style={{
                    fontFamily: "'Manrope', sans-serif", fontSize: 30,
                    lineHeight: 1.2, fontWeight: 800, marginBottom: 18, color: "#fff",
                  }}>
                    {card.title}
                  </h3>
                  <p style={{ fontSize: 17, lineHeight: 1.7, color: "#9ca3af" }}>{card.desc}</p>
                </div>
                <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={card.img}
                    alt={card.alt}
                    style={{ width: "100%", height: "100%", objectFit: "cover", display: "block", transition: "transform 0.5s ease" }}
                    loading="lazy"
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── CORPORATE WELLNESS IN 4 STEPS ── */}
        <section style={{
          padding: "100px 20px",
          background: "linear-gradient(180deg, #FFFFFF 0%, #F5F9FF 100%)",
          textAlign: "center",
        }}>
          <div style={{ maxWidth: 1200, margin: "0 auto" }}>
            <h2 style={{
              fontFamily: "'Manrope', sans-serif",
              fontSize: "clamp(30px, 4vw, 46px)",
              fontWeight: 800, marginBottom: 60,
              lineHeight: 1.2, color: "#111",
            }}>
              Corporate Wellness<br />in 4 Simple Steps
            </h2>

            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 24,
            }}>
              {wellnessSteps.map((step, i) => (
                <div
                  key={i}
                  style={{
                    background: "#ffffff",
                    padding: "48px 28px",
                    borderRadius: 28,
                    boxShadow: "0 15px 45px rgba(0,0,0,0.06)",
                    transition: "all 0.4s ease",
                    position: "relative",
                    display: "flex", flexDirection: "column", alignItems: "center",
                    border: "1px solid rgba(0,0,0,0.03)",
                  }}
                  onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-12px)"; e.currentTarget.style.boxShadow = "0 25px 60px rgba(0,0,0,0.12)"; }}
                  onMouseLeave={e => { e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = "0 15px 45px rgba(0,0,0,0.06)"; }}
                >
                  {/* bottom bar */}
                  <div style={{
                    position: "absolute", bottom: 0, left: "20%", right: "20%",
                    height: 5, borderRadius: "5px 5px 0 0",
                    background: step.color,
                  }} />

                  <div style={{
                    width: 78, height: 78, borderRadius: 20,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 32, marginBottom: 22,
                    background: `${step.color}18`,
                  }}>
                    {step.icon}
                  </div>
                  <h3 style={{ fontFamily: "'Manrope', sans-serif", fontSize: 22, fontWeight: 800, color: "#1a1a1a", marginBottom: 12 }}>{step.label}</h3>
                  <p style={{ fontSize: 15, lineHeight: 1.6, color: "#666", margin: 0 }}>{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── LIFESTYLE MENTORING CTA (cinematic dark) ── */}
        <section style={{
          position: "relative",
          width: "calc(100% - 40px)",
          margin: "30px auto",
          borderRadius: 40,
          padding: "120px 0",
          minHeight: 580,
          display: "flex", alignItems: "center",
          color: "#fff",
          overflow: "hidden",
          boxShadow: "0 20px 50px rgba(0,0,0,0.2)",
          background: "#050505",
        }}>
          {/* bg */}
          <div style={{
            position: "absolute", inset: 0, zIndex: 0,
            backgroundImage: "url('https://xcoach-demo.pbminfotech.com/demo1/wp-content/uploads/sites/2/2023/11/bg-01.jpg')",
            backgroundSize: "cover", backgroundPosition: "center",
            animation: "nsZoom 20s infinite alternate ease-in-out",
            borderRadius: 40,
          }} />
          {/* overlay */}
          <div style={{
            position: "absolute", inset: 0, zIndex: 1, borderRadius: 40,
            background: "linear-gradient(90deg, #000 0%, rgba(0,0,0,0.92) 40%, rgba(0,0,0,0.3) 100%)",
          }} />

          <div style={{ position: "relative", zIndex: 2, maxWidth: 720, marginLeft: "10%", paddingRight: 20 }}>
            <span style={{
              display: "inline-block",
              background: "rgba(255,222,54,0.15)",
              color: C.yellow,
              border: `1px solid ${C.yellow}`,
              padding: "8px 18px", fontWeight: 800,
              fontSize: 13, textTransform: "uppercase",
              letterSpacing: "2px", borderRadius: 4,
              marginBottom: 28,
              boxShadow: "0 0 15px rgba(255,222,54,0.2)",
              fontFamily: "'Manrope', sans-serif",
              animation: "fadeSlideUp 0.8s ease-out 0.2s both",
            }}>
              Be the Best Version of Yourself
            </span>

            <h2 style={{
              fontFamily: "'Manrope', sans-serif",
              fontSize: "clamp(38px, 5.5vw, 62px)",
              fontWeight: 800, margin: "0 0 28px", lineHeight: 1.1, color: "#fff",
              animation: "fadeSlideUp 0.8s ease-out 0.4s both",
            }}>
              Lifestyle Mentoring<br />&amp; Habit Coaching
            </h2>

            <div style={{
              fontSize: 18, lineHeight: 1.8,
              color: "rgba(255,255,255,0.85)",
              borderLeft: `4px solid ${C.green}`,
              paddingLeft: 24,
              animation: "fadeSlideUp 0.8s ease-out 0.6s both",
            }}>
              <p style={{ marginBottom: 18 }}>
                Whether you're managing weight, boosting energy, or improving your relationship with food, Nuetra gives you a clear roadmap.
              </p>
              <p style={{ margin: 0 }}>
                Work 1-on-1 with certified mentors who guide you every step of the way — through simple, achievable actions.
              </p>
            </div>

            <div style={{ marginTop: 40, display: "flex", gap: 16, flexWrap: "wrap" }}>
              <Link href="/register" style={{
                display: "inline-block",
                padding: "18px 42px", borderRadius: 50,
                background: C.green, color: "#fff",
                textDecoration: "none", fontWeight: 700, fontSize: 16,
                border: `2px solid ${C.green}`,
                boxShadow: "0 10px 30px rgba(25,170,65,0.4)",
                transition: "all 0.3s ease",
                fontFamily: "'Manrope', sans-serif",
              }}>
                Get Started →
              </Link>
              <Link href="/login" style={{
                display: "inline-block",
                padding: "16px 42px", borderRadius: 50,
                background: "transparent", color: "#fff",
                textDecoration: "none", fontWeight: 700, fontSize: 16,
                border: "2px solid rgba(255,255,255,0.4)",
                transition: "all 0.3s ease",
                fontFamily: "'Manrope', sans-serif",
              }}>
                Log In
              </Link>
            </div>
          </div>
        </section>

        {/* ── FOOTER ── */}
        <footer style={{
          background: "#050505", color: "#b0b0b0",
          fontFamily: "'DM Sans', sans-serif", overflow: "hidden",
          marginTop: 30,
        }}>
          {/* coloured top bar */}
          <div style={{
            height: 4,
            background: `linear-gradient(90deg, ${C.green} 0%, ${C.green} 25%, ${C.red} 25%, ${C.red} 50%, ${C.blue} 50%, ${C.blue} 75%, ${C.yellow} 75%, ${C.yellow} 100%)`,
          }} />

          <div style={{
            maxWidth: 1240, margin: "0 auto", padding: "80px 20px 40px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 50,
          }}>
            {/* Brand */}
            <div>
              <Image src="/nuetra-logo-new.svg" alt="Nuetra" width={130} height={32}
                style={{ objectFit: "contain", marginBottom: 20, filter: "brightness(0) invert(1)", opacity: 0.9 }} />
              <p style={{ fontSize: 15, lineHeight: 1.8, marginBottom: 28, opacity: 0.8 }}>
                Nuetra is a modern corporate wellness platform delivering certified nutrition care tailored to Indian organizations.
              </p>
              <div style={{ display: "flex", gap: 12 }}>
                <a href="https://www.linkedin.com/company/nuetra/" target="_blank" rel="noreferrer"
                  style={{
                    width: 40, height: 40, background: "rgba(255,255,255,0.05)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    borderRadius: "50%", color: "#fff", textDecoration: "none",
                    border: "1px solid rgba(255,255,255,0.1)", transition: "all 0.3s ease",
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#0077b5"; e.currentTarget.style.transform = "translateY(-3px)"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,0.05)"; e.currentTarget.style.transform = ""; }}
                >
                  <i className="fab fa-linkedin-in" />
                </a>
                <a href="https://wa.me/918587812523" target="_blank" rel="noreferrer"
                  style={{
                    width: 40, height: 40, background: "rgba(255,255,255,0.05)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    borderRadius: "50%", color: "#fff", textDecoration: "none",
                    border: "1px solid rgba(255,255,255,0.1)", transition: "all 0.3s ease",
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#25D366"; e.currentTarget.style.transform = "translateY(-3px)"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,0.05)"; e.currentTarget.style.transform = ""; }}
                >
                  <i className="fab fa-whatsapp" />
                </a>
              </div>
            </div>

            {/* Services */}
            <div>
              <h4 style={{ fontFamily: "'Manrope', sans-serif", fontSize: 18, fontWeight: 700, color: "#fff", marginBottom: 20, position: "relative", display: "inline-block" }}>
                Our Services
                <span style={{ position: "absolute", bottom: -8, left: 0, width: 30, height: 2, background: C.yellow, borderRadius: 2 }} />
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: "16px 0 0" }}>
                {["Personalized Nutrition", "BMI Analysis", "Wellness Coaching", "Health Analytics"].map(s => (
                  <li key={s} style={{ marginBottom: 12 }}>
                    <a href="#services" style={{ textDecoration: "none", color: "#b0b0b0", fontSize: 15, transition: "all 0.3s ease" }}
                      onMouseEnter={e => { e.currentTarget.style.color = "#fff"; e.currentTarget.style.paddingLeft = "5px"; }}
                      onMouseLeave={e => { e.currentTarget.style.color = "#b0b0b0"; e.currentTarget.style.paddingLeft = ""; }}
                    >
                      › {s}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Quick links */}
            <div>
              <h4 style={{ fontFamily: "'Manrope', sans-serif", fontSize: 18, fontWeight: 700, color: "#fff", marginBottom: 20, position: "relative", display: "inline-block" }}>
                Quick Links
                <span style={{ position: "absolute", bottom: -8, left: 0, width: 30, height: 2, background: C.yellow, borderRadius: 2 }} />
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: "16px 0 0" }}>
                {[["Home", "/"], ["About Us", "#about"], ["FAQs", "#"], ["Contact", "#contact"]].map(([label, href]) => (
                  <li key={label} style={{ marginBottom: 12 }}>
                    <a href={href} style={{ textDecoration: "none", color: "#b0b0b0", fontSize: 15, transition: "all 0.3s ease" }}
                      onMouseEnter={e => { e.currentTarget.style.color = "#fff"; e.currentTarget.style.paddingLeft = "5px"; }}
                      onMouseLeave={e => { e.currentTarget.style.color = "#b0b0b0"; e.currentTarget.style.paddingLeft = ""; }}
                    >
                      › {label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Contact */}
            <div id="contact">
              <h4 style={{ fontFamily: "'Manrope', sans-serif", fontSize: 18, fontWeight: 700, color: "#fff", marginBottom: 20, position: "relative", display: "inline-block" }}>
                Contact
                <span style={{ position: "absolute", bottom: -8, left: 0, width: 30, height: 2, background: C.yellow, borderRadius: 2 }} />
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: "16px 0 0" }}>
                <li style={{ display: "flex", gap: 14, marginBottom: 14, fontSize: 14, lineHeight: 1.6 }}>
                  <i className="fas fa-map-marker-alt" style={{ color: C.green, marginTop: 3, flexShrink: 0 }} />
                  <span>H2 Sai Park, Shravasti Nagar, Ghorpadi, Pune, 411001</span>
                </li>
                <li style={{ display: "flex", gap: 14, marginBottom: 14, fontSize: 14 }}>
                  <i className="fas fa-phone-alt" style={{ color: C.green, marginTop: 2, flexShrink: 0 }} />
                  <a href="tel:+918587812523" style={{ color: "#b0b0b0", textDecoration: "none" }}>+91 8587812523</a>
                </li>
                <li style={{ display: "flex", gap: 14, fontSize: 14 }}>
                  <i className="fas fa-envelope" style={{ color: C.green, marginTop: 2, flexShrink: 0 }} />
                  <a href="mailto:info@nuetra.in" style={{ color: "#b0b0b0", textDecoration: "none" }}>info@nuetra.in</a>
                </li>
              </ul>
            </div>
          </div>

          <div style={{
            borderTop: "1px solid rgba(255,255,255,0.08)",
            padding: "24px 20px",
            textAlign: "center",
            fontSize: 14,
            background: "#000",
          }}>
            © 2026 <strong>Nuetra</strong>. All Rights Reserved.
          </div>
        </footer>

        {/* ── WhatsApp Float ── */}
        <a
          href="https://wa.me/918587812523?text=Hello%20I%20would%20like%20to%20know%20more%20about%20your%20services."
          target="_blank" rel="noreferrer"
          style={{
            position: "fixed", bottom: 20, right: 20,
            width: 55, height: 55,
            background: "#25D366", color: "#fff",
            borderRadius: "50%",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 26, boxShadow: "0 8px 20px rgba(0,0,0,0.3)",
            zIndex: 9999, textDecoration: "none",
          }}
          aria-label="Chat on WhatsApp"
        >
          <i className="fab fa-whatsapp" />
        </a>

      </div>
    </>
  );
}