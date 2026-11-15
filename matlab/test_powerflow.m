function test_powerflow
%TEST_POWERFLOW Regresiones numéricas y Excel; solo exporta a un directorio temporal.
matlabDir = fileparts(mfilename('fullpath'));
projectRoot = fileparts(matlabDir);
addpath(matlabDir);
tempRoot = tempname;
mkdir(tempRoot);
cleanup = onCleanup(@() rmdir(tempRoot, 's'));
options = struct('tolerance', 1e-8, 'maxIterations', 1000, ...
    'relaxation', 1.5, 'enforceQLimits', false);
methods = {'Newton-Raphson', 'Gauss-Seidel', 'Desacoplado rápido'};
solvers = {@solve_newton_raphson, @solve_gauss_seidel, @solve_fast_decoupled};

% Casos incluidos: tamaños, convergencia, residual independiente y acuerdo.
counts = [14 20 5; 118 186 54; 300 411 69];
for j = 1:size(counts, 1)
    n = counts(j, 1);
    caseData = load_case_excel(fullfile(projectRoot, 'data', sprintf('IEEE%d.xlsx', n)));
    assert(isequal([caseData.nBus caseData.nBranch caseData.nGen], counts(j,:)));
    assert(caseData.name == sprintf('IEEE%d', n));
    Ybus = build_ybus(caseData);
    assert(isequal(size(Ybus), [n n]) && all(isfinite(Ybus(:))));
    results = cell(1, numel(methods));
    for k = 1:numel(methods)
        results{k} = solve_power_flow(caseData, methods{k}, options);
        check_solution(caseData, results{k}, options);
        assert(max(abs(results{k}.V-results{1}.V)) < 2e-6, 'Los métodos no coinciden.');
        fprintf('IEEE%d | %s | iter=%d | residual=%.3e pu\n', ...
            n, methods{k}, results{k}.iterations, results{k}.maxMismatch);
    end
    if n == 14, case14 = caseData; end
    if n == 300
        [limit, adjusted] = recommended_max_iterations(caseData, options.maxIterations);
        assert(adjusted && limit >= 30000);
        assert(all(cellfun(@(r) r.tolerance == options.tolerance, results)));
    end
end

% VM difiere deliberadamente de VG tanto en Slack como en PV.
slack = find(case14.bus.TYPE == 3);
pv = find(case14.bus.TYPE == 2, 1);
pq = find(case14.bus.TYPE == 1, 1);
slackGen = find(case14.gen.GEN_BUS == case14.bus.BUS_I(slack) & case14.gen.STATUS ~= 0, 1);
pvGen = find(case14.gen.GEN_BUS == case14.bus.BUS_I(pv) & case14.gen.STATUS ~= 0, 1);
regulatedCase = case14;
regulatedCase.bus.VM([slack; pv; pq]) = [0.96; 0.97; 1.0123];
regulatedCase.gen.VG([slackGen; pvGen]) = [1.04; 1.02];
% Un generador en PQ no impone VG (ni siquiera se valida como consigna).
extra = regulatedCase.gen(pvGen,:);
extra.GEN_BUS = regulatedCase.bus.BUS_I(pq);
extra.PG = 0; extra.QG = 0; extra.VG = NaN;
regulatedCase.gen = [regulatedCase.gen; extra];
regulatedCase.nGen = height(regulatedCase.gen);
V0 = initial_voltage(regulatedCase);
assert(max(abs(abs(V0([slack; pv; pq]))-[1.04; 1.02; 1.0123])) < 1e-12);
assert(abs(angle(V0(slack))-case14.bus.VA(slack)*pi/180) < 1e-12);
reference = check_wrapped_and_direct(regulatedCase, methods, solvers, options);

% VM no es consigna ni necesita ser válido si VG activo lo reemplaza.
unusedVM = regulatedCase;
unusedVM.bus.VM([slack; pv]) = [NaN; 0];
validate_case(unusedVM);
check_wrapped_and_direct(unusedVM, methods, solvers, options);

