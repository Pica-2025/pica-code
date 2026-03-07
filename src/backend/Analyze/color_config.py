
COLOR_PALETTE = {
    'coral': '#FC757B',
    'orange': '#F97F5F',
    'peach': '#FAA26F',
    'sand': '#FDCD94',
    'cream': '#FEE199',
    'mint': '#B0D6A9',
    'teal': '#65BDBA',
    'ocean': '#3C9BC9',
}

COLORS = {
    'user': '#F97F5F',
    'gt': '#3C9BC9',
    'base_stage': '#FAA26F',
    'agent_stage': '#65BDBA',
    'neutral': '#FDCD94',
    'dimension': '#FEE199',

    'sand': '#FDCD94',
    'coral': '#FC757B',
    'orange': '#F97F5F',
    'peach': '#FAA26F',
    'cream': '#FEE199',
    'teal': '#65BDBA',
    'ocean': '#3C9BC9',

    'primary': '#3C9BC9',
    'secondary': '#FC757B',
    'tertiary': '#B0D6A9',
    'quaternary': '#FEE199',
    'positive': '#B0D6A9',
    'negative': '#FC757B',

    'light_blue': '#65BDBA',
    'light_red': '#FAA26F',
    'light_green': '#B0D6A9',
    'mint': '#B0D6A9',

    'grid': '#E0E0E0',
    'border': '#000000',
    'text': '#333333',
    'background': '#FFFFFF',
}

DIMENSION_COLORS = {
    'SpatialComposition': '#FEE199',
    'Style': '#FEE199',
    'SubjectScene': '#FEE199',
    'LightingColor': '#FEE199',
    'DetailTexture': '#FEE199',
    'Others': '#FEE199',
}

QUALITY_COLORS = {
    'ai_similarity_score': '#3C9BC9',
    'user_manual_score': '#FC757B',
    'average_star_score': '#FEE199',
    'style_score': '#B0D6A9',
    'object_count_score': '#65BDBA',
    'perspective_score': '#F97F5F',
    'depth_background_score': '#FDCD94',
}

WARM_GRADIENT = ['#FC757B', '#F97F5F', '#FAA26F', '#FDCD94', '#FEE199']
COOL_GRADIENT = ['#3C9BC9', '#65BDBA', '#B0D6A9']
FULL_GRADIENT = ['#FC757B', '#F97F5F', '#FAA26F', '#FDCD94', '#FEE199',
                 '#B0D6A9', '#65BDBA', '#3C9BC9']

def get_color(color_name, alpha=1.0):
    if color_name not in COLORS:
        raise ValueError(f"Unknown color: {color_name}")

    color = COLORS[color_name]
    if alpha == 1.0:
        return color
    else:
        import matplotlib.colors as mcolors
        rgb = mcolors.hex2color(color)
        return (*rgb, alpha)

def get_dimension_color(dimension_name):
    return DIMENSION_COLORS.get(dimension_name, COLORS['dimension'])

def get_quality_color(metric_name):
    return QUALITY_COLORS.get(metric_name, COLORS['primary'])

def get_gradient_colors(n_steps, gradient_type='full'):
    import numpy as np
    import matplotlib.colors as mcolors

    if gradient_type == 'warm':
        base = WARM_GRADIENT
    elif gradient_type == 'cool':
        base = COOL_GRADIENT
    else:
        base = FULL_GRADIENT

    if n_steps <= len(base):
        indices = np.linspace(0, len(base)-1, n_steps, dtype=int)
        return [base[i] for i in indices]

    rgb_colors = [mcolors.hex2color(c) for c in base]
    result = []
    for i in range(n_steps):
        t = i / (n_steps - 1) * (len(rgb_colors) - 1)
        idx = int(t)
        if idx >= len(rgb_colors) - 1:
            result.append(base[-1])
        else:
            t_local = t - idx
            rgb = np.array(rgb_colors[idx]) * (1 - t_local) + np.array(rgb_colors[idx + 1]) * t_local
            result.append(mcolors.rgb2hex(rgb))
    return result

def preview_colors():
    print(f"\n{'='*60}")
    print("颜色映射规则")
    print(f"{'='*60}\n")

    print("核心分类:")
    print(f"  User数据:       {COLORS['user']} (橙色)")
    print(f"  Ground Truth:   {COLORS['gt']} (海蓝色)")
    print(f"  Base Stage:     {COLORS['base_stage']} (桃色)")
    print(f"  Agent Stage:    {COLORS['agent_stage']} (青绿色)")
    print(f"  无关分类:       {COLORS['neutral']} (沙色)")
    print(f"  Dimension:      {COLORS['dimension']} (奶油色)")
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    preview_colors()
