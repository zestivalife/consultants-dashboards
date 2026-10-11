import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

function readAccessToken() {
  return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
}

export default function ResolveProductLine() {
  const router = useRouter();
  const [message, setMessage] = useState('Resolving your authorised workspace…');

  useEffect(() => {
    if (!router.isReady) return;
    const token = readAccessToken();
    if (!token) {
      window.location.replace('/login');
      return;
    }
    fetch('/api/routing-state', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { Authorization: `Bearer ${token}` },
    }).then(async (response) => {
      if (!response.ok) throw new Error('Workspace authority could not be resolved.');
      const returnTo = typeof router.query.returnTo === 'string' && router.query.returnTo.startsWith('/')
        ? router.query.returnTo
        : '/dashboard/consultant';
      window.location.replace(returnTo);
    }).catch(() => {
      setMessage('Workspace access could not be resolved. Please sign in again.');
      window.setTimeout(() => window.location.replace('/login'), 1200);
    });
  }, [router.isReady, router.query.returnTo]);

  return <main style={{minHeight:'100vh',display:'grid',placeItems:'center',fontFamily:'system-ui',background:'#f8fafc',color:'#0f172a'}}><section role="status" style={{maxWidth:480,padding:32,border:'1px solid #e2e8f0',borderRadius:24,background:'#fff',boxShadow:'0 20px 50px rgba(15,23,42,.08)',textAlign:'center'}}><h1 style={{fontSize:24,margin:'0 0 12px'}}>Consultant workspace</h1><p style={{margin:0,lineHeight:1.6,color:'#475569'}}>{message}</p></section></main>;
}
