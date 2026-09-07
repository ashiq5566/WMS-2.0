/**
 * WMS Centralized Order Calculations & Helpers
 */

export interface OrderLineItem {
	product: number;
	product_name: string;
	product_size?: number | null;
	size: number;
	quantity: number;
	price_at_time_of_order: number;
	total?: number;
	unit?: string | null;
	stock?: number;
	cost_price?: number;
}

/**
 * Calculates line total price: quantity * unit price
 */
export function calculateLineTotal(quantity: number, unitPrice: number): number {
	const qty = Math.max(0, Number(quantity) || 0);
	const price = Math.max(0, Number(unitPrice) || 0);
	return Math.round(qty * price * 100) / 100;
}

/**
 * Computes Gross Amount / Subtotal across all order items
 */
export function calculateGrossAmount(items: OrderLineItem[]): number {
	if (!items || items.length === 0) return 0;
	return items.reduce((sum, item) => {
		const lineTotal = item.total != null ? Number(item.total) : calculateLineTotal(item.quantity, item.price_at_time_of_order);
		return sum + (lineTotal || 0);
	}, 0);
}

/**
 * Computes Net Amount after deducting discount (bounded to not go below 0)
 */
export function calculateNetAmount(grossAmount: number, discount: number): number {
	const gross = Math.max(0, Number(grossAmount) || 0);
	const disc = Math.max(0, Number(discount) || 0);
	return Math.max(0, gross - disc);
}

/**
 * Calculates Outstanding Balance Due: Net Amount minus Down Payment
 */
export function calculateBalanceDue(netAmount: number, downPayment: number): number {
	const net = Math.max(0, Number(netAmount) || 0);
	const paid = Math.max(0, Number(downPayment) || 0);
	return Math.max(0, net - paid);
}

/**
 * Calculates Gross Margin % for sales orders
 */
export function calculateGrossMargin(sellingPrice: number, costPrice: number): number | null {
	if (!sellingPrice || sellingPrice <= 0 || costPrice == null) return null;
	const margin = ((sellingPrice - costPrice) / sellingPrice) * 100;
	return Math.round(margin);
}

/**
 * Currency formatter (INR Indian Rupee)
 */
export function formatCurrency(val: number | null | undefined): string {
	if (val == null || isNaN(val)) return "₹0";
	return new Intl.NumberFormat("en-IN", {
		style: "currency",
		currency: "INR",
		maximumFractionDigits: 0,
	}).format(val);
}

/**
 * Standard number formatter
 */
export function formatNumber(val: number | null | undefined): string {
	if (val == null || isNaN(val)) return "0";
	return new Intl.NumberFormat("en-IN").format(val);
}

/**
 * Status severity color tokens for PrimeVue Tags
 */
export function getOrderStatusSeverity(status: string): "success" | "info" | "warn" | "danger" | "secondary" {
	switch (status) {
		case "Delivered":
		case "Recieved":
			return "success";
		case "Issued":
			return "warn";
		case "Cancelled":
			return "danger";
		case "Closed":
			return "info";
		default:
			return "secondary";
	}
}

/**
 * Human-readable order type label
 */
export function getOrderTypeLabel(type: string): string {
	return type === "SO" ? "Sales Order" : type === "PO" ? "Purchase Order" : type;
}
