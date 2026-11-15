function results = main(inputFile, outputFile, makePlots, options)
%MAIN Ejecuta los tres métodos sobre un caso Excel.
% Uso desde MATLAB:
%   addpath('matlab'); results = main;
%   results = main('data/IEEE118.xlsx', 'resultados_IEEE118_matlab.xlsx', true);
%   results = main('data/IEEE118_escenario1.xlsx', [], false, struct('verbose',true));
% El cuarto argumento permite cambiar opciones; verbose=true por defecto imprime
% cada iteración para la grabación continua, incluida la exportación del Excel.

matlabDir = fileparts(mfilename('fullpath'));
addpath(matlabDir);
if nargin < 1, inputFile = []; end
if nargin < 2, outputFile = []; end
[inputFile, outputFile] = resolve_powerflow_files(inputFile, outputFile);
if nargin < 3, makePlots = true; end

caseData = load_case_excel(inputFile);
if nargin < 4, options = struct(); end
if ~isfield(options, 'tolerance'), options.tolerance = 1e-8; end
if ~isfield(options, 'maxIterations'), options.maxIterations = 1000; end
if ~isfield(options, 'relaxation'), options.relaxation = 1.5; end
if ~isfield(options, 'enforceQLimits'), options.enforceQLimits = false; end
if ~isfield(options, 'verbose'), options.verbose = true; end
requestedMax = options.maxIterations;
[options.maxIterations, maxIterationsAdjusted] = recommended_max_iterations(caseData, requestedMax);
assert(~strcmpi(char(java.io.File(inputFile).getCanonicalPath()), ...
    char(java.io.File(outputFile).getCanonicalPath())), ...
    'powerflow:SameInputOutput', 'La salida no puede reemplazar el Excel de entrada.');
methods = {'Newton-Raphson', 'Gauss-Seidel', 'Desacoplado rápido'};
resultCells = cell(1, numel(methods));

fprintf('\nCaso: %s | %d barras | %d ramas | %d generadores | base %.2f MVA\n', ...
    char(caseData.name), caseData.nBus, caseData.nBranch, caseData.nGen, caseData.baseMVA);
if maxIterationsAdjusted
    fprintf('Caso grande detectado: máximo de iteraciones ajustado automáticamente de %d a %d.\n', ...
        requestedMax, options.maxIterations);
end
fprintf('Tolerancia %.3e pu | máximo %d | relajación GS %.2f | límites Q %d\n', ...
    options.tolerance, options.maxIterations, options.relaxation, options.enforceQLimits);
fprintf('Inicio: VM/VA del Excel; VG de generadores activos en PV y Slack (no perfil plano).\n');
for k = 1:numel(methods)
    fprintf('\n--- %s ---\n', methods{k});
    resultCells{k} = solve_power_flow(caseData, methods{k}, options);
    r = resultCells{k};
    status = 'NO CONVERGIÓ';
    if r.converged, status = 'OK'; end
    fprintf('%s: %s | iter=%d | error=%.3e pu | tiempo=%.4f s | P_loss=%.4f MW\n', ...
        r.method, status, r.iterations, r.maxMismatch, r.elapsedSeconds, r.summary.P_loss_MW);
end

results = [resultCells{:}];
export_results_excel(outputFile, caseData, results);
fprintf('Resultados exportados a: %s\n', outputFile);
if makePlots, plot_results(results); end
end
