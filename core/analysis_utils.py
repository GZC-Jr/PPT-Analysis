# core/analysis_utils.py
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN


def calculate_module_strength(cluster_points):
    if cluster_points.empty: return 0
    counts = cluster_points['ActionType'].value_counts()
    x = counts.get('MOVE', 0)
    y = counts.get('HOVER', 0)
    z = counts.get('CLICK', 0)
    strength = np.log1p(x + 15 * y + 30 * z) + 3
    return float(strength)  # <-- 确保返回的是原生float


def get_inter_module_connections(page_df, module1_indices, module2_indices):
    count = 0
    combined_indices = sorted(list(module1_indices) + list(module2_indices))
    for i in range(len(combined_indices) - 1):
        idx1, idx2 = combined_indices[i], combined_indices[i + 1]
        if idx2 == idx1 + 1:
            if (idx1 in module1_indices and idx2 in module2_indices) or \
                    (idx1 in module2_indices and idx2 in module1_indices):
                count += 1
    return int(count)  # <-- 确保返回的是原生int


def process_module_analysis(df, page_num, eps, min_samples, strength_threshold):
    if page_num > 0:
        page_df = df[df['SlideIndex'] == page_num].copy()
    else:
        page_df = df.copy()

    # 转换为原生Python类型以进行JSON序列化
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
                'label': int(label),  # <-- 确保label是原生int
                'points': cluster_df,
                'strength': float(strength),
                'center_x': float(cluster_df['X'].mean()),
                'center_y': float(cluster_df['Y'].mean())
            })

    for mod in valid_modules:
        nodes.append({
            'id': f"module_{mod['label']}",
            'name': f"模块 {mod['label']}",
            'x': mod['center_x'],
            'y': mod['center_y'],
            'value': mod['strength'],
            'symbolSize': float(eps * 2),  # <-- 确保是原生float
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
                    'value': float(association),  # <-- 确保是原生float
                    'lineStyle': {'width': min(1 + association / 3.0, 15)}
                })

    valid_indices = pd.Index([])
    if valid_modules:
        valid_indices = pd.concat([m['points'] for m in valid_modules]).index
    invalid_points_df = page_df[~page_df.index.isin(valid_indices)]

    # 再次转换，确保所有散点都是安全的Python类型
    safe_scatters = [
        {'X': float(p['X']), 'Y': float(p['Y']), 'ActionType': p['ActionType']}
        for p in invalid_points_df[['X', 'Y', 'ActionType']].to_dict('records')
    ]

    return {'nodes': nodes, 'links': links, 'scatters': safe_scatters}


# ... (interpage analysis function remains the same) ...
def process_interpage_analysis(df, all_modules_data):
    # ... (此处代码不变) ...
    page_strengths = {}
    for mod in all_modules_data:
        page = mod['page']
        strength = mod['strength']
        page_strengths[page] = page_strengths.get(page, 0) + strength
    transitions = []
    for i in range(1, len(df)):
        prev_page, curr_page = df.iloc[i - 1]['SlideIndex'], df.iloc[i]['SlideIndex']
        if curr_page != prev_page and curr_page != prev_page + 1:
            transitions.append({'source': prev_page, 'target': curr_page})
    return {'strengths': [{'page': p, 'strength': s} for p, s in page_strengths.items()], 'transitions': transitions}