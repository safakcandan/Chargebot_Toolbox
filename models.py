def calculate_needs(target_ev, ratio):
    total_needed = max(1, int(target_ev / ratio))
    return {'total': total_needed, 'ac': int(total_needed * 0.8), 'dc': int(total_needed * 0.2)}

def chargebot_logic(target_ev, capacity):
    return max(1, int(target_ev / capacity))

def calculate_grid_load(ev_count, peak_hour=True):
    concurrency_factor = 0.25 if peak_hour else 0.05
    return ev_count * 7 * concurrency_factor
