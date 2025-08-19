import React from 'react';
import { InventoryItem, StockLevel } from '../../types/inventory';

interface InventoryItemCardProps {
  item: InventoryItem;
  stockLevel?: StockLevel;
  onClick: () => void;
}

const InventoryItemCard: React.FC<InventoryItemCardProps> = ({
  item,
  stockLevel,
  onClick,
}) => {
  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'in_stock':
        return 'success';
      case 'low_stock':
        return 'warning';
      case 'out_of_stock':
        return 'danger';
      case 'overstock':
        return 'info';
      default:
        return 'neutral';
    }
  };

  const getStatusLabel = (status?: string) => {
    switch (status) {
      case 'in_stock':
        return 'In Stock';
      case 'low_stock':
        return 'Low Stock';
      case 'out_of_stock':
        return 'Out of Stock';
      case 'overstock':
        return 'Overstock';
      default:
        return 'Unknown';
    }
  };

  const getStockPercentage = () => {
    if (!stockLevel || stockLevel.parLevel === 0) return 0;
    return Math.min((stockLevel.currentStock / stockLevel.parLevel) * 100, 100);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const isExpiringSoon = () => {
    if (!item.expirationDate) return false;
    const expirationDate = new Date(item.expirationDate);
    const today = new Date();
    const daysUntilExpiration = Math.ceil((expirationDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return daysUntilExpiration <= 7 && daysUntilExpiration > 0;
  };

  const isExpired = () => {
    if (!item.expirationDate) return false;
    const expirationDate = new Date(item.expirationDate);
    const today = new Date();
    return expirationDate < today;
  };

  const statusColor = getStatusColor(stockLevel?.status);
  const stockPercentage = getStockPercentage();

  return (
    <div 
      className={`inventory-item-card inventory-item-card--${statusColor}`}
      onClick={onClick}
    >
      <div className="inventory-item-card__header">
        <div className="inventory-item-card__title">
          <h4>{item.name}</h4>
          <span className="inventory-item-card__category">{item.category}</span>
        </div>
        <div className={`inventory-item-card__status inventory-item-card__status--${statusColor}`}>
          {getStatusLabel(stockLevel?.status)}
        </div>
      </div>

      <div className="inventory-item-card__details">
        <div className="inventory-item-card__location">
          <span className="inventory-item-card__label">Location:</span>
          <span className="inventory-item-card__value">{item.location.name}</span>
        </div>
        
        <div className="inventory-item-card__barcode">
          <span className="inventory-item-card__label">Barcode:</span>
          <span className="inventory-item-card__value">{item.barcode}</span>
        </div>
      </div>

      <div className="inventory-item-card__stock">
        <div className="inventory-item-card__stock-info">
          <div className="inventory-item-card__stock-current">
            <span className="inventory-item-card__stock-value">
              {stockLevel?.currentStock || 0}
            </span>
            <span className="inventory-item-card__stock-unit">{item.unitOfMeasure}</span>
          </div>
          <div className="inventory-item-card__stock-par">
            Par: {item.parLevel} {item.unitOfMeasure}
          </div>
        </div>

        <div className="inventory-item-card__stock-bar">
          <div 
            className={`inventory-item-card__stock-fill inventory-item-card__stock-fill--${statusColor}`}
            style={{ width: `${stockPercentage}%` }}
          />
        </div>
      </div>

      <div className="inventory-item-card__footer">
        <div className="inventory-item-card__cost">
          <span className="inventory-item-card__label">Cost:</span>
          <span className="inventory-item-card__value">
            {formatCurrency(item.costPerUnit)} / {item.unitOfMeasure}
          </span>
        </div>

        {item.expirationDate && (
          <div className={`inventory-item-card__expiration ${
            isExpired() ? 'inventory-item-card__expiration--expired' :
            isExpiringSoon() ? 'inventory-item-card__expiration--warning' : ''
          }`}>
            <span className="inventory-item-card__label">Expires:</span>
            <span className="inventory-item-card__value">
              {new Date(item.expirationDate).toLocaleDateString()}
            </span>
          </div>
        )}
      </div>

      {(isExpired() || isExpiringSoon()) && (
        <div className={`inventory-item-card__alert ${
          isExpired() ? 'inventory-item-card__alert--danger' : 'inventory-item-card__alert--warning'
        }`}>
          {isExpired() ? '⚠️ Expired' : '⏰ Expires Soon'}
        </div>
      )}

      <div className="inventory-item-card__actions">
        <button className="inventory-item-card__action-btn">
          Adjust Stock
        </button>
      </div>
    </div>
  );
};

export default InventoryItemCard;