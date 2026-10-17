import { useState } from 'react';
import ZestivaLogo from './ZestivaLogo';
import s from '../../styles/PublicHeader.module.css';

const ROOT='https://consultant.nuetra.in/';
const links=[['Product','#product'],['Intelligence','#intelligence'],['Health Records','#health'],['Solutions','#solutions'],['Security','#security']];

export default function PublicHeader({ action='signup' }){
  const[open,setOpen]=useState(false);
  const actionLabel=action==='login'?'Sign in':action==='signup'?'Create account':null;
  const actionUrl=action==='login'?'https://consultant.nuetra.in/login':'https://consultant.nuetra.in/signup';
  return <>
    <header className={s.header}>
      <a href={ROOT} aria-label="Zestiva Consultant home" className={s.logoLink}><ZestivaLogo className={s.logo}/><span>Consultant</span></a>
      <nav className={s.desktopNav} aria-label="Public navigation">{links.map(([label,hash])=><a key={hash} href={`${ROOT}${hash}`}>{label}</a>)}</nav>
      <div className={s.actions}>{actionLabel&&<a className={s.action} href={actionUrl}>{actionLabel}</a>}<button className={s.menu} aria-label="Toggle navigation" aria-expanded={open} onClick={()=>setOpen(!open)}><i/><i/></button></div>
    </header>
    {open&&<nav className={s.mobileNav} aria-label="Mobile public navigation">{links.map(([label,hash])=><a key={hash} href={`${ROOT}${hash}`}>{label}</a>)}{actionLabel&&<a href={actionUrl}>{actionLabel}</a>}</nav>}
  </>;
}
