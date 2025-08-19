import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { 
  InventoryState, 
  InventoryItem, 
  StockLevel, 
  Location, 
  InventoryTransaction, 
  InventoryAdjustment,
  InventoryFilter,
  WebSocketMessage 
} from '../../types/inventory';
import { inventoryAPI } from '../../services/inventoryAPI';

const initialState: InventoryState = {
  items: [],
  stockLevels: [],
  locations: [],
  transactions: [],
  filters: {
    locationId: undefined,
    category: undefined,
    status: 'all',
    searchTerm: undefined,
  },
  isLoading: false,
  error: null,
  isConnected: false,
  lastUpdated: null,
};

// Async thunks
export const fetchInventoryItems = createAsyncThunk<InventoryItem[], InventoryFilter | undefined>(
  'inventory/fetchItems',
  async (filters, { rejectWithValue }) => {
    try {
      return await inventoryAPI.getInventoryItems(filters);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch inventory items');
    }
  }
);

export const fetchStockLevels = createAsyncThunk<StockLevel[], string | undefined>(
  'inventory/fetchStockLevels',
  async (locationId, { rejectWithValue }) => {
    try {
      return await inventoryAPI.getStockLevels(locationId);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch stock levels');
    }
  }
);

export const fetchLocations = createAsyncThunk<Location[]>(
  'inventory/fetchLocations',
  async (_, { rejectWithValue }) => {
    try {
      return await inventoryAPI.getLocations();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch locations');
    }
  }
);

export const fetchTransactions = createAsyncThunk<InventoryTransaction[], { itemId?: string; locationId?: string; limit?: number }>(
  'inventory/fetchTransactions',
  async ({ itemId, locationId, limit }, { rejectWithValue }) => {
    try {
      return await inventoryAPI.getTransactions(itemId, locationId, limit);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch transactions');
    }
  }
);

export const createInventoryAdjustment = createAsyncThunk<InventoryTransaction, InventoryAdjustment>(
  'inventory/createAdjustment',
  async (adjustment, { rejectWithValue }) => {
    try {
      return await inventoryAPI.createAdjustment(adjustment);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to create adjustment');
    }
  }
);

const inventorySlice = createSlice({
  name: 'inventory',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<Partial<InventoryFilter>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = initialState.filters;
    },
    setConnectionStatus: (state, action: PayloadAction<boolean>) => {
      state.isConnected = action.payload;
    },
    updateStockLevel: (state, action: PayloadAction<StockLevel>) => {
      const index = state.stockLevels.findIndex(
        level => level.itemId === action.payload.itemId && level.locationId === action.payload.locationId
      );
      if (index !== -1) {
        state.stockLevels[index] = action.payload;
      } else {
        state.stockLevels.push(action.payload);
      }
      state.lastUpdated = new Date().toISOString();
    },
    addTransaction: (state, action: PayloadAction<InventoryTransaction>) => {
      state.transactions.unshift(action.payload);
      // Keep only the latest 100 transactions in memory
      if (state.transactions.length > 100) {
        state.transactions = state.transactions.slice(0, 100);
      }
    },
    handleWebSocketMessage: (state, action: PayloadAction<WebSocketMessage>) => {
      const { type, data } = action.payload;
      
      switch (type) {
        case 'stock_update':
          const stockUpdate = data as StockLevel;
          const stockIndex = state.stockLevels.findIndex(
            level => level.itemId === stockUpdate.itemId && level.locationId === stockUpdate.locationId
          );
          if (stockIndex !== -1) {
            state.stockLevels[stockIndex] = stockUpdate;
          } else {
            state.stockLevels.push(stockUpdate);
          }
          state.lastUpdated = new Date().toISOString();
          break;
          
        case 'transaction':
          const transaction = data as InventoryTransaction;
          state.transactions.unshift(transaction);
          if (state.transactions.length > 100) {
            state.transactions = state.transactions.slice(0, 100);
          }
          break;
          
        case 'alert':
          // Handle alerts if needed
          break;
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch inventory items
      .addCase(fetchInventoryItems.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchInventoryItems.fulfilled, (state, action) => {
        state.isLoading = false;
        state.items = action.payload;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchInventoryItems.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Fetch stock levels
      .addCase(fetchStockLevels.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchStockLevels.fulfilled, (state, action) => {
        state.isLoading = false;
        state.stockLevels = action.payload;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchStockLevels.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Fetch locations
      .addCase(fetchLocations.fulfilled, (state, action) => {
        state.locations = action.payload;
      })
      .addCase(fetchLocations.rejected, (state, action) => {
        state.error = action.payload as string;
      })
      
      // Fetch transactions
      .addCase(fetchTransactions.fulfilled, (state, action) => {
        state.transactions = action.payload;
      })
      .addCase(fetchTransactions.rejected, (state, action) => {
        state.error = action.payload as string;
      })
      
      // Create adjustment
      .addCase(createInventoryAdjustment.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createInventoryAdjustment.fulfilled, (state, action) => {
        state.isLoading = false;
        state.transactions.unshift(action.payload);
        if (state.transactions.length > 100) {
          state.transactions = state.transactions.slice(0, 100);
        }
      })
      .addCase(createInventoryAdjustment.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  setFilters,
  clearFilters,
  setConnectionStatus,
  updateStockLevel,
  addTransaction,
  handleWebSocketMessage,
  clearError,
} = inventorySlice.actions;

export default inventorySlice.reducer;