def bill_context(analysis, rate):
    monthly = []
    for month in analysis.get('monthly', []):
        hours = month['valid_hours']
        monthly.append(dict(month=month['month'], observed_kwh=month['observed_kwh'],
            estimated_usage_cost=round(month['observed_kwh'] * rate, 2),
            coverage_fraction=hours / month['expected_hours'], complete=month['complete'],
            average_daily_kwh=month['observed_kwh'] / hours * 24 if hours else None))
    ranked = sorted(monthly, key=lambda row: row['observed_kwh'], reverse=True)
    return dict(highest_usage_months=ranked[:5],
        comparison_note='Monthly totals depend on consumption intensity and hours covered. Average daily energy is normalized to 24 observed hours, not an imputed total.',
        bill_drivers=[
            'More kWh increases usage cost at a fixed rate.',
            'Longer billing periods can raise totals even if daily usage stays similar.',
            'Hot or cold weather can increase heating or cooling demand when those systems use electricity.',
            'Longer operating hours, occupancy changes and equipment schedules can change consumption.',
            'Rates, time-of-use pricing, demand charges, taxes and fixed fees can change actual bills. Only the entered flat usage rate is calculated here.'],
        evidence_note='Possible influences, not identified causes. Consumption alone cannot identify appliance use, occupancy, tariff changes or weather.',
        sources=['https://www.eia.gov/energyexplained/electricity/use-of-electricity.php',
                 'https://www.eia.gov/energyexplained/use-of-energy/homes.php'])
