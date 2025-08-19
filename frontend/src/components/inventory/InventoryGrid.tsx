import React from 'react';
import { InventoryItem, StockLevel } from '../../types/inventory';
import InventoryItemCard from './InventoryItemCard';

interface InventoryGridProps {
  items: InventoryItem[];
  stockLevels: StockLevel[];
  onItemSelect: (itemId: string) => void;
  isLoading: boolean;
}

const InventoryGrid: React.FC<InventoryGridProps> = ({
  items,
  stockLevels,
  onItemSelect,
  isLoading,
}) => {
  const getStockLevelForItem = (itemId: string, locationId: string): StockLevel | undefined => {
    return stockLevels.find(level => 
      level.itemId === itemId && level.locationId === locationId
    );
  };

  if (isLoading && items.length === 0) {
    return (
      <div className="inventory-grid__loading">
        <div className="inventory-grid__loading-spinner"></div>
        <p>Loading inventory items...</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="inventory-grid__empty">
        <div className="inventory-grid__empty-icon">📦</div>
        <h3>No items found</h3>
        <p>Try adjusting your filters or search terms.</p>
      </div>
    );
  }

  return (
    <div className="inventory-grid">
      <div className="inventory-grid__header">
        <h3>Inventory Items ({items.length})</h3>
        {isLoading && (
          <div className="inventory-grid__loading-indicator">
            <div className="inventory-grid__loading-spinner inventory-grid__loading-spinner--small"></div>
            <span>Updating...</span>
          </div>
        )}
      </div>

      <div className="inventory-grid__items">
        {items.map(item => {
          const stockLevel = getStockLevelForItem(item.id, item.location.id);
          
          return (
            <InventoryItemCard
              key={`${item.id}-${item.location.id}`}
              item={item}
              stockLevel={stockLevel}
              onClick={() => onItemSelect(item.id)}
            />
          );
        })}
      </div>
    </div>
  );
};

export default InventoryGrid;