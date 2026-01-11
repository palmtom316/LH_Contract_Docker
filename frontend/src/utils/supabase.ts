/**
 * Supabase Client Configuration
 * ==============================
 * Initialize Supabase client for frontend usage.
 * 
 * This file provides:
 * - Configured Supabase client instance
 * - Type-safe database access
 * - Auth state management helpers
 */

import { createClient } from '@supabase/supabase-js';
import type { Database } from '@/types/database';

// Environment variables (set in .env.local or Vite config)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:8001';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY ||
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';

/**
 * Supabase client instance with full type safety
 */
export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
    auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
    },
    realtime: {
        params: {
            eventsPerSecond: 10,
        },
    },
});

/**
 * Get current authenticated user
 */
export const getCurrentUser = async () => {
    const { data: { user }, error } = await supabase.auth.getUser();
    if (error) {
        console.error('Error getting user:', error);
        return null;
    }
    return user;
};

/**
 * Get current session
 */
export const getSession = async () => {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) {
        console.error('Error getting session:', error);
        return null;
    }
    return session;
};

/**
 * Sign out current user
 */
export const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
        console.error('Error signing out:', error);
        throw error;
    }
};

/**
 * Subscribe to auth state changes
 */
export const onAuthStateChange = (
    callback: (event: string, session: any) => void
) => {
    return supabase.auth.onAuthStateChange(callback);
};

// Re-export types for convenience
export type { Database } from '@/types/database';
