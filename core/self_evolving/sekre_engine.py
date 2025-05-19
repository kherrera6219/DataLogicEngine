import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import sys
import os
import json

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class SekreEngine:
    """
    Self-Evolving Knowledge Refinement Engine (SEKRE)
    
    This component is responsible for the continuous improvement and evolution
    of the UKG. It analyzes system performance, identifies knowledge gaps, and
    proposes improvements to the ontology and knowledge structures.
    """
    
    def __init__(self, config=None, graph_manager=None, memory_manager=None, 
               usm=None, validation_engine=None):
        """
        Initialize the SEKRE Engine.
        
        Args:
            config (dict, optional): Configuration dictionary
            graph_manager: Graph Manager reference
            memory_manager: Structured Memory Manager reference
            usm: United System Manager reference
            validation_engine: Validation Engine reference
        """
        logging.info(f"[{datetime.now()}] Initializing SekreEngine...")
        self.config = config or {}
        self.graph_manager = graph_manager
        self.memory_manager = memory_manager
        self.usm = usm
        self.validation_engine = validation_engine
        
        # Configure SEKRE settings
        self.sekre_config = self.config.get('sekre_engine', {})
        self.enable_auto_improvement = self.sekre_config.get('enable_auto_improvement', False)
        self.auto_improvement_threshold = self.sekre_config.get('auto_improvement_threshold', 0.9)
        self.review_required_threshold = self.sekre_config.get('review_required_threshold', 0.75)
        self.min_confidence_for_proposals = self.sekre_config.get('min_confidence_for_proposals', 0.6)
        
        # Operational state
        self.improvement_proposals = {}  # proposal_id -> proposal_data
        self.ontology_updates = {}  # update_id -> update_data
        self.performance_metrics = {}  # metric_id -> metric_data
        
        # Initialize metrics tracking
        self._initialize_metrics()
        
        logging.info(f"[{datetime.now()}] SekreEngine initialized with auto-improvement set to {self.enable_auto_improvement}")
    
    def _initialize_metrics(self):
        """
        Initialize performance metrics tracking.
        """
        self.performance_metrics = {
            'axis_performance': {},  # axis_num -> performance_data
            'overall_performance': {
                'total_simulations': 0,
                'successful_simulations': 0,
                'failed_simulations': 0,
                'avg_confidence': 0.0,
                'avg_execution_time': 0.0
            },
            'identified_gaps': [],
            'improvement_metrics': {
                'proposals_generated': 0,
                'proposals_accepted': 0,
                'proposals_rejected': 0,
                'auto_improvements_applied': 0,
                'manual_improvements_applied': 0
            }
        }
    
    def analyze_simulation_results(self, session_id: str) -> Dict:
        """
        Analyze the results of a simulation to identify improvement opportunities.
        
        Args:
            session_id: The session ID to analyze
            
        Returns:
            dict: Analysis results
        """
        logging.info(f"[{datetime.now()}] SEKRE: Analyzing simulation results for session {session_id}")
        
        # Get session history from memory manager
        if not self.memory_manager:
            logging.warning(f"[{datetime.now()}] SEKRE: Cannot analyze simulation without memory manager")
            return {
                'status': 'error',
                'message': 'Memory manager not available'
            }
        
        session_history = self.memory_manager.get_session_history(session_id)
        
        if not session_history or session_history.get('status') == 'not_found':
            logging.warning(f"[{datetime.now()}] SEKRE: Session {session_id} not found")
            return {
                'status': 'error',
                'message': 'Session not found'
            }
        
        # Extract relevant data
        user_query = session_history.get('user_query', '')
        final_confidence = session_history.get('final_confidence', 0.0)
        status = session_history.get('status', 'unknown')
        memory_entries = session_history.get('raw_memory_entries', [])
        
        # Identify performance issues
        # For each axis, calculate metrics based on relevant memory entries
        axis_performance = {}
        knowledge_gaps = []
        reasoning_issues = []
        
        # Simple confidence metric: if final is below threshold, there's an issue
        overall_success = (
            status == 'completed' and 
            final_confidence >= self.config.get('target_confidence_overall', 0.85)
        )
        
        # Update overall metrics
        self.performance_metrics['overall_performance']['total_simulations'] += 1
        
        if overall_success:
            self.performance_metrics['overall_performance']['successful_simulations'] += 1
        else:
            self.performance_metrics['overall_performance']['failed_simulations'] += 1
        
        # Calculate running average for confidence
        old_avg = self.performance_metrics['overall_performance']['avg_confidence']
        old_count = (
            self.performance_metrics['overall_performance']['successful_simulations'] + 
            self.performance_metrics['overall_performance']['failed_simulations'] - 1
        )
        if old_count > 0:
            self.performance_metrics['overall_performance']['avg_confidence'] = (
                (old_avg * old_count + final_confidence) / (old_count + 1)
            )
        else:
            self.performance_metrics['overall_performance']['avg_confidence'] = final_confidence
        
        # Look for knowledge gaps in memory entries
        for entry in memory_entries:
            entry_type = entry.get('entry_type')
            content = entry.get('content', {})
            
            # Look for knowledge retrieval entries with low confidence
            if entry_type == 'knowledge_retrieval' and content.get('confidence', 1.0) < 0.7:
                knowledge_gaps.append({
                    'query': content.get('query', ''),
                    'confidence': content.get('confidence', 0.0),
                    'axis': content.get('axis_number'),
                    'timestamp': entry.get('created_at')
                })
            
            # Look for reasoning steps with errors or low confidence
            if entry_type == 'reasoning_step' and (
                content.get('status') == 'error' or content.get('confidence', 1.0) < 0.7
            ):
                reasoning_issues.append({
                    'step': content.get('step_name', 'unknown'),
                    'confidence': content.get('confidence', 0.0),
                    'error': content.get('error'),
                    'axis': content.get('axis_number'),
                    'timestamp': entry.get('created_at')
                })
        
        # Analyze KA executions to identify axis-specific performance
        ka_executions = [e for e in memory_entries if e.get('entry_type') in 
                       ('ka_execution_start', 'ka_execution_complete', 'ka_execution_error')]
        
        # Group by algorithm
        ka_results = {}
        for exec_entry in ka_executions:
            content = exec_entry.get('content', {})
            ka_id = content.get('ka_id')
            
            if not ka_id:
                continue
                
            if ka_id not in ka_results:
                ka_results[ka_id] = {
                    'executions': 0,
                    'successes': 0,
                    'errors': 0,
                    'total_time': 0.0,
                    'avg_confidence': 0.0
                }
            
            if exec_entry.get('entry_type') == 'ka_execution_complete':
                ka_results[ka_id]['executions'] += 1
                ka_results[ka_id]['successes'] += 1
                ka_results[ka_id]['total_time'] += content.get('execution_time', 0.0)
                
                # Update running average for confidence
                output_data = content.get('output_data', {})
                confidence = output_data.get('confidence', 0.0)
                old_avg = ka_results[ka_id]['avg_confidence']
                old_count = ka_results[ka_id]['successes'] - 1
                
                if old_count > 0:
                    ka_results[ka_id]['avg_confidence'] = (
                        (old_avg * old_count + confidence) / (old_count + 1)
                    )
                else:
                    ka_results[ka_id]['avg_confidence'] = confidence
            
            elif exec_entry.get('entry_type') == 'ka_execution_error':
                ka_results[ka_id]['executions'] += 1
                ka_results[ka_id]['errors'] += 1
        
        # Prepare analysis results
        analysis_results = {
            'session_id': session_id,
            'user_query': user_query,
            'overall_success': overall_success,
            'final_confidence': final_confidence,
            'knowledge_gaps': knowledge_gaps,
            'reasoning_issues': reasoning_issues,
            'ka_performance': ka_results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Record analysis in memory
        if self.memory_manager:
            self.memory_manager.add_memory_entry(
                session_id=session_id,
                entry_type='sekre_analysis',
                content=analysis_results
            )
        
        # Generate improvement proposals if needed
        if not overall_success or knowledge_gaps or reasoning_issues:
            self._generate_improvement_proposals(analysis_results)
        
        return analysis_results
    
    def _generate_improvement_proposals(self, analysis_results: Dict) -> List[Dict]:
        """
        Generate improvement proposals based on analysis results.
        
        Args:
            analysis_results: Analysis results from analyze_simulation_results
            
        Returns:
            list: List of improvement proposals
        """
        proposals = []
        session_id = analysis_results.get('session_id')
        
        # Generate proposals for knowledge gaps
        for gap in analysis_results.get('knowledge_gaps', []):
            proposal_id = f"PROP_KG_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
            
            proposal = {
                'proposal_id': proposal_id,
                'proposal_type': 'knowledge_gap',
                'session_id': session_id,
                'axis': gap.get('axis'),
                'query': gap.get('query'),
                'confidence': gap.get('confidence'),
                'proposed_action': 'add_knowledge',
                'details': f"Add knowledge to address query: {gap.get('query')}",
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'auto_approval_eligible': gap.get('confidence', 0) < self.min_confidence_for_proposals
            }
            
            proposals.append(proposal)
            self.improvement_proposals[proposal_id] = proposal
        
        # Generate proposals for reasoning issues
        for issue in analysis_results.get('reasoning_issues', []):
            proposal_id = f"PROP_RI_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
            
            proposal = {
                'proposal_id': proposal_id,
                'proposal_type': 'reasoning_issue',
                'session_id': session_id,
                'axis': issue.get('axis'),
                'step': issue.get('step'),
                'confidence': issue.get('confidence'),
                'error': issue.get('error'),
                'proposed_action': 'improve_reasoning',
                'details': f"Improve reasoning for step: {issue.get('step')}",
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'auto_approval_eligible': False  # Reasoning improvements typically need review
            }
            
            proposals.append(proposal)
            self.improvement_proposals[proposal_id] = proposal
        
        # Generate proposals for algorithm performance issues
        for ka_id, ka_data in analysis_results.get('ka_performance', {}).items():
            if ka_data.get('errors', 0) > 0 or ka_data.get('avg_confidence', 1.0) < 0.7:
                proposal_id = f"PROP_KA_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
                
                proposal = {
                    'proposal_id': proposal_id,
                    'proposal_type': 'algorithm_issue',
                    'session_id': session_id,
                    'ka_id': ka_id,
                    'error_rate': ka_data.get('errors', 0) / max(1, ka_data.get('executions', 1)),
                    'avg_confidence': ka_data.get('avg_confidence', 0.0),
                    'proposed_action': 'improve_algorithm',
                    'details': f"Improve algorithm {ka_id} to address performance issues",
                    'status': 'pending',
                    'created_at': datetime.now().isoformat(),
                    'auto_approval_eligible': False  # Algorithm improvements typically need review
                }
                
                proposals.append(proposal)
                self.improvement_proposals[proposal_id] = proposal
        
        # Record proposals in memory
        if self.memory_manager and session_id:
            self.memory_manager.add_memory_entry(
                session_id=session_id,
                entry_type='sekre_improvement_proposals',
                content={
                    'proposals': proposals,
                    'timestamp': datetime.now().isoformat()
                }
            )
        
        # Update metrics
        self.performance_metrics['improvement_metrics']['proposals_generated'] += len(proposals)
        
        # Auto-apply eligible proposals if auto-improvement is enabled
        if self.enable_auto_improvement:
            auto_applied = []
            for proposal in proposals:
                if (proposal.get('auto_approval_eligible', False) and 
                    proposal.get('confidence', 0) <= self.auto_improvement_threshold):
                    result = self.apply_improvement(proposal.get('proposal_id'))
                    if result.get('status') == 'success':
                        auto_applied.append(proposal.get('proposal_id'))
            
            if auto_applied:
                logging.info(f"[{datetime.now()}] SEKRE: Auto-applied {len(auto_applied)} improvements")
                self.performance_metrics['improvement_metrics']['auto_improvements_applied'] += len(auto_applied)
        
        return proposals
    
    def get_improvement_proposals(self, status: Optional[str] = None, 
                               proposal_type: Optional[str] = None,
                               limit: int = 100) -> List[Dict]:
        """
        Get improvement proposals with optional filtering.
        
        Args:
            status: Optional status filter
            proposal_type: Optional proposal type filter
            limit: Maximum number of proposals to return
            
        Returns:
            list: List of improvement proposals
        """
        proposals = list(self.improvement_proposals.values())
        
        # Apply filters
        if status:
            proposals = [p for p in proposals if p.get('status') == status]
        
        if proposal_type:
            proposals = [p for p in proposals if p.get('proposal_type') == proposal_type]
        
        # Sort by created timestamp (newest first)
        proposals.sort(key=lambda p: p.get('created_at', ''), reverse=True)
        
        # Apply limit
        return proposals[:limit]
    
    def approve_improvement(self, proposal_id: str) -> Dict:
        """
        Approve and apply an improvement proposal.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            dict: Result of applying the improvement
        """
        if proposal_id not in self.improvement_proposals:
            return {
                'status': 'error',
                'message': f"Proposal {proposal_id} not found"
            }
        
        proposal = self.improvement_proposals[proposal_id]
        
        # Don't approve already approved or rejected proposals
        if proposal.get('status') != 'pending':
            return {
                'status': 'error',
                'message': f"Proposal {proposal_id} is not pending (status: {proposal.get('status')})"
            }
        
        # Apply the improvement
        result = self.apply_improvement(proposal_id)
        
        # Update metrics
        if result.get('status') == 'success':
            self.performance_metrics['improvement_metrics']['proposals_accepted'] += 1
            self.performance_metrics['improvement_metrics']['manual_improvements_applied'] += 1
        
        return result
    
    def reject_improvement(self, proposal_id: str, reason: Optional[str] = None) -> Dict:
        """
        Reject an improvement proposal.
        
        Args:
            proposal_id: Proposal ID
            reason: Optional reason for rejection
            
        Returns:
            dict: Result of rejecting the improvement
        """
        if proposal_id not in self.improvement_proposals:
            return {
                'status': 'error',
                'message': f"Proposal {proposal_id} not found"
            }
        
        proposal = self.improvement_proposals[proposal_id]
        
        # Don't reject already approved or rejected proposals
        if proposal.get('status') != 'pending':
            return {
                'status': 'error',
                'message': f"Proposal {proposal_id} is not pending (status: {proposal.get('status')})"
            }
        
        # Update proposal
        proposal['status'] = 'rejected'
        proposal['rejection_reason'] = reason
        proposal['rejected_at'] = datetime.now().isoformat()
        
        # Update metrics
        self.performance_metrics['improvement_metrics']['proposals_rejected'] += 1
        
        return {
            'status': 'success',
            'message': f"Proposal {proposal_id} rejected",
            'proposal': proposal
        }
    
    def apply_improvement(self, proposal_id: str) -> Dict:
        """
        Apply an improvement proposal.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            dict: Result of applying the improvement
        """
        if proposal_id not in self.improvement_proposals:
            return {
                'status': 'error',
                'message': f"Proposal {proposal_id} not found"
            }
        
        proposal = self.improvement_proposals[proposal_id]
        proposal_type = proposal.get('proposal_type')
        proposed_action = proposal.get('proposed_action')
        
        try:
            # Different actions based on proposal type and action
            if proposal_type == 'knowledge_gap' and proposed_action == 'add_knowledge':
                # In a full implementation, this would actually add knowledge to the system
                # Here we just update the proposal status
                proposal['status'] = 'approved'
                proposal['approved_at'] = datetime.now().isoformat()
                proposal['implementation_status'] = 'completed'
                proposal['implemented_at'] = datetime.now().isoformat()
                
                logging.info(f"[{datetime.now()}] SEKRE: Applied knowledge improvement for proposal {proposal_id}")
                
                return {
                    'status': 'success',
                    'message': f"Knowledge improvement applied for proposal {proposal_id}",
                    'proposal': proposal
                }
            
            elif proposal_type == 'reasoning_issue' and proposed_action == 'improve_reasoning':
                # In a full implementation, this would actually improve reasoning
                # Here we just update the proposal status
                proposal['status'] = 'approved'
                proposal['approved_at'] = datetime.now().isoformat()
                proposal['implementation_status'] = 'completed'
                proposal['implemented_at'] = datetime.now().isoformat()
                
                logging.info(f"[{datetime.now()}] SEKRE: Applied reasoning improvement for proposal {proposal_id}")
                
                return {
                    'status': 'success',
                    'message': f"Reasoning improvement applied for proposal {proposal_id}",
                    'proposal': proposal
                }
            
            elif proposal_type == 'algorithm_issue' and proposed_action == 'improve_algorithm':
                # In a full implementation, this would actually improve the algorithm
                # Here we just update the proposal status
                proposal['status'] = 'approved'
                proposal['approved_at'] = datetime.now().isoformat()
                proposal['implementation_status'] = 'completed'
                proposal['implemented_at'] = datetime.now().isoformat()
                
                logging.info(f"[{datetime.now()}] SEKRE: Applied algorithm improvement for proposal {proposal_id}")
                
                return {
                    'status': 'success',
                    'message': f"Algorithm improvement applied for proposal {proposal_id}",
                    'proposal': proposal
                }
            
            else:
                return {
                    'status': 'error',
                    'message': f"Unsupported proposal type/action: {proposal_type}/{proposed_action}",
                    'proposal': proposal
                }
                
        except Exception as e:
            logging.error(f"[{datetime.now()}] SEKRE: Error applying improvement for proposal {proposal_id}: {str(e)}")
            
            # Update proposal status
            proposal['status'] = 'error'
            proposal['error'] = str(e)
            proposal['error_time'] = datetime.now().isoformat()
            
            return {
                'status': 'error',
                'message': f"Error applying improvement: {str(e)}",
                'proposal': proposal
            }
    
    def analyze_system_performance(self) -> Dict:
        """
        Analyze overall system performance across all simulations.
        
        Returns:
            dict: Performance analysis
        """
        return {
            'overall_performance': self.performance_metrics['overall_performance'],
            'improvement_metrics': self.performance_metrics['improvement_metrics'],
            'identified_gaps_count': len(self.performance_metrics['identified_gaps']),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_health(self) -> Dict:
        """
        Get health status of the SEKRE Engine.
        
        Returns:
            dict: Health status
        """
        return {
            'status': 'healthy',
            'proposals_count': len(self.improvement_proposals),
            'pending_proposals': len([p for p in self.improvement_proposals.values() if p.get('status') == 'pending']),
            'auto_improvement_enabled': self.enable_auto_improvement,
            'timestamp': datetime.now().isoformat()
        }