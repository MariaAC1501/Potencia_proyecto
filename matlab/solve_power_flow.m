function result = solve_power_flow(caseData, method, options)
%SOLVE_POWER_FLOW Ejecuta uno de los tres métodos propios.
if nargin < 3, options = struct(); end
if ~isfield(options, 'tolerance') || isempty(options.tolerance), options.tolerance = 1e-8; end
if ~isfield(options, 'maxIterations') || isempty(options.maxIterations), options.maxIterations = 1000; end
if ~isfield(options, 'relaxation'), options.relaxation = 1.5; end
if ~isfield(options, 'enforceQLimits'), options.enforceQLimits = false; end
if ~isfield(options, 'verbose'), options.verbose = false; end
requestedMaxIterations = options.maxIterations;
[options.maxIterations, maxIterationsAdjusted] = recommended_max_iterations(caseData, options.maxIterations);
validate_case(caseData);
methodKey = lower(string(method));
methodKey = replace(methodKey, ["-", "_"], " ");
if contains(methodKey, "newton")
    methodName = 'Newton-Raphson'; solver = @solve_newton_raphson;
elseif contains(methodKey, "gauss")
    methodName = 'Gauss-Seidel'; solver = @solve_gauss_seidel;
elseif contains(methodKey, "desacoplado") || contains(methodKey, "fast") || methodKey == "fdlf"
    methodName = 'Desacoplado rápido'; solver = @solve_fast_decoupled;
else
    error('Método no reconocido: %s', method);
end
work = caseData; switched = [];
timer = tic;
for attempt = 1:(caseData.nBus+1)
    raw = solver(work, options);
    result = assemble_result(work, methodName, raw, options.tolerance, toc(timer));
    if ~options.enforceQLimits || ~raw.converged, break; end
    [work, changed] = apply_q_limits(work, raw.V);
    if isempty(changed), break; end
    switched = [switched; changed]; %#ok<AGROW>
end
result.elapsedSeconds = toc(timer);
result.options = options;
if maxIterationsAdjusted
    result.message = sprintf('Máximo de iteraciones ajustado automáticamente de %g a %g para caso de %d barras. %s', ...
        requestedMaxIterations, options.maxIterations, caseData.nBus, result.message);
end
if ~isempty(switched)
    result.message = sprintf('%s Barras PV convertidas a PQ por límites Q: %s.', result.message, mat2str(unique(switched)'));
end
end
