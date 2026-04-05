import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
    AriaComponent,
    GridComponent,
    LegendComponent,
    TitleComponent,
    TooltipComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
    BarChart,
    LineChart,
    PieChart,
    AriaComponent,
    GridComponent,
    LegendComponent,
    TitleComponent,
    TooltipComponent,
    CanvasRenderer
])

export { createBarChartOption, createPieChartOption } from './chartOptions'
export { readChartTheme } from './chartTheme'

export default echarts
