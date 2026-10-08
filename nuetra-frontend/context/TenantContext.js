import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from './AuthContext';
import { getFiteatsyTenantContext } from '../lib/fiteatsyConsultantsApi';
import { normalizeCanonicalTenant, TENANT_CONTEXT_STATUS } from '../lib/tenantContext.mjs';

const TenantContext=createContext({
  currentTenant:null,tenantId:null,tenantName:null,tenantType:null,currentMembershipRole:null,
  membershipStatus:null,status:TENANT_CONTEXT_STATUS.IDLE,error:null,
});

export function TenantProvider({children}){
  const {user,isLoading:authLoading,isBackendAuthEnabled}=useAuth();
  const [state,setState]=useState({currentTenant:null,status:TENANT_CONTEXT_STATUS.IDLE,error:null});
  const requestGeneration=useRef(0);

  useEffect(()=>{
    const generation=++requestGeneration.current;
    const controller=new AbortController();

    if(authLoading){
      setState({currentTenant:null,status:TENANT_CONTEXT_STATUS.LOADING,error:null});
      return ()=>controller.abort();
    }
    if(!user){
      setState({currentTenant:null,status:TENANT_CONTEXT_STATUS.IDLE,error:null});
      return ()=>controller.abort();
    }

    const embedded=normalizeCanonicalTenant({currentTenant:user.currentTenant});
    if(embedded&&!isBackendAuthEnabled){
      setState({currentTenant:embedded,status:TENANT_CONTEXT_STATUS.READY,error:null});
      return ()=>controller.abort();
    }

    setState({currentTenant:null,status:TENANT_CONTEXT_STATUS.LOADING,error:null});
    getFiteatsyTenantContext(controller.signal).then(payload=>{
      if(generation!==requestGeneration.current)return;
      const currentTenant=normalizeCanonicalTenant(payload);
      setState(currentTenant
        ?{currentTenant,status:TENANT_CONTEXT_STATUS.READY,error:null}
        :{currentTenant:null,status:TENANT_CONTEXT_STATUS.UNAVAILABLE,error:'NO_ACTIVE_MEMBERSHIP'});
    }).catch(error=>{
      if(controller.signal.aborted||generation!==requestGeneration.current)return;
      setState({currentTenant:null,status:TENANT_CONTEXT_STATUS.UNAVAILABLE,error:error?.message||'TENANT_CONTEXT_UNAVAILABLE'});
    });
    return ()=>controller.abort();
  },[authLoading,isBackendAuthEnabled,user?.id]);

  const {currentTenant,status,error}=state;
  const value=useMemo(()=>({
    currentTenant,
    tenantId:currentTenant?.tenantId??null,
    tenantName:currentTenant?.tenantName??null,
    tenantType:currentTenant?.tenantType??null,
    currentMembershipRole:currentTenant?.currentMembershipRole??null,
    membershipStatus:currentTenant?.membershipStatus??null,
    status,
    error,
  }),[currentTenant,status,error]);
  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export const useTenant=()=>useContext(TenantContext);
