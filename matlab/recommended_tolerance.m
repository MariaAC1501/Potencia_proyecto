function [tolerance, adjusted] = recommended_tolerance(~, requestedTolerance)
%RECOMMENDED_TOLERANCE Mantiene la tolerancia solicitada.
% Se conserva por compatibilidad, pero ya no relaja automáticamente la
% tolerancia en casos grandes. Para casos de más de 118 barras ahora se
% aumenta el máximo de iteraciones con recommended_max_iterations.

if nargin < 2 || isempty(requestedTolerance)
    requestedTolerance = 1e-8;
end

tolerance = requestedTolerance;
adjusted = false;
end
