import axios from 'axios';
import { InventoryItem, StockLevel, Location, InventoryTransaction, InventoryAdjustment, InventoryFilter } from '../types/inventory';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create axios instance with auth interceptor
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const inventoryAPI = {
  // Get all inventory items
  getInventoryItems: async (filters?: InventoryFilter): Promise<InventoryItem[]> => {
    const params = new URLSearchParams();
    if (filters?.locationId) params.append('location_id', filters.locationId);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.status && filters.status !== 'all') params.append('status', filters.status);
    if (filters?.searchTerm) params.append('search', filters.searchTerm);
    
    const response = await apiClient.get(`/inventory/items?${params.toString()}`);
    return response.data;
  },

  // Get stock levels for all items
  getStockLevels: async (locationId?: string): Promise<StockLevel[]> => {
    const params = locationId ? `?location_id=${locationId}` : '';
    const response = await apiClient.get(`/inventory/stock-levels${params}`);
    return response.data;
  },

  // Get all locations
  getLocations: async (): Promise<Location[]> => {
    const response = await apiClient.get('/inventory/locations');
    return response.data;
  },

  // Get inventory transactions
  getTransactions: async (itemId?: string, locationId?: string, limit = 50): Promise<InventoryTransaction[]> => {
    const params = new URLSearchParams();
    if (itemId) params.append('item_id', itemId);
    if (locationId) params.append('location_id', locationId);
    params.append('limit', limit.toString());
    
    const response = await apiClient.get(`/inventory/transactions?${params.toString()}`);
    return response.data;
  },

  // Create inventory adjustment
  createAdjustment: async (adjustment: InventoryAdjustment): Promise<InventoryTransaction> => {
    const response = await apiClient.post('/inventory/adjustments', adjustment);
    return response.data;
  },

  // Get single inventory item
  getInventoryItem: async (itemId: string): Promise<InventoryItem> => {
    const response = await apiClient.get(`/inventory/items/${itemId}`);
    return response.data;
  },

  // Update inventory item
  updateInventoryItem: async (itemId: string, updates: Partial<InventoryItem>): Promise<InventoryItem> => {
    const response = await apiClient.patch(`/inventory/items/${itemId}`, updates);
    return response.data;
  },

  // Get stock level for specific item and location
  getStockLevel: async (itemId: string, locationId: string): Promise<StockLevel> => {
    const response = await apiClient.get(`/inventory/items/${itemId}/locations/${locationId}/stock`);
    return response.data;
  },
};