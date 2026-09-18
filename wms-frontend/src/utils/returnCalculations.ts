/**
 * WMS Centralized Return Calculations & Helpers
 */

export type ReturnCondition = 'Good' | 'Damaged' | 'Expired' | 'Defective' | 'Wrong Item';

export type ReturnStatus = 'Draft' | 'Pending Approval' | 'Approved' | 'Rejected' | 'Processed' | 'Completed';

export interface ReturnItemDraft {
	order_item_id: number;
	product: number;
	product_name: string;
	product_size: number;
	size: number;
	quantity: number;
	price_at_return: number;
	total: number;
	condition: ReturnCondition;
	reason: string;
	ordered_quantity?: number;
	previously_returned?: number;
	max_returnable: number;
}

/**
 * Calculates line total price: quantity * unit price
 */
export function calculateReturnLineTotal(quantity: number, unitPrice: number): number {
	const qty = Math.max(0, Number(quantity) || 0);
	const price = Math.max(0, Number(unitPrice) || 0);
	return Math.round(qty * price * 100) / 100;
}

/**
 * Computes Total Amount across all return items
 */
export function calculateTotalReturnAmount(items: { total?: number; quantity: number; price_at_return: number }[]): number {
	if (!items || items.length === 0) return 0;
	return items.reduce((sum, item) => {
		const lineTotal = item.total != null ? Number(item.total) : calculateReturnLineTotal(item.quantity, item.price_at_return);
		return sum + (lineTotal || 0);
	}, 0);
}

/**
 * Computes remaining returnable quantity for an order item
 */
export function calculateRemainingReturnable(orderedQty: number, previouslyReturnedQty: number): number {
	const ordered = Math.max(0, Number(orderedQty) || 0);
	const returned = Math.max(0, Number(previouslyReturnedQty) || 0);
	return Math.max(0, ordered - returned);
}

/**
 * Calculates detailed inventory impact breakdown:
 * - sellableUnits: returned items in Good / Wrong Item condition that replenish active stock
 * - quarantinedUnits: returned items in Damaged / Expired / Defective condition that do not inflate sellable stock
 * - deductionUnits: items deducted from warehouse stock (PR)
 */
export function calculateInventoryImpact(returnType: 'SR' | 'PR', items: { quantity: number; condition: ReturnCondition }[]) {
	let sellableUnits = 0;
	let quarantinedUnits = 0;
	let deductionUnits = 0;

	for (const item of items) {
		const qty = Math.max(0, Number(item.quantity) || 0);
		if (returnType === 'SR') {
			if (item.condition === 'Good' || item.condition === 'Wrong Item') {
				sellableUnits += qty;
			} else {
				quarantinedUnits += qty;
			}
		} else {
			deductionUnits += qty;
		}
	}

	return {
		sellableUnits,
		quarantinedUnits,
		deductionUnits,
		totalUnits: sellableUnits + quarantinedUnits + deductionUnits,
	};
}

/**
 * Return type human-friendly label
 */
export function getReturnTypeLabel(type: string): string {
	switch (type) {
		case 'SR':
			return 'Sales Return (Inbound)';
		case 'PR':
			return 'Purchase Return (Outbound)';
		default:
			return type || 'Return';
	}
}

/**
 * Return type severity token for PrimeVue Tag
 */
export function getReturnTypeSeverity(type: string): 'info' | 'warn' | 'success' | 'secondary' {
	switch (type) {
		case 'SR':
			return 'info';
		case 'PR':
			return 'warn';
		default:
			return 'secondary';
	}
}

/**
 * Return status human-friendly severity for PrimeVue Tag
 */
export function getReturnStatusSeverity(status: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' {
	switch (status) {
		case 'Completed':
		case 'Approved':
		case 'Processed':
			return 'success';
		case 'Pending Approval':
			return 'warn';
		case 'Draft':
			return 'secondary';
		case 'Rejected':
			return 'danger';
		default:
			return 'info';
	}
}

/**
 * Item condition severity token for PrimeVue Tag
 */
export function getItemConditionSeverity(condition: string): 'success' | 'warn' | 'danger' | 'secondary' {
	switch (condition) {
		case 'Good':
			return 'success';
		case 'Wrong Item':
			return 'info';
		case 'Damaged':
			return 'warn';
		case 'Defective':
			return 'warn';
		case 'Expired':
			return 'danger';
		default:
			return 'secondary';
	}
}

/**
 * Currency formatter (INR Indian Rupee)
 */
export function formatCurrency(val: number | null | undefined): string {
	if (val == null || isNaN(val)) return '₹0';
	return new Intl.NumberFormat('en-IN', {
		style: 'currency',
		currency: 'INR',
		maximumFractionDigits: 0,
	}).format(val);
}

/**
 * Standard number formatter
 */
export function formatNumber(val: number | null | undefined): string {
	if (val == null || isNaN(val)) return '0';
	return new Intl.NumberFormat('en-IN').format(val);
}
