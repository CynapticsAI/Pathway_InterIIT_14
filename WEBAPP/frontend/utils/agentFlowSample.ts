import { AgentFlowDemo, AgentNode, AgentTransition } from '@/types/agentFlow';

/**
 * Sample Agent Flow Data
 * Demonstrates the orchestrator → research ↔ RAG loop
 */

export const sampleAgentFlow: AgentFlowDemo = {
  title: 'AAPL Stock Analysis',
  description: 'Analyzing Apple stock with multi-agent workflow',
  iterations: 3,
  totalDuration: 14,
  steps: [
    {
      time: 0,
      nodeId: 'input',
      action: 'User asks: "Analyze AAPL stock performance"',
      status: 'active',
    },
    {
      time: 1,
      nodeId: 'orchestrator',
      action: 'Planning research strategy...',
      status: 'active',
    },
    {
      time: 2,
      nodeId: 'research',
      action: 'Fetching AAPL stock data from market APIs',
      status: 'active',
    },
    {
      time: 4,
      nodeId: 'decision',
      action: 'Evaluating data... Need more context (Iteration 1/3)',
      status: 'active',
    },
    {
      time: 5,
      nodeId: 'rag',
      action: 'Querying knowledge base for AAPL historical analysis',
      status: 'active',
    },
    {
      time: 7,
      nodeId: 'decision',
      action: 'Need recent news data (Iteration 2/3)',
      status: 'active',
    },
    {
      time: 8,
      nodeId: 'research',
      action: 'Fetching latest AAPL news and sentiment data',
      status: 'active',
    },
    {
      time: 10,
      nodeId: 'decision',
      action: 'Synthesizing final response (Iteration 3/3)',
      status: 'active',
    },
    {
      time: 11,
      nodeId: 'rag',
      action: 'Generating comprehensive analysis with insights',
      status: 'active',
    },
    {
      time: 13,
      nodeId: 'output',
      action: 'Analysis complete! Presenting results to user',
      status: 'completed',
    },
  ],
};

export const initialNodes: AgentNode[] = [
  {
    id: 'input',
    type: 'input',
    label: 'User Input',
    status: 'pending',
    message: 'Waiting for query...',
  },
  {
    id: 'orchestrator',
    type: 'orchestrator',
    label: 'Orchestrator',
    status: 'pending',
    message: 'AI planner ready',
  },
  {
    id: 'research',
    type: 'research',
    label: 'Research Agent',
    status: 'pending',
    message: 'Standing by for data requests',
  },
  {
    id: 'rag',
    type: 'rag',
    label: 'RAG Agent',
    status: 'pending',
    message: 'Knowledge base ready',
  },
  {
    id: 'decision',
    type: 'decision',
    label: 'Decision Point',
    status: 'pending',
    message: 'Awaiting evaluation',
  },
  {
    id: 'output',
    type: 'output',
    label: 'Output',
    status: 'pending',
    message: 'Ready to deliver results',
  },
];

export const initialEdges: AgentTransition[] = [
  {
    id: 'e-input-orchestrator',
    from: 'input',
    to: 'orchestrator',
    timestamp: new Date(),
    animated: false,
  },
  {
    id: 'e-orchestrator-research',
    from: 'orchestrator',
    to: 'research',
    timestamp: new Date(),
    animated: false,
  },
  {
    id: 'e-orchestrator-rag',
    from: 'orchestrator',
    to: 'rag',
    timestamp: new Date(),
    animated: false,
  },
  {
    id: 'e-research-decision',
    from: 'research',
    to: 'decision',
    timestamp: new Date(),
    animated: false,
  },
  {
    id: 'e-rag-decision',
    from: 'rag',
    to: 'decision',
    timestamp: new Date(),
    animated: false,
  },
  {
    id: 'e-decision-research',
    from: 'decision',
    to: 'research',
    timestamp: new Date(),
    animated: false,
    reason: 'Loop for more data',
  },
  {
    id: 'e-decision-rag',
    from: 'decision',
    to: 'rag',
    timestamp: new Date(),
    animated: false,
    reason: 'Loop for knowledge',
  },
  {
    id: 'e-decision-output',
    from: 'decision',
    to: 'output',
    timestamp: new Date(),
    animated: false,
  },
];

// Node colors for visualization
export const nodeColors: Record<string, string> = {
  input: '#3b82f6',       // Blue
  orchestrator: '#8b5cf6', // Purple
  research: '#10b981',    // Green
  rag: '#f59e0b',         // Orange/Amber
  decision: '#ec4899',    // Pink
  output: '#06b6d4',      // Cyan
};

// Node icons (emoji for now, can be replaced with actual icons)
export const nodeIcons: Record<string, string> = {
  input: '💬',
  orchestrator: '🧠',
  research: '🔍',
  rag: '📚',
  decision: '⚡',
  output: '✅',
};
