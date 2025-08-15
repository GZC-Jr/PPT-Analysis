// 全局变量，用于存储图表实例，方便后续操作（如调整大小、释放资源）
let analysisChart;

/**
 * 主更新函数，由Python调用。
 * 负责解析数据、设置背景、并分发到具体的渲染函数。
 * @param {string} jsonData - 从Python传来的包含配置和数据的JSON字符串。
 */
function updateAnalysis(jsonData) {
    // 调试日志：打印从Python收到的原始数据
    console.log("Received data from Python:", jsonData);

    try {
        const config = JSON.parse(jsonData);
        // 调试日志：打印成功解析后的JavaScript对象
        console.log("Parsed config object:", config);

        const container = document.getElementById('analysis-container');

        // 设置或清除背景图片
        if (config.page_bg_url) {
            container.style.backgroundImage = `url('${config.page_bg_url}')`;
            container.style.backgroundSize = 'contain';
            container.style.backgroundRepeat = 'no-repeat';
            container.style.backgroundPosition = 'center';
        } else {
            container.style.backgroundImage = 'none';
        }

        // 释放旧的图表实例，防止内存泄漏
        if (analysisChart) {
            analysisChart.dispose();
        }
        // 初始化新的ECharts实例
        analysisChart = echarts.init(container, 'dark'); // 使用内置的暗色主题

        // 根据模式调用不同的渲染函数
        if (config.mode === 'module') {
            renderModuleGraph(config.data);
        } else if (config.mode === 'interpage') {
            container.style.backgroundImage = 'none'; // 页际图不应有单页背景
            renderInterpageHeatmap(config.data);
        } else if (config.mode === 'error') {
            container.innerHTML = `<p style="color: orange; font-family: sans-serif; text-align:center;">${config.message}</p>`;
        } else {
            // 如果没有指定模式，显示默认提示
            container.innerHTML = '<p style="color: white; font-family: sans-serif; text-align:center;">请在左侧选择分析模式并生成图表。</p>';
        }

    } catch (e) {
        // 捕获JSON解析或其他JS错误
        console.error("Failed to parse JSON data or render chart:", e);
        console.error("Original data string was:", jsonData);
        const container = document.getElementById('analysis-container');
        container.innerHTML = `<p style="color: red; font-family: sans-serif; text-align:center;">前端错误：无法解析或渲染数据！<br>请在浏览器中打开 http://localhost:8888 检查开发者控制台获取详情。</p>`;
    }
}

/**
 * 渲染模块关系图 (ECharts Graph)。
 * @param {object} data - 包含nodes, links, scatters的数据对象。
 */
function renderModuleGraph(data) {
    const option = {
        backgroundColor: 'transparent', // 使ECharts背景透明以显示CSS背景图
        title: {
            text: '模块间使用关系图',
            left: 'center',
            textStyle: { color: '#fff' }
        },
        tooltip: {
            formatter: function (params) {
                if (params.dataType === 'node') {
                    return `<b>${params.data.name}</b><br/>强度: ${params.data.value.toFixed(2)}`;
                }
                if (params.dataType === 'edge') {
                    return `关联度: ${params.data.value.toFixed(2)}`;
                }
                return '';
            }
        },
        // 定义一个与PPT 1920x1080 分辨率匹配的笛卡尔坐标系
        xAxis: { min: 0, max: 1920, show: false, type: 'value' },
        yAxis: { min: 0, max: 1080, show: false, type: 'value', inverse: true }, // Y轴反转以匹配屏幕坐标
        series: [{
            name: '模块分析',
            type: 'graph',
            layout: 'none', // 使用我们自己提供的x, y坐标
            roam: true,     // 允许用户缩放和拖拽图表
            label: {
                show: true,
                position: 'bottom',
                color: '#fff',
                fontSize: 10
            },
            // 节点（模块）数据
            data: data.nodes.map(node => ({
                ...node,
                itemStyle: {
                    // 强度D映射为透明度
                    opacity: Math.min(1.0, Math.max(0.2, (node.value - 3) / 20.0))
                }
            })),
            // 连线数据
            links: data.links,
            // 连线视觉样式
            edgeSymbol: ['none', 'arrow'],
            edgeSymbolSize: [4, 8],
            lineStyle: {
                color: '#aaa',
                curveness: 0.1
            },
            // 使用 markPoint 在图上绘制未被聚类的散点
            markPoint: {
                symbol: 'circle',
                symbolSize: 6,
                label: { show: false },
                itemStyle: {
                    color: 'rgba(255, 255, 255, 0.5)' // 默认散点颜色
                },
                data: data.scatters.map(p => ({
                    name: p.ActionType,
                    // markPoint需要x,y坐标
                    x: p.X,
                    y: p.Y,
                    // 可以根据动作类型设置不同颜色，以提供更多信息
                    itemStyle: {
                        color: p.ActionType === 'CLICK' ? '#007bff' : (p.ActionType === 'HOVER' ? '#ffc107' : 'rgba(200, 200, 200, 0.5)')
                    }
                }))
            }
        }]
    };
    analysisChart.setOption(option);
}

/**
 * 渲染页际关系热力图。
 * 使用散点图模拟幻灯片网格布局，用lines系列绘制跳转关系。
 * @param {object} data - 包含strengths和transitions的数据对象。
 */
function renderInterpageHeatmap(data) {
    const slidePositions = {};
    const gridCols = Math.ceil(Math.sqrt(data.strengths.length)) || 5; // 动态计算网格列数

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

    const linesData = data.transitions.map(t => ({
        coords: [slidePositions[t.source], slidePositions[t.target]]
    }));

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
            inRange: { // 定义颜色映射
                color: ['#50a3ba', '#eac736', '#d94e5d'] 
            },
            textStyle: { color: '#fff' }
        },
        series: [{
            type: 'scatter',
            symbol: 'rect', // 使用矩形模拟幻灯片
            symbolSize: 80,
            data: chartData
        }, {
            type: 'lines',
            coordinateSystem: 'cartesian2d',
            zlevel: 2,
            effect: { show: true, symbolSize: 8, trailLength: 0.5 }, // 添加特效
            lineStyle: { width: 2, curveness: 0.2, color: '#ffb402' },
            data: linesData
        }]
    };
    analysisChart.setOption(option);
}