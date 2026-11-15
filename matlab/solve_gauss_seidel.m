function raw = solve_gauss_seidel(caseData, options)
%SOLVE_GAUSS_SEIDEL Flujo de potencia por Gauss-Seidel.
if options.relaxation <= 0 || options.relaxation > 2
    error('La relajación debe estar entre 0 y 2.');
end
[Ybus, index] = build_ybus(caseData);
[Pspec, Qspec] = specified_power(caseData, index);
[slack, pv, pq] = bus_sets(caseData); %#ok<ASGLU>
allBuses = (1:caseData.nBus)';
nonSlack = allBuses(~ismember(allBuses, slack));
pvSet = false(caseData.nBus,1); pvSet(pv) = true;
V = initial_voltage(caseData);
vmSet = abs(V);
history = [];
[~, err] = power_mismatch(Ybus, V, Pspec, Qspec, slack, pq);
history(end+1,1) = err;
log_powerflow_iteration(options, 'GS', 0, err);
if ~isfinite(err)
    raw = pack_raw(false, 0, V, history, 'El error inicial no es finito.');
    return;
end
if err <= options.tolerance
    raw = pack_raw(true, 0, V, history, 'Convergió desde la condición inicial.');
    return;
end
for iteration = 1:options.maxIterations
    for ii = 1:numel(nonSlack)
        i = nonSlack(ii);
        if pvSet(i)
            S = V .* conj(Ybus*V);
            q_i = imag(S(i));
        else
            q_i = Qspec(i);
        end
        S_i = Pspec(i) + 1i*q_i;
        sumOther = Ybus(i,:)*V - Ybus(i,i)*V(i);
        candidate = (conj(S_i/V(i)) - sumOther) / Ybus(i,i);
        updated = V(i) + options.relaxation*(candidate - V(i));
        if pvSet(i)
            updated = vmSet(i)*exp(1i*angle(updated));
        end
        V(i) = updated;
    end
    [~, err] = power_mismatch(Ybus, V, Pspec, Qspec, slack, pq);
    history(end+1,1) = err;
    log_powerflow_iteration(options, 'GS', iteration, err);
    if ~isfinite(err)
        raw = pack_raw(false, iteration, V, history, 'El error se volvió no finito; posible divergencia.');
        return;
    end
    if err <= options.tolerance
        raw = pack_raw(true, iteration, V, history, 'Convergió correctamente.');
        return;
    end
end
raw = pack_raw(false, options.maxIterations, V, history, 'No convergió dentro del máximo de iteraciones.');
end

function raw = pack_raw(converged, iterations, V, history, message)
raw = struct('converged', converged, 'iterations', iterations, 'V', V, ...
    'history', history, 'message', message);
end
