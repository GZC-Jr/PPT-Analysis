// 全局变量，用于存储图表实例，方便后续操作（如图表导出）
let chartInstances = {};

// Python将调用此函数来更新所有图表
function updateCharts(jsonData) {
    // 解析从Python传来的JSON字符串
    const config = JSON.parse(jsonData);
    const container = document.getElementById('chart-container');
    
    // 清空旧的图表
    container.innerHTML = '';
    for (let key in chartInstances) {
        chartInstances[key].dispose();
    }
    chartInstances = {};

    if (!config.active_charts || config.active_charts.length === 0) {
        // 如果没有选择图表类型，可以显示提示信息
        container.innerHTML = '<p style="color: white; font-family: sans-serif;">请在左侧选择图表类型并生成。</p>';
        return;
    }
    
    // 根据需要显示的图表数量，动态创建div
    config.active_charts.forEach(chartType => {
        const chartDiv = document.createElement('div');
        chartDiv.id = chartType + '-chart';
        chartDiv.className = 'chart';
        container.appendChild(chartDiv);
        
        // 初始化ECharts实例
        const chart = echarts.init(document.getElementById(chartDiv.id), 'dark');
        chartInstances[chartType] = chart;
        
        // 构建ECharts的option对象
        const option = buildOption(chartType, config.data, config.title);
        
        // 设置option并渲染图表
        chart.setOption(option);
    });
}

// 根据图表类型和数据构建ECharts option
function buildOption(type, data, title) {
    const baseOption = {
        title: {
            text: title.text,
            subtext: title.subtext,
            left: 'center',
            textStyle: { color: '#fff' }
        },
        tooltip: { trigger: 'axis' },
        legend: {
            data: [data.y_var],
            bottom: 10,
            textStyle: { color: '#ccc' }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '10%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.x_data
        },
        yAxis: {
            type: 'value'
        },
        series: [{
            name: data.y_var,
            type: type, // 'bar', 'line', 'scatter'
            data: data.y_data,
            smooth: type === 'line' ? true : false, // 折线图平滑
            symbolSize: type === 'scatter' ? 10 : 4, // 散点图大小
        }]
    };
    return baseOption;
}

// 用于图表导出的函数
function getChartBase64(chartType) {
    if (chartInstances[chartType]) {
        return chartInstances[chartType].getDataURL({
            type: 'png',
            pixelRatio: 2, // 提高分辨率
            backgroundColor: '#2E2E2E'
        });
    }
    return '';
}

// --- 新增：显示错误信息的函数 ---
function showError(errorMessage) {
    const container = document.getElementById('chart-container');
    
    // 清空旧的图表并释放资源
    container.innerHTML = '';
    for (let key in chartInstances) {
        chartInstances[key].dispose();
    }
    chartInstances = {};

    // 创建并显示错误信息
    const errorDiv = document.createElement('div');
    errorDiv.style.color = 'orange';
    errorDiv.style.fontFamily = 'sans-serif';
    errorDiv.style.textAlign = 'center';
    errorDiv.style.margin = 'auto'; // 垂直和水平居中
    errorDiv.innerHTML = '<h3>图表生成失败</h3><p>' + errorMessage + '</p>';
    
    container.appendChild(errorDiv);
}