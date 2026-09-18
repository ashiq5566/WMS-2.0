/**
 * CoreWMS Breadcrumb Navigation Resolver Utility
 */

export interface BreadcrumbItem {
  label: string;
  to: string;
  icon?: string;
  isCurrent: boolean;
}

const SECTION_METADATA: Record<string, { label: string; icon: string; singular: string }> = {
  stocks: { label: 'Stocks', icon: 'pi pi-box', singular: 'Product' },
  orders: { label: 'Orders', icon: 'pi pi-shopping-cart', singular: 'Order' },
  payments: { label: 'Payments', icon: 'pi pi-wallet', singular: 'Payment' },
  returns: { label: 'Returns', icon: 'pi pi-undo', singular: 'Return' },
  stakeholders: { label: 'Stakeholders', icon: 'pi pi-users', singular: 'Stakeholder' },
  users: { label: 'Users', icon: 'pi pi-user', singular: 'User' },
};

/**
 * Resolves breadcrumb items based on current route path and route params
 */
export function resolveBreadcrumbs(path: string, params: Record<string, any> = {}): BreadcrumbItem[] {
  // Always start with Dashboard
  const homeItem: BreadcrumbItem = {
    label: 'Dashboard',
    to: '/home',
    icon: 'pi pi-home',
    isCurrent: path === '/' || path === '/home',
  };

  if (path === '/' || path === '/home') {
    return [homeItem];
  }

  const items: BreadcrumbItem[] = [{ ...homeItem, isCurrent: false }];
  const segments = path.split('/').filter(Boolean);

  if (segments.length === 0) {
    return [homeItem];
  }

  const section = segments[0];
  const sectionMeta = SECTION_METADATA[section];

  if (!sectionMeta) {
    items.push({
      label: section.charAt(0).toUpperCase() + section.slice(1),
      to: `/${section}`,
      isCurrent: segments.length === 1,
    });
  } else {
    items.push({
      label: sectionMeta.label,
      to: `/${section}`,
      icon: sectionMeta.icon,
      isCurrent: segments.length === 1,
    });
  }

  if (segments.length > 1) {
    const sub = segments[1];
    let subLabel = sub;

    if (sub === 'create') {
      if (section === 'orders') subLabel = 'Create Order';
      else if (section === 'returns') subLabel = 'Create Return';
      else if (section === 'stakeholders') subLabel = 'New Stakeholder';
      else subLabel = 'Create New';
    } else {
      const idVal = params.id || sub;
      if (section === 'orders') {
        subLabel = `Order #${idVal}`;
      } else if (section === 'returns') {
        subLabel = `RMA-${String(idVal).padStart(4, '0')}`;
      } else if (section === 'payments') {
        subLabel = `Payment #${idVal}`;
      } else if (section === 'stakeholders') {
        subLabel = `Stakeholder #${idVal}`;
      } else {
        subLabel = `#${idVal}`;
      }
    }

    items.push({
      label: subLabel,
      to: path,
      isCurrent: true,
    });
  }

  return items;
}
