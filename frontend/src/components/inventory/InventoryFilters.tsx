import React, { useState } from 'react';
import { InventoryFilter, Location } from '../../types/inventory';

interface InventoryFiltersProps {
  filters: InventoryFilter;
  locations: Location[];
  onFilterChange: (filters: Partial<InventoryFilter>) => void;
  onClearFilters: () => void;
}

const InventoryFilters: React.FC<InventoryFiltersProps> = ({
  filters,
  locations,
  onFilterChange,
  onClearFilters,
}) => {
  const [searchTerm, setSearchTerm] = useState(filters.searchTerm || '');

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    
    // Debounce search
    setTimeout(() => {
      onFilterChange({ searchTerm: value || undefined });
    }, 300);
  };

  const handleLocationChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onFilterChange({ locationId: value || undefined });
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onFilterChange({ category: value || undefined });
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value as InventoryFilter['status'];
    onFilterChange({ status: value });
  };

  const hasActiveFilters = filters.locationId || filters.category || filters.status !== 'all' || filters.searchTerm;

  return (
    <div className="inventory-filters">
      <div className="inventory-filters__header">
        <h3>Filters</h3>
        {hasActiveFilters && (
          <button 
            className="inventory-filters__clear-btn"
            onClick={onClearFilters}
          >
            Clear All
          </button>
        )}
      </div>

      <div className="inventory-filters__controls">
        <div className="inventory-filters__control">
          <label htmlFor="search" className="inventory-filters__label">
            Search Items
          </label>
          <input
            id="search"
            type="text"
            className="inventory-filters__input"
            placeholder="Search by name or barcode..."
            value={searchTerm}
            onChange={handleSearchChange}
          />
        </div>

        <div className="inventory-filters__control">
          <label htmlFor="location" className="inventory-filters__label">
            Location
          </label>
          <select
            id="location"
            className="inventory-filters__select"
            value={filters.locationId || ''}
            onChange={handleLocationChange}
          >
            <option value="">All Locations</option>
            {locations.map(location => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
        </div>

        <div className="inventory-filters__control">
          <label htmlFor="category" className="inventory-filters__label">
            Category
          </label>
          <select
            id="category"
            className="inventory-filters__select"
            value={filters.category || ''}
            onChange={handleCategoryChange}
          >
            <option value="">All Categories</option>
            <option value="spirits">Spirits</option>
            <option value="beer">Beer</option>
            <option value="wine">Wine</option>
            <option value="mixers">Mixers</option>
            <option value="garnishes">Garnishes</option>
            <option value="supplies">Supplies</option>
          </select>
        </div>

        <div className="inventory-filters__control">
          <label htmlFor="status" className="inventory-filters__label">
            Stock Status
          </label>
          <select
            id="status"
            className="inventory-filters__select"
            value={filters.status || 'all'}
            onChange={handleStatusChange}
          >
            <option value="all">All Items</option>
            <option value="in_stock">In Stock</option>
            <option value="low_stock">Low Stock</option>
            <option value="out_of_stock">Out of Stock</option>
          </select>
        </div>
      </div>

      {hasActiveFilters && (
        <div className="inventory-filters__active">
          <span className="inventory-filters__active-label">Active filters:</span>
          <div className="inventory-filters__active-tags">
            {filters.locationId && (
              <span className="inventory-filters__tag">
                Location: {locations.find(l => l.id === filters.locationId)?.name}
                <button 
                  onClick={() => onFilterChange({ locationId: undefined })}
                  className="inventory-filters__tag-remove"
                >
                  ×
                </button>
              </span>
            )}
            {filters.category && (
              <span className="inventory-filters__tag">
                Category: {filters.category}
                <button 
                  onClick={() => onFilterChange({ category: undefined })}
                  className="inventory-filters__tag-remove"
                >
                  ×
                </button>
              </span>
            )}
            {filters.status !== 'all' && (
              <span className="inventory-filters__tag">
                Status: {filters.status?.replace('_', ' ')}
                <button 
                  onClick={() => onFilterChange({ status: 'all' })}
                  className="inventory-filters__tag-remove"
                >
                  ×
                </button>
              </span>
            )}
            {filters.searchTerm && (
              <span className="inventory-filters__tag">
                Search: "{filters.searchTerm}"
                <button 
                  onClick={() => {
                    setSearchTerm('');
                    onFilterChange({ searchTerm: undefined });
                  }}
                  className="inventory-filters__tag-remove"
                >
                  ×
                </button>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryFilters;