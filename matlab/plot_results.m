function plot_results(results)
%PLOT_RESULTS Grafica convergencia y perfil de tensión.
figure('Name','Comparación de flujos de potencia','Color','w');
tiledlayout(2,2);
convAxes = nexttile;
plot_convergence(convAxes, results);
nexttile; hold on; grid on;
for k = 1:numel(results)
    plot(results(k).busResults.BUS_I, results(k).busResults.VM_pu, 'LineWidth', 1.2, 'DisplayName', results(k).method);
end
yline(1.0,'k--'); xlabel('Barra'); ylabel('|V| (pu)'); title('Perfil de tensión'); legend('Location','best');
nexttile; hold on; grid on;
for k = 1:numel(results)
    plot(results(k).busResults.BUS_I, results(k).busResults.VA_deg, 'LineWidth', 1.2, 'DisplayName', results(k).method);
end
xlabel('Barra'); ylabel('Ángulo (°)'); title('Ángulos de tensión');
nexttile;
iterations = arrayfun(@(r) r.iterations, results); losses = arrayfun(@(r) r.summary.P_loss_MW, results);
bar(categorical({results.method}), [iterations(:), losses(:)]); grid on; title('Iteraciones y pérdidas'); legend('Iteraciones','P pérdidas MW');
end
