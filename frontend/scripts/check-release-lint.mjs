import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = new URL('..', import.meta.url).pathname
const srcDir = join(root, 'src')
const forbidden = [
  { pattern: /\bdebugger\b/, label: 'debugger statement' },
  { pattern: /\bconsole\.log\s*\(/, label: 'console.log call' },
  { pattern: /\beval\s*\(/, label: 'eval call' },
  { pattern: /\.innerHTML\s*=/, label: 'innerHTML assignment' },
  { pattern: /\bv-html\s*=/, label: 'v-html usage' }
]

function walk(dir) {
  const entries = readdirSync(dir)
  const files = []
  for (const entry of entries) {
    const path = join(dir, entry)
    const stat = statSync(path)
    if (stat.isDirectory()) {
      files.push(...walk(path))
    } else if (/\.(js|ts|vue)$/.test(entry)) {
      files.push(path)
    }
  }
  return files
}

const failures = []
for (const file of walk(srcDir)) {
  const content = readFileSync(file, 'utf8')
  const lines = content.split(/\r?\n/)
  lines.forEach((line, index) => {
    for (const rule of forbidden) {
      if (rule.pattern.test(line)) {
        failures.push(`${relative(root, file)}:${index + 1}: ${rule.label}`)
      }
    }
  })
}

if (failures.length) {
  console.error('Release lint failed:')
  for (const failure of failures) {
    console.error(`  ${failure}`)
  }
  process.exit(1)
}

console.log('Release lint passed')
