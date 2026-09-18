/**
 * WMS Centralized Payment & Financial Calculations
 */

export interface PaymentRecord {
	id?: number;
	payment_number?: string;
	payment_type?: 'INBOUND' | 'OUTBOUND' | 'REFUND';
	status?: 'Completed' | 'Pending' | 'Failed' | 'Cancelled';
	reference?: string;
	notes?: string;
	order?: number | null;
	order_obj?: any;
	company?: number | null;
	company_obj?: any;
	amount: number;
	payment_date: string;
	payment_method: 'CASH' | 'CARD' | 'BANK' | 'OTHER';
	created_at?: string;
	updated_at?: string;
}

/**
 * Currency formatter (INR Indian Rupee)
 */
export function formatCurrency(val: number | null | undefined): string {
	if (val == null || isNaN(Number(val))) return "₹0";
	return new Intl.NumberFormat("en-IN", {
		style: "currency",
		currency: "INR",
		maximumFractionDigits: 0,
	}).format(Number(val));
}

/**
 * Standard number formatter
 */
export function formatNumber(val: number | null | undefined): string {
	if (val == null || isNaN(Number(val))) return "0";
	return new Intl.NumberFormat("en-IN").format(Number(val));
}

/**
 * Payment type label and color severity
 */
export function getPaymentTypeInfo(type?: string): {
	label: string;
	severity: "success" | "warn" | "danger" | "info" | "secondary";
	icon: string;
	direction: "in" | "out" | "neutral";
} {
	switch (type) {
		case 'INBOUND':
			return {
				label: 'Customer Receipt',
				severity: 'success',
				icon: 'pi pi-arrow-down-left',
				direction: 'in',
			};
		case 'OUTBOUND':
			return {
				label: 'Supplier Disbursement',
				severity: 'warn',
				icon: 'pi pi-arrow-up-right',
				direction: 'out',
			};
		case 'REFUND':
			return {
				label: 'Customer Refund',
				severity: 'danger',
				icon: 'pi pi-replay',
				direction: 'out',
			};
		default:
			return {
				label: type || 'Receipt',
				severity: 'info',
				icon: 'pi pi-wallet',
				direction: 'in',
			};
	}
}

/**
 * Status severity color tokens
 */
export function getPaymentStatusSeverity(status?: string): "success" | "warn" | "danger" | "secondary" {
	switch (status) {
		case 'Completed':
			return 'success';
		case 'Pending':
			return 'warn';
		case 'Failed':
		case 'Cancelled':
			return 'danger';
		default:
			return 'secondary';
	}
}

/**
 * Payment method visual icons and labels
 */
export function getPaymentMethodInfo(method?: string): { label: string; icon: string } {
	switch (method) {
		case 'CASH':
			return { label: 'Cash', icon: 'pi pi-money-bill' };
		case 'CARD':
			return { label: 'Debit / Credit Card', icon: 'pi pi-credit-card' };
		case 'BANK':
			return { label: 'Bank Transfer (NEFT/RTGS/IMPS)', icon: 'pi pi-building' };
		case 'OTHER':
		default:
			return { label: method || 'Other Method', icon: 'pi pi-wallet' };
	}
}

/**
 * Returns Tailwind badge classes for a given payment method
 */
export function getMethodBadgeClass(method?: string): string {
	switch (method) {
		case 'CASH':
			return 'px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400';
		case 'CARD':
			return 'px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-400';
		case 'BANK':
			return 'px-2 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800 dark:bg-purple-950/40 dark:text-purple-400';
		case 'UPI':
			return 'px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400';
		default:
			return 'px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300';
	}
}

/**
 * Evaluates commercial order payment condition
 */
export function evaluateOrderPaymentStatus(totalAmount: number, pendingAmount: number): {
	status: 'Paid' | 'Partially Paid' | 'Unpaid';
	severity: 'success' | 'warn' | 'danger';
	paidAmount: number;
	progressPercentage: number;
} {
	const total = Math.max(0, Number(totalAmount) || 0);
	const pending = Math.max(0, Number(pendingAmount) || 0);
	const paid = Math.max(0, total - pending);

	if (total <= 0 || pending <= 0) {
		return { status: 'Paid', severity: 'success', paidAmount: total, progressPercentage: 100 };
	}
	if (paid > 0 && pending > 0) {
		const progress = Math.min(100, Math.round((paid / total) * 100));
		return { status: 'Partially Paid', severity: 'warn', paidAmount: paid, progressPercentage: progress };
	}
	return { status: 'Unpaid', severity: 'danger', paidAmount: 0, progressPercentage: 0 };
}

/**
 * Client-side validation for recording payments
 */
export function validatePaymentPayload(data: {
	amount: number | string;
	payment_date: string | Date;
	payment_method: string;
	company?: any;
	order?: any;
	pendingAmount?: number;
}): Record<string, string> {
	const errors: Record<string, string> = {};

	const numAmount = Number(data.amount);
	if (!data.amount || isNaN(numAmount) || numAmount <= 0) {
		errors.amount = "Payment amount must be greater than zero.";
	} else if (data.pendingAmount != null && numAmount > Number(data.pendingAmount)) {
		errors.amount = `Amount (₹${numAmount}) exceeds outstanding balance (₹${data.pendingAmount}).`;
	}

	if (!data.payment_method) {
		errors.payment_method = "Payment method is required.";
	}

	if (!data.payment_date) {
		errors.payment_date = "Payment date is required.";
	}

	if (!data.company && !data.order) {
		errors.company = "A linked order or stakeholder partner must be selected.";
	}

	return errors;
}
