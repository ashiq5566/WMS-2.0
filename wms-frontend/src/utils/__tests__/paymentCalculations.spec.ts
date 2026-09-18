import { describe, it, expect } from 'vitest';
import {
	formatCurrency,
	formatNumber,
	getPaymentTypeInfo,
	getPaymentStatusSeverity,
	evaluateOrderPaymentStatus,
	validatePaymentPayload,
} from '../paymentCalculations';

describe('Payment & Financial Calculation Engine (Frontend)', () => {
	describe('formatCurrency & formatNumber', () => {
		it('formats currency with INR symbol and Indian grouping', () => {
			expect(formatCurrency(1000)).toMatch(/₹\s?1,000/);
			expect(formatCurrency(150000)).toMatch(/₹\s?1,50,000/);
			expect(formatCurrency(0)).toMatch(/₹\s?0/);
			expect(formatCurrency(null)).toBe('₹0');
			expect(formatCurrency(undefined)).toBe('₹0');
		});

		it('formats numbers with Indian grouping', () => {
			expect(formatNumber(1000)).toBe('1,000');
			expect(formatNumber(150000)).toBe('1,50,000');
			expect(formatNumber(null)).toBe('0');
		});
	});

	describe('getPaymentTypeInfo & Severity', () => {
		it('returns correct classification metadata for INBOUND, OUTBOUND, and REFUND', () => {
			const inbound = getPaymentTypeInfo('INBOUND');
			expect(inbound.label).toBe('Customer Receipt');
			expect(inbound.severity).toBe('success');
			expect(inbound.direction).toBe('in');

			const outbound = getPaymentTypeInfo('OUTBOUND');
			expect(outbound.label).toBe('Supplier Disbursement');
			expect(outbound.severity).toBe('warn');
			expect(outbound.direction).toBe('out');

			const refund = getPaymentTypeInfo('REFUND');
			expect(refund.label).toBe('Customer Refund');
			expect(refund.severity).toBe('danger');
			expect(refund.direction).toBe('out');
		});

		it('maps status to correct PrimeVue severity token', () => {
			expect(getPaymentStatusSeverity('Completed')).toBe('success');
			expect(getPaymentStatusSeverity('Pending')).toBe('warn');
			expect(getPaymentStatusSeverity('Failed')).toBe('danger');
			expect(getPaymentStatusSeverity('Cancelled')).toBe('danger');
		});
	});

	describe('evaluateOrderPaymentStatus', () => {
		it('evaluates completely paid order (pending == 0)', () => {
			const res = evaluateOrderPaymentStatus(5000, 0);
			expect(res.status).toBe('Paid');
			expect(res.severity).toBe('success');
			expect(res.paidAmount).toBe(5000);
			expect(res.progressPercentage).toBe(100);
		});

		it('evaluates partially paid order', () => {
			const res = evaluateOrderPaymentStatus(10000, 4000);
			expect(res.status).toBe('Partially Paid');
			expect(res.severity).toBe('warn');
			expect(res.paidAmount).toBe(6000);
			expect(res.progressPercentage).toBe(60);
		});

		it('evaluates completely unpaid order (pending == total)', () => {
			const res = evaluateOrderPaymentStatus(8000, 8000);
			expect(res.status).toBe('Unpaid');
			expect(res.severity).toBe('danger');
			expect(res.paidAmount).toBe(0);
			expect(res.progressPercentage).toBe(0);
		});

		it('handles non-negative clamping on edge cases', () => {
			const res = evaluateOrderPaymentStatus(-100, -50);
			expect(res.status).toBe('Paid');
			expect(res.paidAmount).toBe(0);
			expect(res.progressPercentage).toBe(100);
		});
	});

	describe('validatePaymentPayload (Client-side Overpayment Guards)', () => {
		it('rejects non-positive and zero payment amounts', () => {
			const errZero = validatePaymentPayload({
				amount: 0,
				payment_date: '2026-09-18',
				payment_method: 'CASH',
				order: 1,
				pendingAmount: 500,
			});
			expect(errZero.amount).toBe('Payment amount must be greater than zero.');

			const errNegative = validatePaymentPayload({
				amount: -100,
				payment_date: '2026-09-18',
				payment_method: 'CASH',
				order: 1,
				pendingAmount: 500,
			});
			expect(errNegative.amount).toBe('Payment amount must be greater than zero.');
		});

		it('enforces overpayment guard when amount exceeds pendingAmount', () => {
			const errOver = validatePaymentPayload({
				amount: 750,
				payment_date: '2026-09-18',
				payment_method: 'BANK',
				order: 1,
				pendingAmount: 500,
			});
			expect(errOver.amount).toBe('Amount (₹750) exceeds outstanding balance (₹500).');
		});

		it('passes validation when amount <= pendingAmount and fields are valid', () => {
			const errors = validatePaymentPayload({
				amount: 500,
				payment_date: '2026-09-18',
				payment_method: 'BANK',
				order: 1,
				pendingAmount: 500,
			});
			expect(Object.keys(errors).length).toBe(0);
		});

		it('requires payment method, payment date, and link target', () => {
			const errors = validatePaymentPayload({
				amount: 100,
				payment_date: '',
				payment_method: '',
			});
			expect(errors.payment_method).toBe('Payment method is required.');
			expect(errors.payment_date).toBe('Payment date is required.');
			expect(errors.company).toBe('A linked order or stakeholder partner must be selected.');
		});
	});
});