% Varias unidades activas: misma consigna y generación total sin cambios.
multi = regulatedCase;
rows = [slackGen; pvGen];
extra = multi.gen(rows,:);
multi.gen.PG(rows) = multi.gen.PG(rows)/2;
multi.gen.QG(rows) = multi.gen.QG(rows)/2;
extra.PG = extra.PG/2; extra.QG = extra.QG/2;
extra.VG(2) = extra.VG(2)+1e-12; % tolerancia de redondeo, no conflicto real
multi.gen = [multi.gen; extra];
multi.nGen = height(multi.gen);
multiResults = check_wrapped_and_direct(multi, methods, solvers, options);
assert_same_voltages(reference, multiResults);

% STATUS=0 no aporta potencia, no regula y no causa conflictos de VG.
inactive = regulatedCase;
extra = inactive.gen(rows,:);
extra.STATUS(:) = 0; extra.VG = [NaN; -8];
extra.PG(:) = 1e9; extra.QG(:) = -1e9;
inactive.gen = [inactive.gen; extra];
inactive.nGen = height(inactive.gen);
inactiveResults = check_wrapped_and_direct(inactive, methods, solvers, options);
assert_same_voltages(reference, inactiveResults);

% Sin ninguna unidad activa, una PV debe resolverse como PQ, no fijar VM.
noPV = regulatedCase;
noPV.gen.STATUS(pvGen) = 0;
noPV.gen.VG(pvGen) = NaN;
[~, effectivePV, effectivePQ] = bus_sets(noPV);
assert(~ismember(pv, effectivePV) && ismember(pv, effectivePQ));
V0 = initial_voltage(noPV);
assert(abs(abs(V0(pv))-noPV.bus.VM(pv)) < 1e-12);
noPVResults = check_wrapped_and_direct(noPV, methods, solvers, options);
explicitPQ = noPV;
explicitPQ.bus.TYPE(pv) = 1;
explicitPQResults = check_wrapped_and_direct(explicitPQ, methods, solvers, options);
assert_same_voltages(noPVResults, explicitPQResults);
assert(abs(abs(noPVResults(1).V(pv))-noPV.bus.VM(pv)) > 1e-4);

% VG contradictorias y valores regulados inválidos: también llamadas directas.
for row = rows'
    conflict = regulatedCase;
    extra = conflict.gen(row,:);
    extra.VG = extra.VG+0.01;
    conflict.gen = [conflict.gen; extra];
    conflict.nGen = height(conflict.gen);
    check_rejected(conflict, 'powerflow:ConflictingVG', methods, solvers, options);
    for value = [0 -1 NaN Inf]
        invalid = regulatedCase;
        invalid.gen.VG(row) = value;
        check_rejected(invalid, 'powerflow:InvalidVG', methods, solvers, options);
    end
end
invalid = regulatedCase;
invalid.gen.VG(pvGen) = 1+1i;
check_rejected(invalid, 'powerflow:InvalidVG', methods, solvers, options);
for value = [0 -1 NaN Inf]
    invalid = regulatedCase;
    invalid.bus.VM(pq) = value;
    check_rejected(invalid, 'powerflow:InvalidVoltage', methods, solvers, options);
end
noSlack = regulatedCase;
noSlack.gen.STATUS(slackGen) = 0;
check_rejected(noSlack, 'powerflow:InactiveSlack', methods, solvers, options);
fprintf('Regresiones VG, unidades múltiples e inactivas: OK (wrapper y solvers directos).\n');

% Excel sin columna VG conserva VM por identificador, no por orden de filas.
legacy = case14;
legacy.bus.VM([slack; pv]) = [1.031; 1.021];
legacy.bus = flipud(legacy.bus);
legacy.gen = flipud(removevars(legacy.gen, 'VG'));
legacyFile = fullfile(tempRoot, 'legacy.xlsx');
write_case(legacyFile, legacy);
loaded = load_case_excel(legacyFile);
[~, busRows] = ismember(loaded.gen.GEN_BUS, loaded.bus.BUS_I);
assert(isequal(loaded.gen.VG, loaded.bus.VM(busRows)));
check_wrapped_and_direct(loaded, methods, solvers, options);
% La compatibilidad también aplica a casos construidos directamente sin VG.
withoutVG = loaded;
withoutVG.gen = removevars(withoutVG.gen, 'VG');
check_wrapped_and_direct(withoutVG, methods, solvers, options);

