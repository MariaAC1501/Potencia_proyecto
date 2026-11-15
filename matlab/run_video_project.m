function study = run_video_project(makePlots)
%RUN_VIDEO_PROJECT Caso base y escenario 1 reproducibles, con Excel completos.
%   addpath('matlab'); study = run_video_project(false);
% Antes: python tools/prepare_scenario1.py (crea y resalta la copia de entrada).
% Esta ejecución técnica NO sustituye el video continuo grabado por el grupo.
if nargin < 1, makePlots = true; end
root = fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(root, 'matlab'));
baseFile = fullfile(root, 'data', 'IEEE118.xlsx');
scenarioFile = fullfile(root, 'data', 'IEEE118_escenario1.xlsx');
assert(isfile(scenarioFile), 'powerflow:MissingScenario', ...
    'Prepare primero la copia resaltada: python tools/prepare_scenario1.py');
baseCase = load_case_excel(baseFile);
scenarioCase = load_case_excel(scenarioFile);
removed = validate_line_outage(baseCase, scenarioCase);
assert(baseCase.nBus == 118 && baseCase.nBranch == 186 && baseCase.nGen == 54, ...
    'Se espera el caso base IEEE118 incluido.');
fprintf('\nESCENARIO 1: retirar únicamente línea 26–30, rama %d, fila Excel %d.\n', removed, removed+1);
fprintf('Caso base intacto. STATUS escenario=0. Topología conectada, sin islas.\n');
baseOutput = fullfile(root, 'resultados_IEEE118_matlab.xlsx');
scenarioOutput = fullfile(root, 'resultados_IEEE118_escenario1_matlab.xlsx');
comparisonOutput = fullfile(root, 'comparacion_escenario1.xlsx');
study.base = main(baseFile, baseOutput, false);
study.scenario = main(scenarioFile, scenarioOutput, false);
study.analysis = compare_scenario1(baseCase, scenarioCase, study.base, study.scenario, comparisonOutput);
assets = fullfile(root, 'escenario1_assets');
plot_scenario1(study.base(1), study.scenario(1), study.analysis, assets, makePlots);
disp(study.analysis.comparacion);
fprintf('\nCinco ramas con mayor cambio de flujo global, incluida la retirada (MVA y %%):\n');
disp(study.analysis.cambios_top5_total);
fprintf('\nCinco ramas activas con mayor cambio para explicar la redistribución (MVA y %%):\n');
disp(study.analysis.cambios_top5);
fprintf('Línea retirada: flujo base y pérdida propios de sus dos extremos:\n');
disp(study.analysis.linea_retirada);
fprintf('No se acredita seguridad térmica: RATE_A=0. Límites Q desactivados.\n');
metadata = struct('matlabVersion', version, 'timestampUTC', ...
    char(datetime('now', 'TimeZone', 'UTC', 'Format', "yyyy-MM-dd'T'HH:mm:ss'Z'")), ...
    'baseInput', baseFile, 'scenarioInput', scenarioFile, 'branchIndex', removed, ...
    'baseOutput', baseOutput, 'scenarioOutput', scenarioOutput, 'comparisonOutput', comparisonOutput, ...
    'tolerance_pu', 1e-8, 'relaxation', 1.5, 'enforceQLimits', false, ...
    'voltageGuideLower', .95, 'voltageGuideUpper', 1.05, 'voltageRoundingMargin', 1e-8, ...
    'allConverged', all([study.base.converged]) && all([study.scenario.converged]), ...
    'recordingStatus', 'Ejecución técnica automatizada; video con voces del grupo pendiente');
fid = fopen(fullfile(assets, 'ejecucion.json'), 'w', 'n', 'UTF-8');
assert(fid ~= -1, 'No se pudo crear el registro de ejecución.');
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, '%s\n', jsonencode(metadata, 'PrettyPrint', true));
fprintf('Comparación exportada a: %s\n', comparisonOutput);
end
