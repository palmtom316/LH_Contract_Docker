import { beforeEach, describe, expect, it } from 'vitest'
import { buildTopRankedItems, createHorizontalRankOption, createStackedCategoryOption } from '../dashboardRanking'

describe('buildTopRankedItems', () => {
  it('sorts by value desc, folds the tail into 其他 after the top six, and sanitizes inputs', () => {
    const items = [
      { name: 'A', value: 5 },
      { name: 'B', value: 60 },
      { name: 'C', amount: 25 },
      { name: 'D', value: 40 },
      { amount: 15 },
      { name: 'E', value: 50 },
      { name: 'F', value: 20 },
      { name: 'G', value: 12 },
      { name: 'H', value: 4 },
      { name: 'I', value: 0 },
      { name: 'J', value: -10 }
    ]

    const ranked = buildTopRankedItems(items)

    expect(ranked).toEqual([
      { name: 'B', value: 60 },
      { name: 'E', value: 50 },
      { name: 'D', value: 40 },
      { name: 'C', value: 25 },
      { name: 'F', value: 20 },
      { name: '未分类', value: 15 },
      { name: '其他', value: 21 }
    ])
    expect(ranked.every(item => item.value > 0)).toBe(true)
    expect(ranked.some(item => item.name === '未分类')).toBe(true)
    expect(ranked.some(item => item.name === 'I')).toBe(false)
    expect(ranked.some(item => item.name === 'J')).toBe(false)
  })
})

describe('createHorizontalRankOption', () => {
  beforeEach(() => {
    document.documentElement.style.setProperty('--text-secondary', '#475569')
    document.documentElement.style.setProperty('--text-primary', '#0f172a')
    document.documentElement.style.setProperty('--border-subtle', '#d7dfeb')
    document.documentElement.style.setProperty('--surface-panel', '#ffffff')
  })

  it('creates a horizontal bar chart with category labels on the y-axis', () => {
    const option = createHorizontalRankOption({
      title: '上游合同分类',
      items: [
        { name: '安装', value: 80000 },
        { name: '市政', value: 100000 }
      ]
    })

    expect(option.xAxis.type).toBe('value')
    expect(option.yAxis.type).toBe('category')
    expect(option.yAxis.data).toEqual(['市政', '安装'])
    expect(option.series[0].type).toBe('bar')
    expect(option.series[0].data).toEqual([100000, 80000])
  })

  it('falls back to a stabilized empty state when ranked data is missing', () => {
    const option = createHorizontalRankOption({
      title: '无排名数据',
      items: [
        { name: '零值', value: 0 },
        { name: '负值', value: -5 }
      ]
    })

    expect(option.yAxis.data).toEqual(['暂无数据'])
    expect(option.series[0].data).toEqual([0])
  })
})

describe('createStackedCategoryOption', () => {
  it('creates one stacked bar row for expense comparison', () => {
    const option = createStackedCategoryOption({
      title: '支出构成',
      categories: ['本期支出'],
      series: [
        { name: '下游合同', data: [10] },
        { name: '管理合同', data: [20] }
      ]
    })

    expect(option.yAxis.data).toEqual(['本期支出'])
    expect(option.series.every(item => item.stack === 'total')).toBe(true)
  })
})
