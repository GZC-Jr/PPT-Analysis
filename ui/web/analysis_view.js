/**
 * @file analysis_view.js
 * @description This script handles the rendering of advanced analysis charts (Module Graph, Interpage Heatmap)
 * using ECharts. It is controlled by the Python backend via QWebEngineView.
 */

// Global variables to hold the chart instance and its current configuration
let analysisChart;
let currentOption;

// Global objects to store the current style settings for each mode
let currentModuleStyle = {
    startColor: '#4575b4', // Default start color for module gradient
    endColor: '#d73027',   // Default end color for module gradient
    linkColor: '#aaa'       // Default color for links
};
let currentInterpageStyle = {
    startColor: '#50a3ba', // Default start color for heatmap gradient (weak)
    endColor: '#d94e5d'   // Default end color for heatmap gradient (strong)
};

/**
 * Main update function, called directly from Python.
 * It receives a pre-parsed JavaScript object as its configuration.
 * @param {object} config - The configuration object from Python, containing mode, data, and settings.
 */
function updateAnalysis(config) {
    console.log("Received config object from Python:", config);

    try {
        const container = document.getElementById('analysis-container');

        // 1. Set or clear the background image (only for module view)
        if (config.mode === 'module' && config.page_bg_url) {
            container.style.backgroundImage = `url('${config.page_bg_url}')`;
            container.style.backgroundSize = 'contain';
            container.style.backgroundRepeat = 'no-repeat';
            container.style.backgroundPosition = 'center';
        } else {
            container.style.backgroundImage = 'none';
        }

        // 2. Dispose of the old chart instance to prevent memory leaks
        if (analysisChart) {
            analysisChart.dispose();
        }
        // 3. Initialize a new ECharts instance with a dark theme
        analysisChart = echarts.init(container, 'dark');

        // 4. Route to the appropriate rendering function based on the mode
        if (config.mode === 'module') {
            renderModuleGraph(config.data);
        } else if (config.mode === 'interpage') {
            renderInterpageHeatmap(config.data);
        } else if (config.mode === 'error') {
            container.innerHTML = `<p style="color: orange; font-family: sans-serif; text-align:center;">${config.message}</p>`;
        } else {
            // Default message if no mode is specified
            container.innerHTML = '<p style="color: white; font-family: sans-serif; text-align:center;">请在左侧选择分析模式并生成图表。</p>';
        }

    } catch (e) {
        // Catch any errors during rendering and display a helpful message
        console.error("Error during chart rendering:", e);
        const container = document.getElementById('analysis-container');
        container.innerHTML = `<p style="color: red; font-family: sans-serif; text-align:center;">前端渲染错误！<br>请在浏览器中打开 http://localhost:8888 检查开发者控制台获取详情。</p>`;
    }
}

/**
 * Renders the Module Relationship Graph.
 * @param {object} data - An object containing nodes, links, and scatters data from the backend.
 */
function renderModuleGraph(data) {
    const startColor = currentModuleStyle.startColor;
    const endColor = currentModuleStyle.endColor;

    currentOption = {
        backgroundColor: 'transparent', // Make ECharts background transparent
        title: { text: '模块间使用关系图', left: 'center', textStyle: { color: '#fff' } },
        tooltip: {
            formatter: (params) => {
                if (params.dataType === 'node') return `<b>${params.data.name}</b><br/>强度: ${params.data.value.toFixed(2)}`;
                if (params.dataType === 'edge') return `关联度: ${params.data.value.toFixed(2)}`;
                return '';
            }
        },
        xAxis: { min: 0, max: 1920, show: false, type: 'value' },
        yAxis: { min: 0, max: 1080, show: false, type: 'value', inverse: true },
        series: [{
            name: '模块分析',
            type: 'graph',
            layout: 'none',
            roam: true,
            label: { show: true, position: 'bottom', color: '#fff', fontSize: 10 },
            data: data.nodes.map(node => ({
                ...node,
                itemStyle: {
                    color: interpolateColor(startColor, endColor, node.pos_norm),
                    opacity: Math.min(1.0, Math.max(0.2, (node.value - 3) / 20.0))
                }
            })),
            links: data.links,
            edgeSymbol: ['none', 'arrow'],
            edgeSymbolSize: [4, 8],
            lineStyle: { color: currentModuleStyle.linkColor, curveness: 0.1 },
            markPoint: {
                symbol: 'circle',
                symbolSize: 6,
                label: { show: false },
                data: data.scatters.map(p => ({
                    name: p.ActionType, x: p.X, y: p.Y,
                    itemStyle: { color: p.ActionType === 'CLICK' ? '#007bff' : (p.ActionType === 'HOVER' ? '#ffc107' : 'rgba(200, 200, 200, 0.5)') }
                }))
            }
        }]
    };
    analysisChart.setOption(currentOption);
}

/**
 * Renders the Interpage Relationship Heatmap (Calendar View).
 * @param {object} data - An object containing strengths and transitions data.
 */
