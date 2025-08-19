import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import InventoryOverview from './InventoryOverview';
import { StockLevel, Location } from '../../types/inventory';

const mockLocations: Location[] = [
  {
    id: '1',
    name: 'Main Bar',
    type: 'main_bar',
    isActive: true,
  },
  {
    id: '2',
    name: 'Rooftop',
    type: 'rooftop',
    isActive: true,
  },
];

const mockStockLevels: StockLevel[] = [
  {
    itemId: '1',
    locationId: '1',
    currentStock: 10,
    parLevel: 20,
    reorderPoint: 5,
    lastUpdated: '2023-01-01T00:00:00Z',
    status: 'in_stock',
  },
  {
    itemId: '2',
    locationId: '1',
    currentStock: 2,
    parLevel: 10,
    reorderPoint: 5,
    lastUpdated: '2023-01-01T00:00:00Z',
    status: 'low_stock',
  },
  {
    itemId: '3',
    locationId: '2',
    currentStock: 0,
    parLevel: 15,
    reorderPoint: 3,
    lastUpdated: '2023-01-01T00:00:00Z',
    status: 'out_of_stock',
  },
];

describe('InventoryOverview', () => {
  it('renders all locations overview by default', () => {
    render(
      <InventoryOverview
        stockLevels={mockStockLevels}
        locations={mockLocations}
      />
    );

    expect(screen.getByText('All Locations Overview')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument(); // Total items
    expect(screen.getByText('1')).toBeInTheDocument(); // In stock
    expect(screen.getByText('1')).toBeInTheDocument(); // Low stock
    expect(screen.getByText('1')).toBeInTheDocument(); // Out of stock
  });

  it('renders specific location overview when location is selected', () => {
    render(
      <InventoryOverview
        stockLevels={mockStockLevels}
        locations={mockLocations}
        selectedLocationId="1"
      />
    );

    expect(screen.getByText('Main Bar Overview')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Total items for location 1
  });

  it('displays correct stock statistics', () => {
    render(
      <InventoryOverview
        stockLevels={mockStockLevels}
        locations={mockLocations}
      />
    );

    // Check for stat labels
    expect(screen.getByText('Total Items')).toBeInTheDocument();
    expect(screen.getByText('In Stock')).toBeInTheDocument();
    expect(screen.getByText('Low Stock')).toBeInTheDocument();
    expect(screen.getByText('Out of Stock')).toBeInTheDocument();
    expect(screen.getByText('Total Value')).toBeInTheDocument();
  });

  it('calculates percentages correctly', () => {
    render(
      <InventoryOverview
        stockLevels={mockStockLevels}
        locations={mockLocations}
      />
    );

    // With 3 total items: 1 in stock (33%), 1 low stock (33%), 1 out of stock (33%)
    const percentages = screen.getAllByText(/33%/);
    expect(percentages).toHaveLength(2); // In stock and low stock percentages
  });
});