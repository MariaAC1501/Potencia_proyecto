function plot_convergence(ax, results)
%PLOT_CONVERGENCE Grafica el error con la misma escala en figuras y UIAxes.
cla(ax);
% Con hold activo, semilogy no siempre cambia un eje lineal a logarítmico.
set(ax, 'XScale', 'linear', 'YScale', 'log', ...
    'XLimMode', 'auto', 'YLimMode', 'auto', 'XTickMode', 'auto', 'YTickMode', 'auto');
hold(ax, 'on');
for k = 1:numel(results)
    errors = results(k).mismatchHistory(:);
    % Los ceros necesitan un piso positivo; los valores inválidos no se trazan.
    errors(~isfinite(errors) | errors < 0) = NaN;
    errors(errors == 0) = eps;
    markerIndices = unique(round(linspace(1, numel(errors), min(12, numel(errors)))));
    semilogy(ax, 0:numel(errors)-1, errors, '-o', ...
        'LineWidth', 1.4, 'MarkerSize', 3, 'MarkerIndices', markerIndices, ...
        'DisplayName', results(k).method);
end
% Recalcular los límites también al cambiar de caso o método en la interfaz.
xlim(ax, 'tight');
ylim(ax, 'padded');
grid(ax, 'on');
ax.YMinorGrid = 'on';
xlabel(ax, 'Iteración');
ylabel(ax, 'Error máximo (pu)');
title(ax, 'Convergencia');
legend(ax, 'show', 'Location', 'best');
hold(ax, 'off');
end
