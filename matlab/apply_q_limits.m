function [caseData, changed] = apply_q_limits(caseData, V)
%APPLY_Q_LIMITS Convierte PV a PQ cuando se excede QMIN/QMAX.
[Ybus, ~] = build_ybus(caseData);
[~, Qcalc] = calculate_power(Ybus, V, caseData.baseMVA);
changed = [];
for i = 1:caseData.nBus
    if caseData.bus.TYPE(i) ~= 2, continue; end
    rows = find(caseData.gen.GEN_BUS == caseData.bus.BUS_I(i) & caseData.gen.STATUS ~= 0);
    if isempty(rows), continue; end
    qRequired = Qcalc(i) + caseData.bus.QD(i);
    qMin = sum(caseData.gen.QMIN(rows)); qMax = sum(caseData.gen.QMAX(rows));
    target = min(max(qRequired, qMin), qMax);
    if qRequired < qMin-1e-8 || qRequired > qMax+1e-8
        caseData.bus.TYPE(i) = 1;
        caseData.gen.QG(rows) = 0;
        caseData.gen.QG(rows(1)) = target;
        changed(end+1,1) = caseData.bus.BUS_I(i); %#ok<AGROW>
    end
end
end
