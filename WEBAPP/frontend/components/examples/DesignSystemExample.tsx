/**
 * Example Component - Demonstrates New Design System
 * 
 * This shows how to use the new design tokens, elevation system,
 * and utility functions in your components.
 */

import { Send, TrendingUp, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

export function DesignSystemExample() {
  return (
    <div className="p-6 space-y-6">
      {/* Typography Example */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Typography System
        </h2>
        <p className="text-base text-[var(--color-text-secondary)]">
          Body text with consistent sizing and colors
        </p>
        <p className="text-sm text-[var(--color-text-tertiary)]">
          Small text for labels and captions
        </p>
      </section>

      {/* Elevation Example */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Elevation System (No Borders!)
        </h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="elevation-1 p-4 rounded-lg bg-[var(--color-surface)]">
            <p className="text-sm">Elevation 1</p>
          </div>
          <div className="elevation-3 p-4 rounded-lg bg-[var(--color-surface)]">
            <p className="text-sm">Elevation 3</p>
          </div>
          <div className="elevation-5 p-4 rounded-lg bg-[var(--color-surface)]">
            <p className="text-sm">Elevation 5</p>
          </div>
        </div>
      </section>

      {/* Icons with Lucide */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Material Icons (Lucide React)
        </h2>
        <div className="flex gap-4">
          <button className="p-3 rounded-lg elevation-2 hover-elevate bg-[var(--color-surface)] transition-smooth">
            <Send className="w-5 h-5 text-[var(--color-primary)]" />
          </button>
          <button className="p-3 rounded-lg elevation-2 hover-elevate bg-[var(--color-surface)] transition-smooth">
            <TrendingUp className="w-5 h-5 text-[var(--color-gain)]" />
          </button>
          <button className="p-3 rounded-lg elevation-2 hover-elevate bg-[var(--color-surface)] transition-smooth">
            <Settings className="w-5 h-5 text-[var(--color-text-secondary)]" />
          </button>
        </div>
      </section>

      {/* Financial Data Colors */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Financial Data Colors
        </h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="elevation-2 p-4 rounded-lg bg-[var(--color-surface)]">
            <p className="text-sm text-[var(--color-text-tertiary)]">AAPL</p>
            <p className="text-2xl font-semibold text-gain">+2.45%</p>
          </div>
          <div className="elevation-2 p-4 rounded-lg bg-[var(--color-surface)]">
            <p className="text-sm text-[var(--color-text-tertiary)]">TSLA</p>
            <p className="text-2xl font-semibold text-loss">-1.23%</p>
          </div>
          <div className="elevation-2 p-4 rounded-lg bg-[var(--color-surface)]">
            <p className="text-sm text-[var(--color-text-tertiary)]">MSFT</p>
            <p className="text-2xl font-semibold text-neutral">0.00%</p>
          </div>
        </div>
      </section>

      {/* Button Variants with CN utility */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Using CN Utility
        </h2>
        <div className="flex gap-4">
          <button
            className={cn(
              'px-4 py-2 rounded-lg font-medium',
              'elevation-2 hover-elevate',
              'bg-[var(--color-primary)] text-white',
              'transition-smooth'
            )}
          >
            Primary Button
          </button>
          <button
            className={cn(
              'px-4 py-2 rounded-lg font-medium',
              'elevation-1 hover-elevate',
              'bg-[var(--color-surface)] text-[var(--color-text-primary)]',
              'transition-smooth'
            )}
          >
            Secondary Button
          </button>
        </div>
      </section>

      {/* Cards with Elevation */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Modern Cards (Elevated Surfaces)
        </h2>
        <div className="elevation-3 p-6 rounded-lg bg-[var(--color-surface)] hover-elevate transition-smooth">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
            Stock Analysis Card
          </h3>
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">
            This card uses elevation instead of borders for a modern, professional look.
          </p>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[var(--color-gain)]" />
            <span className="text-sm font-medium text-gain">+15.3%</span>
          </div>
        </div>
      </section>
    </div>
  );
}
