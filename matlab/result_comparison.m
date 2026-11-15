function comparison = result_comparison(results)
%RESULT_COMPARISON Tabla de métodos exigida por la guía del video.
n = numel(results);
methods = strings(n,1); converged = false(n,1);
iterations = zeros(n,1); errorFinal = zeros(n,1); elapsed = zeros(n,1);
pLoss = zeros(n,1); qLoss = zeros(n,1); pSlack = zeros(n,1); qSlack = zeros(n,1);
for k = 1:n
    r = results(k);
    methods(k) = string(r.method); converged(k) = r.converged;
    iterations(k) = r.iterations; errorFinal(k) = r.maxMismatch;
    elapsed(k) = r.elapsedSeconds;
    pLoss(k) = r.summary.P_loss_MW; qLoss(k) = r.summary.Q_loss_MVAr;
    slack = r.busResults.BUS_I == r.summary.slackBus;
    pSlack(k) = sum(r.busResults.P_gen_calculada_MW(slack));
    qSlack(k) = sum(r.busResults.Q_gen_calculada_MVAr(slack));
end
comparison = table(methods, converged, iterations, errorFinal, elapsed, pLoss, qLoss, pSlack, qSlack, ...
    'VariableNames', {'Metodo','Convergio','Iteraciones','Error_final_pu','Tiempo_s', ...
    'Perdidas_P_MW','Perdidas_Q_MVAr','P_slack_MW','Q_slack_MVAr'});
end
