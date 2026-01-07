'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface ChartCardProps {
  title: string;
  description?: string;
  isSample?: boolean;
  children: React.ReactNode;
  onTryAsk?: () => void;
}

export function ChartCard({
  title,
  description,
  isSample = false,
  children,
  onTryAsk,
}: ChartCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-gradient-to-br from-[var(--color-background)] to-[var(--color-ai-message)]/10 rounded-xl border border-[var(--color-border)] overflow-hidden shadow-lg hover:shadow-xl transition-shadow duration-300"
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-[var(--color-border)] bg-[var(--color-background)]/50 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-bold text-[var(--color-foreground)]">
                {title}
              </h3>
              {isSample && (
                <span className="px-2.5 py-1 text-xs font-semibold bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 rounded-full border border-blue-500/30">
                  📊 Sample
                </span>
              )}
            </div>
            {description && (
              <p className="text-sm text-gray-400 mt-1">
                {description}
              </p>
            )}
          </div>

          {isSample && onTryAsk && (
            <button
              onClick={onTryAsk}
              className="ml-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors duration-200 flex items-center gap-2"
            >
              <span>💬</span>
              Ask AI
            </button>
          )}
        </div>
      </div>

      {/* Chart Content */}
      <div className="p-4">
        {children}
      </div>
    </motion.div>
  );
}
