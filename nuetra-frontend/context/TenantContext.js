import React, { createContext, useContext, useMemo } from 'react';
import { useAuth } from './AuthContext';

const TenantContext=createContext({currentTenant:null,tenantId:null,tenantName:null,tenantType:null,currentMembershipRole:null});

export function TenantProvider({children}){
  const {user}=useAuth();
  const currentTenant=user?.currentTenant??null;
  const value=useMemo(()=>({
    currentTenant,
    tenantId:currentTenant?.tenantId??null,
    tenantName:currentTenant?.tenantName??null,
    tenantType:currentTenant?.tenantType??null,
    currentMembershipRole:currentTenant?.currentMembershipRole??null,
  }),[currentTenant]);
  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export const useTenant=()=>useContext(TenantContext);
