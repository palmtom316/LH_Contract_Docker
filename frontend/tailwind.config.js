/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    // Don't apply Tailwind's base styles to avoid conflicts with Element Plus
    corePlugins: {
        preflight: false,
    },
    theme: {
        extend: {
            colors: {
                // LH Contract Brand Colors
                primary: {
                    50: '#e6f7ff',
                    100: '#bae7ff',
                    200: '#91d5ff',
                    300: '#69c0ff',
                    400: '#40a9ff',
                    500: '#1890ff', // Main primary color
                    600: '#096dd9',
                    700: '#0050b3',
                    800: '#003a8c',
                    900: '#002766',
                },
                success: '#52c41a',
                warning: '#faad14',
                danger: '#ff4d4f',
                info: '#1890ff',
            },
            fontFamily: {
                sans: ['Inter', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
            },
            spacing: {
                'safe-bottom': 'env(safe-area-inset-bottom)',
                'safe-top': 'env(safe-area-inset-top)',
            },
            screens: {
                'xs': '375px',
                'sm': '640px',
                'md': '768px',
                'lg': '1024px',
                'xl': '1280px',
                '2xl': '1536px',
            },
        },
    },
    plugins: [],
}
