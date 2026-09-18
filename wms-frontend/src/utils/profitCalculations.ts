/**
 * CoreWMS Profit Tracking & Margin Analytics Calculation Engine
 */

export interface ProfitKpiData {
	total_revenue: number;
	total_cogs: number;
	gross_profit: number;
	profit_margin_pct: number;
	total_orders_count: number;
	total_items_sold: number;
	total_returned_units: number;
	total_returned_revenue: number;
	profitable_products_count: number;
	loss_products_count: number;
}

export interface ProductProfitRow {
	product_id: string;
	raw_product_id: number;
	product_name: string;
	size_id: number | null;
	size: string | number;
	unit: string;
	units_sold: number;
	units_returned: number;
	avg_selling_price: number;
	cost_price: number;
	total_revenue: number;
	total_cogs: number;
	gross_profit: number;
	profit_margin_pct: number;
	is_profitable: boolean;
}

export interface OrderProfitRow {
	order_id: number;
	order_number: string;
	order_date: string | null;
	stakeholder_name: string;
	order_status: string;
	items_count: number;
	total_revenue: number;
	total_cogs: number;
	gross_profit: number;
	profit_margin_pct: number;
	is_profitable: boolean;
}

export interface MonthlyProfitTrend {
	month: string;
	revenue: number;
	cogs: number;
	gross_profit: number;
	margin_pct: number;
}

/**
 * Calculates Gross Profit: Revenue - COGS
 */
export function calculateGrossProfit(revenue: number, cogs: number): number {
	const rev = Number(revenue) || 0;
	const cost = Number(cogs) || 0;
	return Number((rev - cost).toFixed(2));
}

/**
 * Calculates Profit Margin (%): ((Revenue - COGS) / Revenue) * 100
 * Handles non-positive revenue safely (returns 0.0)
 */
export function calculateProfitMargin(revenue: number, cogs: number): number {
	const rev = Number(revenue) || 0;
	const cost = Number(cogs) || 0;
	if (rev <= 0) return 0.0;
	const profit = rev - cost;
	return Number(((profit / rev) * 100).toFixed(1));
}

/**
 * Maps profit margin percentage to PrimeVue severity badge token
 */
export function getMarginBadgeSeverity(marginPct: number | null | undefined): 'success' | 'warn' | 'danger' {
	if (marginPct == null || isNaN(Number(marginPct))) return 'warn';
	const margin = Number(marginPct);
	if (margin >= 25) return 'success';
	if (margin >= 0) return 'warn';
	return 'danger';
}

/**
 * Formats a margin percentage with sign and symbol
 */
export function formatMargin(marginPct: number | null | undefined): string {
	if (marginPct == null || isNaN(Number(marginPct))) return '0.0%';
	const margin = Number(marginPct);
	return `${margin >= 0 ? '+' : ''}${margin.toFixed(1)}%`;
}

/**
 * Descriptive label for profit status
 */
export function getProfitStatusText(marginPct: number | null | undefined): string {
	if (marginPct == null || isNaN(Number(marginPct))) return 'Break-Even';
	const margin = Number(marginPct);
	if (margin > 30) return 'High Margin';
	if (margin > 15) return 'Healthy Margin';
	if (margin >= 0) return 'Low Margin';
	return 'Loss-Making';
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
 * Standard integer / count formatter
 */
export function formatNumber(val: number | null | undefined): string {
	if (val == null || isNaN(Number(val))) return "0";
	return new Intl.NumberFormat("en-IN").format(Number(val));
}
