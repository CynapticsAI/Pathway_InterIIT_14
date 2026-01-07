/**
 * Agent Flow Types
 * Defines the structure for agent workflow visualization
 */

export type AgentNodeType = 'input' | 'orchestrator' | 'research' | 'rag' | 'decision' | 'output';
export type NodeStatus = 'pending' | 'active' | 'completed' | 'error';

export interface AgentNode {
  id: string;
  type: AgentNodeType;
  label: string;
  status: NodeStatus;
  timestamp?: Date;
  message?: string;
  data?: Record<string, any>;
}

export interface AgentTransition {
  id: string;
  from: string;
  to: string;
  timestamp: Date;
  animated?: boolean;
  reason?: string;
}

export interface AgentFlowState {
  nodes: AgentNode[];
  edges: AgentTransition[];
  currentNodeId: string | null;
  iterationCount: number;
  maxIterations: number;
  isPlaying: boolean;
  speed: number; // 0.5x, 1x, 2x
  startTime?: Date;
  endTime?: Date;
}

export interface FlowStep {
  time: number; // seconds from start
  nodeId: string;
  action: string;
  status: NodeStatus;
}

export interface AgentFlowDemo {
  title: string;
  description: string;
  iterations: number;
  steps: FlowStep[];
  totalDuration: number; // seconds
}
