function raw = solve_newton_raphson(caseData, options)
%SOLVE_NEWTON_RAPHSON Flujo de potencia por Newton-Raphson completo.
[Ybus, index] = build_ybus(caseData);
[Pspec, Qspec] = specified_power(caseData, index);
[slack, ~, pq] = bus_sets(caseData);
allBuses = (1:caseData.nBus)';
angleBuses = allBuses(~ismember(allBuses, slack));
V = initial_voltage(caseData);
history = [];
[mis, err, Pcalc, Qcalc] = power_mismatch(Ybus, V, Pspec, Qspec, slack, pq); %#ok<ASGLU>
history(end+1,1) = err;
log_powerflow_iteration(options, 'NR', 0, err);
if ~isfinite(err)
    raw = pack_raw(false, 0, V, history, 'El error inicial no es finito.');
    return;
end
if err <= options.tolerance
    raw = pack_raw(true, 0, V, history, 'Convergió desde la condición inicial.');
    return;
end
G = real(Ybus); B = imag(Ybus);
for iteration = 1:options.maxIterations
    [mis, ~, Pcalc, Qcalc] = power_mismatch(Ybus, V, Pspec, Qspec, slack, pq);
    vm = abs(V); theta = angle(V);
    nAng = numel(angleBuses); nPQ = numel(pq);
    J = zeros(nAng+nPQ, nAng+nPQ);
    for r = 1:nAng
        i = angleBuses(r);
        for c = 1:nAng
            k = angleBuses(c);
            if i == k
                J(r,c) = -Qcalc(i) - B(i,i)*vm(i)^2;
            else
                delta = theta(i)-theta(k);
                J(r,c) = vm(i)*vm(k)*(G(i,k)*sin(delta)-B(i,k)*cos(delta));
            end
        end
        for c = 1:nPQ
            k = pq(c);
            if i == k
                J(r,nAng+c) = Pcalc(i)/vm(i) + G(i,i)*vm(i);
            else
                delta = theta(i)-theta(k);
                J(r,nAng+c) = vm(i)*(G(i,k)*cos(delta)+B(i,k)*sin(delta));
            end
        end
    end
    for r = 1:nPQ
        i = pq(r);
        row = nAng+r;
        for c = 1:nAng
            k = angleBuses(c);
            if i == k
                J(row,c) = Pcalc(i) - G(i,i)*vm(i)^2;
            else
                delta = theta(i)-theta(k);
                J(row,c) = -vm(i)*vm(k)*(G(i,k)*cos(delta)+B(i,k)*sin(delta));
            end
        end
        for c = 1:nPQ
            k = pq(c);
            if i == k
                J(row,nAng+c) = Qcalc(i)/vm(i) - B(i,i)*vm(i);
            else
                delta = theta(i)-theta(k);
                J(row,nAng+c) = vm(i)*(G(i,k)*sin(delta)-B(i,k)*cos(delta));
            end
        end
    end
    try
        correction = J\mis;
    catch exception
        raw = pack_raw(false, iteration-1, V, history, ['Jacobiano singular: ', exception.message]);
        return;
    end
    theta(angleBuses) = theta(angleBuses) + correction(1:nAng);
    vm(pq) = vm(pq) + correction(nAng+1:end);
    if any(vm <= 0)
        raw = pack_raw(false, iteration, V, history, 'La iteración produjo un voltaje no positivo.');
        return;
    end
    V = vm .* exp(1i*theta);
    [~, err] = power_mismatch(Ybus, V, Pspec, Qspec, slack, pq);
    history(end+1,1) = err;
    log_powerflow_iteration(options, 'NR', iteration, err);
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
