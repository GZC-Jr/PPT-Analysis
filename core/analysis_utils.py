# core/analysis_utils.py
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import pdist


def calculate_min_enclosing_radius(points_df):
    """计算点集最小包围圆半径的高效近似：最远点对距离的一半。"""
    if len(points_df) < 2:
        return 25.0  # 为单个点或空集提供一个默认半径
    distances = pdist(points_df[['X', 'Y']].values)
    return float(np.max(distances) / 2.0)


def calculate_module_strength(cluster_points):
    if cluster_points.empty: return 0
    counts = cluster_points['ActionType'].value_counts()
    x, y, z = counts.get('MOVE', 0), counts.get('HOVER', 0), counts.get('CLICK', 0)
    strength = np.log1p(x + 15 * y + 30 * z) + 3
    return float(strength)


def get_inter_module_connections(page_df, module1_indices, module2_indices):
    count = 0
    combined_indices = sorted(list(module1_indices) + list(module2_indices))
    for i in range(len(combined_indices) - 1):
        idx1, idx2 = combined_indices[i], combined_indices[i + 1]
        if idx2 == idx1 + 1:
            if (idx1 in module1_indices and idx2 in module2_indices) or \
                    (idx1 in module2_indices and idx2 in module1_indices):
                count += 1
    return int(count)


def process_module_analysis(df, page_num, eps, min_samples, strength_threshold):
    if page_num > 0:
        page_df = df[df['SlideIndex'] == page_num].copy()
    else:
        page_df = df.copy()

    safe_scatters = [
        {'X': float(p['X']), 'Y': float(p['Y']), 'ActionType': p['ActionType']}
        for p in page_df[['X', 'Y', 'ActionType']].to_dict('records')
    ]
    if len(page_df) < min_samples:
        return {'nodes': [], 'links': [], 'scatters': safe_scatters}

    coords = page_df[['X', 'Y']].values
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    page_df['cluster'] = db.labels_

    nodes, links, valid_modules = [], [], []

    for label in set(db.labels_):
        if label == -1: continue
        cluster_df = page_df[page_df['cluster'] == label]
        strength = calculate_module_strength(cluster_df)
        if strength >= strength_threshold:
            valid_modules.append({
                'label': int(label),
                'points': cluster_df,
                'strength': float(strength),
                'center_x': float(cluster_df['X'].mean()),
                'center_y': float(cluster_df['Y'].mean()),
                'radius': calculate_min_enclosing_radius(cluster_df)
            })

    # --- 核心修改：计算用于颜色映射的归一化位置值 ---
    if valid_modules:
        positions = np.array([[m['center_x'], m['center_y']] for m in valid_modules])
        # 使用到左上角(0,0)的距离作为位置度量
        distances = np.sqrt(positions[:, 0] ** 2 + positions[:, 1] ** 2)
        min_dist, max_dist = np.min(distances), np.max(distances)

        for i, mod in enumerate(valid_modules):
            # 归一化到 [0, 1] 区间
            if max_dist > min_dist:
                mod['pos_norm'] = (distances[i] - min_dist) / (max_dist - min_dist)
            else:
                mod['pos_norm'] = 0.5  # 如果所有模块在同一点

    for mod in valid_modules:
        nodes.append({
            'id': f"module_{mod['label']}",
            'name': f"模块 {mod['label']}",
            'x': mod['center_x'], 'y': mod['center_y'],
            'value': mod['strength'],
            'symbolSize': mod['radius'] * 2,  # 使用计算出的真实半径
            'pos_norm': mod.get('pos_norm', 0.5),  # 传递归一化位置
            'label': {'show': True, 'formatter': f"强度: {mod['strength']:.2f}"}
        })

    for i in range(len(valid_modules)):
        for j in range(i + 1, len(valid_modules)):
            mod1, mod2 = valid_modules[i], valid_modules[j]
            D1, D2 = mod1['strength'], mod2['strength']
            C = get_inter_module_connections(page_df, mod1['points'].index, mod2['points'].index)
            if C > 0:
                association = np.log1p(D1 + D2) + C
                links.append({
                    'source': f"module_{mod1['label']}",
                    'target': f"module_{mod2['label']}",
                    'value': float(association),
                    'lineStyle': {'width': min(1 + association / 3.0, 15)}
                })

    valid_indices = pd.Index([])
    if valid_modules:
        valid_indices = pd.concat([m['points'] for m in valid_modules]).index
    invalid_points_df = page_df[~page_df.index.isin(valid_indices)]
    safe_scatters = [
        {'X': float(p['X']), 'Y': float(p['Y']), 'ActionType': p['ActionType']}
        for p in invalid_points_df[['X', 'Y', 'ActionType']].to_dict('records')
    ]

    return {'nodes': nodes, 'links': links, 'scatters': safe_scatters}


def process_interpage_analysis(df, all_modules_data):
    # ... (此处代码不变) ...
    page_strengths = {}
    for mod in all_modules_data:
        page = mod['page']
        strength = mod['strength']
        page_strengths[page] = page_strengths.get(page, 0) + strength
    transitions = []
    for i in range(1, len(df)):
        prev_page, curr_page = df.iloc[i-1]['SlideIndex'], df.iloc[i]['SlideIndex']
        if curr_page != prev_page and curr_page != prev_page + 1:
            transitions.append({'source': prev_page, 'target': curr_page})
    return {'strengths': [{'page': p, 'strength': s} for p, s in page_strengths.items()], 'transitions': transitions}