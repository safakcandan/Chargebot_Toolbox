def estimate_detailed_costs(gap, infra_factor, config):
    """
    Geleneksel sabit şarj altyapısı maliyetini kalem kalem hesaplar.
    """
    infra = config['fixed_infrastructure']
    
    # 1. İnşaat ve Kazı (Asfalt yenileme, kazı, işçilik)
    civil = gap * infra['base_installation_cost'] * infra_factor
    
    # 2. Donanım (AC ve DC ünite bedelleri)
    hardware = (gap * 0.8 * infra['ac_unit_cost']) + (gap * 0.2 * infra['dc_unit_cost'])
    
    # 3. Şebeke ve İzinler (Trafo katılım bedeli, mühendislik, proje onay)
    grid = gap * 5000 * infra_factor 
    
    total = civil + hardware + grid
    
    return {
        "total": total,
        "civil": civil,
        "hardware": hardware,
        "grid": grid
    }

def get_investment_comparison(gap, infra_factor, config, bots):
    """
    Sabit Yatırım vs ChargeBot mobil ünite yatırımını karşılaştırmalı liste olarak döner.
    """
    infra = config['fixed_infrastructure']
    bot_price = config['chargebot']['unit_price_euro']
    
    # Sabit Sistem Donanım Maliyeti
    fixed_hw = (gap * 0.8 * infra['ac_unit_cost']) + (gap * 0.2 * infra['dc_unit_cost'])
    
    return [
        {"Kalem": "Donanım / Ünite Maliyeti", "Sabit Yatırım (€)": fixed_hw, "ChargeBot (€)": bots * bot_price},
        {"Kalem": "İnşaat, Kazı & İşçilik", "Sabit Yatırım (€)": gap * 5000 * infra_factor, "ChargeBot (€)": 0},
        {"Kalem": "Şebeke & Trafo Maliyeti", "Sabit Yatırım (€)": gap * 3500 * infra_factor, "ChargeBot (€)": 0},
        {"Kalem": "İzinler ve Projelendirme", "Sabit Yatırım (€)": gap * 1500 * infra_factor, "ChargeBot (€)": 0}
    ]