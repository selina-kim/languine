import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

/**
 * Platform-aware secure storage utility
 * - Native (iOS/Android): Uses expo-secure-store (encrypted)
 * - Web: Uses localStorage (not encrypted)
 */

const isWeb = Platform.OS === "web";

export const storage = {
  /**
   * Store a value securely
   */
  async setItem(key: string, value: string): Promise<void> {
    try {
      if (isWeb) {
        localStorage.setItem(key, value);
      } else {
        await SecureStore.setItemAsync(key, value);
      }
    } catch (error) {
      console.error(`Error storing ${key}:`, error);
      throw error;
    }
  },

  /**
   * Retrieve a stored value
   */
  async getItem(key: string): Promise<string | null> {
    try {
      if (isWeb) {
        return localStorage.getItem(key);
      } else {
        return await SecureStore.getItemAsync(key);
      }
    } catch (error) {
      console.error(`Error retrieving ${key}:`, error);
      return null;
    }
  },

  /**
   * Delete a stored value
   */
  async deleteItem(key: string): Promise<void> {
    try {
      if (isWeb) {
        localStorage.removeItem(key);
      } else {
        await SecureStore.deleteItemAsync(key);
      }
    } catch (error) {
      console.error(`Error deleting ${key}:`, error);
      throw error;
    }
  },
};
