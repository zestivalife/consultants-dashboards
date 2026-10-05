import Script from 'next/script';
import { useCallback, useEffect, useRef, useState } from 'react';

const SITE_KEY = process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY;
const READY_CALLBACK = '__fiteatsyRecaptchaReady';

export default function RecaptchaCheckbox({ onVerify }) {
  const containerRef = useRef(null);
  const widgetRef = useRef(null);
  const [canLoadScript, setCanLoadScript] = useState(false);
  const render = useCallback(() => {
    const api = window.grecaptcha;
    if (!SITE_KEY || !containerRef.current || typeof api?.render !== 'function' || widgetRef.current != null) return;
    widgetRef.current = api.render(containerRef.current, {
      sitekey: SITE_KEY,
      callback: (token) => onVerify(token),
      'expired-callback': () => onVerify(''),
      'error-callback': () => onVerify(''),
    });
  }, [onVerify]);
  useEffect(() => {
    window[READY_CALLBACK] = render;
    setCanLoadScript(true);
    render();
    return () => {
      if (window[READY_CALLBACK] === render) delete window[READY_CALLBACK];
    };
  }, [render]);
  return <div>
    {canLoadScript ? <Script
      src={`https://www.google.com/recaptcha/api.js?onload=${READY_CALLBACK}&render=explicit`}
      strategy="afterInteractive"
      onReady={render}
    /> : null}
    {SITE_KEY ? <div ref={containerRef} /> : <p role="alert" className="text-sm text-[#b10e1c]">CAPTCHA is unavailable. Please try again later.</p>}
  </div>;
}
