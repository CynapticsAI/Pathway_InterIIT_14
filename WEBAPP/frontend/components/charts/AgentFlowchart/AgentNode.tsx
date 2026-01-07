'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { motion } from 'framer-motion';
import { nodeColors, nodeIcons } from '@/utils/agentFlowSample';
import type { NodeStatus } from '@/types/agentFlow';

interface AgentNodeData {
  label: string;
  type: string;
  status: NodeStatus;
  message?: string;
}

export function AgentNode({ data, isConnectable }: NodeProps<AgentNodeData>) {
  const status = data.status || 'pending';
  const nodeType = data.type || 'input';
  const color = nodeColors[nodeType] || '#6b7280';
  const icon = nodeIcons[nodeType] || '⚙️';

  const isActive = status === 'active';
  const isCompleted = status === 'completed';
  const isPending = status === 'pending';

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{
        scale: isActive ? [1, 1.05, 1] : 1,
        opacity: 1,
      }}
      transition={{
        scale: {
          repeat: isActive ? Infinity : 0,
          duration: 2,
          ease: 'easeInOut',
        },
        opacity: { duration: 0.3 },
      }}
      className="relative"
    >
      {/* Input Handles */}
      {nodeType !== 'input' && (
        <Handle
          type="target"
          position={Position.Top}
          isConnectable={isConnectable}
          className="w-3 h-3 !bg-blue-500 border-2 border-white"
        />
      )}

      {/* Node Card */}
      <motion.div
        className={`
          min-w-[180px] px-5 py-4 rounded-xl border-2
          shadow-lg backdrop-blur-sm
          ${isPending ? 'bg-gray-800/50 border-gray-600' : ''}
          ${isActive ? 'bg-gradient-to-br from-gray-800 to-gray-900 border-current' : ''}
          ${isCompleted ? 'bg-gradient-to-br from-gray-800/70 to-gray-900/70 border-green-500' : ''}
        `}
        style={{
          borderColor: isActive ? color : undefined,
          boxShadow: isActive
            ? `0 0 20px ${color}40, 0 0 40px ${color}20`
            : undefined,
        }}
        animate={{
          boxShadow: isActive
            ? [
                `0 0 20px ${color}40, 0 0 40px ${color}20`,
                `0 0 30px ${color}60, 0 0 60px ${color}30`,
                `0 0 20px ${color}40, 0 0 40px ${color}20`,
              ]
            : undefined,
        }}
        transition={{
          duration: 2,
          repeat: isActive ? Infinity : 0,
          ease: 'easeInOut',
        }}
      >
        {/* Icon & Title */}
        <div className="flex items-center gap-3 mb-2">
          <motion.div
            className="text-2xl"
            animate={{
              scale: isActive ? [1, 1.2, 1] : 1,
              rotate: isActive ? [0, 5, -5, 0] : 0,
            }}
            transition={{
              duration: 2,
              repeat: isActive ? Infinity : 0,
            }}
          >
            {icon}
          </motion.div>
          <div>
            <h3
              className="font-bold text-sm"
              style={{ color: isActive || isCompleted ? color : '#9ca3af' }}
            >
              {data.label}
            </h3>
          </div>
        </div>

        {/* Message */}
        {data.message && (
          <motion.p
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className={`text-xs leading-relaxed text-break ${
              isActive ? 'text-gray-200' : 'text-gray-400'
            }`}
          >
            {data.message.slice(0, 100)}
          </motion.p>
        )}

        {/* Status Indicator */}
        <div className="flex items-center gap-2 mt-3">
          <motion.div
            className={`w-2 h-2 rounded-full ${
              isPending ? 'bg-gray-500' :
              isActive ? 'bg-blue-400' :
              isCompleted ? 'bg-green-400' : 'bg-gray-500'
            }`}
            animate={{
              scale: isActive ? [1, 1.5, 1] : 1,
              opacity: isActive ? [0.5, 1, 0.5] : 1,
            }}
            transition={{
              duration: 1.5,
              repeat: isActive ? Infinity : 0,
            }}
          />
          <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">
            {status}
          </span>
        </div>

        {/* Active Animation Border */}
        {isActive && (
          <motion.div
            className="absolute inset-0 rounded-xl pointer-events-none"
            style={{
              background: `linear-gradient(135deg, ${color}20, transparent)`,
            }}
            animate={{
              opacity: [0.3, 0.6, 0.3],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
            }}
          />
        )}
      </motion.div>

      {/* Output Handles */}
      {nodeType !== 'output' && (
        <Handle
          type="source"
          position={Position.Bottom}
          isConnectable={isConnectable}
          className="w-3 h-3 !bg-blue-500 border-2 border-white"
        />
      )}
    </motion.div>
  );
}
