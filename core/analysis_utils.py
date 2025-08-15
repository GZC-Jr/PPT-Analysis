# core/analysis_utils.py
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import pdist


# ... (calculate_min_enclosing_radius, get_inter_module_connections, process_module_analysis)
# ... 和 precompute_clusters 函数都保持不变，因为它们仍然被“模块”分析和CSV导出功能使用。
# ... 为简洁起见，此处省略这些不变的函数，只展示被修改的 process_interpage_analysis 函数...

def calculate_min_enclosing_radius(points_df):
    if len(points_df) < 2: return 25.0
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
    safe_scatters = [{'X': float(p['X']), 'Y': float(p['Y']), 'ActionType': p['ActionType']} for p in
                     page_df[['X', 'Y', 'ActionType']].to_dict('records')]
    if len(page_df) < min_samples: return {'nodes': [], 'links': [], 'scatters': safe_scatters}
    coords = page_df[['X', 'Y']].values;
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords);
    page_df['cluster'] = db.labels_
    nodes, links, valid_modules = [], [], []
    for label in set(db.labels_):
        if label == -1: continue
        cluster_df = page_df[page_df['cluster'] == label];
        strength = calculate_module_strength(cluster_df)
        if strength >= strength_threshold:
            valid_modules.append({'label': int(label), 'points': cluster_df, 'strength': float(strength),
                                  'center_x': float(cluster_df['X'].mean()), 'center_y': float(cluster_df['Y'].mean()),
                                  'radius': calculate_min_enclosing_radius(cluster_df)})
    if valid_modules:
        positions = np.array([[m['center_x'], m['center_y']] for m in valid_modules]);
        distances = np.sqrt(positions[:, 0] ** 2 + positions[:, 1] ** 2);
        min_dist, max_dist = np.min(distances), np.max(distances)
        for i, mod in enumerate(valid_modules):
            mod['pos_norm'] = (distances[i] - min_dist) / (max_dist - min_dist) if max_dist > min_dist else 0.5
    for mod in valid_modules:
        nodes.append(
            {'id': f"module_{mod['label']}", 'name': f"模块 {mod['label']}", 'x': mod['center_x'], 'y': mod['center_y'],
             'value': mod['strength'], 'symbolSize': mod['radius'] * 2, 'pos_norm': mod.get('pos_norm', 0.5),
             'label': {'show': True, 'formatter': f"强度: {mod['strength']:.2f}"}})
    for i in range(len(valid_modules)):
        for j in range(i + 1, len(valid_modules)):
            mod1, mod2 = valid_modules[i], valid_modules[j];
            D1, D2 = mod1['strength'], mod2['strength'];
            C = get_inter_module_connections(page_df, mod1['points'].index, mod2['points'].index)
            if C > 0:
                association = np.log1p(D1 + D2) + C;
                links.append({'source': f"module_{mod1['label']}", 'target': f"module_{mod2['label']}",
                              'value': float(association), 'lineStyle': {'width': min(1 + association / 3.0, 15)}})
    valid_indices = pd.Index([])
    if valid_modules: valid_indices = pd.concat([m['points'] for m in valid_modules]).index
    invalid_points_df = page_df[~page_df.index.isin(valid_indices)]
    safe_scatters = [{'X': float(p['X']), 'Y': float(p['Y']), 'ActionType': p['ActionType']} for p in
                     invalid_points_df[['X', 'Y', 'ActionType']].to_dict('records')]
    return {'nodes': nodes, 'links': links, 'scatters': safe_scatters}


def precompute_clusters(df, eps, min_samples):
    if df is None or df.empty: return None

    def get_clusters(page_group):
        if len(page_group) < min_samples:
            page_group['cluster'] = -1
            return page_group
        db_labels = DBSCAN(eps=eps, min_samples=min_samples).fit(page_group[['X', 'Y']]).labels_
        page_group['cluster'] = db_labels
        return page_group

    df_with_clusters = df.copy().groupby('SlideIndex', group_keys=False).apply(get_clusters)
    return df_with_clusters.reset_index(drop=True)


# --- 核心修改：重写 process_interpage_analysis ---
def process_interpage_analysis(df):
    """
    进行页际关系分析。
    这个函数现在直接基于整个页面的动作计数，不再依赖于聚类。
    """
    if df is None or df.empty:
        return {'strengths': [], 'transitions': []}

    # 1. 高效计算每页的强度 P = ln(x+15y+30z)

    # 按页面分组，并计算每种动作类型的数量
    action_counts = df.groupby('SlideIndex')['ActionType'].value_counts().unstack(fill_value=0)

    # 确保 MOVE, HOVER, CLICK 列都存在
    for col in ['MOVE', 'HOVER', 'CLICK']:
        if col not in action_counts.columns:
            action_counts[col] = 0

    # 计算公式的参数
    log_arg = action_counts['MOVE'] + 15 * action_counts['HOVER'] + 30 * action_counts['CLICK']

    # 计算强度 P，使用 np.log1p (即 log(1+x)) 来优雅地处理参数为0的情况，避免-inf
    page_strengths_series = np.log1p(log_arg)

    # 创建一个包含所有页码的字典，以确保即使某页没有动作，也会被包含（强度为0）
    all_pages = df['SlideIndex'].unique()
    page_strengths = {page: page_strengths_series.get(page, 0) for page in all_pages}

    # 2. 识别歧线 (此部分逻辑不变)
    transitions = []
    df_sorted = df.sort_values(by='Timestamp')
    for i in range(1, len(df_sorted)):
        prev_page = df_sorted.iloc[i - 1]['SlideIndex']
        curr_page = df_sorted.iloc[i]['SlideIndex']
        if curr_page != prev_page and curr_page != prev_page + 1:
            transitions.append({'source': int(prev_page), 'target': int(curr_page)})

    strength_list = [{'page': int(p), 'strength': float(s)} for p, s in page_strengths.items()]

    return {'strengths': strength_list, 'transitions': transitions}