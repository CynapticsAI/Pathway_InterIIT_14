/**
 * Add Stock Form Component - Modern Design
 * 
 * Updated with new Input and Button components from design system
 */

'use client';

import React, { useState } from 'react';
import { usePortfolio } from '@/contexts/PortfolioContext';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import type { StockFormData } from '@/types/portfolio';

export function AddStockForm() {
  const { addStock, isLoading } = usePortfolio();
  const [formData, setFormData] = useState<StockFormData>({
    symbol: '',
    quantity: '',
    cost_basis: '',
  });
  const [errors, setErrors] = useState<Partial<StockFormData>>({});

  const validate = (): boolean => {
    const newErrors: Partial<StockFormData> = {};

    if (!formData.symbol.trim()) {
      newErrors.symbol = 'Symbol is required';
    } else if (!/^[A-Z]{1,5}$/.test(formData.symbol.toUpperCase())) {
      newErrors.symbol = 'Invalid symbol format';
    }

    const quantity = parseFloat(formData.quantity as string);
    if (!formData.quantity || isNaN(quantity) || quantity <= 0) {
      newErrors.quantity = 'Quantity must be greater than 0';
    }

    const costBasis = parseFloat(formData.cost_basis as string);
    if (!formData.cost_basis || isNaN(costBasis) || costBasis <= 0) {
      newErrors.cost_basis = 'Cost basis must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    try {
      await addStock({
        symbol: formData.symbol.toUpperCase(),
        quantity: parseFloat(formData.quantity as string),
        cost_basis: parseFloat(formData.cost_basis as string),
      });

      // Reset form
      setFormData({
        symbol: '',
        quantity: '',
        cost_basis: '',
      });
      setErrors({});
    } catch (err) {
      console.error('Failed to add stock:', err);
    }
  };

  const handleChange = (field: keyof StockFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: e.target.value,
    }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  return (
    <div className={cn(
      'bg-[var(--color-surface)]',
      'rounded-lg p-6',
      'elevation-2'
    )}>
      <h3 className="text-lg font-semibold mb-4 text-[var(--color-foreground)]">
        Add Stock to Portfolio
      </h3>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Symbol Input */}
          <div>
            <label
              htmlFor="symbol"
              className="block text-sm font-medium text-[var(--color-foreground)] mb-1"
            >
              Symbol
            </label>
            <Input
              type="text"
              id="symbol"
              value={formData.symbol}
              onChange={handleChange('symbol')}
              placeholder="AAPL"
              error={!!errors.symbol}
              helperText={errors.symbol}
              disabled={isLoading}
              className="uppercase"
              variant="filled"
            />
          </div>

          {/* Quantity Input */}
          <div>
            <label
              htmlFor="quantity"
              className="block text-sm font-medium text-[var(--color-foreground)] mb-1"
            >
              Quantity
            </label>
            <Input
              type="number"
              id="quantity"
              value={formData.quantity}
              onChange={handleChange('quantity')}
              placeholder="100"
              step="0.0001"
              min="0"
              error={!!errors.quantity}
              helperText={errors.quantity?.toString()}
              disabled={isLoading}
              variant="filled"
            />
          </div>

          {/* Cost Basis Input */}
          <div>
            <label
              htmlFor="cost_basis"
              className="block text-sm font-medium text-[var(--color-foreground)] mb-1"
            >
              Cost Basis ($)
            </label>
            <Input
              type="number"
              id="cost_basis"
              value={formData.cost_basis}
              onChange={handleChange('cost_basis')}
              placeholder="150.50"
              step="0.01"
              min="0"
              error={!!errors.cost_basis}
              helperText={errors.cost_basis?.toString()}
              disabled={isLoading}
              variant="filled"
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <Button
            type="submit"
            disabled={isLoading}
            variant="primary"
            isLoading={isLoading}
          >
            {isLoading ? 'Adding...' : 'Add Stock'}
          </Button>
        </div>
      </form>
    </div>
  );
}
