import React, { createContext, useContext, useState, useReducer } from 'react';
import axios from 'axios';

// Initial state for UKG operations
const initialState = {
  loading: false,
  error: null,
  simulationResults: null,
  graphData: null,
  activeLayer: 0,
  confidenceThreshold: 0.85,
  refinementSteps: 12,
  systemSettings: null,
  lastQuery: null,
  lastResponse: null,
  history: []
};

// Actions for UKG operations
const UKG_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_SIMULATION_RESULTS: 'SET_SIMULATION_RESULTS',
  SET_GRAPH_DATA: 'SET_GRAPH_DATA',
  SET_ACTIVE_LAYER: 'SET_ACTIVE_LAYER',
  SET_CONFIDENCE_THRESHOLD: 'SET_CONFIDENCE_THRESHOLD',
  SET_REFINEMENT_STEPS: 'SET_REFINEMENT_STEPS',
  SET_SYSTEM_SETTINGS: 'SET_SYSTEM_SETTINGS',
  SET_QUERY_RESPONSE: 'SET_QUERY_RESPONSE',
  ADD_TO_HISTORY: 'ADD_TO_HISTORY',
  CLEAR_ERROR: 'CLEAR_ERROR',
  RESET_STATE: 'RESET_STATE'
};

// Reducer for UKG operations
const ukgReducer = (state, action) => {
  switch (action.type) {
    case UKG_ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload };
    case UKG_ACTIONS.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
    case UKG_ACTIONS.SET_SIMULATION_RESULTS:
      return { ...state, simulationResults: action.payload, loading: false };
    case UKG_ACTIONS.SET_GRAPH_DATA:
      return { ...state, graphData: action.payload };
    case UKG_ACTIONS.SET_ACTIVE_LAYER:
      return { ...state, activeLayer: action.payload };
    case UKG_ACTIONS.SET_CONFIDENCE_THRESHOLD:
      return { ...state, confidenceThreshold: action.payload };
    case UKG_ACTIONS.SET_REFINEMENT_STEPS:
      return { ...state, refinementSteps: action.payload };
    case UKG_ACTIONS.SET_SYSTEM_SETTINGS:
      return { ...state, systemSettings: action.payload };
    case UKG_ACTIONS.SET_QUERY_RESPONSE:
      return { 
        ...state, 
        lastQuery: action.payload.query, 
        lastResponse: action.payload.response,
        loading: false
      };
    case UKG_ACTIONS.ADD_TO_HISTORY:
      return { 
        ...state, 
        history: [...state.history, action.payload]
      };
    case UKG_ACTIONS.CLEAR_ERROR:
      return { ...state, error: null };
    case UKG_ACTIONS.RESET_STATE:
      return { ...initialState };
    default:
      return state;
  }
};

// Create context
const UKGContext = createContext();

