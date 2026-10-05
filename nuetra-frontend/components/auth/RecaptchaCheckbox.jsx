import Script from 'next/script';
import { useCallback, useEffect, useRef } from 'react';

const SITE_KEY = process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY;

export default function RecaptchaCheckbox({ onVerify }) {
  const containerRef = useRef(null);
  const widgetRef = useRef(null);
  const render = useCallback(() => {
    if (!SITE_KEY || !containerRef.current || !window.grecaptcha || widgetRef.current != null) return;
    widgetRef.current = window.grecaptcha.render(containerRef.current, {
      sitekey: SITE_KEY,
      callback: (token) => onVerify(token),
      'expired-callback': () => onVerify(''),
      'error-callback': () => onVerify(''),
    });
  }, [onVerify]);
  useEffect(() => { render(); }, [render]);
  return <div>
    <Script src="https://www.google.com/recaptcha/api.js?render=explicit" strategy="afterInteractive" onLoad={render} />
    {SITE_KEY ? <div ref={containerRef} /> : <p role="alert" className="text-sm text-[#b10e1c]">CAPTCHA is unavailable. Please try again later.</p>}
  </div>;
}
