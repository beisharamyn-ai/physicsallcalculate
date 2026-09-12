from flask import Flask, render_template_string, request
import sympy as sp

app = Flask(__name__)

# 1. Определяем символы величин и константы
PI = sp.pi
N_A = 6.02214076e23       # Число Авогадро
R_gas = 8.314462618       # Газовая постоянная
g_acc = 9.81              # Ускорение свободного падения

# Переменные механики и термодинамики
F, m, a, v, v0, t, S, p_imp, E_k, E_p, h = sp.symbols('F m a v v_0 t S p_imp E_k E_p h', real=True)
P, V, n, T = sp.symbols('P V n T', real=True)
I_curr, U, R_res, P_el = sp.symbols('I_curr U R_res P_el', real=True)

# 2. База физических формул
PHYSICS_FORMULAS = [
    # Механика
    sp.Eq(F, m * a),
    sp.Eq(v, v0 + a * t),
    sp.Eq(S, v0 * t + (a * t**2) / 2),
    sp.Eq(p_imp, m * v),
    sp.Eq(E_k, (m * v**2) / 2),
    sp.Eq(E_p, m * g_acc * h),
    # Термодинамика и газы
    sp.Eq(P * V, n * R_gas * T),
    # Электричество
    sp.Eq(I_curr, U / R_res),
    sp.Eq(P_el, I_curr * U),
]

# Словарь для отображения красивых названий
VAR_NAMES = {
    'F': 'Сила (F), Н',
    'm': 'Масса (m), кг',
    'a': 'Ускорение (a), м/с²',
    'v': 'Конечная скорость (v), м/с',
    'v_0': 'Начальная скорость (v0), м/с',
    't': 'Время (t), с',
    'S': 'Расстояние (S), м',
    'p_imp': 'Импульс (p), кг·м/с',
    'E_k': 'Кинетическая энергия (E_k), Дж',
    'E_p': 'Потенциальная энергия (E_p), Дж',
    'h': 'Высота (h), м',
    'P': 'Давление (P), Па',
    'V': 'Объем (V), м³',
    'n': 'Количество вещества (n), моль',
    'T': 'Температура (T), К',
    'I_curr': 'Сила тока (I), А',
    'U': 'Напряжение (U), В',
    'R_res': 'Сопротивление (R), Ом',
    'P_el': 'Электрическая мощность (P), Вт',
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Универсальный Физический Решатель</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; margin: 30px; }
        .container { max-width: 800px; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: auto; }
        h2 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px; }
        .input-group { display: flex; flex-direction: column; }
        label { font-size: 13px; font-weight: 600; color: #444; margin-bottom: 3px; }
        input { padding: 8px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }
        button { margin-top: 25px; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; }
        button:hover { background: #1557b0; }
        .results { margin-top: 25px; padding: 20px; background: #e8f0fe; border-radius: 8px; border-left: 5px solid #1a73e8; }
        .results ul { list-style: none; padding-left: 0; }
        .results li { padding: 6px 0; border-bottom: 1px solid #d0e1fd; font-size: 15px; }
        .special-note { margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 6px; font-size: 13px; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Универсальный Физический Решатель</h2>
        <p>Введите любые известные данные из вашей задачи (остальные поля оставьте пустыми):</p>
        
        <form method="POST">
            <div class="grid">
                {% for var_key, var_label in var_names.items() %}
                <div class="input-group">
                    <label>{{ var_label }}</label>
                    <input type="number" step="any" name="{{ var_key }}" value="{{ request.form.get(var_key, '') }}">
                </div>
                {% endfor %}
            </div>
            
            <button type="submit">Рассчитать всё возможное</button>
        </form>

        {% if special_notes %}
            {% for note in special_notes %}
                <div class="special-note">💡 <strong>Физический вывод:</strong> {{ note }}</div>
            {% endfor %}
        {% endif %}

        {% if results %}
        <div class="results">
            <h3>Рассчитанные и известные величины:</h3>
            <ul>
                {% for name, val in results.items() %}
                    <li><strong>{{ name }}:</strong> {{ val }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    results = {}
    special_notes = []
    
    sym_map = {str(sym): sym for sym in [F, m, a, v, v0, t, S, p_imp, E_k, E_p, h, P, V, n, T, I_curr, U, R_res, P_el]}
    
    if request.method == 'POST':
        known = {}
        
        for key, sym in sym_map.items():
            val_str = request.form.get(key, '').strip()
            if val_str != '':
                try:
                    known[sym] = float(val_str)
                except ValueError:
                    pass

        if P in known and known[P] == 0:
            special_notes.append("При абсолютном давлении P = 0 Па идеальный газ находится при абсолютном нуле температуры (T = 0 K) или объем устремляется к бесконечности.")
            known.setdefault(T, 0.0)

        calculated = True
        while calculated:
            calculated = False
            for eq in PHYSICS_FORMULAS:
                unknowns = [var for var in eq.free_symbols if var not in known and var not in (R_gas, g_acc, PI)]
                
                if len(unknowns) == 1:
                    target = unknowns[0]
                    subbed_eq = eq.subs(known)
                    sols = sp.solve(subbed_eq, target)
                    if sols:
                        val = float(sols[0].evalf())
                        known[target] = val
                        calculated = True

        for sym, val in known.items():
            str_key = str(sym)
            label = VAR_NAMES.get(str_key, str_key)
            results[label] = f"{val:.4f}"

    return render_template_string(HTML_TEMPLATE, var_names=VAR_NAMES, results=results, special_notes=special_notes)

if __name__ == '__main__':
    app.run(debug=True)