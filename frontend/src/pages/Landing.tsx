import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Landing() {
  const { isAuthenticated } = useAuth();

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg-surface)', display: 'flex', flexDirection: 'column' }}>
      {/* Public Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '1rem 2rem',
        borderBottom: '1px solid var(--color-border)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ 
            width: '32px', 
            height: '32px', 
            backgroundColor: 'var(--color-brand)', 
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '20px'
          }}>
            S
          </div>
          <span style={{ 
            color: 'var(--color-brand)', 
            fontSize: '1.5rem', 
            fontWeight: '700',
            letterSpacing: '-0.5px'
          }}>
            Splitly
          </span>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {isAuthenticated ? (
            <Link to="/dashboard" className="btn btn-primary">Go to Dashboard</Link>
          ) : (
            <>
              <Link to="/login" style={{ color: 'var(--color-text-main)', fontWeight: 500 }}>Log in</Link>
              <Link to="/register" className="btn btn-primary">Sign up</Link>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '4rem 2rem', textAlign: 'center' }}>
        <h1 style={{ 
          fontSize: '3.5rem', 
          fontWeight: 800, 
          color: 'var(--color-text-main)',
          maxWidth: '800px',
          lineHeight: 1.2,
          marginBottom: '1.5rem'
        }}>
          Less stress when sharing expenses <span style={{ color: 'var(--color-brand)' }}>with anyone.</span>
        </h1>
        <p style={{
          fontSize: '1.25rem',
          color: 'var(--color-text-muted)',
          maxWidth: '600px',
          marginBottom: '3rem',
          lineHeight: 1.6
        }}>
          Keep track of your shared expenses and balances with housemates, trips, groups, friends, and family.
        </p>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <Link to="/register" className="btn btn-primary" style={{ padding: '1rem 2rem', fontSize: '1.125rem', borderRadius: '8px' }}>
            Get started for free
          </Link>
        </div>
        
        {/* Placeholder for feature illustration */}
        <div style={{
          marginTop: '4rem',
          width: '100%',
          maxWidth: '800px',
          height: '400px',
          backgroundColor: '#f8f9fa',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-text-muted)'
        }}>
          [Hero Image / UI Mockup placeholder]
        </div>
      </main>

      {/* Simple Footer */}
      <footer style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.875rem', borderTop: '1px solid var(--color-border)' }}>
        &copy; 2026 Splitly Inc. All rights reserved.
      </footer>
    </div>
  );
}
