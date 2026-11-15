function test_plot_convergence
%TEST_PLOT_CONVERGENCE Regresiones de escala para las gráficas de main y GUI.
addpath(fileparts(mfilename('fullpath')));
fig = figure('Visible', 'off');
cleanupFigure = onCleanup(@() delete(fig));
ui = uifigure('Visible', 'off');
cleanupUI = onCleanup(@() delete(ui));
axesToTest = {axes(fig), uiaxes(ui)};
results = struct('method', {'Newton-Raphson', 'Gauss-Seidel', 'Desacoplado rápido'}, ...
    'mismatchHistory', {[2 1e-2 1e-5 1e-10], logspace(2, -8, 1501)', [2 1e-3 1e-9]});
for j = 1:numel(axesToTest)
    ax = axesToTest{j};
    % Reproduce el eje lineal con hold on y límites de una ejecución anterior.
    set(ax, 'YScale', 'linear', 'XLim', [0 1], 'YLim', [0 1]);
    hold(ax, 'on');
    plot_convergence(ax, results);
    check_traces(ax, results);
    assert(strcmp(ax.YLimMode, 'auto') && strcmp(ax.YLimitMethod, 'padded'));
    assert(strcmp(ax.XScale, 'linear'));
    assert(strcmp(ax.YLabel.String, 'Error máximo (pu)'));
    assert(ax.YLim(1) < 1e-10 && ax.YLim(2) > 100);

    % Al cambiar de método, la escala no debe conservar el rango anterior.
    single = struct('method', 'Inicial', 'mismatchHistory', 1e-6);
    plot_convergence(ax, single);
    check_traces(ax, single);
    assert(ax.YLim(2) < 1e-3 && ax.YLim(1) > 1e-9);
    line = findobj(ax, 'Type', 'line');
    assert(isequal(line.MarkerIndices, 1)); % visible aun sin iteraciones

    % No ocultar errores positivos menores que eps ni trazar datos no finitos.
    special = struct('method', 'Datos especiales', ...
        'mismatchHistory', [1 NaN Inf -1 1e-20 0]);
    plot_convergence(ax, special);
    line = findobj(ax, 'Type', 'line');
    assert(all(isnan(line.YData(2:4))));
    assert(line.YData(5) == 1e-20 && line.YData(6) == eps);
    assert(ax.YLim(1) < 1e-20 && ax.YLim(2) > 1);

    special.mismatchHistory = [NaN Inf];
    plot_convergence(ax, special);
    assert(strcmp(ax.YScale, 'log') && all(isfinite(ax.YLim)) && all(ax.YLim > 0));
end
fprintf('test_plot_convergence: escala logarítmica y autoajuste OK en axes y UIAxes.\n');
end

function check_traces(ax, results)
assert(strcmp(ax.YScale, 'log'));
lines = findobj(ax, 'Type', 'line');
assert(numel(lines) == numel(results));
for k = 1:numel(results)
    line = findobj(ax, 'Type', 'line', 'DisplayName', results(k).method);
    history = results(k).mismatchHistory(:)';
    assert(isequal(line.XData, 0:numel(history)-1));
    assert(isequal(line.YData, history));
    assert(ax.XLim(1) <= 0 && ax.XLim(2) >= numel(history)-1);
    assert(ax.YLim(1) < min(history) && ax.YLim(2) > max(history));
    assert(line.MarkerIndices(1) == 1 && line.MarkerIndices(end) == numel(history));
end
end
