'use client';

import React from 'react';
import { EdgeProps, getBezierPath } from 'reactflow';
import { motion } from 'framer-motion';

export function AnimatedEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  markerEnd,
}: EdgeProps) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const isActive = data?.animated || false;
  const isLoop = data?.isLoop || false;

  return (
    <>
      {/* Background path */}
      <path
        id={id}
        style={style}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={2}
        stroke={isActive ? '#60a5fa' : '#374151'}
        strokeOpacity={isActive ? 0.8 : 0.3}
        fill="none"
      />

      {/* Animated dashed line when active */}
      {isActive && (
        <motion.path
          d={edgePath}
          stroke="#3b82f6"
          strokeWidth={2}
          strokeDasharray="8 8"
          fill="none"
          initial={{ strokeDashoffset: 0 }}
          animate={{ strokeDashoffset: -16 }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      )}

      {/* Flowing particles when active */}
      {isActive && (
        <>
          <circle r="3" fill="#3b82f6">
            <animateMotion dur="2s" repeatCount="indefinite" path={edgePath} />
          </circle>
          <circle r="3" fill="#60a5fa">
            <animateMotion dur="2s" repeatCount="indefinite" path={edgePath}>
              <animate attributeName="opacity" values="0;1;0" dur="2s" repeatCount="indefinite" />
            </animateMotion>
          </circle>
        </>
      )}

      {/* Arrow marker */}
      <path
        d={edgePath}
        strokeWidth={2}
        stroke="transparent"
        fill="none"
        markerEnd={markerEnd}
      />

      {/* Loop indicator */}
      {isLoop && (
        <text>
          <textPath href={`#${id}`} startOffset="50%" textAnchor="middle">
            <tspan
              dy="-5"
              fontSize="10"
              fill="#9ca3af"
              className="font-mono"
            >
              ↻ loop
            </tspan>
          </textPath>
        </text>
      )}
    </>
  );
}
