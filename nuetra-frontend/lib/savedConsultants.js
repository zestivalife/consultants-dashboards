export const SAVED_CONSULTANTS_KEY='zestiva.public.saved-consultants.v1';
export const SAVED_CONSULTANTS_LIMIT=10;
export const COMPARISON_LIMIT=4;
const clean=items=>[...new Set((Array.isArray(items)?items:[]).filter(item=>typeof item==='string'&&/^[a-z0-9-]{1,180}$/.test(item)))].slice(0,SAVED_CONSULTANTS_LIMIT);
export function readSavedConsultants(){if(typeof window==='undefined')return[];try{return clean(JSON.parse(localStorage.getItem(SAVED_CONSULTANTS_KEY)||'[]'))}catch{return[]}}
export function writeSavedConsultants(items){const safe=clean(items);if(typeof window!=='undefined'){localStorage.setItem(SAVED_CONSULTANTS_KEY,JSON.stringify(safe));window.dispatchEvent(new CustomEvent('zestiva:saved-consultants',{detail:safe}))}return safe}
export function toggleSavedConsultant(slug){const items=readSavedConsultants();if(items.includes(slug))return{items:writeSavedConsultants(items.filter(item=>item!==slug)),saved:false};if(items.length>=SAVED_CONSULTANTS_LIMIT)return{items,saved:false,limit:true};return{items:writeSavedConsultants([...items,slug]),saved:true}}
export function clearSavedConsultants(){return writeSavedConsultants([])}
