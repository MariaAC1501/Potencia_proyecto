function test_scenario1
%TEST_SCENARIO1 Regresiones de entrada, salida de rama, rankings y exportación.
root = fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(root, 'matlab'));
tempRoot = tempname; mkdir(tempRoot);
cleanup = onCleanup(@() rmdir(tempRoot, 's')); %#ok<NASGU>
b = load_case_excel(fullfile(root, 'data', 'IEEE118.xlsx'));
s = load_case_excel(fullfile(root, 'data', 'IEEE118_escenario1.xlsx'));
removed = validate_line_outage(b, s);
assert(removed == 38 && s.branch.STATUS(removed) == 0);
assert(sum(b.branch.STATUS ~= 0) == 186 && sum(s.branch.STATUS ~= 0) == 185);
[Yb, index] = build_ybus(b); Ys = build_ybus(s);
rows = [index(26) index(30)];
D = Yb-Ys; other = setdiff(1:118, rows);
assert(max(abs(D(other,:)), [], 'all') < 1e-12);
assert(max(abs(D(:,other)), [], 'all') < 1e-12);
y = 1/(b.branch.BR_R(removed)+1i*b.branch.BR_X(removed));
charging = 1i*b.branch.BR_B(removed)/2;
assert(max(abs(D(rows,rows)-[y+charging -y; -y y+charging]), [], 'all') < 1e-12);
options = struct('verbose', false, 'tolerance', 1e-8, 'maxIterations', 1000, ...
    'relaxation', 1.5, 'enforceQLimits', false);
methods = {'Newton-Raphson','Gauss-Seidel','Desacoplado rápido'};
bc = cell(1,3); sc = cell(1,3);
for k = 1:3
    bc{k} = solve_power_flow(b, methods{k}, options);
    sc{k} = solve_power_flow(s, methods{k}, options);
    assert(bc{k}.converged && sc{k}.converged && sc{k}.maxMismatch <= 1e-8);
    assert(max(abs(sc{k}.V-sc{1}.V)) < 1e-7);
    flow = sc{k}.branchResults(removed,:);
    assert(all(flow{1,{'P_from_MW','Q_from_MVAr','P_to_MW','Q_to_MVAr', ...
        'S_from_MVA','S_to_MVA','P_loss_MW','Q_loss_MVAr'}} == 0));
    % Cada iteración, incluida la cero, tiene evidencia de consola opcional.
    verbose = options; verbose.verbose = true;
    transcript = evalc('r = solve_power_flow(s, methods{k}, verbose);');
    assert(numel(strfind(transcript, 'mismatch')) == numel(r.mismatchHistory));
end
br = [bc{:}]; sr = [sc{:}];
assert(abs(br(1).summary.P_loss_MW-132.862872) < 1e-5);
assert(abs(sr(1).summary.P_loss_MW-165.8977) < 1e-3);
output = fullfile(tempRoot, 'comparison.xlsx');
a = compare_scenario1(b,s,br,sr,output);
assert(isfile(output));
assert(height(a.comparacion) >= 10 && height(a.cambios_top5) == 5);
assert(~ismember(removed, a.cambios_top5.Rama));
assert(isequal(a.cambios_top5_total.Rama, [38;32;31;36;33]));
assert(a.cambios_top5_total.Delta_pct(1) == -100);
assert(all(a.cambios_top5.Activa_base & a.cambios_top5.Activa_escenario));
assert(all(diff(a.cambios_top5.Abs_delta_MVA) <= 0));
assert(max(abs(a.cambios_top5.Delta_pct - ...
    100*a.cambios_top5.Delta_MVA./a.cambios_top5.S_base_MVA)) < 1e-12);
assert(height(a.fuera_base) == 3 && height(a.fuera_escenario) == 6);
assert(isequal(a.fuera_escenario.BUS_I, [20;21;22;53;76;118]));
assert(all(diff(a.base_top5_bajas.VM_pu) >= 0));
assert(all(diff(a.base_top5_flujos.S_max_MVA) <= 0));
assert(all(ismember(string(fieldnames(a)), sheetnames(output))));
% Rechazar datos alterados, falta de línea, y evidencia no convergente.
bad = s; bad.bus.PD(1) = bad.bus.PD(1)+1;
expect_error(@() validate_line_outage(b,bad), 'powerflow:ScenarioChanges');
bad = s; bad.branch.STATUS(1) = 0;
expect_error(@() validate_line_outage(b,bad), 'powerflow:ScenarioChanges');
bad = b; bad.branch = [bad.branch;bad.branch(removed,:)];
expect_error(@() validate_line_outage(bad,s), 'powerflow:OutageNotUnique');
badResults = sr; badResults(2).converged = false;
expect_error(@() compare_scenario1(b,s,br,badResults), 'powerflow:UnconvergedScenario');
expect_error(@() compare_scenario1(b,s,br,br), 'powerflow:StaleScenarioResult');
stale = sr; stale(1).branchResults.P_from_MW(removed) = 1;
expect_error(@() compare_scenario1(b,s,br,stale), 'powerflow:StaleScenarioResult');
% Exportar únicamente GS no puede etiquetarlo erróneamente como NR.
singleFile = fullfile(tempRoot,'only_GS.xlsx');
export_results_excel(singleFile,s,sr(2));
sheets = sheetnames(singleFile);
assert(ismember('GS_bus',sheets) && ~ismember('NR_bus',sheets));
comp = readtable(singleFile,'Sheet','comparacion');
assert(ismember('P_slack_MW',comp.Properties.VariableNames));
assert(ismember('Q_slack_MVAr',comp.Properties.VariableNames));
assert(abs(comp.P_slack_MW-sr(2).busResults.P_gen_calculada_MW(69)) < 1e-10);
input = fullfile(root,'data','IEEE118.xlsx');
expect_error(@() main(input,input,false,options), 'powerflow:SameInputOutput');
fprintf('test_scenario1: único cambio STATUS, Ybus, 6 soluciones, flujos nulos, rankings, consola y Excel OK.\n');
end

function expect_error(action, identifier)
try
    action();
catch exception
    assert(strcmp(exception.identifier,identifier), 'Se esperaba %s, recibido %s: %s', ...
        identifier, exception.identifier, exception.message);
    return;
end
error('test_scenario1:ExpectedError','Falta error %s.',identifier);
end
