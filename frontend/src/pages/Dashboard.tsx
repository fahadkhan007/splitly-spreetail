import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { groups as groupsApi } from '../api';
import type { Group } from '../api';

export function Dashboard() {
  const { user } = useAuth();
  const [groups, setGroups] = useState<Group[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    groupsApi.getGroups()
      .then(setGroups)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
        borderBottom: '1px solid var(--color-border)',
        paddingBottom: '1rem'
      }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Dashboard</h1>
      </div>

      <p style={{ color: 'var(--color-text-muted)', marginBottom: '2rem' }}>
        Welcome back, {user?.display_name}. Here are your active groups:
      </p>

      {isLoading ? (
        <div>Loading groups...</div>
      ) : groups.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem 0' }}>
          <h2 style={{ fontSize: '1.25rem', color: 'var(--color-text-main)', marginBottom: '0.5rem' }}>
            You are not in any groups yet
          </h2>
          <p style={{ color: 'var(--color-text-muted)' }}>
            Create a new group or ask a friend to invite you.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
          {groups.map(g => (
            <Link 
              key={g.id} 
              to={`/groups/${g.id}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '1rem',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-text-main)',
                backgroundColor: 'white',
                boxShadow: 'var(--shadow-sm)',
                transition: 'transform 0.2s, box-shadow 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = 'var(--shadow-md)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
              }}
            >
              <div style={{ 
                width: '40px', 
                height: '40px', 
                borderRadius: '8px', 
                backgroundColor: '#333',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '18px',
                marginRight: '1rem'
              }}>
                {g.name.charAt(0).toUpperCase()}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '1.125rem' }}>{g.name}</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Base currency: {g.base_currency}</div>
              </div>
              <div style={{ color: 'var(--color-brand)', fontWeight: 500, fontSize: '0.875rem' }}>
                View group &rarr;
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
