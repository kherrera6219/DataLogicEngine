
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button, Card, Form, Spinner } from 'react-bootstrap';

const LocationMap = ({ initialLocations }) => {
  const [locations, setLocations] = useState(initialLocations || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [searchCriteria, setSearchCriteria] = useState({
    name: '',
    type: '',
    lat: '',
    lng: '',
    radius: '50',
  });
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'hierarchy'
  const [hierarchy, setHierarchy] = useState([]);
  const mapRef = useRef(null);
  const googleMapRef = useRef(null);
  const markersRef = useRef([]);

  const fetchLocations = useCallback(async (params = {}) => {
    setLoading(true);
    setError(null);

    try {
      // Build query string from params
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value) queryParams.append(key, value);
      });

      const response = await fetch(`/api/locations?${queryParams.toString()}`);
      const data = await response.json();

      if (data.success) {
        setLocations(data.locations || []);
      } else {
        setError(data.error || 'Failed to fetch locations');
      }
    } catch (err) {
      setError('Error fetching locations: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch locations on initial load
  useEffect(() => {
    fetchLocations();
  }, [fetchLocations]);

  const initializeMap = useCallback(() => {
    if (!mapRef.current) return;

    // Get center coordinates from first location or use default
    let center = { lat: 0, lng: 0 };
    let bounds = new window.google.maps.LatLngBounds();
    let hasValidCoordinates = false;

    locations.forEach(location => {
      if (location.latitude && location.longitude) {
        bounds.extend({ lat: location.latitude, lng: location.longitude });
        hasValidCoordinates = true;
      }
    });

    if (!hasValidCoordinates) {
      center = { lat: 39.8283, lng: -98.5795 }; // Center of US as default
    }

    // Create map
    googleMapRef.current = new window.google.maps.Map(mapRef.current, {
      center: center,
      zoom: 4,
      mapTypeId: 'roadmap'
    });

    // Add markers for each location
    markersRef.current = locations
      .filter(loc => loc.latitude && loc.longitude)
      .map(location => {
        const marker = new window.google.maps.Marker({
          position: { lat: location.latitude, lng: location.longitude },
          map: googleMapRef.current,
          title: location.name,
          animation: window.google.maps.Animation.DROP
        });

        // Add click listener
        marker.addListener('click', () => {
          setSelectedLocation(location);
        });

        return marker;
      });

    // Fit map to bounds if we have coordinates
    if (hasValidCoordinates) {
      googleMapRef.current.fitBounds(bounds);
    }
  }, [locations]);

  // Initialize map when locations are loaded
  useEffect(() => {
    if (locations.length > 0 && viewMode === 'map' && window.google && window.google.maps) {
      initializeMap();
    }
  }, [locations, viewMode, initializeMap]);

  // Load Google Maps API
  useEffect(() => {
    if (viewMode === 'map' && !window.google) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places`;
      script.async = true;
      script.defer = true;
      script.onload = () => {
        if (locations.length > 0) {
          initializeMap();
        }
      };
      document.head.appendChild(script);

      return () => {
        document.head.removeChild(script);
      };
    }
  }, [viewMode, initializeMap, locations.length]);

  const fetchHierarchy = async (rootUid = null) => {
    setLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams();
      if (rootUid) {
        queryParams.append('root_uid', rootUid);
      }

      const response = await fetch(`/api/locations/hierarchy?${queryParams.toString()}`);
      const data = await response.json();

      if (data.success) {
        setHierarchy(data.hierarchies || [data.hierarchy] || []);
        setViewMode('hierarchy');
      } else {
        setError(data.error || 'Failed to fetch location hierarchy');
      }
    } catch (err) {
      setError('Error fetching hierarchy: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchLocations(searchCriteria);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSearchCriteria(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const renderHierarchyNode = (node, level = 0) => {
    return (
      <div key={node.uid} className="location-hierarchy-node mb-2">
        <div 
          className="d-flex align-items-center" 
          style={{ paddingLeft: `${level * 20}px` }}
        >
          <i className={`bi bi-geo-alt me-2 ${level === 0 ? 'text-primary' : ''}`}></i>
          <span 
            className={`location-name ${level === 0 ? 'fw-bold' : ''}`}
            onClick={() => setSelectedLocation(node)}
            style={{ cursor: 'pointer' }}
          >
            {node.name} 
            <span className="text-muted ms-2 small">
              ({node.location_type})
            </span>
          </span>
        </div>
        
        {node.children && node.children.length > 0 && (
          <div className="children-container">
            {node.children.map(child => renderHierarchyNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="location-manager">
      <div className="d-flex justify-content-between mb-4">
        <h2>Location Management (Axis 12)</h2>
        <div className="btn-group">
          <Button 
            variant={viewMode === 'list' ? 'primary' : 'outline-primary'}
            onClick={() => setViewMode('list')}
          >
            <i className="bi bi-list me-1"></i> List View
          </Button>
          <Button 
            variant={viewMode === 'map' ? 'primary' : 'outline-primary'}
            onClick={() => setViewMode('map')}
          >
            <i className="bi bi-map me-1"></i> Map View
          </Button>
          <Button 
            variant={viewMode === 'hierarchy' ? 'primary' : 'outline-primary'}
            onClick={() => fetchHierarchy()}
          >
            <i className="bi bi-diagram-3 me-1"></i> Hierarchy
          </Button>
        </div>
      </div>

      <div className="row">
        <div className="col-md-4">
          <Card className="mb-4">
            <Card.Header>Location Search</Card.Header>
            <Card.Body>
              <Form onSubmit={handleSearchSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Name</Form.Label>
                  <Form.Control 
                    type="text" 
                    name="name" 
                    placeholder="Search by name"
                    value={searchCriteria.name}
                    onChange={handleInputChange}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Type</Form.Label>
                  <Form.Select 
                    name="type" 
                    value={searchCriteria.type}
                    onChange={handleInputChange}
                  >
                    <option value="">All Types</option>
                    <option value="Country">Country</option>
                    <option value="State">State/Province</option>
                    <option value="City">City</option>
                    <option value="County">County</option>
                    <option value="Region">Region</option>
                    <option value="SupranationalRegion">Supranational Region</option>
                  </Form.Select>
                </Form.Group>

                <div className="row">
                  <div className="col-6">
                    <Form.Group className="mb-3">
                      <Form.Label>Latitude</Form.Label>
                      <Form.Control 
                        type="number" 
                        name="lat" 
                        placeholder="e.g. 40.7128"
                        value={searchCriteria.lat}
                        onChange={handleInputChange}
                        step="any"
                      />
                    </Form.Group>
                  </div>
                  <div className="col-6">
                    <Form.Group className="mb-3">
                      <Form.Label>Longitude</Form.Label>
                      <Form.Control 
                        type="number" 
                        name="lng" 
                        placeholder="e.g. -74.0060"
                        value={searchCriteria.lng}
                        onChange={handleInputChange}
                        step="any"
                      />
                    </Form.Group>
                  </div>
                </div>

                <Form.Group className="mb-3">
                  <Form.Label>Radius (km)</Form.Label>
                  <Form.Control 
                    type="number" 
                    name="radius" 
                    placeholder="Search radius in km"
                    value={searchCriteria.radius}
                    onChange={handleInputChange}
                    min="1"
                    max="5000"
                  />
                </Form.Group>

                <div className="d-grid">
                  <Button variant="primary" type="submit" disabled={loading}>
                    {loading ? <Spinner size="sm" animation="border" /> : <i className="bi bi-search me-1"></i>}
                    Search Locations
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>

          {selectedLocation && (
            <Card className="location-details">
              <Card.Header className="d-flex justify-content-between align-items-center">
                <span>Location Details</span>
                <Button 
                  variant="link" 
                  className="p-0 text-muted" 
                  onClick={() => setSelectedLocation(null)}
                >
                  <i className="bi bi-x-lg"></i>
                </Button>
              </Card.Header>
              <Card.Body>
                <h4>{selectedLocation.name}</h4>
                <p className="text-muted">{selectedLocation.location_type}</p>
                
                {selectedLocation.latitude && selectedLocation.longitude && (
                  <p>
                    <strong>Coordinates:</strong> {selectedLocation.latitude}, {selectedLocation.longitude}
                  </p>
                )}
                
                {selectedLocation.attributes && Object.keys(selectedLocation.attributes).length > 0 && (
                  <div className="mt-3">
                    <h5>Attributes</h5>
                    <ul className="list-unstyled">
                      {Object.entries(selectedLocation.attributes).map(([key, value]) => (
                        <li key={key} className="mb-1">
                          <strong>{key}:</strong> {
                            typeof value === 'object' 
                              ? JSON.stringify(value) 
                              : value
                          }
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {selectedLocation.parent && (
                  <div className="mt-3">
                    <h5>Parent Location</h5>
                    <p 
                      className="mb-0 cursor-pointer" 
                      onClick={() => setSelectedLocation(selectedLocation.parent)}
                      style={{ cursor: 'pointer' }}
                    >
                      <i className="bi bi-arrow-up-right me-1"></i>
                      {selectedLocation.parent.name} ({selectedLocation.parent.location_type})
                    </p>
                  </div>
                )}

                {selectedLocation.children && selectedLocation.children.length > 0 && (
                  <div className="mt-3">
                    <h5>Sub-Locations ({selectedLocation.children.length})</h5>
                    <ul className="list-unstyled">
                      {selectedLocation.children.slice(0, 5).map(child => (
                        <li key={child.uid} className="mb-1">
                          <span 
                            className="cursor-pointer" 
                            onClick={() => setSelectedLocation(child)}
                            style={{ cursor: 'pointer' }}
                          >
                            <i className="bi bi-geo-alt-fill me-1 small"></i>
                            {child.name} ({child.location_type})
                          </span>
                        </li>
                      ))}
                      {selectedLocation.children.length > 5 && (
                        <li className="text-muted small">
                          + {selectedLocation.children.length - 5} more locations
                        </li>
                      )}
                    </ul>
                  </div>
                )}

                <div className="mt-3 d-grid gap-2">
                  <Button 
                    variant="outline-primary" 
                    size="sm"
                    onClick={() => fetchHierarchy(selectedLocation.uid)}
                  >
                    <i className="bi bi-diagram-3 me-1"></i>
                    View in Hierarchy
                  </Button>
                </div>
              </Card.Body>
            </Card>
          )}
        </div>

        <div className="col-md-8">
          {error && (
            <div className="alert alert-danger">
              <i className="bi bi-exclamation-triangle me-2"></i>
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-center my-5">
              <Spinner animation="border" />
              <p className="mt-2">Loading location data...</p>
            </div>
          ) : (
            <>
              {viewMode === 'list' && (
                <div className="location-list">
                  <Card>
                    <Card.Header>
                      <div className="d-flex justify-content-between align-items-center">
                        <span>Locations ({locations.length})</span>
                        <div>
                          <Form.Select 
                            size="sm" 
                            className="d-inline-block" 
                            style={{ width: 'auto' }}
                            onChange={(e) => {
                              setSearchCriteria(prev => ({
                                ...prev,
                                type: e.target.value
                              }));
                              fetchLocations({
                                ...searchCriteria,
                                type: e.target.value
                              });
                            }}
                            value={searchCriteria.type}
                          >
                            <option value="">All Types</option>
                            <option value="Country">Countries</option>
                            <option value="State">States/Provinces</option>
                            <option value="City">Cities</option>
                            <option value="County">Counties</option>
                            <option value="Region">Regions</option>
                          </Form.Select>
                        </div>
                      </div>
                    </Card.Header>
                    <div className="table-responsive">
                      <table className="table table-hover mb-0">
                        <thead>
                          <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Coordinates</th>
                            {searchCriteria.lat && searchCriteria.lng && (
                              <th>Distance</th>
                            )}
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {locations.length === 0 ? (
                            <tr>
                              <td colSpan="5" className="text-center py-3">
                                <i className="bi bi-inbox me-2"></i>
                                No locations found
                              </td>
                            </tr>
                          ) : (
                            locations.map(location => (
                              <tr 
                                key={location.uid}
                                onClick={() => setSelectedLocation(location)}
                                style={{ cursor: 'pointer' }}
                                className={selectedLocation?.uid === location.uid ? 'table-primary' : ''}
                              >
                                <td>{location.name}</td>
                                <td>
                                  <span className="badge bg-secondary">
                                    {location.location_type}
                                  </span>
                                </td>
                                <td>
                                  {location.latitude && location.longitude ? (
                                    <small>{location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}</small>
                                  ) : (
                                    <span className="text-muted">N/A</span>
                                  )}
                                </td>
                                {searchCriteria.lat && searchCriteria.lng && (
                                  <td>
                                    {location.distance !== undefined ? (
                                      <span>{location.distance.toFixed(1)} km</span>
                                    ) : (
                                      <span className="text-muted">N/A</span>
                                    )}
                                  </td>
                                )}
                                <td>
                                  <Button 
                                    size="sm" 
                                    variant="link"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setSelectedLocation(location);
                                    }}
                                  >
                                    <i className="bi bi-info-circle"></i>
                                  </Button>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                </div>
              )}

              {viewMode === 'map' && (
                <Card>
                  <Card.Header>Location Map</Card.Header>
                  <Card.Body className="p-0">
                    <div 
                      ref={mapRef} 
                      style={{ height: '600px', width: '100%' }}
                      className="location-map"
                    >
                      {!window.google && (
                        <div className="text-center p-5">
                          <p>Loading map...</p>
                          <Spinner animation="border" />
                        </div>
                      )}
                    </div>
                  </Card.Body>
                </Card>
              )}

              {viewMode === 'hierarchy' && (
                <Card>
                  <Card.Header>Location Hierarchy</Card.Header>
                  <Card.Body>
                    {hierarchy.length === 0 ? (
                      <div className="text-center py-3">
                        <p>No hierarchy data available</p>
                      </div>
                    ) : (
                      <div className="location-hierarchy">
                        {hierarchy.map(node => renderHierarchyNode(node))}
                      </div>
                    )}
                  </Card.Body>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default LocationMap;
