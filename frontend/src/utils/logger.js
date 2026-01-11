"""
Production Logger - Removes console logs in production
"""
const isDev = import.meta.env.DEV

export const logger = {
    log: isDev ? console.log.bind(console) : () => {},
    warn: isDev ? console.warn.bind(console) : () => {},
    error: console.error.bind(console), // Always log errors
    info: isDev ? console.info.bind(console) : () => {},
    debug: isDev ? console.debug.bind(console) : () => {}
}

export default logger
