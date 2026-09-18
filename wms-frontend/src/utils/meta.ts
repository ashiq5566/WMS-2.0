/**
 * CoreWMS Dynamic Page Title & Meta Management Utility
 */
import { watch, isRef, onMounted, type Ref } from 'vue';

export interface RouteMetaInfo {
  title: string;
  description?: string;
}

export const APP_NAME = 'CoreWMS';
export const DEFAULT_DESCRIPTION =
  'CoreWMS - Enterprise Warehouse Management System for inventory control, multi-variant order fulfillment, returns, and financial ledgers.';

/**
 * Static route dictionary mapping path patterns to page titles and descriptions
 */
export const ROUTE_TITLES: Record<string, RouteMetaInfo> = {
  '/': {
    title: 'Dashboard',
    description: 'Executive overview of warehouse inventory turnover, sales revenue, supplier payables, and pending receivables.',
  },
  '/home': {
    title: 'Dashboard',
    description: 'Executive overview of warehouse inventory turnover, sales revenue, supplier payables, and pending receivables.',
  },
  '/login': {
    title: 'Staff Login',
    description: 'Secure authentication portal for CoreWMS warehouse administrators and staff members.',
  },
  '/stocks': {
    title: 'Stock & Inventory Control',
    description: 'Manage SKU product catalog, size variants, stock levels, warehouse movements, and pricing.',
  },
  '/orders': {
    title: 'Orders Management',
    description: 'Track and manage customer sales orders (SO) and vendor purchase orders (PO) across lifecycles.',
  },
  '/orders/create': {
    title: 'Create Order',
    description: 'Draft and issue new customer sales orders or supplier purchase orders with multi-variant items.',
  },
  '/payments': {
    title: 'Financial Dashboard & Payments',
    description: 'Real-time money movement ledger tracking cash inflows, supplier disbursements, and settlement analytics.',
  },
  '/profit': {
    title: 'Profit & Margin Analytics',
    description: 'Track real-time profitability, cost of goods sold (COGS), gross profit, and margin percentages across products and orders.',
  },
  '/returns': {
    title: 'Returns & RMA Management',
    description: 'Process customer returns (SR) and vendor purchase returns (PR) with stock restoration and ledger balance adjustments.',
  },
  '/returns/create': {
    title: 'Create Return (RMA)',
    description: 'Initiate and submit a new return merchandise authorization directly or from an issued order.',
  },
  '/stakeholders': {
    title: 'Stakeholder Directory (MDM)',
    description: 'Master Data Management directory for commercial customers and vendors with credit terms and tax compliance.',
  },
  '/stakeholders/create': {
    title: 'Register New Stakeholder',
    description: 'Register and profile a new customer or supplier with logistics addresses and financial terms.',
  },
  '/users': {
    title: 'User Management',
    description: 'Manage staff credentials, operational roles, and system access permissions.',
  },
};

/**
 * Dynamically resolves the title and description for any route path (including param routes)
 */
export function resolveRouteMeta(path: string, params: Record<string, any> = {}): RouteMetaInfo {
  // Direct match
  if (ROUTE_TITLES[path]) {
    return ROUTE_TITLES[path];
  }

  // Dynamic parameterized routes
  if (path.startsWith('/orders/') && path !== '/orders/create') {
    const id = params.id || path.replace('/orders/', '');
    return {
      title: id ? `Order Details #${id}` : 'Order Details',
      description: 'Review order items, payment status, installment receipts, and RMA return documents.',
    };
  }

  if (path.startsWith('/payments/') && path !== '/payments/create') {
    const id = params.id || path.replace('/payments/', '');
    return {
      title: id ? `Payment Voucher #${id}` : 'Payment Voucher Details',
      description: 'Official settlement payment voucher with partner billing address and transaction audit timestamps.',
    };
  }

  if (path.startsWith('/returns/') && path !== '/returns/create') {
    const id = params.id || path.replace('/returns/', '');
    return {
      title: id ? `Return Authorization #${id}` : 'Return Authorization Details',
      description: 'RMA return document details, inspection states, and inventory reconciliation records.',
    };
  }

  if (path.startsWith('/stakeholders/') && path !== '/stakeholders/create') {
    const id = params.id || path.replace('/stakeholders/', '');
    return {
      title: id ? `Stakeholder 360 Profile` : 'Stakeholder Profile',
      description: '360-degree commercial profile, transaction ledger, active orders, and credit utilization history.',
    };
  }

  return {
    title: 'Warehouse Management System',
    description: DEFAULT_DESCRIPTION,
  };
}

/**
 * Updates the document title and description meta tag in the browser head
 */
export function setPageTitle(title?: string, description?: string): void {
  if (typeof document === 'undefined') return;

  const formattedTitle = title
    ? `${title.trim()} | ${APP_NAME}`
    : `${APP_NAME} - Warehouse Management System`;

  document.title = formattedTitle;

  if (description) {
    let metaDesc = document.querySelector('meta[name="description"]');
    if (!metaDesc) {
      metaDesc = document.createElement('meta');
      metaDesc.setAttribute('name', 'description');
      document.head.appendChild(metaDesc);
    }
    metaDesc.setAttribute('content', description);
  }
}

/**
 * Vue composable to declaratively set dynamic page titles within components
 */
export function usePageTitle(
  title: string | Ref<string>,
  description?: string | Ref<string>
): void {
  const apply = () => {
    const rawTitle = isRef(title) ? title.value : title;
    const rawDesc = isRef(description) ? description.value : description;
    setPageTitle(rawTitle, rawDesc);
  };

  onMounted(() => {
    apply();
  });

  if (isRef(title)) {
    watch(title, () => apply());
  }

  if (isRef(description)) {
    watch(description, () => apply());
  }
}
