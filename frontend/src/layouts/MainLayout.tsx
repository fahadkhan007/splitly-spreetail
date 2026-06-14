import { useEffect, useState } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Header } from '../components/Header';
import { SidebarLeft } from '../components/SidebarLeft';
import { groups as groupsApi } from '../api';
import type { Group } from '../api';

export function MainLayout() {
  const { isAuthenticated, isLoading } = useAuth();
  const [groups, setGroups] = useState<Group[]>([]);

  useEffect(() => {
    if (isAuthenticated) {
      groupsApi.getGroups()
        .then(setGroups)
        .catch(console.error);
    }
  }, [isAuthenticated]);

  if (isLoading) {
    return <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center' }}>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header />
      
      {/* 56px matches the Header height */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center',
        paddingTop: '56px',
        flex: 1,
      }}>
        {/* Main Content Wrapper - constrained width */}
        <div style={{ 
          display: 'flex', 
          width: '100%', 
          maxWidth: '1000px', 
          padding: '0 1rem' 
        }}>
          
          {/* Left Column (Navigation & Groups) */}
          <aside style={{ 
            width: '220px', 
            flexShrink: 0,
            paddingRight: '1rem' 
          }}>
            <SidebarLeft groups={groups} />
          </aside>

          {/* Center Column (Main Content Area) */}
          <main style={{ 
            flex: 1, 
            backgroundColor: 'var(--color-bg-surface)',
            boxShadow: '0 0 10px rgba(0,0,0,0.02)',
            minHeight: 'calc(100vh - 56px)',
            borderLeft: '1px solid var(--color-border)',
            borderRight: '1px solid var(--color-border)'
          }}>
            <Outlet />
          </main>

        </div>
      </div>
    </div>
  );
}
