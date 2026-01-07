'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useChatContext } from '@/contexts/ChatContext';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MarkerType,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { motion } from 'framer-motion';
import { AgentNode } from './AgentNode';
import { AnimatedEdge } from './AnimatedEdge';
import { sampleAgentFlow, initialNodes, initialEdges, nodeColors } from '@/utils/agentFlowSample';
import type { NodeStatus } from '@/types/agentFlow';

const nodeTypes = {
  agentNode: AgentNode,
};

const edgeTypes = {
  animated: AnimatedEdge,
};

export function AgentFlowchart() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [iteration, setIteration] = useState(0);
  const { agentTracking } = useChatContext();

  // Initialize nodes and edges with proper ReactFlow format
  useEffect(() => {
    // Define agent nodes based on your architecture and diagram
    const agentNodes: Node[] = [
      {
        id: 'clarification',
        type: 'agentNode',
        position: { x: 250, y: 50 },
        data: { label: 'Clarification', type: 'clarification', status: 'pending' },
      },
      {
        id: 'orchestrator',
        type: 'agentNode',
        position: { x: 250, y: 180 },
        data: { label: 'Orchestrator', type: 'orchestrator', status: 'pending' },
      },
      {
        id: 'market',
        type: 'agentNode',
        position: { x: 100, y: 340 },
        data: { label: 'Market Analyser Agent', type: 'market', status: 'pending' },
      },
      {
        id: 'macro',
        type: 'agentNode',
        position: { x: 400, y: 340 },
        data: { label: 'Macro Economic Agent', type: 'macro', status: 'pending' },
      },
    ];

    // Edges between agents (simplified, adjust as per your diagram)
    const agentEdges: Edge[] = [
      {
        id: 'e-clarification-orchestrator',
        source: 'clarification',
        target: 'orchestrator',
        type: 'animated',
        animated: false,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#374151' },
      },
      {
        id: 'e-orchestrator-market',
        source: 'orchestrator',
        target: 'market',
        type: 'animated',
        animated: false,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#374151' },
      },
      {
        id: 'e-orchestrator-macro',
        source: 'orchestrator',
        target: 'macro',
        type: 'animated',
        animated: false,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#374151' },
      },
    ];

    // If agentTracking is present, update node statuses
    let updatedNodes = agentNodes;
    if (agentTracking) {
      updatedNodes = agentNodes.map((node) => {
        let status: NodeStatus = 'pending';
        if (agentTracking.agent && node.data.label && agentTracking.agent.toLowerCase().includes(node.data.label.toLowerCase())) {
          status = agentTracking.status?.toLowerCase() === 'processing' ? 'active' : agentTracking.status?.toLowerCase() === 'completed' ? 'completed' : 'pending';
        }
        return {
          ...node,
          data: {
            ...node.data,
            status,
            message: agentTracking.agent === node.data.label ? agentTracking.messages?.[0]?.content || '' : node.data.message,
          },
        };
      });
    }

    setNodes(updatedNodes);
    setEdges(agentEdges);
  }, [agentTracking]);

  // Animation logic
  useEffect(() => {
    if (!isPlaying || currentStep >= sampleAgentFlow.steps.length) {
      if (currentStep >= sampleAgentFlow.steps.length) {
        setIsPlaying(false);
      }
      return;
    }

    const step = sampleAgentFlow.steps[currentStep];
    const nextStep = sampleAgentFlow.steps[currentStep + 1];
    const delay = nextStep
      ? ((nextStep.time - step.time) * 1000) / speed
      : 2000 / speed;

    const timer = setTimeout(() => {
      // Update node status
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === step.nodeId) {
            return {
              ...node,
              data: {
                ...node.data,
                status: step.status,
                message: step.action,
              },
            };
          }
          // Mark previous nodes as completed
          const prevSteps = sampleAgentFlow.steps.slice(0, currentStep);
          const wasPreviouslyActive = prevSteps.some(s => s.nodeId === node.id);
          if (wasPreviouslyActive && node.id !== step.nodeId) {
            return {
              ...node,
              data: {
                ...node.data,
                status: 'completed' as NodeStatus,
              },
            };
          }
          return node;
        })
      );

      // Animate edges
      if (nextStep) {
        setEdges((eds) =>
          eds.map((edge) => {
            const isActiveEdge =
              edge.source === step.nodeId && edge.target === nextStep.nodeId;
            return {
              ...edge,
              animated: isActiveEdge,
              data: { ...edge.data, animated: isActiveEdge },
              markerEnd: {
                type: MarkerType.ArrowClosed,
                color: isActiveEdge ? '#3b82f6' : '#374151',
              },
            };
          })
        );
      }

      // Update iteration count
      if (step.nodeId === 'decision') {
        const iterationMatch = step.action.match(/Iteration (\d+)\/(\d+)/);
        if (iterationMatch) {
          setIteration(parseInt(iterationMatch[1]));
        }
      }

      setCurrentStep((prev) => prev + 1);
    }, delay);

    return () => clearTimeout(timer);
  }, [isPlaying, currentStep, speed, setNodes, setEdges]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    setIteration(0);
    
    // Reset all nodes to pending
    setNodes((nds) =>
      nds.map((node, idx) => ({
        ...node,
        data: {
          ...initialNodes[idx],
          type: node.data.type,
        },
      }))
    );

    // Reset all edges
    setEdges((eds) =>
      eds.map((edge) => ({
        ...edge,
        animated: false,
        data: { ...edge.data, animated: false },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#374151' },
      }))
    );
  };

  const progress = (currentStep / sampleAgentFlow.steps.length) * 100;

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-2xl">🤖</span>
              {sampleAgentFlow.title}
            </h3>
            <p className="text-sm text-gray-300 mt-1">{sampleAgentFlow.description}</p>
          </div>
          
          {/* Iteration Counter */}
          <div className="bg-gray-800/50 px-4 py-2 rounded-lg border border-gray-600">
            <div className="text-xs text-gray-400 mb-1">Iteration</div>
            <div className="text-2xl font-bold text-blue-400">
              {iteration}/{sampleAgentFlow.iterations}
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex-shrink-0 bg-gray-800/50 border-b border-gray-700 px-6 py-3">
        <div className="flex items-center gap-4">
          {/* Play/Pause Button */}
          <button
            onClick={handlePlayPause}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {isPlaying ? (
              <>
                <span>⏸</span> Pause
              </>
            ) : (
              <>
                <span>▶️</span> Play
              </>
            )}
          </button>

          {/* Reset Button */}
          <button
            onClick={handleReset}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <span>🔄</span> Reset
          </button>

          {/* Speed Control */}
          <div className="flex items-center gap-2 ml-4">
            <span className="text-sm text-gray-400">Speed:</span>
            {[0.5, 1, 2].map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`px-3 py-1 rounded ${
                  speed === s
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                } transition-colors text-sm font-medium`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Progress Bar */}
          <div className="flex-1 ml-6">
            <div className="flex items-center gap-3">
              <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
                <motion.div
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <span className="text-sm text-gray-400 font-mono min-w-[60px] text-right">
                {Math.round(progress)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Flow Chart */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          minZoom={0.5}
          maxZoom={1.5}
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#4b5563" gap={16} />
          <Controls className="bg-gray-800 border-gray-700" />
        </ReactFlow>
      </div>

      {/* Legend */}
      <div className="flex-shrink-0 bg-gray-800/50 border-t border-gray-700 px-6 py-3">
        <div className="flex items-center gap-6 text-xs">
          <span className="text-gray-400 font-semibold">Legend:</span>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-500"></div>
            <span className="text-gray-300">Pending</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-400 animate-pulse"></div>
            <span className="text-gray-300">Active</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-400"></div>
            <span className="text-gray-300">Completed</span>
          </div>
          <div className="ml-4 flex items-center gap-2">
            <svg width="20" height="2">
              <line x1="0" y1="1" x2="20" y2="1" stroke="#9ca3af" strokeWidth="2" strokeDasharray="4,4" />
            </svg>
            <span className="text-gray-300">Loop Connection</span>
          </div>
        </div>
      </div>
    </div>
  );
}
