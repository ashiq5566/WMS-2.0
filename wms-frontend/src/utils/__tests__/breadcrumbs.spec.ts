import { describe, it, expect } from 'vitest';
import { resolveBreadcrumbs } from '../breadcrumbs';

describe('resolveBreadcrumbs utility', () => {
  it('returns single breadcrumb on root or dashboard', () => {
    const homeCrumbs = resolveBreadcrumbs('/home');
    expect(homeCrumbs).toHaveLength(1);
    expect(homeCrumbs[0]).toEqual({
      label: 'Dashboard',
      to: '/home',
      icon: 'pi pi-home',
      isCurrent: true,
    });

    const rootCrumbs = resolveBreadcrumbs('/');
    expect(rootCrumbs).toHaveLength(1);
    expect(rootCrumbs[0].isCurrent).toBe(true);
  });

  it('returns 2 breadcrumbs on section index pages', () => {
    const stockCrumbs = resolveBreadcrumbs('/stocks');
    expect(stockCrumbs).toHaveLength(2);
    expect(stockCrumbs[0].label).toBe('Dashboard');
    expect(stockCrumbs[0].isCurrent).toBe(false);
    expect(stockCrumbs[1].label).toBe('Stocks');
    expect(stockCrumbs[1].to).toBe('/stocks');
    expect(stockCrumbs[1].isCurrent).toBe(true);

    const ordersCrumbs = resolveBreadcrumbs('/orders');
    expect(ordersCrumbs).toHaveLength(2);
    expect(ordersCrumbs[1].label).toBe('Orders');
    expect(ordersCrumbs[1].isCurrent).toBe(true);
  });

  it('returns 3 breadcrumbs on nested creation pages', () => {
    const orderCreateCrumbs = resolveBreadcrumbs('/orders/create');
    expect(orderCreateCrumbs).toHaveLength(3);
    expect(orderCreateCrumbs[0].label).toBe('Dashboard');
    expect(orderCreateCrumbs[1].label).toBe('Orders');
    expect(orderCreateCrumbs[2].label).toBe('Create Order');
    expect(orderCreateCrumbs[2].isCurrent).toBe(true);

    const returnCreateCrumbs = resolveBreadcrumbs('/returns/create');
    expect(returnCreateCrumbs).toHaveLength(3);
    expect(returnCreateCrumbs[2].label).toBe('Create Return');
  });

  it('returns formatted label on dynamic detail pages', () => {
    const orderDetailCrumbs = resolveBreadcrumbs('/orders/102', { id: '102' });
    expect(orderDetailCrumbs).toHaveLength(3);
    expect(orderDetailCrumbs[2].label).toBe('Order #102');
    expect(orderDetailCrumbs[2].to).toBe('/orders/102');

    const returnDetailCrumbs = resolveBreadcrumbs('/returns/5', { id: '5' });
    expect(returnDetailCrumbs).toHaveLength(3);
    expect(returnDetailCrumbs[2].label).toBe('RMA-0005');
  });
});
