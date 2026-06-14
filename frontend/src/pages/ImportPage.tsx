import { useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Upload, FileText, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { csvImport } from '../api';
import type { ImportReportOut, ImportRowResult } from '../api';

export function ImportPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [report, setReport] = useState<ImportReportOut | null>(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError('');
      setReport(null);
    }
  };

  const handleUpload = async () => {
    if (!file || !groupId) return;
    
    setIsUploading(true);
    setError('');
    try {
      const data = await csvImport.uploadCsv(groupId, file);
      setReport(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload and process CSV.');
    } finally {
      setIsUploading(false);
    }
  };

  const renderRowStatus = (row: ImportRowResult) => {
    switch (row.outcome) {
      case 'IMPORTED':
      case 'CONVERTED':
        return <CheckCircle size={16} color="var(--color-brand)" />;
      case 'SKIPPED':
        return <XCircle size={16} color="#ef4444" />;
      default:
        return <AlertCircle size={16} color="#f59e0b" />;
    }
  };

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
        <div>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
            <Link to={`/groups/${groupId}`} style={{ color: 'var(--color-brand)' }}>&larr; Back to group</Link>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Import Expenses (CSV)</h1>
        </div>
      </div>

      {!report ? (
        <div style={{ 
          maxWidth: '600px', 
          margin: '0 auto', 
          padding: '2rem',
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--color-border)',
          textAlign: 'center'
        }}>
          <div style={{ marginBottom: '2rem', color: 'var(--color-text-muted)' }}>
            <FileText size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
            <p>Select a CSV file containing your expenses to import them into this group.</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Expected columns: date, description, amount, currency, paid_by, split_among, notes
            </p>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <input 
              type="file" 
              accept=".csv" 
              onChange={handleFileChange}
              ref={fileInputRef}
              style={{ display: 'none' }}
            />
            <button 
              className="btn btn-secondary"
              onClick={() => fileInputRef.current?.click()}
            >
              {file ? file.name : 'Select CSV File'}
            </button>
          </div>

          {error && (
            <div style={{ 
              backgroundColor: '#fee2e2', 
              color: '#991b1b', 
              padding: '0.75rem', 
              borderRadius: 'var(--radius-sm)',
              marginBottom: '1rem',
              fontSize: '0.875rem',
              textAlign: 'left'
            }}>
              {error}
            </div>
          )}

          <button 
            className="btn btn-primary" 
            style={{ width: '100%' }}
            disabled={!file || isUploading}
            onClick={handleUpload}
          >
            {isUploading ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                <Upload size={18} className="animate-pulse" /> Processing...
              </span>
            ) : (
              'Upload and Import'
            )}
          </button>
        </div>
      ) : (
        <div>
          {/* Summary Card */}
          <div style={{ 
            backgroundColor: 'white',
            borderRadius: 'var(--radius-md)',
            padding: '1.5rem',
            border: '1px solid var(--color-border)',
            boxShadow: 'var(--shadow-sm)',
            marginBottom: '2rem',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '1rem'
          }}>
            <div>
              <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Total Rows</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{report.total_rows}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Successfully Imported</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--color-brand)' }}>{report.imported}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Skipped / Errors</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#ef4444' }}>{report.skipped}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Warnings Auto-Resolved</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#f59e0b' }}>{report.warning_count}</div>
            </div>
          </div>

          <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>Row Details</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {report.rows.map((row, idx) => (
              <div key={idx} style={{ 
                backgroundColor: 'white',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                borderLeft: `4px solid ${row.outcome === 'IMPORTED' || row.outcome === 'CONVERTED' ? 'var(--color-brand)' : '#ef4444'}`,
                padding: '1rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                    {renderRowStatus(row)}
                    Row {row.row_number} - {row.outcome}
                  </div>
                </div>
                
                <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
                  {Object.entries(row.raw_data).map(([key, val]) => (
                    <span key={key} style={{ marginRight: '1rem' }}>
                      <strong>{key}:</strong> {val || '-'}
                    </span>
                  ))}
                </div>

                {row.anomalies.length > 0 && (
                  <div style={{ 
                    backgroundColor: '#fffbeb', 
                    border: '1px solid #fde68a',
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.875rem',
                    color: '#b45309'
                  }}>
                    <strong style={{ display: 'block', marginBottom: '0.25rem' }}>Anomalies Detected:</strong>
                    <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                      {row.anomalies.map((anom, i) => (
                        <li key={i}>{anom}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          <div style={{ marginTop: '2rem', textAlign: 'center' }}>
            <button className="btn btn-secondary" onClick={() => setReport(null)}>
              Import Another File
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
