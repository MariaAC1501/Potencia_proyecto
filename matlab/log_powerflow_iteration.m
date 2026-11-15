function log_powerflow_iteration(options, method, iteration, mismatch)
%LOG_POWERFLOW_ITERATION Evidencia de cada paso, incluido el estado inicial.
% verbose es opcional para conservar silenciosas las llamadas a solvers/tests.
if isfield(options, 'verbose') && options.verbose
    fprintf('%s | iter=%4d | mismatch máximo=%.12e pu\n', method, iteration, mismatch);
end
end
