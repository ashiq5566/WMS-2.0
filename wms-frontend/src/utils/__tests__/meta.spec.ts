import { describe, it, expect, beforeEach } from 'vitest';
import { resolveRouteMeta, setPageTitle, ROUTE_TITLES, APP_NAME } from '../meta';

describe('Meta & Page Title Utility', () => {
  beforeEach(() => {
    document.title = '';
    const existingMeta = document.querySelector('meta[name="description"]');
    if (existingMeta) {
      existingMeta.remove();
    }
  });

  it('should correctly resolve static route meta', () => {
    expect(resolveRouteMeta('/home').title).toBe('Dashboard');
    expect(resolveRouteMeta('/stocks').title).toBe('Stock & Inventory Control');
    expect(resolveRouteMeta('/orders').title).toBe('Orders Management');
    expect(resolveRouteMeta('/orders/create').title).toBe('Create Order');
    expect(resolveRouteMeta('/payments').title).toBe('Financial Dashboard & Payments');
    expect(resolveRouteMeta('/returns').title).toBe('Returns & RMA Management');
    expect(resolveRouteMeta('/returns/create').title).toBe('Create Return (RMA)');
    expect(resolveRouteMeta('/stakeholders').title).toBe('Stakeholder Directory (MDM)');
    expect(resolveRouteMeta('/stakeholders/create').title).toBe('Register New Stakeholder');
    expect(resolveRouteMeta('/users').title).toBe('User Management');
    expect(resolveRouteMeta('/login').title).toBe('Staff Login');
  });

  it('should dynamically resolve parameterized route meta', () => {
    const orderMeta = resolveRouteMeta('/orders/42', { id: '42' });
    expect(orderMeta.title).toBe('Order Details #42');

    const paymentMeta = resolveRouteMeta('/payments/10', { id: '10' });
    expect(paymentMeta.title).toBe('Payment Voucher #10');

    const returnMeta = resolveRouteMeta('/returns/5', { id: '5' });
    expect(returnMeta.title).toBe('Return Authorization #5');

    const stakeholderMeta = resolveRouteMeta('/stakeholders/1', { id: '1' });
    expect(stakeholderMeta.title).toBe('Stakeholder 360 Profile');
  });

  it('should update document.title and meta description correctly', () => {
    setPageTitle('Test Page', 'This is a test description');
    expect(document.title).toBe(`Test Page | ${APP_NAME}`);

    const meta = document.querySelector('meta[name="description"]');
    expect(meta).not.toBeNull();
    expect(meta?.getAttribute('content')).toBe('This is a test description');
  });

  it('should fallback to default title when title is empty', () => {
    setPageTitle('');
    expect(document.title).toBe(`${APP_NAME} - Warehouse Management System`);
  });
});
