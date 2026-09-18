import { describe, it, expect } from 'vitest';
import {
	calculateGrossProfit,
	calculateProfitMargin,
	getMarginBadgeSeverity,
	formatMargin,
	getProfitStatusText,
	formatCurrency,
	formatNumber,
} from '../profitCalculations';

describe('Profit & Margin Calculations Engine (Frontend)', () => {
	describe('calculateGrossProfit', () => {
		it('calculates positive gross profit correctly', () => {
			expect(calculateGrossProfit(1000, 600)).toBe(400);
			expect(calculateGrossProfit(50000, 32000)).toBe(18000);
		});

		it('calculates negative gross profit (loss) correctly', () => {
			expect(calculateGrossProfit(400, 600)).toBe(-200);
		});

		it('handles zero revenue and costs gracefully', () => {
			expect(calculateGrossProfit(0, 0)).toBe(0);
		});
	});

	describe('calculateProfitMargin', () => {
		it('calculates standard positive profit margins', () => {
			// (400 / 1000) * 100 = 40.0%
			expect(calculateProfitMargin(1000, 600)).toBe(40.0);
			// (500 / 1200) * 100 = 41.7%
			expect(calculateProfitMargin(1200, 700)).toBe(41.7);
		});

		it('handles negative profit margins (loss-making lines)', () => {
			// (-200 / 400) * 100 = -50.0%
			expect(calculateProfitMargin(400, 600)).toBe(-50.0);
		});

		it('protects against division by zero when revenue <= 0', () => {
			expect(calculateProfitMargin(0, 100)).toBe(0.0);
			expect(calculateProfitMargin(-50, 100)).toBe(0.0);
			expect(calculateProfitMargin(0, 0)).toBe(0.0);
		});
	});

	describe('getMarginBadgeSeverity', () => {
		it('assigns success to high margins (>= 25%)', () => {
			expect(getMarginBadgeSeverity(35.5)).toBe('success');
			expect(getMarginBadgeSeverity(25.0)).toBe('success');
		});

		it('assigns warn to low positive margins (0% to 24.9%)', () => {
			expect(getMarginBadgeSeverity(15.0)).toBe('warn');
			expect(getMarginBadgeSeverity(0.0)).toBe('warn');
		});

		it('assigns danger to negative margins (< 0%)', () => {
			expect(getMarginBadgeSeverity(-5.2)).toBe('danger');
			expect(getMarginBadgeSeverity(-50.0)).toBe('danger');
		});
	});

	describe('formatMargin & getProfitStatusText', () => {
		it('formats positive margin with plus sign', () => {
			expect(formatMargin(42.5)).toBe('+42.5%');
			expect(formatMargin(0.0)).toBe('+0.0%');
		});

		it('formats negative margin with minus sign', () => {
			expect(formatMargin(-12.3)).toBe('-12.3%');
		});

		it('returns accurate descriptive status text', () => {
			expect(getProfitStatusText(35)).toBe('High Margin');
			expect(getProfitStatusText(20)).toBe('Healthy Margin');
			expect(getProfitStatusText(5)).toBe('Low Margin');
			expect(getProfitStatusText(-10)).toBe('Loss-Making');
		});
	});

	describe('formatCurrency & formatNumber', () => {
		it('formats currency in Indian Rupee format', () => {
			expect(formatCurrency(125000)).toMatch(/₹\s?1,25,000/);
			expect(formatCurrency(0)).toMatch(/₹\s?0/);
		});

		it('formats integer values in Indian numbering system', () => {
			expect(formatNumber(125000)).toBe('1,25,000');
			expect(formatNumber(100)).toBe('100');
		});
	});
});
