import React, { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { createInventoryAdjustment, fetchTransactions } from '../../store/slices/inventorySlice';
import { InventoryAdjustment, InventoryItem, StockLevel } from '../../types/inventory';
import Modal from '../common/Modal';
import LoadingSpinner from '../common/LoadingSpinner';

interface InventoryAdjustmentModalProps {
  itemId: string;
  onClose: () => void;
}

const InventoryAdjustmentModal: React.FC<InventoryAdjustmentModalProps> = ({
  itemId,
  onClose,
}) => {
  const dispatch = useAppDispatch();
  const { items, stockLevels, transactions, isLoading } = useAppSelector((state) => state.inventory);
  
  const [adjustmentType, setAdjustmentType] = useState<'add' | 'subtract' | 'set'>('add');
  const [quantity, setQuantity] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [selectedLocationId, setSelectedLocationId] = useState<string>('');

  const item = items.find(i => i.id === itemId);
  const itemStockLevels = stockLevels.filter(level => level.itemId === itemId);
  const itemTransactions = transactions.filter(t => t.itemId === itemId).slice(0, 10);

  useEffect(() => {
    if (item && !selectedLocationId) {
      setSelectedLocationId(item.location.id);
    }
  }, [item, selectedLocationId]);

  useEffect(() => {
    // Fetch recent transactions for this item
    dispatch(fetchTransactions({ itemId, limit: 10 }));
  }, [dispatch, itemId]);

  const selectedStockLevel = itemStockLevels.find(level => level.locationId === selectedLocationId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedLocationId || !quantity || !reason) {
      return;
    }

    const adjustment: InventoryAdjustment = {
      itemId,
      locationId: selectedLocationId,
      adjustmentType,
      quantity: parseFloat(quantity),
      reason,
      notes: notes || undefined,
    };

    try {
      await dispatch(createInventoryAdjustment(adjustment)).unwrap();
      onClose();
    } catch (error) {
      console.error('Failed to create adjustment:', error);
    }
  };

  const getNewStockLevel = () => {
    if (!selectedStockLevel || !quantity) return selectedStockLevel?.currentStock || 0;
    
    const currentStock = selectedStockLevel.currentStock;
    const adjustmentAmount = parseFloat(quantity);
    
    switch (adjustmentType) {
      case 'add':
        return currentStock + adjustmentAmount;
      case 'subtract':
        return Math.max(0, currentStock - adjustmentAmount);
      case 'set':
        return adjustmentAmount;
      default:
        return currentStock;
    }
  };

  if (!item) {
    return (
      <Modal onClose={onClose}>
        <div className="adjustment-modal__error">
          <h3>Item not found</h3>
          <p>The selected inventory item could not be found.</p>
        </div>
      </Modal>
    );
  }

  return (
    <Modal onClose={onClose}>
      <div className="adjustment-modal">
        <div className="adjustment-modal__header">
          <h2>Adjust Inventory</h2>
          <button 
            className="adjustment-modal__close-btn"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <div className="adjustment-modal__item-info">
          <h3>{item.name}</h3>
          <p className="adjustment-modal__item-details">
            {item.category} • {item.barcode}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="adjustment-modal__form">
          <div className="adjustment-modal__form-group">
            <label htmlFor="location" className="adjustment-modal__label">
              Location
            </label>
            <select
              id="location"
              className="adjustment-modal__select"
              value={selectedLocationId}
              onChange={(e) => setSelectedLocationId(e.target.value)}
              required
            >
              {itemStockLevels.map(level => {
                const location = items.find(i => i.location.id === level.locationId)?.location;
                return (
                  <option key={level.locationId} value={level.locationId}>
                    {location?.name || level.locationId}
                  </option>
                );
              })}
            </select>
          </div>

          {selectedStockLevel && (
            <div className="adjustment-modal__current-stock">
              <div className="adjustment-modal__stock-info">
                <span className="adjustment-modal__stock-label">Current Stock:</span>
                <span className="adjustment-modal__stock-value">
                  {selectedStockLevel.currentStock} {item.unitOfMeasure}
                </span>
              </div>
              <div className="adjustment-modal__stock-info">
                <span className="adjustment-modal__stock-label">Par Level:</span>
                <span className="adjustment-modal__stock-value">
                  {selectedStockLevel.parLevel} {item.unitOfMeasure}
                </span>
              </div>
            </div>
          )}

          <div className="adjustment-modal__form-group">
            <label className="adjustment-modal__label">Adjustment Type</label>
            <div className="adjustment-modal__radio-group">
              <label className="adjustment-modal__radio-label">
                <input
                  type="radio"
                  name="adjustmentType"
                  value="add"
                  checked={adjustmentType === 'add'}
                  onChange={(e) => setAdjustmentType(e.target.value as 'add')}
                />
                Add Stock
              </label>
              <label className="adjustment-modal__radio-label">
                <input
                  type="radio"
                  name="adjustmentType"
                  value="subtract"
                  checked={adjustmentType === 'subtract'}
                  onChange={(e) => setAdjustmentType(e.target.value as 'subtract')}
                />
                Remove Stock
              </label>
              <label className="adjustment-modal__radio-label">
                <input
                  type="radio"
                  name="adjustmentType"
                  value="set"
                  checked={adjustmentType === 'set'}
                  onChange={(e) => setAdjustmentType(e.target.value as 'set')}
                />
                Set Exact Amount
              </label>
            </div>
          </div>

          <div className="adjustment-modal__form-group">
            <label htmlFor="quantity" className="adjustment-modal__label">
              Quantity ({item.unitOfMeasure})
            </label>
            <input
              id="quantity"
              type="number"
              step="0.01"
              min="0"
              className="adjustment-modal__input"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              required
            />
          </div>

          <div className="adjustment-modal__form-group">
            <label htmlFor="reason" className="adjustment-modal__label">
              Reason
            </label>
            <select
              id="reason"
              className="adjustment-modal__select"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
            >
              <option value="">Select a reason</option>
              <option value="physical_count">Physical Count</option>
              <option value="damaged">Damaged/Broken</option>
              <option value="expired">Expired</option>
              <option value="theft">Theft/Loss</option>
              <option value="spillage">Spillage</option>
              <option value="receiving">Receiving Goods</option>
              <option value="transfer">Transfer</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="adjustment-modal__form-group">
            <label htmlFor="notes" className="adjustment-modal__label">
              Notes (Optional)
            </label>
            <textarea
              id="notes"
              className="adjustment-modal__textarea"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Additional details about this adjustment..."
            />
          </div>

          {quantity && (
            <div className="adjustment-modal__preview">
              <div className="adjustment-modal__preview-title">Preview:</div>
              <div className="adjustment-modal__preview-calculation">
                {selectedStockLevel?.currentStock || 0} {item.unitOfMeasure}
                {adjustmentType === 'add' && ` + ${quantity}`}
                {adjustmentType === 'subtract' && ` - ${quantity}`}
                {adjustmentType === 'set' && ` → ${quantity}`}
                {' = '}
                <strong>{getNewStockLevel()} {item.unitOfMeasure}</strong>
              </div>
            </div>
          )}

          <div className="adjustment-modal__actions">
            <button
              type="button"
              className="adjustment-modal__cancel-btn"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="adjustment-modal__submit-btn"
              disabled={isLoading || !quantity || !reason}
            >
              {isLoading ? 'Processing...' : 'Create Adjustment'}
            </button>
          </div>
        </form>

        {itemTransactions.length > 0 && (
          <div className="adjustment-modal__history">
            <h4>Recent Transactions</h4>
            <div className="adjustment-modal__transactions">
              {itemTransactions.map(transaction => (
                <div key={transaction.id} className="adjustment-modal__transaction">
                  <div className="adjustment-modal__transaction-info">
                    <span className="adjustment-modal__transaction-type">
                      {transaction.transactionType}
                    </span>
                    <span className="adjustment-modal__transaction-quantity">
                      {transaction.quantity > 0 ? '+' : ''}{transaction.quantity} {item.unitOfMeasure}
                    </span>
                  </div>
                  <div className="adjustment-modal__transaction-meta">
                    <span className="adjustment-modal__transaction-user">
                      {transaction.userName}
                    </span>
                    <span className="adjustment-modal__transaction-date">
                      {new Date(transaction.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                  {transaction.notes && (
                    <div className="adjustment-modal__transaction-notes">
                      {transaction.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default InventoryAdjustmentModal;