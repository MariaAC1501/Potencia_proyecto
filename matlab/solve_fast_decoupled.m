function raw = solve_fast_decoupled(caseData, options)
%SOLVE_FAST_DECOUPLED Flujo de potencia desacoplado rápido.
[Ybus, index] = build_ybus(caseData);
[Pspec, Qspec] = specified_power(caseData, index);
[slack, ~, pq] = bus_sets(caseData);
allBuses = (1:caseData.nBus)';
angleBuses = allBuses(~ismember(allBuses, slack));
V = initial_voltage(caseData);
[BprimeFull, BdoubleFull] = fast_decoupled_matrices(caseData, index);
Bprime = BprimeFull(angleBuses, angleBuses);
Bdouble = BdoubleFull(pq, pq);
history = [];
[~, err] = power_mismatch(Ybus, V, Pspec, Qspec, slack, pq);
history(end+1,1) = err;
log_powerflow_iteration(options, 'FDLF', 0, err);
if ~isfinite(err)
    raw = pack_raw(false, 0, V, history, 'El error inicial no es finito.');
    return;
end
if err <= options.tolerance
    raw = pack_raw(true, 0, V, history, 'Convergió desde la condición inicial.');
    return;
end
for iteration = 1:options.maxIterations
    vm = abs(V);
    [~, ~, Pcalc, ~] = power_mismatch(Ybus, V, Pspec, Qspec, slack, pq);
    dP = (Pspec(angleBuses)-Pcalc(angleBuses))./vm(angleBuses);
    try
        dTheta = Bprime\dP;
    catch exception
        raw = pack_raw(false, iteration-1, V, history, ['Matriz B'' singular: ', exception.message]);
        return;
    end
    theta = angle(V);
    theta(angleBuses) = theta(angleBuses)+dTheta;
    V = vm.*exp(1i*theta);

    vm = abs(V);
    [~, ~, ~, Qcalc] = power_mismatch(Ybus, V, Pspec, Qspec, slack, pq);
    dQ = (Qspec(pq)-Qcalc(pq))./vm(pq);
    try
        dVm = Bdouble\dQ;
    catch exception
        raw = pack_raw(false, iteration-1, V, history, ['Matriz B'''' singular: ', exception.message]);
        return;
    end
    vm(pq) = vm(pq)+dVm;
    if any(vm <= 0)
        raw = pack_raw(false, iteration, V, history, 'La iteración produjo un voltaje no positivo.');
        return;
    end
    V = vm.*exp(1i*angle(V));
    [~, err] = power_mismatch(Ybus, V, Pspec, Qspec, slack, pq);
    history(end+1,1) = err;
    log_powerflow_iteration(options, 'FDLF', iteration, err);
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
