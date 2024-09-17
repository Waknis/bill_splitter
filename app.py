import os
from flask import Flask, render_template, request, redirect, url_for
from decimal import Decimal, ROUND_HALF_UP

app = Flask(__name__)

# Utility function for rounding
def round_currency(value):
    return float(Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Retrieve form data
        people_names = [name.strip() for name in request.form.get('people').split(',')]
        items = []
        item_names = request.form.getlist('item_name')
        item_costs = request.form.getlist('item_cost')
        item_shared = request.form.getlist('item_shared')

        for name, cost, shared in zip(item_names, item_costs, item_shared):
            shared_people = [p.strip() for p in shared.split(',')] if shared.lower() != 'all' else people_names
            items.append({
                'item_name': name.strip(),
                'cost': float(cost),
                'people': shared_people
            })

        tax_input_type = request.form.get('tax_input_type')
        tip_input_type = request.form.get('tip_input_type')

        if tax_input_type == 'percent':
            tax_rate = float(request.form.get('tax_rate'))
            total_tax = None
        else:
            tax_rate = None
            total_tax = float(request.form.get('total_tax'))

        if tip_input_type == 'percent':
            tip_rate = float(request.form.get('tip_rate'))
            total_tip = None
        else:
            tip_rate = None
            total_tip = float(request.form.get('total_tip'))

        # Perform calculations
        results = calculate_individual_totals(items, tax_rate, tip_rate, total_tax, total_tip)

        return render_template('result.html', results=results)
    return render_template('index.html')

def calculate_individual_totals(items, tax_rate=None, tip_rate=None, total_tax=None, total_tip=None):
    # Calculate subtotals
    subtotals = {}
    for item in items:
        shared_people_count = len(item['people'])
        split_cost = item['cost'] / shared_people_count

        for person in item['people']:
            subtotals[person] = subtotals.get(person, 0) + split_cost

    grand_subtotal = sum(subtotals.values())

    # Calculate total tax and tip if percentages are provided
    if tax_rate is not None:
        total_tax = grand_subtotal * (tax_rate / 100)
    if tip_rate is not None:
        total_tip = grand_subtotal * (tip_rate / 100)

    # Calculate the proportional tax and tip for each person
    totals_per_person = {}
    for person, subtotal in subtotals.items():
        proportional_tax = (subtotal / grand_subtotal) * total_tax if total_tax else 0
        proportional_tip = (subtotal / grand_subtotal) * total_tip if total_tip else 0
        total = subtotal + proportional_tax + proportional_tip
        totals_per_person[person] = {
            'subtotal': round_currency(subtotal),
            'tax': round_currency(proportional_tax),
            'tip': round_currency(proportional_tip),
            'total': round_currency(total),
            'items': []
        }

    # Assign items to each person
    for item in items:
        shared_people_count = len(item['people'])
        split_cost = item['cost'] / shared_people_count
        for person in item['people']:
            totals_per_person[person]['items'].append({
                'item_name': item['item_name'],
                'cost': round_currency(split_cost)
            })

    return totals_per_person

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))  # Use the PORT environment variable
    app.run(host='0.0.0.0', port=port)