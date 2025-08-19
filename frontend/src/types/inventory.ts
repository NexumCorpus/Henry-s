export interface Location {
  id: string;
  name: string;
  type: 'main_bar' | 'rooftop' | 'storage' | 'kitchen';
  isActive: boolean;
}

export interface InventoryItem {
  id: string;
  name: string;
  category: string;
  barcode: string;
  currentStock: number;
  unitOfMeasure: string;
  location: Location;
  parLevel: number;
  reorderPoint: number;
  costPerUnit: number;
  supplierId: string;
  expirationDate?: string;
  createdAt: string;
  updatedAt: string;
}

export interface StockLevel {
  itemId: string;
  locationId: string;
  currentStock: number;
  parLevel: number;
  reorderPoint: number;
  lastUpdated: string;
  status: 'in_stock' | 'low_stock' | 'out_of_stock' | 'overstock';
}

export interface InventoryTransaction {
  id: string;
  itemId: string;
  locationId: string;
  transactionType: 'sale' | 'adjustment' | 'receive' | 'waste' | 'transfer';
  quantity: number;
  unitCost?: number;
  userId: string;
  userName: string;
  posTransactionId?: string;
  timestamp: string;
  notes?: string;
}

export interface InventoryAdjustment {
  itemId: string;
  locationId: string;
  adjustmentType: 'add' | 'subtract' | 'set';
  quantity: number;
  reason: string;
  notes?: string;
}

export interface InventoryFilter {
  locationId?: string;
  category?: string;
  status?: 'all' | 'in_stock' | 'low_stock' | 'out_of_stock';
  searchTerm?: string;
}

export interface InventoryState {
  items: InventoryItem[];
  stockLevels: StockLevel[];
  locations: Location[];
  transactions: InventoryTransaction[];
  filters: InventoryFilter;
  isLoading: boolean;
  error: string | null;
  isConnected: boolean; // WebSocket connection status
  lastUpdated: string | null;
}

export interface WebSocketMessage {
  type: 'stock_update' | 'transaction' | 'alert';
  data: any;
  timestamp: string;
}

export interface StockAlert {
  id: string;
  itemId: string;
  itemName: string;
  locationId: string;
  locationName: string;
  alertType: 'low_stock' | 'out_of_stock' | 'expiring_soon';
  currentStock: number;
  threshold: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  createdAt: string;
}