// UKG Provider component
export const UKGProvider = ({ children }) => {
  const [state, dispatch] = useReducer(ukgReducer, initialState);
  
  // Run a knowledge query through the UKG system
  const runQuery = async (query, options = {}) => {
    dispatch({ type: UKG_ACTIONS.SET_LOADING, payload: true });
    dispatch({ type: UKG_ACTIONS.CLEAR_ERROR });
    
    try {
      const response = await axios.post('/api/query', {
        query,
        confidenceThreshold: options.confidenceThreshold || state.confidenceThreshold,
        refinementSteps: options.refinementSteps || state.refinementSteps,
        maxLayer: options.maxLayer || state.activeLayer,
        includeGraph: options.includeGraph || false
      });
      
      // Handle response
      dispatch({ 
        type: UKG_ACTIONS.SET_QUERY_RESPONSE, 
        payload: {
          query,
          response: response.data.response
        }
      });
      
      // Add to history
      const historyItem = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        query,
        response: response.data.response,
        confidenceScore: response.data.confidenceScore,
        activeLayer: response.data.activeLayer,
        elapsedTime: response.data.elapsedTime
      };
      
      dispatch({ 
        type: UKG_ACTIONS.ADD_TO_HISTORY, 
        payload: historyItem
      });
      
      // If graph data was requested
      if (options.includeGraph && response.data.graphData) {
        dispatch({ 
          type: UKG_ACTIONS.SET_GRAPH_DATA, 
          payload: response.data.graphData
        });
      }
      
      return {
        success: true,
        data: response.data
      };
      
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to process query';
      dispatch({ type: UKG_ACTIONS.SET_ERROR, payload: errorMessage });
      
      return {
        success: false,
        error: errorMessage
      };
    }
  };
  
  // Run a simulation with the UKG system
  const runSimulation = async (simulationParams) => {
    dispatch({ type: UKG_ACTIONS.SET_LOADING, payload: true });
    dispatch({ type: UKG_ACTIONS.CLEAR_ERROR });
    
    try {
      const response = await axios.post('/api/simulation/run', simulationParams);
      
      dispatch({ 
        type: UKG_ACTIONS.SET_SIMULATION_RESULTS, 
        payload: response.data
      });
      
      if (response.data.graphData) {
        dispatch({ 
          type: UKG_ACTIONS.SET_GRAPH_DATA, 
          payload: response.data.graphData
        });
      }
      
      return {
        success: true,
        data: response.data
      };
      
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Simulation failed';
      dispatch({ type: UKG_ACTIONS.SET_ERROR, payload: errorMessage });
      
      return {
        success: false,
        error: errorMessage
      };
    }
  };
  
  // Get graph data for visualization
  const getGraphData = async (params = {}) => {
    dispatch({ type: UKG_ACTIONS.SET_LOADING, payload: true });
    
    try {
      const response = await axios.get('/api/graph', { params });
      
      dispatch({ 
        type: UKG_ACTIONS.SET_GRAPH_DATA, 
        payload: response.data
      });
      
      dispatch({ type: UKG_ACTIONS.SET_LOADING, payload: false });
      return {
        success: true,
        data: response.data
      };
      
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to fetch graph data';
      dispatch({ type: UKG_ACTIONS.SET_ERROR, payload: errorMessage });
      
      return {
        success: false,
        error: errorMessage
      };
    }
  };
  
  // Get system settings
  const getSystemSettings = async () => {
    try {
      const response = await axios.get('/api/settings');
      
      dispatch({ 
        type: UKG_ACTIONS.SET_SYSTEM_SETTINGS, 
        payload: response.data
      });
      
      return {
        success: true,
        data: response.data
      };
      
    } catch (error) {
      console.error('Failed to fetch system settings:', error);
      return {
        success: false,
        error: 'Failed to fetch system settings'
      };
    }
  };
  
  // Update system settings
  const updateSystemSettings = async (newSettings) => {
    dispatch({ type: UKG_ACTIONS.SET_LOADING, payload: true });
    
    try {
      const response = await axios.put('/api/settings', newSettings);
      
      dispatch({ 
        type: UKG_ACTIONS.SET_SYSTEM_SETTINGS, 
        payload: response.data
      });
      
      dispatch({ type: UKG_ACTIONS.SET_LOADING, payload: false });
      return {
        success: true,
        data: response.data
      };
      
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to update system settings';
      dispatch({ type: UKG_ACTIONS.SET_ERROR, payload: errorMessage });
      
      return {
        success: false,
        error: errorMessage
      };
    }
  };
  
  // Set active layer for simulations
  const setActiveLayer = (layerNumber) => {
    dispatch({ 
      type: UKG_ACTIONS.SET_ACTIVE_LAYER, 
      payload: layerNumber
    });
  };
  
  // Set confidence threshold
  const setConfidenceThreshold = (threshold) => {
    dispatch({ 
      type: UKG_ACTIONS.SET_CONFIDENCE_THRESHOLD, 
      payload: threshold
    });
  };
  
  // Set refinement steps
  const setRefinementSteps = (steps) => {
    dispatch({ 
      type: UKG_ACTIONS.SET_REFINEMENT_STEPS, 
      payload: steps
    });
  };
  
  // Clear any errors
  const clearError = () => {
    dispatch({ type: UKG_ACTIONS.CLEAR_ERROR });
  };
  
  // Reset state to initial
  const resetState = () => {
    dispatch({ type: UKG_ACTIONS.RESET_STATE });
  };
  
  // Value object with state and actions
  const value = {
    ...state,
    runQuery,
    runSimulation,
    getGraphData,
    getSystemSettings,
    updateSystemSettings,
    setActiveLayer,
    setConfidenceThreshold,
    setRefinementSteps,
    clearError,
    resetState
  };
  
  return <UKGContext.Provider value={value}>{children}</UKGContext.Provider>;
};

// Custom hook for using UKG context
export const useUKG = () => {
  const context = useContext(UKGContext);
  if (!context) {
    throw new Error('useUKG must be used within a UKGProvider');
  }
  return context;
};

export default UKGContext;