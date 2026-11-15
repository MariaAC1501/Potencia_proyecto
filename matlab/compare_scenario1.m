function analysis = compare_scenario1(baseCase, scenarioCase, baseResults, scenarioResults, outputFile)
%COMPARE_SCENARIO1 Evidencia exigida por la guía para retirar la línea 26–30.
% Valores eléctricos de NR. Se conservan rankings y los tres métodos completos.
if nargin < 5, outputFile = ''; end
removed = validate_line_outage(baseCase, scenarioCase, 26, 30);
assert(all([baseResults.converged]) && all([scenarioResults.converged]), ...
    'powerflow:UnconvergedScenario', 'No interpretar resultados sin convergencia.');
check_case_results(baseCase, baseResults);
check_case_results(scenarioCase, scenarioResults);
b = select_method(baseResults, 'newton'); s = select_method(scenarioResults, 'newton');
bgs = select_method(baseResults, 'gauss'); sgs = select_method(scenarioResults, 'gauss');
assert(isequal(b.busResults.BUS_I, s.busResults.BUS_I), 'Orden de barras diferente.');
assert(isequal(b.branchResults.Desde, s.branchResults.Desde) && ...
    isequal(b.branchResults.Hasta, s.branchResults.Hasta), 'Orden de ramas diferente.');
voltageEpsilon = 1e-8; % evita contar redondeo numérico exactamente en 0.95 o 1.05
outside = @(T) T.VM_pu < 0.95-voltageEpsilon | T.VM_pu > 1.05+voltageEpsilon;
baseOutside = b.busResults(outside(b.busResults),:);
scenarioOutside = s.busResults(outside(s.busResults),:);
bSlack = b.busResults(b.busResults.BUS_I == b.summary.slackBus,:);
sSlack = s.busResults(s.busResults.BUS_I == s.summary.slackBus,:);
assert(isscalar(bSlack.BUS_I) && bSlack.BUS_I == 69 && sSlack.BUS_I == 69, ...
    'Se espera Slack 69 para esta versión IEEE118.');
variables = ["Tensión mínima (pu)"; "Barra de tensión mínima"; ...
    "Tensión máxima (pu)"; "Barra de tensión máxima"; ...
    "Barras fuera de 0.95–1.05 pu"; "P de la barra slack 69 (MW)"; ...
    "Q de la barra slack 69 (MVAr)"; "Pérdidas totales (MW)"; ...
    "Iteraciones Newton-Raphson"; "Iteraciones Gauss-Seidel"; ...
    "Pérdidas netas Q de ramas (MVAr)"];
baseValues = [b.summary.minVoltagePU; b.summary.minVoltageBus; ...
    b.summary.maxVoltagePU; b.summary.maxVoltageBus; height(baseOutside); ...
    bSlack.P_gen_calculada_MW; bSlack.Q_gen_calculada_MVAr; b.summary.P_loss_MW; ...
    b.iterations; bgs.iterations; b.summary.Q_loss_MVAr];
scenarioValues = [s.summary.minVoltagePU; s.summary.minVoltageBus; ...
    s.summary.maxVoltagePU; s.summary.maxVoltageBus; height(scenarioOutside); ...
    sSlack.P_gen_calculada_MW; sSlack.Q_gen_calculada_MVAr; s.summary.P_loss_MW; ...
    s.iterations; sgs.iterations; s.summary.Q_loss_MVAr];
difference = scenarioValues-baseValues;
% Los identificadores no son magnitudes: su diferencia no tiene significado.
difference([2,4]) = NaN;
analysis.comparacion = table(variables, baseValues, scenarioValues, difference, ...
    'VariableNames', {'Variable','Caso_base','Escenario','Diferencia'});
baseFlows = b.branchResults; scenarioFlows = s.branchResults;
baseFlows.S_max_MVA = max(baseFlows.S_from_MVA, baseFlows.S_to_MVA);
scenarioFlows.S_max_MVA = max(scenarioFlows.S_from_MVA, scenarioFlows.S_to_MVA);
baseTop = sortrows(baseFlows(baseCase.branch.STATUS ~= 0,:), 'S_max_MVA', 'descend');
scenarioTop = sortrows(scenarioFlows(scenarioCase.branch.STATUS ~= 0,:), 'S_max_MVA', 'descend');
baseLow = sortrows(b.busResults, {'VM_pu','BUS_I'});
scenarioLow = sortrows(s.busResults, {'VM_pu','BUS_I'});
analysis.base_top5_bajas = baseLow(1:min(5,height(baseLow)),:);
analysis.escenario_top5_bajas = scenarioLow(1:min(5,height(scenarioLow)),:);
analysis.base_top5_flujos = baseTop(1:min(5,height(baseTop)),:);
analysis.escenario_top5_flujos = scenarioTop(1:min(5,height(scenarioTop)),:);
delta = scenarioFlows.S_max_MVA - baseFlows.S_max_MVA;
percent = nan(size(delta)); nonzero = baseFlows.S_max_MVA > 1e-9;
percent(nonzero) = 100*delta(nonzero)./baseFlows.S_max_MVA(nonzero);
changes = table(baseFlows.Rama, baseFlows.Desde, baseFlows.Hasta, ...
    baseFlows.S_max_MVA, scenarioFlows.S_max_MVA, delta, percent, abs(delta), ...
    baseCase.branch.STATUS ~= 0, scenarioCase.branch.STATUS ~= 0, ...
    'VariableNames', {'Rama','Desde','Hasta','S_base_MVA','S_escenario_MVA', ...
    'Delta_MVA','Delta_pct','Abs_delta_MVA','Activa_base','Activa_escenario'});
