import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
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
    GridComponent,
    LegendComponent,
    TitleComponent,
    TooltipComponent,
    CanvasRenderer
])

export { createBarChartOption } from './chartOptions'
export { readChartTheme } from './chartTheme'

export default echarts
