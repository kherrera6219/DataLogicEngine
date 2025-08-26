
import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import ComplianceSpiderweb from '../components/ui/ComplianceSpiderweb';

export default function CompliancePage() {
  const [standardTypes, setStandardTypes] = useState([]);
  const [selectedType, setSelectedType] = useState('');
  const [standards, setStandards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedStandard, setSelectedStandard] = useState(null);
  
  useEffect(() => {
    // Fetch all standard types when component mounts
    fetchStandardTypes();
  }, []);
  
  useEffect(() => {
    // Fetch standards when selected type changes
    if (!selectedType) return;

    const fetchStandards = async (type) => {
      try {
        setLoading(true);
        const response = await fetch(`/api/compliance/standards?type=${type}`);
        const data = await response.json();

        if (data.status === 'success') {
          const standardsList = [];

          // Extract standards from hierarchy
          if (data.hierarchy) {
            Object.values(data.hierarchy).forEach(mega => {
              standardsList.push(mega.standard);

              if (mega.large_standards) {
                Object.values(mega.large_standards).forEach(large => {
                  standardsList.push(large.standard);
                });
              }
            });
          }

          setStandards(standardsList);

          // Select the first standard by default
          if (standardsList.length > 0 && !selectedStandard) {
            setSelectedStandard(standardsList[0].id);
          }
        } else {
          setError(data.message || 'Failed to load standards');
        }
      } catch (err) {
        setError('Error fetching standards: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStandards(selectedType);
  }, [selectedType, selectedStandard]);

  const fetchStandardTypes = async () => {
    try {
      setLoading(true);
      // In a real implementation, you would fetch this from the API
      const types = [
        { id: 'iso', name: 'ISO Standards' },
        { id: 'nist', name: 'NIST Standards' },
        { id: 'pci', name: 'PCI Standards' },
        { id: 'hipaa', name: 'HIPAA Standards' },
        { id: 'gdpr', name: 'GDPR Standards' }
      ];
      setStandardTypes(types);
      setSelectedType(types[0].id);
    } catch (err) {
      setError('Error fetching standard types: ' + err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleTypeChange = (e) => {
    setSelectedType(e.target.value);
    setSelectedStandard(null);
  };
  
  const handleStandardChange = (e) => {
    setSelectedStandard(e.target.value);
  };
  
  return (
    <Layout>
      <Head>
        <title>Compliance Standards | UKG System</title>
      </Head>
      
      <div className="container mt-4">
        <h1>Compliance Standards</h1>
        <p className="lead">Explore the Spiderweb structure of Compliance Standards (Axis 7)</p>
        
        <div className="row mt-4">
          <div className="col-md-3">
            <div className="card">
              <div className="card-header">
                <h5 className="card-title mb-0">Filters</h5>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <label htmlFor="standardType" className="form-label">Standard Type</label>
                  <select 
                    id="standardType" 
                    className="form-select"
                    value={selectedType}
                    onChange={handleTypeChange}
                  >
                    <option value="">Select a type</option>
                    {standardTypes.map(type => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>
                
                <div className="mb-3">
                  <label htmlFor="standard" className="form-label">Standard</label>
                  <select 
                    id="standard" 
                    className="form-select"
                    value={selectedStandard || ''}
                    onChange={handleStandardChange}
                    disabled={loading || standards.length === 0}
                  >
                    <option value="">Select a standard</option>
                    {standards.map(std => (
                      <option key={std.id} value={std.id}>{std.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            <div className="card mt-3">
              <div className="card-header">
                <h5 className="card-title mb-0">Spiderweb Structure</h5>
              </div>
              <div className="card-body">
                <p className="small">The spiderweb structure represents compliance standards with:</p>
                <ul className="small">
                  <li><strong>Mega:</strong> Top-level frameworks</li>
                  <li><strong>Large:</strong> Primary standards</li>
                  <li><strong>Medium:</strong> Standard domains</li>
                  <li><strong>Small:</strong> Individual controls</li>
                  <li><strong>Granular:</strong> Detailed requirements</li>
                </ul>
              </div>
            </div>
          </div>
          
          <div className="col-md-9">
            {loading ? (
              <div className="text-center p-5">
                <div className="spinner-border" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <p className="mt-2">Loading compliance data...</p>
              </div>
            ) : error ? (
              <div className="alert alert-danger">{error}</div>
            ) : selectedStandard ? (
              <ComplianceSpiderweb standardId={selectedStandard} />
            ) : (
              <div className="alert alert-info">Select a standard to view its spiderweb structure</div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