explicitFile = fullfile(tempRoot, 'explicit_VG.xlsx');
write_case(explicitFile, regulatedCase);
loaded = load_case_excel(explicitFile);
assert(isequaln(loaded.gen.VG, regulatedCase.gen.VG));
check_wrapped_and_direct(loaded, methods, solvers, options);
invalidFile = fullfile(tempRoot, 'invalid_VG.xlsx');
invalid = regulatedCase;
invalid.gen.VG(pvGen) = -1;
write_case(invalidFile, invalid);
assert_error(@() load_case_excel(invalidFile), 'powerflow:InvalidVG');
conflictFile = fullfile(tempRoot, 'conflicting_VG.xlsx');
write_case(conflictFile, conflict);
assert_error(@() load_case_excel(conflictFile), 'powerflow:ConflictingVG');

% Defaults probados sin ejecutar main con salida predeterminada del proyecto.
check_file_defaults(projectRoot, tempRoot);
exportFile = fullfile(tempRoot, 'export_IEEE14.xlsx');
exported = main(fullfile(projectRoot, 'data', 'IEEE14.xlsx'), exportFile, false);
check_export(exportFile, case14, exported);
defaultExportFile = fullfile(tempRoot, 'export_default_IEEE118.xlsx');
defaultResults = main([], defaultExportFile, false);
assert(all(arrayfun(@(r) r.summary.nBus == 118 && r.summary.nBranch == 186, defaultResults)));
defaultCase = load_case_excel(fullfile(projectRoot, 'data', 'IEEE118.xlsx'));
check_export(defaultExportFile, defaultCase, defaultResults);
fprintf('Defaults IEEE118/nombre de salida y exportaciones temporales: OK.\n');
fprintf('test_powerflow: todas las pruebas pasaron.\n');
end

function results = check_wrapped_and_direct(caseData, methods, solvers, options)
validate_case(caseData);
cells = cell(1, numel(methods));
for k = 1:numel(methods)
    cells{k} = solve_power_flow(caseData, methods{k}, options);
    solver = solvers{k};
    direct = solver(caseData, options);
    check_solution(caseData, cells{k}, options);
    check_solution(caseData, direct, options);
    assert(max(abs(cells{k}.V-direct.V)) < 1e-10, 'El solver directo difiere del wrapper.');
end
results = [cells{:}];
end

function check_solution(caseData, result, options)
assert(result.converged, 'No convergió: %s', result.message);
assert(all(isfinite(result.V)));
[Ybus, index] = build_ybus(caseData);
[Pspec, Qspec] = specified_power(caseData, index);
[slack, ~, pq] = bus_sets(caseData);
[~, residual] = power_mismatch(Ybus, result.V, Pspec, Qspec, slack, pq);
assert(isfinite(residual) && residual <= options.tolerance, 'Residual fuera de tolerancia: %.3e.', residual);
for g = 1:caseData.nGen
    i = find(caseData.bus.BUS_I == caseData.gen.GEN_BUS(g));
    if caseData.gen.STATUS(g) == 0 || caseData.bus.TYPE(i) == 1, continue; end
    if ismember('VG', caseData.gen.Properties.VariableNames)
        expected = caseData.gen.VG(g);
    else
        expected = caseData.bus.VM(i);
    end
    assert(abs(abs(result.V(i))-expected) < 1e-10, 'No se respeta VG en barra %g.', caseData.bus.BUS_I(i));
end
assert(max(abs(result.V(slack)./abs(result.V(slack))-exp(1i*pi/180*caseData.bus.VA(slack)))) < 1e-12);
end

function assert_same_voltages(a, b)
for k = 1:numel(a)
    assert(max(abs(a(k).V-b(k).V)) < 1e-9, 'Cambio inesperado de voltajes.');
end
end

