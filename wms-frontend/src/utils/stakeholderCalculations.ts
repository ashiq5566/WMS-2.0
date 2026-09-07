/**
 * WMS Centralized Stakeholder Master Data Calculations & Helpers
 */

export interface StakeholderRecord {
	id?: number;
	stakeholder_id?: string;
	name: string;
	company_name?: string;
	contact_person?: string;
	address?: string;
	shipping_address?: string;
	city?: string;
	state?: string;
	country?: string;
	postal_code?: string;
	mobile?: string;
	alternate_phone?: string;
	email?: string;
	website?: string;
	type: 'Customer' | 'Supplier';
	tax_id?: string;
	pan_number?: string;
	payment_terms?: string;
	credit_limit?: number;
	opening_balance?: number;
	notes?: string;
	is_active?: boolean;
	is_deleted?: boolean;
	total_pending_amount?: number;
	total_setteled_amount?: number;
	total_orders_count?: number;
	total_sales_amount?: number;
	total_returns_count?: number;
	date_added?: string;
	date_updated?: string;
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
 * Status severity color tokens for PrimeVue Tags
 */
export function getStakeholderStatusSeverity(isDeleted?: boolean, isActive?: boolean): "success" | "danger" | "warn" {
	if (isDeleted === true || isActive === false) {
		return "danger";
	}
	return "success";
}

/**
 * Human-readable status label
 */
export function getStakeholderStatusLabel(isDeleted?: boolean, isActive?: boolean): "ACTIVE" | "INACTIVE" {
	return (isDeleted === true || isActive === false) ? "INACTIVE" : "ACTIVE";
}

/**
 * Type severity color tokens for PrimeVue Tags
 */
export function getStakeholderTypeSeverity(type: string): "info" | "warn" | "secondary" {
	if (type === 'Customer') return "info";
	if (type === 'Supplier') return "warn";
	return "secondary";
}

/**
 * Calculates credit utilization percentage and remaining limit
 */
export function calculateCreditUtilization(pendingBalance: number, creditLimit: number): {
	percentage: number;
	remaining: number;
	isExceeded: boolean;
	severity: 'success' | 'warn' | 'danger';
} {
	const pending = Math.max(0, Number(pendingBalance) || 0);
	const limit = Math.max(0, Number(creditLimit) || 0);

	if (limit <= 0) {
		return {
			percentage: 0,
			remaining: 0,
			isExceeded: false,
			severity: 'success',
		};
	}

	const percentage = Math.min(100, Math.round((pending / limit) * 100));
	const remaining = Math.max(0, limit - pending);
	const isExceeded = pending > limit;

	let severity: 'success' | 'warn' | 'danger' = 'success';
	if (isExceeded || percentage >= 90) {
		severity = 'danger';
	} else if (percentage >= 70) {
		severity = 'warn';
	}

	return {
		percentage,
		remaining,
		isExceeded,
		severity,
	};
}

/**
 * Calculates debt settlement progress percentage
 */
export function calculateSettlementProgress(settledAmount: number, pendingAmount: number): number {
	const settled = Math.max(0, Number(settledAmount) || 0);
	const pending = Math.max(0, Number(pendingAmount) || 0);
	const total = settled + pending;
	if (total <= 0) return 100;
	return Math.min(100, Math.round((settled / total) * 100));
}

/**
 * Client-side validation for stakeholder forms
 */
export function validateStakeholder(form: Partial<StakeholderRecord>): Record<string, string> {
	const errors: Record<string, string> = {};

	if (!form.name || !form.name.trim()) {
		errors.name = "Name is required.";
	} else if (form.name.trim().length < 2) {
		errors.name = "Name must be at least 2 characters.";
	}

	if (!form.type || !['Customer', 'Supplier'].includes(form.type)) {
		errors.type = "Type must be either Customer or Supplier.";
	}

	if (form.email && form.email.trim()) {
		const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
		if (!emailPattern.test(form.email.trim())) {
			errors.email = "Please enter a valid email address.";
		}
	}

	if (form.mobile && form.mobile.trim()) {
		const phoneClean = form.mobile.replace(/[\s\-\(\)\+]/g, '');
		if (phoneClean.length < 7 || phoneClean.length > 15) {
			errors.mobile = "Phone number must be between 7 and 15 digits.";
		}
	}

	if (form.credit_limit != null && Number(form.credit_limit) < 0) {
		errors.credit_limit = "Credit limit cannot be negative.";
	}

	return errors;
}
