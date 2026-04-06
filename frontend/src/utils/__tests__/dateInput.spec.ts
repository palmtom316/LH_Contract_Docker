import { describe, expect, it } from 'vitest'
import {
  formatDateInputDisplay,
  isValidDateParts,
  parseFlexibleDateInput
} from '@/utils/dateInput'

describe('parseFlexibleDateInput', () => {
  it('parses four-digit year with slash separators', () => {
    expect(parseFlexibleDateInput('2026/04/06')).toEqual({
      isoValue: '2026-04-06',
      displayValue: '2026/04/06',
      year: 2026,
      month: 4,
      day: 6
    })
  })

  it('parses two-digit year into 2000-2099', () => {
    expect(parseFlexibleDateInput('26/4/6')?.isoValue).toBe('2026-04-06')
  })

  it('normalizes mixed separators', () => {
    expect(parseFlexibleDateInput('2026。4-6')?.displayValue).toBe('2026/04/06')
  })

  it('rejects impossible calendar dates', () => {
    expect(parseFlexibleDateInput('2026/2/31')).toBeNull()
  })

  it('rejects incomplete values', () => {
    expect(parseFlexibleDateInput('2026/04')).toBeNull()
  })
})

describe('formatDateInputDisplay', () => {
  it('formats iso values for input display', () => {
    expect(formatDateInputDisplay('2026-04-06')).toBe('2026/04/06')
  })
})

describe('isValidDateParts', () => {
  it('accepts leap day in leap year', () => {
    expect(isValidDateParts(2028, 2, 29)).toBe(true)
  })

  it('rejects leap day in non-leap year', () => {
    expect(isValidDateParts(2027, 2, 29)).toBe(false)
  })
})
