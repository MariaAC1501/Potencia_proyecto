function export_results_excel(filename, caseData, results)
%EXPORT_RESULTS_EXCEL Exporta entradas, comparación y resultados a Excel.
if nargin < 3 || isempty(results), error('Debe proporcionar resultados.'); end
% Libro temporal: un fallo no debe borrar la evidencia anterior.
destination = filename;
folder = fileparts(destination);
if isempty(folder), folder = pwd; end
filename = [tempname(folder), '.xlsx'];
cleanup = onCleanup(@() delete_temp(filename)); %#ok<NASGU>
writetable(caseData.bus, filename, 'Sheet', 'entrada_bus');
writetable(caseData.gen, filename, 'Sheet', 'entrada_gen');
writetable(caseData.branch, filename, 'Sheet', 'entrada_branch');
writetable(table(caseData.baseMVA, 'VariableNames', {'baseMVA'}), filename, 'Sheet', 'config');
comparison = result_comparison(results);
writetable(comparison, filename, 'Sheet', 'comparacion');
if isfield(results, 'options')
    opts = results(1).options;
    parameters = table(["Tolerancia_pu"; "Maximo_iteraciones"; "Relajacion_GS"; ...
        "Aplicar_limites_Q"; "Inicio"; "Alcance_tiempo"], ...
        [string(opts.tolerance); string(opts.maxIterations); string(opts.relaxation); ...
        string(opts.enforceQLimits); "VM/VA de Excel y VG activa, no perfil plano"; ...
        "Solución y ensamblado de resultados, incluye consola si verbose; excluye Excel y gráficas"], ...
        'VariableNames', {'Parametro','Valor'});
    writetable(parameters, filename, 'Sheet', 'parametros');
end
for k = 1:numel(results)
    if contains(lower(results(k).method), 'newton')
        prefix = 'NR';
    elseif contains(lower(results(k).method), 'gauss')
        prefix = 'GS';
    else
        prefix = 'FDLF';
    end
    writetable(results(k).busResults, filename, 'Sheet', [prefix, '_bus']);
    writetable(results(k).branchResults, filename, 'Sheet', [prefix, '_branch']);
    convergence = table((0:numel(results(k).mismatchHistory)-1)', results(k).mismatchHistory, ...
        'VariableNames', {'Iteracion','Error_max_pu'});
    writetable(convergence, filename, 'Sheet', [prefix, '_conv']);
end
[ok, message] = movefile(filename, destination, 'f');
assert(ok, 'No se pudo guardar la salida: %s', message);
end

function delete_temp(filename)
if isfile(filename), delete(filename); end
end
