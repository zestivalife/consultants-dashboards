import {useMemo} from 'react';

export const PHONE_COUNTRIES=[
  {iso:'IN',name:'India',dial:'+91'},
  {iso:'US',name:'United States',dial:'+1'},
  {iso:'GB',name:'United Kingdom',dial:'+44'},
  {iso:'AE',name:'United Arab Emirates',dial:'+971'},
  {iso:'SG',name:'Singapore',dial:'+65'},
  {iso:'AU',name:'Australia',dial:'+61'},
  {iso:'CA',name:'Canada',dial:'+1'},
];

export function toE164(dial,nationalNumber){
  const digits=String(nationalNumber||'').replace(/\D/g,'');
  return digits?`${dial}${digits}`:'';
}

export default function PhoneNumberField({countryIso2,onCountryChange,nationalNumber,onNationalNumberChange,label='Mobile'}){
  const country=useMemo(()=>PHONE_COUNTRIES.find(item=>item.iso===countryIso2)||PHONE_COUNTRIES[0],[countryIso2]);
  const id=label.toLowerCase().replace(/[^a-z0-9]+/g,'-');
  return <fieldset className="min-w-0">
    <legend className="text-sm font-semibold">{label}</legend>
    <div className="mt-2 grid gap-2 sm:grid-cols-[minmax(10rem,0.9fr)_minmax(0,1.1fr)]">
      <label className="sr-only" htmlFor={`${id}-country`}>{label} country code</label>
      <select id={`${id}-country`} aria-label={`${label} country code`} value={country.iso} onChange={event=>onCountryChange(event.target.value)} className="min-h-12 w-full rounded-xl border border-slate-200 bg-white px-3 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100">
        {PHONE_COUNTRIES.map(item=><option key={item.iso} value={item.iso}>{item.name} ({item.dial})</option>)}
      </select>
      <label className="sr-only" htmlFor={`${id}-number`}>{label} national number</label>
      <div className="flex min-h-12 items-center rounded-xl border border-slate-200 bg-white focus-within:border-blue-600 focus-within:ring-2 focus-within:ring-blue-100">
        <span aria-hidden="true" className="border-r border-slate-200 px-3 text-sm font-semibold text-slate-600">{country.dial}</span>
        <input id={`${id}-number`} aria-label={`${label} national number`} type="tel" inputMode="numeric" autoComplete="tel-national" value={nationalNumber} onChange={event=>onNationalNumberChange(event.target.value.replace(/[^0-9 ()-]/g,''))} placeholder="97620 06688" className="min-w-0 flex-1 bg-transparent px-3 outline-none"/>
      </div>
    </div>
  </fieldset>;
}
