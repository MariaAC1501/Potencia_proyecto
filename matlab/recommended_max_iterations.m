function [maxIterations, adjusted] = recommended_max_iterations(caseData, requestedMaxIterations)
%RECOMMENDED_MAX_ITERATIONS Aumenta iteraciones para casos grandes.
% Para sistemas de más de 118 barras, Gauss-Seidel puede necesitar miles de
% iteraciones. Se elimina el límite práctico de 1000 usando un valor mínimo
% proporcional al tamaño del sistema, manteniendo la tolerancia solicitada.

if nargin < 2 || isempty(requestedMaxIterations)
    requestedMaxIterations = 1000;
end

if isfield(caseData, 'nBus')
    nBus = caseData.nBus;
else
    nBus = height(caseData.bus);
end

maxIterations = requestedMaxIterations;
adjusted = false;

if isinf(requestedMaxIterations)
    maxIterations = 1000000;
    adjusted = true;
    return;
end

minimumLargeCaseIterations = max(5000, 100*nBus);
if nBus > 118 && requestedMaxIterations < minimumLargeCaseIterations
    maxIterations = minimumLargeCaseIterations;
    adjusted = true;
end
end
