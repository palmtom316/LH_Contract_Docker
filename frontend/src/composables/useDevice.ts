/**
 * Device Detection Composable
 * ============================
 * Detects whether the user is on a mobile device and provides
 * reactive screen size information.
 * 
 * Usage:
 * const { isMobile, isTablet, isDesktop, screenWidth } = useDevice();
 */

import { ref, onMounted, onUnmounted, computed } from 'vue';

// Breakpoints matching Tailwind config
const BREAKPOINTS = {
    xs: 375,
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    '2xl': 1536,
};

export function useDevice() {
    const screenWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024);
    const screenHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 768);

    // Device type detection
    const isMobile = computed(() => screenWidth.value < BREAKPOINTS.md);
    const isTablet = computed(() =>
        screenWidth.value >= BREAKPOINTS.md && screenWidth.value < BREAKPOINTS.lg
    );
    const isDesktop = computed(() => screenWidth.value >= BREAKPOINTS.lg);

    // Orientation
    const isPortrait = computed(() => screenHeight.value > screenWidth.value);
    const isLandscape = computed(() => screenWidth.value > screenHeight.value);

    // Touch device detection (more reliable than width alone)
    const isTouchDevice = ref(false);

    // Update handler
    const updateScreenSize = () => {
        screenWidth.value = window.innerWidth;
        screenHeight.value = window.innerHeight;
    };

    // Detect touch capability
    const detectTouchDevice = () => {
        isTouchDevice.value = (
            'ontouchstart' in window ||
            navigator.maxTouchPoints > 0 ||
            // @ts-ignore - for older browsers
            navigator.msMaxTouchPoints > 0
        );
    };

    onMounted(() => {
        updateScreenSize();
        detectTouchDevice();
        window.addEventListener('resize', updateScreenSize);
        window.addEventListener('orientationchange', updateScreenSize);
    });

    onUnmounted(() => {
        window.removeEventListener('resize', updateScreenSize);
        window.removeEventListener('orientationchange', updateScreenSize);
    });

    return {
        // Screen dimensions
        screenWidth,
        screenHeight,

        // Device types
        isMobile,
        isTablet,
        isDesktop,
        isTouchDevice,

        // Orientation
        isPortrait,
        isLandscape,

        // Breakpoints for custom comparisons
        breakpoints: BREAKPOINTS,
    };
}

/**
 * Check if current device is mobile (can be used outside Vue components)
 */
export function checkIsMobile(): boolean {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < BREAKPOINTS.md;
}