function check_rejected(caseData, identifier, methods, solvers, options)
assert_error(@() validate_case(caseData), identifier);
assert_error(@() initial_voltage(caseData), identifier);
for k = 1:numel(methods)
    assert_error(@() solve_power_flow(caseData, methods{k}, options), identifier);
    solver = solvers{k};
    assert_error(@() solver(caseData, options), identifier);
end
end

function assert_error(action, identifier)
try
    action();
catch exception
    assert(strcmp(exception.identifier, identifier), 'Error esperado %s, recibido %s: %s', ...
        identifier, exception.identifier, exception.message);
    return;
end
error('test_powerflow:ExpectedError', 'Se esperaba el error %s.', identifier);
end

function write_case(filename, caseData)
writetable(caseData.bus, filename, 'Sheet', 'bus');
writetable(caseData.gen, filename, 'Sheet', 'gen');
writetable(caseData.branch, filename, 'Sheet', 'branch');
writetable(table(caseData.baseMVA, 'VariableNames', {'baseMVA'}), filename, 'Sheet', 'config');
end

function check_file_defaults(projectRoot, tempRoot)
originalDir = pwd;
cleanup = onCleanup(@() cd(originalDir));
cd(tempRoot); % los defaults no deben depender del directorio de trabajo
expectedInput = fullfile(projectRoot, 'data', 'IEEE118.xlsx');
expectedOutput = fullfile(projectRoot, 'resultados_IEEE118_matlab.xlsx');
[inputFile, outputFile] = resolve_powerflow_files();
assert(strcmp(inputFile, expectedInput) && strcmp(outputFile, expectedOutput));
[inputFile, outputFile] = resolve_powerflow_files("", "");
assert(strcmp(inputFile, expectedInput) && strcmp(outputFile, expectedOutput));
loaded = load_case_excel(inputFile);
assert(loaded.nBus == 118 && loaded.name == "IEEE118");
for name = ["IEEE14", "IEEE118", "IEEE300", "caso con espacios"]
    input = fullfile(tempRoot, name+".xlsx");
    [inputFile, outputFile] = resolve_powerflow_files(input);
    assert(strcmp(inputFile, input));
    assert(strcmp(outputFile, fullfile(projectRoot, "resultados_"+name+"_matlab.xlsx")));
    [~, emptyOutput] = resolve_powerflow_files(input, []);
    assert(strcmp(outputFile, emptyOutput));
end
explicitOutput = fullfile(tempRoot, 'explicit.xlsx');
[inputFile, outputFile] = resolve_powerflow_files([], explicitOutput);
assert(strcmp(inputFile, expectedInput) && strcmp(outputFile, explicitOutput));
end

function check_export(filename, caseData, results)
assert(isfile(filename) && numel(results) == 3 && all([results.converged]));
expected = ["entrada_bus", "entrada_gen", "entrada_branch", "comparacion", ...
    "NR_bus", "NR_branch", "NR_conv", "GS_bus", "GS_branch", "GS_conv", ...
    "FDLF_bus", "FDLF_branch", "FDLF_conv"];
assert(all(ismember(expected, sheetnames(filename))));
comparison = readtable(filename, 'Sheet', 'comparacion', 'VariableNamingRule', 'preserve');
assert(height(comparison) == 3 && all(comparison.Convergio));
assert(all(comparison.Error_final_pu <= 1e-8));
for k = 1:3
    prefixes = {'NR', 'GS', 'FDLF'};
    bus = readtable(filename, 'Sheet', [prefixes{k}, '_bus'], 'VariableNamingRule', 'preserve');
    branch = readtable(filename, 'Sheet', [prefixes{k}, '_branch'], 'VariableNamingRule', 'preserve');
    history = readtable(filename, 'Sheet', [prefixes{k}, '_conv'], 'VariableNamingRule', 'preserve');
    assert(height(bus) == caseData.nBus && height(branch) == caseData.nBranch);
    assert(max(abs(bus.VM_pu-abs(results(k).V))) < 1e-12);
    assert(height(history) == results(k).iterations+1);
end
end
