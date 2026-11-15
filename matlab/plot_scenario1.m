function plot_scenario1(baseResult, scenarioResult, analysis, outputDir, visible)
%PLOT_SCENARIO1 Figuras comparativas; no modifica figuras abiertas previamente.
if nargin < 5, visible = false; end
if ~isfolder(outputDir), mkdir(outputDir); end
visibility = 'off'; if visible, visibility = 'on'; end
b = baseResult.busResults; s = scenarioResult.busResults;
f = figure('Visible', visibility, 'Name', 'Escenario 1: tensiones');
ax = axes(f); hold(ax, 'on');
plot(ax, b.BUS_I, b.VM_pu, '-', 'LineWidth', 1.4, 'DisplayName', 'Caso base');
plot(ax, s.BUS_I, s.VM_pu, '--', 'LineWidth', 1.4, 'DisplayName', 'Sin línea 26–30');
yline(ax, .95, ':r', '0.95 pu (guía)', 'HandleVisibility', 'off');
yline(ax, 1.05, ':r', '1.05 pu (guía)', 'HandleVisibility', 'off');
xlabel(ax, 'Barra'); ylabel(ax, 'Tensión [pu]'); grid(ax, 'on'); legend(ax, 'Location', 'best');
title(ax, 'IEEE118: comparación base y salida de línea 26–30 (NR)');
exportgraphics(f, fullfile(outputDir, 'perfil_escenario1.png'), 'Resolution', 180);
if ~visible, close(f); end
f = figure('Visible', visibility, 'Name', 'Escenario 1: redistribución');
ax = axes(f); T = analysis.cambios_top5;
bar(ax, [T.S_base_MVA T.S_escenario_MVA]);
xticks(ax, 1:height(T)); xticklabels(ax, string(T.Desde)+"–"+string(T.Hasta));
xlabel(ax, 'Rama (top 5 por cambio absoluto; retirada excluida)');
ylabel(ax, 'Máximo de potencia aparente en ambos extremos [MVA]');
legend(ax, 'Caso base', 'Sin línea 26–30', 'Location', 'best'); grid(ax, 'on');
title(ax, 'Redistribución de flujos tras la contingencia');
exportgraphics(f, fullfile(outputDir, 'redistribucion_escenario1.png'), 'Resolution', 180);
if ~visible, close(f); end
end