function renderInterpageHeatmap(data) {
    if (!data.strengths || data.strengths.length === 0) {
        analysisChart.clear();
        analysisChart.setOption({
            backgroundColor: 'transparent',
            title: { text: '页际关系热力图', subtext: '没有可分析的页面强度数据', left: 'center', textStyle: { color: '#fff' } }
        });
        return;
    }

    const slidePositions = {};
    const allPages = data.strengths.map(s => s.page).sort((a, b) => a - b);
    const gridCols = Math.ceil(Math.sqrt(allPages.length)) || 5;

    // 为所有存在的页面分配位置
    allPages.forEach((page, index) => {
        const row = Math.floor(index / gridCols);
        const col = index % gridCols;
        slidePositions[page] = [col, row];
    });
    
    // 创建散点图数据
    const chartData = data.strengths.map(item => ({
        name: `第 ${item.page} 页`,
        value: [...slidePositions[item.page], item.strength], // [x, y, strength]
        label: { show: true, formatter: `P${item.page}` } // 只显示页码
    }));

    // 创建歧线数据
    const linesData = data.transitions.map(t => {
        // 确保source和target都在位置字典中，防止因过滤导致错误
        if (slidePositions[t.source] && slidePositions[t.target]) {
            return {
                name: `${t.source} -> ${t.target}`,
                coords: [slidePositions[t.source], slidePositions[t.target]]
            };
        }
        return null;
    }).filter(Boolean); // 过滤掉null项

    const strengths = data.strengths.map(s => s.strength);
    const minStrength = strengths.length > 0 ? Math.min(...strengths) : 0;
    const maxStrength = strengths.length > 0 ? Math.max(...strengths) : 1;

    currentOption = {
        backgroundColor: 'transparent',
        title: { text: '页际关系热力图 (日历视图)', left: 'center', textStyle: { color: '#fff' } },
        tooltip: {
            trigger: 'item',
            formatter: (params) => {
                if (params.seriesType === 'scatter') {
                    return `${params.name}<br/>强度: ${params.value[2].toFixed(2)}`;
                }
                if (params.seriesType === 'lines') {
                    return `异常跳转: ${params.name}`;
                }
                return '';
            }
        },
        grid: { top: '15%', bottom: '15%', left: '5%', right: '5%' },
        xAxis: { type: 'value', show: false, max: gridCols },
        yAxis: { type: 'value', show: false, inverse: true },
        visualMap: {
            min: minStrength,
            max: maxStrength,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '5%',
            text: ['强', '弱'],
            // 使用全局样式变量
            inRange: { color: [currentInterpageStyle.startColor, currentInterpageStyle.endColor] },
            textStyle: { color: '#fff' }
        },
        series: [{
            name: '页面强度',
            type: 'scatter',
            symbol: 'rect', // 使用矩形模拟幻灯片
            symbolSize: [80, 60],
            data: chartData,
            label: { color: '#000', fontWeight: 'bold' }
        }, {
            name: '歧线',
            type: 'lines',
            coordinateSystem: 'cartesian2d',
            zlevel: 2,
            effect: { show: true, period: 6, trailLength: 0.7, color: '#fff', symbolSize: 5 },
            lineStyle: { color: 'red', width: 2, curveness: 0.2 },
            data: linesData
        }]
    };
    analysisChart.setOption(currentOption);
}


/**
 * A helper function to interpolate between two colors.
 * @param {string} color1 - The start color.
 * @param {string} color2 - The end color.
 * @param {number} factor - The interpolation factor (0 to 1).
 * @returns {string} The resulting color in 'rgb(r,g,b)' format.
 */
function interpolateColor(color1, color2, factor) {
    factor = Math.max(0, Math.min(1, factor));
    const c1 = echarts.color.parse(color1);
    const c2 = echarts.color.parse(color2);
    const result = [
        Math.round(c1[0] + factor * (c2[0] - c1[0])),
        Math.round(c1[1] + factor * (c2[1] - c1[1])),
        Math.round(c1[2] + factor * (c2[2] - c1[2])),
    ];
    return `rgb(${result[0]}, ${result[1]}, ${result[2]})`;
}

/**
 * Public API function to dynamically update the Module Graph's style.
 * @param {object} styleConfig - An object with startColor, endColor, linkColor.
 */
function setModuleStyle(styleConfig) {
    if (!analysisChart || !currentOption || currentOption.series[0].type !== 'graph') return;
    console.log("Updating module style with:", styleConfig);
    currentModuleStyle = styleConfig;
    // 重新计算每个节点的颜色
    currentOption.series[0].data.forEach(node => {
        if (node.itemStyle) { // 确保itemStyle存在
            node.itemStyle.color = interpolateColor(currentModuleStyle.startColor, currentModuleStyle.endColor, node.pos_norm);
        }
    });
    // 更新连线颜色
    currentOption.series[0].lineStyle.color = currentModuleStyle.linkColor;
    analysisChart.setOption(currentOption);
}

/**
 * Public API function to dynamically update the Interpage Heatmap's style.
 * @param {object} styleConfig - An object with startColor and endColor.
 */
function setInterpageStyle(styleConfig) {
    if (!analysisChart || !currentOption || !currentOption.visualMap) return;
    console.log("Updating interpage style with:", styleConfig);
    currentInterpageStyle = styleConfig;
    // 更新visualMap的颜色范围
    currentOption.visualMap.inRange.color = [styleConfig.startColor, styleConfig.endColor];
    analysisChart.setOption(currentOption);
}