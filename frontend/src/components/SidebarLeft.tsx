import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, List, Plus, Upload, BarChart2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Group } from '../api';
import { CreateGroupModal } from './groups/CreateGroupModal';

interface SidebarLeftProps {
  groups: Group[];
}

export function SidebarLeft({ groups }: SidebarLeftProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const navItemStyle = (path: string, exact: boolean = false) => {
    const isActive = exact 
      ? location.pathname === path 
      : location.pathname.startsWith(path);
      
    return {
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      padding: '0.5rem 1rem',
      color: isActive ? 'var(--color-brand)' : 'var(--color-text-main)',
      fontWeight: isActive ? 600 : 400,
      borderLeft: isActive ? '4px solid var(--color-brand)' : '4px solid transparent',
      backgroundColor: isActive ? 'rgba(72, 190, 157, 0.05)' : 'transparent',
    };
  };

  return (
    <div style={{ padding: '1rem 0' }}>
      <nav style={{ marginBottom: '2rem' }}>
        <Link to="/dashboard" style={navItemStyle('/dashboard', true)}>
          <LayoutDashboard size={18} />
          Dashboard
        </Link>
        <Link to="/all-expenses" style={navItemStyle('/all-expenses')}>
          <List size={18} />
          All expenses
        </Link>
      </nav>

      <div style={{ padding: '0 1rem' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '0.5rem',
          color: 'var(--color-text-muted)',
          fontSize: '0.75rem',
          fontWeight: 600,
          letterSpacing: '0.5px'
        }}>
          <span>GROUPS</span>
          <button 
            onClick={() => setIsCreateModalOpen(true)}
            style={{ color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '2px', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            <Plus size={14} /> add
          </button>
        </div>
        
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {groups.map(g => (
            <li key={g.id}>
              <Link 
                to={`/groups/${g.id}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.375rem 0.5rem',
                  color: location.pathname === `/groups/${g.id}` ? 'var(--color-text-main)' : 'var(--color-text-muted)',
                  fontWeight: location.pathname === `/groups/${g.id}` ? 600 : 400,
                  fontSize: '0.875rem',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: location.pathname === `/groups/${g.id}` ? '#ebebeb' : 'transparent',
                }}
              >
                {/* Generic group icon circle */}
                <div style={{ 
                  width: '20px', 
                  height: '20px', 
                  borderRadius: '4px', 
                  backgroundColor: '#ccc',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '10px'
                }}>
                  {g.name.charAt(0).toUpperCase()}
                </div>
                {g.name}
              </Link>
              {/* Show sub-links if this group is active */}
              {location.pathname.startsWith(`/groups/${g.id}`) && (
                <div style={{ paddingLeft: '2.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem', marginTop: '0.25rem' }}>
                  <Link
                    to={`/groups/${g.id}/import`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.25rem 0.5rem',
                      color: location.pathname === `/groups/${g.id}/import` ? 'var(--color-brand)' : 'var(--color-text-muted)',
                      fontSize: '0.8rem',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <Upload size={14} /> Import CSV
                  </Link>
                  <Link
                    to={`/groups/${g.id}/reports`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.25rem 0.5rem',
                      color: location.pathname === `/groups/${g.id}/reports` ? 'var(--color-brand)' : 'var(--color-text-muted)',
                      fontSize: '0.8rem',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <BarChart2 size={14} /> Reports
                  </Link>
                </div>
              )}
            </li>
          ))}
          {groups.length === 0 && (
            <li style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
              No groups yet.
            </li>
          )}
        </ul>
      </div>

      <CreateGroupModal 
        isOpen={isCreateModalOpen} 
        onClose={() => setIsCreateModalOpen(false)} 
        onSuccess={(newGroupId) => {
          navigate(`/groups/${newGroupId}`);
          // The MainLayout will ideally trigger a refetch of groups since location changed, 
          // or we can rely on a global refresh if implemented, but navigating to it is a good start.
          // Wait, we need MainLayout to refetch. For now, navigate forces a route change.
          // A full window reload might be needed if MainLayout doesn't refetch on route change.
          window.location.href = `/groups/${newGroupId}`;
        }} 
      />
    </div>
  );
}
