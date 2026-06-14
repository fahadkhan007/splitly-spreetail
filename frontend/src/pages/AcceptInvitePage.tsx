import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { groups } from '../api';
import { useAuth } from '../context/AuthContext';
import { CheckCircle, XCircle } from 'lucide-react';

export function AcceptInvitePage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { user } = useAuth();

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setErrorMsg('No invitation token provided in the URL.');
      return;
    }

    if (!user) {
      // User is not logged in. They should be redirected to login, and then back here.
      // But typically React Router PrivateRoute handles that if this is inside MainLayout.
      // Let's assume they are logged in since this will be inside MainLayout.
      return;
    }

    groups.acceptInvite(token)
      .then(() => {
        setStatus('success');
      })
      .catch((err) => {
        setStatus('error');
        setErrorMsg(err.response?.data?.detail || 'Failed to accept invitation. It may be invalid or expired.');
      });
  }, [token, user]);

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: 'var(--color-bg-main)'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '3rem',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-md)',
        maxWidth: '400px',
        width: '100%',
        textAlign: 'center'
      }}>
        {status === 'loading' && (
          <div>
            <div style={{ marginBottom: '1rem', color: 'var(--color-text-muted)' }}>
              Verifying invitation...
            </div>
          </div>
        )}

        {status === 'success' && (
          <div>
            <CheckCircle size={48} color="var(--color-brand)" style={{ margin: '0 auto 1rem' }} />
            <h1 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Invitation Accepted!</h1>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '2rem' }}>
              You have successfully joined the group.
            </p>
            <button className="btn btn-primary" onClick={() => navigate('/dashboard')} style={{ width: '100%' }}>
              Go to Dashboard
            </button>
          </div>
        )}

        {status === 'error' && (
          <div>
            <XCircle size={48} color="#ef4444" style={{ margin: '0 auto 1rem' }} />
            <h1 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Invitation Failed</h1>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '2rem' }}>
              {errorMsg}
            </p>
            <Link to="/dashboard" className="btn btn-secondary" style={{ display: 'block', width: '100%', boxSizing: 'border-box' }}>
              Return to Dashboard
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
