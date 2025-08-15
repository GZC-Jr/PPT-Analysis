/**
 * @file analysis_view.js
 * @description This script handles the rendering of advanced analysis charts (Module Graph, Interpage Heatmap)
 * using ECharts. It is controlled by the Python backend via QWebEngineView.
 */

// Global variables to hold the chart instance and its current configuration
let analysisChart;
let currentOption;

// Global object to store the current style settings (colors)
let currentStyle = {
    startColor: '#4575b4', // Default start color for module gradient
    endColor: '#d73027',   // Default end color for module gradient
    linkColor: '#aaa'       // Default color for links
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

        // 1. Set or clear the background image
        if (config.page_bg_url) {
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
        // 3. Initialize a new ECharts instance
        analysisChart = echarts.init(container, 'dark'); // Use built-in dark theme

        // 4. Route to the appropriate rendering function based on the mode
        if (config.mode === 'module') {
            renderModuleGraph(config.data);
        } else if (config.mode === 'interpage') {
            container.style.backgroundImage = 'none'; // Interpage view should not have a background
            renderInterpageHeatmap(config.data);
        } else if (config.mode === 'error') {
            container.innerHTML = `<p style="color: orange; font-family: sans-serif; text-align:center;">${config.message}</p>`;
        } else {
            container.innerHTML = '<p style="color: white; font-family: sans-serif; text-align:center;">请在左侧选择分析模式并生成图表。</p>';
        }

    } catch (e) {
        // Catch any errors during JSON parsing or chart rendering
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
    const startColor = currentStyle.startColor;
    const endColor = currentStyle.endColor;

    currentOption = {
        backgroundColor: 'transparent', // Make ECharts background transparent to show the CSS background image
        title: { text: '模块间使用关系图', left: 'center', textStyle: { color: '#fff' } },
        tooltip: {
            formatter: (params) => {
                if (params.dataType === 'node') return `<b>${params.data.name}</b><br/>强度: ${params.data.value.toFixed(2)}`;
                if (params.dataType === 'edge') return `关联度: ${params.data.value.toFixed(2)}`;
                return '';
            }
        },
        // Define a Cartesian coordinate system matching the 1920x1080 PPT resolution
        xAxis: { min: 0, max: 1920, show: false, type: 'value' },
        yAxis: { min: 0, max: 1080, show: false, type: 'value', inverse: true }, // Y-axis is inverted to match screen coordinates
        series: [{
            name: '模块分析',
            type: 'graph',
            layout: 'none', // We provide our own x, y coordinates
            roam: true,     // Allow zooming and panning
            label: { show: true, position: 'bottom', color: '#fff', fontSize: 10 },
            data: data.nodes.map(node => ({
                ...node,
                itemStyle: {
                    // Color is interpolated based on normalized position
                    color: interpolateColor(startColor, endColor, node.pos_norm),
                    // Opacity is mapped from strength D
                    opacity: Math.min(1.0, Math.max(0.2, (node.value - 3) / 20.0))
                }
            })),
            links: data.links,
            edgeSymbol: ['none', 'arrow'],
            edgeSymbolSize: [4, 8],
            lineStyle: {
                color: currentStyle.linkColor,
                curveness: 0.1
            },
            // Use markPoint to render un-clustered scatter points
            markPoint: {
                symbol: 'circle',
                symbolSize: 6,
                label: { show: false },
                itemStyle: { color: 'rgba(255, 255, 255, 0.5)' },
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
 * A helper function to interpolate between two hex/rgb colors.
 * @param {string} color1 - The start color (e.g., '#ff0000' or 'rgb(255,0,0)').
 * @param {string} color2 - The end color.
 * @param {number} factor - The interpolation factor, from 0 to 1.
 * @returns {string} The resulting color in 'rgb(r,g,b)' format.
 */
function interpolateColor(color1, color2, factor) {
    factor = Math.max(0, Math.min(1, factor));
    const c1 = echarts.color.parse(color1); // ECharts' utility to parse color into [r,g,b,a]
    const c2 = echarts.color.parse(color2);
    const result = [
        Math.round(c1[0] + factor * (c2[0] - c1[0])),
        Math.round(c1[1] + factor * (c2[1] - c1[1])),
        Math.round(c1[2] + factor * (c2[2] - c1[2])),
    ];
    return `rgb(${result[0]}, ${result[1]}, ${result[2]})`;
}

/**
 * Public API function called from Python to dynamically update the chart's style.
 * @param {object} styleConfig - An object containing startColor, endColor, and linkColor.
 */
function setModuleStyle(styleConfig) {
    if (!analysisChart || !currentOption) return;
    
    console.log("Updating style with:", styleConfig);

    // Update the global style object
    currentStyle.startColor = styleConfig.startColor;
    currentStyle.endColor = styleConfig.endColor;
    currentStyle.linkColor = styleConfig.linkColor;

    // Recalculate color for each node based on the new gradient
    currentOption.series[0].data.forEach(node => {
        if (node.itemStyle) {
            node.itemStyle.color = interpolateColor(currentStyle.startColor, currentStyle.endColor, node.pos_norm);
        }
    });
    
    // Update the link color
    currentOption.series[0].lineStyle.color = currentStyle.linkColor;

    // Re-apply the updated option to the chart
    analysisChart.setOption(currentOption);
}

/**
 * Renders the Interpage Relationship Heatmap.
 * (This function remains as a placeholder for future expansion, based on previous implementation)
 */
function renderInterpageHeatmap(data) {
    const slidePositions = {};
    const gridCols = Math.ceil(Math.sqrt(data.strengths.length)) || 5;
    const chartData = data.strengths.map((item, index) => {
        const row = Math.floor(index / gridCols);
        const col = index % gridCols;
        slidePositions[item.page] = [col, row];
        return {
            name: `Page ${item.page}`,
            value: [col, row, item.strength],
            label: { show: true, formatter: `P${item.page}\nS:${item.strength.toFixed(2)}` }
        };
    });
    const linesData = data.transitions.map(t => ({ coords: [slidePositions[t.source], slidePositions[t.target]] }));
    const strengths = data.strengths.map(s => s.strength);
    const minStrength = strengths.length > 0 ? Math.min(...strengths) : 0;
    const maxStrength = strengths.length > 0 ? Math.max(...strengths) : 1;

    const option = {
        backgroundColor: 'transparent',
        title: { text: '页际关系热力图', left: 'center', textStyle: { color: '#fff' } },
        tooltip: { formatter: '{b}' },
        grid: { top: '10%', bottom: '10%', left: '10%', right: '10%' },
        xAxis: { type: 'value', show: false, max: gridCols },
        yAxis: { type: 'value', show: false, inverse: true },
        visualMap: {
            min: minStrength,
            max: maxStrength,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '0%',
            inRange: { color: ['#50a3ba', '#eac736', '#d94e5d'] },
            textStyle: { color: '#fff' }
        },
        series: [
            { type: 'scatter', symbol: 'rect', symbolSize: 80, data: chartData },
            { type: 'lines', coordinateSystem: 'cartesian2d', zlevel: 2, effect: { show: true, symbolSize: 8, trailLength: 0.5 }, lineStyle: { width: 2, curveness: 0.2, color: '#ffb402' }, data: linesData }
        ]
    };
    analysisChart.setOption(option);
}