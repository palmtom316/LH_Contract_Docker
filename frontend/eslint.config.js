/**
 * ESLint Configuration
 * 
 * Key rules:
 * - no-console: Blocks console.log in production builds
 */
export default {
    root: true,
    env: {
        browser: true,
        es2022: true,
        node: true
    },
    extends: [
        'eslint:recommended'
    ],
    parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module'
    },
    rules: {
        // Block console.log in production, warn in development
        'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'warn',

        // Allow unused vars with underscore prefix
        'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }]
    },
    ignorePatterns: [
        'dist/',
        'node_modules/'
    ]
}