analysis.cambios_ramas = sortrows(changes, {'Abs_delta_MVA','Rama'}, {'descend','ascend'});
% Ranking literal de la guía: todas las ramas, incluida la retirada.
analysis.cambios_top5_total = analysis.cambios_ramas(1:min(5,height(changes)),:);
% La línea retirada se muestra aparte: no confundir su caída a cero con redistribución.
inService = changes.Activa_base & changes.Activa_escenario;
topChanges = sortrows(changes(inService,:), {'Abs_delta_MVA','Rama'}, {'descend','ascend'});
analysis.cambios_top5 = topChanges(1:min(5,height(topChanges)),:);
analysis.fuera_base = baseOutside;
analysis.fuera_escenario = scenarioOutside;
analysis.linea_retirada = baseFlows(removed,:);
analysis.base_metodos = result_comparison(baseResults);
analysis.escenario_metodos = result_comparison(scenarioResults);
analysis.definiciones = table(["Referencia eléctrica"; "Rango de tensión"; ...
    "Potencia de rama"; "Delta MVA"; "Delta %"; "Top 5 global"; "Top 5 redistribución"; "Límites térmicos"], ...
    ["Newton-Raphson convergente; GS/FDLF como contraste interno"; ...
    "0.95–1.05 pu de la guía; margen de redondeo 1e-8 pu; no VMIN/VMAX del Excel"; ...
    "S_max_MVA = max(abs(S_desde), abs(S_hasta))"; ...
    "S_max escenario menos S_max base; signo conservado"; ...
    "100*Delta_MVA/S_base_MVA; NaN si base <= 1e-9 MVA"; ...
    "cambios_top5_total: mayor abs(Delta_MVA) entre TODAS las ramas, incluida la retirada"; ...
    "Orden por abs(Delta_MVA) en ramas activas en ambos casos; retirada aparte"; ...
    "RATE_A=0 no acredita margen térmico; no se concluye ausencia de sobrecargas"], ...
    'VariableNames', {'Concepto','Definicion'});
if strlength(string(outputFile)) > 0
    destination = outputFile; folder = fileparts(destination);
    if isempty(folder), folder = pwd; end
    temporary = [tempname(folder), '.xlsx'];
    cleanup = onCleanup(@() delete_temp(temporary)); %#ok<NASGU>
    fields = fieldnames(analysis);
    for k = 1:numel(fields)
        writetable(analysis.(fields{k}), temporary, 'Sheet', fields{k});
    end
    [ok, message] = movefile(temporary, destination, 'f');
    assert(ok, 'No se pudo guardar la comparación: %s', message);
end
end

function check_case_results(caseData, results)
% Evita comparar por accidente dos corridas base o evidencia de otro archivo.
[Ybus, index] = build_ybus(caseData);
[Pspec, Qspec] = specified_power(caseData, index);
[slack, ~, pq] = bus_sets(caseData);
for k = 1:numel(results)
    r = results(k);
    assert(numel(r.V) == caseData.nBus && all(isfinite(r.V)), ...
        'powerflow:StaleScenarioResult', 'Tensiones incompatibles con el caso.');
    [~, residual] = power_mismatch(Ybus, r.V, Pspec, Qspec, slack, pq);
    assert(isfinite(residual) && residual <= 1e-8 && r.maxMismatch <= 1e-8, ...
        'powerflow:StaleScenarioResult', ...
        'El resultado no corresponde al caso o no cumple 1e-8 pu (residual %.3e).', residual);
    expected = calculate_branch_flows(caseData, r.V);
    columns = {'P_from_MW','Q_from_MVAr','P_to_MW','Q_to_MVAr'};
    assert(isequal(size(expected),size(r.branchResults)) && ...
        max(abs(expected{:,columns}-r.branchResults{:,columns}), [], 'all') <= 1e-7, ...
        'powerflow:StaleScenarioResult', 'Los flujos no corresponden al caso y tensiones suministrados.');
end
end

function result = select_method(results, key)
index = find(arrayfun(@(r) contains(lower(string(r.method)), key), results));
assert(isscalar(index), 'Debe existir exactamente un resultado del método %s.', key);
result = results(index);
end

function delete_temp(filename)
if isfile(filename), delete(filename); end
end
