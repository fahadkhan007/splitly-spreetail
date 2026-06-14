import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, User as UserIcon } from 'lucide-react';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header style={{
      backgroundColor: 'var(--color-brand)',
      color: 'var(--color-header-text)',
      height: '56px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2rem',
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 100,
      boxShadow: 'var(--shadow-sm)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {/* Simple logo treatment */}
        <div style={{ 
          width: '28px', 
          height: '28px', 
          backgroundColor: 'white', 
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-brand)',
          fontWeight: 'bold',
          fontSize: '18px'
        }}>
          S
        </div>
        <Link to="/dashboard" style={{ 
          color: 'white', 
          fontSize: '1.25rem', 
          fontWeight: '700',
          letterSpacing: '-0.5px'
        }}>
          Splitly
        </Link>
      </div>

      {user && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: 'rgba(255,255,255,0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <UserIcon size={18} color="white" />
            </div>
            <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>
              {user.display_name}
            </span>
          </div>
          <button 
            onClick={logout}
            style={{ 
              color: 'rgba(255,255,255,0.8)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
              fontSize: '0.875rem'
            }}
            title="Log out"
          >
            <LogOut size={16} />
          </button>
        </div>
      )}
    </header>
  );
}
