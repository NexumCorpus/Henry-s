import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { useWebSocket } from '../hooks/useWebSocket';
import {
  fetchInventoryItems,
  fetchStockLevels,
  fetchLocations,
  setFilters,
  clearFilters,
} from '../store/slices/inventorySlice';
import InventoryOverview from '../components/inventory/InventoryOverview';
import InventoryFilters from '../components/inventory/InventoryFilters';
import InventoryGrid from '../components/inventory/InventoryGrid';
import InventoryAdjustmentModal from '../components/inventory/InventoryAdjustmentModal';
import ConnectionStatus from '../components/common/ConnectionStatus';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

const Inventory: React.FC = () => {
  const dispatch = useAppDispatch();
  const { 
    items, 
    stockLevels, 
    locations, 
    filters, 
    isLoading, 
    error, 
    isConnected, 
    lastUpdated 
  } = useAppSelector((state) => state.inventory);
  
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [showAdjustmentModal, setShowAdjustmentModal] = useState(false);

  // Initialize WebSocket connection
  useWebSocket();

  useEffect(() => {
    // Load initial data
    dispatch(fetchLocations());
    dispatch(fetchInventoryItems(filters));
    dispatch(fetchStockLevels());
  }, [dispatch]);

  useEffect(() => {
    // Refetch items when filters change
    dispatch(fetchInventoryItems(filters));
  }, [dispatch, filters]);

  const handleFilterChange = (newFilters: any) => {
    dispatch(setFilters(newFilters));
  };

  const handleClearFilters = () => {
    dispatch(clearFilters());
  };

  const handleItemSelect = (itemId: string) => {
    setSelectedItem(itemId);
    setShowAdjustmentModal(true);
  };

  const handleCloseAdjustmentModal = () => {
    setSelectedItem(null);
    setShowAdjustmentModal(false);
  };

  const handleRefresh = () => {
    dispatch(fetchInventoryItems(filters));
    dispatch(fetchStockLevels(filters.locationId));
  };

  if (isLoading && items.length === 0) {
    return <LoadingSpinner message="Loading inventory data..." />;
  }

  return (
    <div className="inventory">
      <div className="inventory__header">
        <div className="inventory__title-section">
          <h1>Inventory Management</h1>
          <p className="inventory__subtitle">
            Real-time stock levels across all locations
          </p>
        </div>
        
        <div className="inventory__header-actions">
          <ConnectionStatus isConnected={isConnected} />
          <button 
            className="inventory__refresh-btn"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
          {lastUpdated && (
            <span className="inventory__last-updated">
              Last updated: {new Date(lastUpdated).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {error && (
        <ErrorMessage 
          message={error} 
          onDismiss={() => dispatch({ type: 'inventory/clearError' })} 
        />
      )}

      <InventoryOverview 
        stockLevels={stockLevels}
        locations={locations}
        selectedLocationId={filters.locationId}
      />

      <div className="inventory__content">
        <div className="inventory__filters-section">
          <InventoryFilters
            filters={filters}
            locations={locations}
            onFilterChange={handleFilterChange}
            onClearFilters={handleClearFilters}
          />
        </div>

        <div className="inventory__grid-section">
          <InventoryGrid
            items={items}
            stockLevels={stockLevels}
            onItemSelect={handleItemSelect}
            isLoading={isLoading}
          />
        </div>
      </div>

      {showAdjustmentModal && selectedItem && (
        <InventoryAdjustmentModal
          itemId={selectedItem}
          onClose={handleCloseAdjustmentModal}
        />
      )}
    </div>
  );
};

export default Inventory;