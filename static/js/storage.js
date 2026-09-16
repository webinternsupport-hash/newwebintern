/**
 * Web Intern Platform - IndexedDB Local Persistence Cache
 * Database Name: InternshipComLocalDB
 */

const DB_NAME = 'InternshipComLocalDB';
const DB_VERSION = 1;

class LocalDB {
  constructor() {
    this.db = null;
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        const stores = [
          'users', 'profiles', 'enrollments', 
          'applications', 'offerLetters', 'certificates', 'documents'
        ];

        stores.forEach(storeName => {
          if (!db.objectStoreNames.contains(storeName)) {
            db.createObjectStore(storeName, { keyPath: 'id' });
          }
        });
      };

      request.onsuccess = (event) => {
        this.db = event.target.result;
        console.log('[IndexedDB] InternshipComLocalDB initialized successfully');
        resolve(this.db);
      };

      request.onerror = (event) => {
        console.error('[IndexedDB] Failed to open database:', event.target.error);
        resolve(null); // Non-blocking fallback
      };
    });
  }

  async save(storeName, item) {
    if (!this.db) await this.init();
    if (!this.db) return null;

    return new Promise((resolve) => {
      try {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        store.put(item);
        transaction.oncomplete = () => resolve(item);
        transaction.onerror = () => resolve(null);
      } catch (e) {
        console.error(`[IndexedDB] Error saving to ${storeName}:`, e);
        resolve(null);
      }
    });
  }

  async get(storeName, key) {
    if (!this.db) await this.init();
    if (!this.db) return null;

    return new Promise((resolve) => {
      try {
        const transaction = this.db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.get(key);
        request.onsuccess = () => resolve(request.result || null);
        request.onerror = () => resolve(null);
      } catch (e) {
        resolve(null);
      }
    });
  }

  async getAll(storeName) {
    if (!this.db) await this.init();
    if (!this.db) return [];

    return new Promise((resolve) => {
      try {
        const transaction = this.db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result || []);
        request.onerror = () => resolve([]);
      } catch (e) {
        resolve([]);
      }
    });
  }

  async clearStore(storeName) {
    if (!this.db) await this.init();
    if (!this.db) return;

    try {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      store.clear();
    } catch (e) {
      console.error(`[IndexedDB] Error clearing ${storeName}:`, e);
    }
  }
}

export const localDB = new LocalDB();
