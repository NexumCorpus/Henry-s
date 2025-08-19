import React from 'react';
import { StockLevel, Location } from '../../types/inventory';

interface InventoryOverviewProps {
  stockLevels: StockLevel[];
  locations: Location[];
  selectedLocationId?: string;
}

const InventoryOverview: React.FC<InventoryOverviewProps> = ({
  stockLevels,
  locations,
  selectedLocationId,
}) => {
  const getStockStats = () => {
    const filteredLevels = selectedLocationId 
      ? stockLevels.filter(level => level.locationId === selectedLocationId)
      : stockLevels;

    const totalItems = filteredLevels.length;
    const inStock = filteredLevels.filter(level => level.status === 'in_stock').length;
    const lowStock = filteredLevels.filter(level => level.status === 'low_stock').length;
    const outOfStock = filteredLevels.filter(level => level.status === 'out_of_stock').length;
    const overstock = filteredLevels.filter(level => level.status === 'overstock').length;

    const totalValue = filteredLevels.reduce((sum, level) => {
      // Note: We'd need to join with inventory items to get cost per unit
      // For now, using a placeholder calculation
      return sum + (level.currentStock * 10); // Placeholder cost
    }, 0);

    return {
      totalItems,
      inStock,
      lowStock,
      outOfStock,
      overstock,
      totalValue,
      inStockPercentage: totalItems > 0 ? Math.round((inStock / totalItems) * 100) : 0,
      lowStockPercentage: totalItems > 0 ? Math.round((lowStock / totalItems) * 100) : 0,
    };
  };

  const stats = getStockStats();
  const selectedLocation = selectedLocationId 
    ? locations.find(loc => loc.id === selectedLocationId)
    : null;

  return (
    <div className="inventory-overview">
      <div className="inventory-overview__header">
        <h2>
          {selectedLocation ? `${selectedLocation.name} Overview` : 'All Locations Overview'}
        </h2>
      </div>

      <div className="inventory-overview__stats">
        <div className="inventory-overview__stat-card inventory-overview__stat-card--primary">
          <div className="inventory-overview__stat-value">{stats.totalItems}</div>
          <div className="inventory-overview__stat-label">Total Items</div>
        </div>

        <div className="inventory-overview__stat-card inventory-overview__stat-card--success">
          <div className="inventory-overview__stat-value">{stats.inStock}</div>
          <div className="inventory-overview__stat-label">In Stock</div>
          <div className="inventory-overview__stat-percentage">{stats.inStockPercentage}%</div>
        </div>

        <div className="inventory-overview__stat-card inventory-overview__stat-card--warning">
          <div className="inventory-overview__stat-value">{stats.lowStock}</div>
          <div className="inventory-overview__stat-label">Low Stock</div>
          <div className="inventory-overview__stat-percentage">{stats.lowStockPercentage}%</div>
        </div>

        <div className="inventory-overview__stat-card inventory-overview__stat-card--danger">
          <div className="inventory-overview__stat-value">{stats.outOfStock}</div>
          <div className="inventory-overview__stat-label">Out of Stock</div>
        </div>

        <div className="inventory-overview__stat-card inventory-overview__stat-card--info">
          <div className="inventory-overview__stat-value">${stats.totalValue.toLocaleString()}</div>
          <div className="inventory-overview__stat-label">Total Value</div>
        </div>
      </div>

      <div className="inventory-overview__status-bar">
        <div className="inventory-overview__status-bar-fill">
          <div 
            className="inventory-overview__status-segment inventory-overview__status-segment--success"
            style={{ width: `${stats.inStockPercentage}%` }}
          />
          <div 
            className="inventory-overview__status-segment inventory-overview__status-segment--warning"
            style={{ width: `${stats.lowStockPercentage}%` }}
          />
          <div 
            className="inventory-overview__status-segment inventory-overview__status-segment--danger"
            style={{ width: `${(stats.outOfStock / stats.totalItems) * 100}%` }}
          />
        </div>
      </div>

      <div className="inventory-overview__legend">
        <div className="inventory-overview__legend-item">
          <div className="inventory-overview__legend-color inventory-overview__legend-color--success"></div>
          <span>In Stock</span>
        </div>
        <div className="inventory-overview__legend-item">
          <div className="inventory-overview__legend-color inventory-overview__legend-color--warning"></div>
          <span>Low Stock</span>
        </div>
        <div className="inventory-overview__legend-item">
          <div className="inventory-overview__legend-color inventory-overview__legend-color--danger"></div>
          <span>Out of Stock</span>
        </div>
      </div>
    </div>
  );
};

export default InventoryOverview;