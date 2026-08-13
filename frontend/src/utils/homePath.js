export function resolveHomePath({ role, permissions = [], isSuperuser = false, isMobile = false }) {
  const canViewWarehouse = isSuperuser || permissions.includes('view_warehouse_inventory')
  const canViewDashboard = isSuperuser || permissions.includes('view_dashboard')
  if (role === 'COMPANY_STOREKEEPER' || (canViewWarehouse && !canViewDashboard)) {
    return isMobile ? '/m/warehouse' : '/warehouse/overview'
  }
  return isMobile ? '/m/contracts' : '/'
}
