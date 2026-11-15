function result = assemble_result(caseData, method, raw, tolerance, elapsedSeconds)
%ASSEMBLE_RESULT Convierte el estado complejo en tablas y resumen.
[Ybus, index] = build_ybus(caseData);
[Pcalc, Qcalc] = calculate_power(Ybus, raw.V, caseData.baseMVA);
[PspecPU, QspecPU] = specified_power(caseData, index);
[slack, ~, pq] = bus_sets(caseData);

busResults = caseData.bus;
types = caseData.bus.TYPE;
typeName = strings(caseData.nBus,1);
typeName(types == 1) = "PQ"; typeName(types == 2) = "PV"; typeName(types == 3) = "Slack";
busResults.TipoNombre = typeName;
busResults.VM_pu = abs(raw.V);
busResults.VA_deg = angle(raw.V)*180/pi;
busResults.P_calc_MW = Pcalc; busResults.Q_calc_MVAr = Qcalc;
busResults.P_spec_MW = PspecPU*caseData.baseMVA; busResults.Q_spec_MVAr = QspecPU*caseData.baseMVA;
busResults.P_gen_calculada_MW = Pcalc + caseData.bus.PD;
busResults.Q_gen_calculada_MVAr = Qcalc + caseData.bus.QD;
busResults.P_load_MW = caseData.bus.PD; busResults.Q_load_MVAr = caseData.bus.QD;
busResults.Error_P_MW = (PspecPU - Pcalc/caseData.baseMVA)*caseData.baseMVA;
busResults.Error_Q_MVAr = (QspecPU - Qcalc/caseData.baseMVA)*caseData.baseMVA;
busResults.Es_variable_angulo = true(caseData.nBus,1); busResults.Es_variable_angulo(slack) = false;
busResults.Es_variable_VM = false(caseData.nBus,1); busResults.Es_variable_VM(pq) = true;

branchResults = calculate_branch_flows(caseData, raw.V);
pLoss = sum(branchResults.P_loss_MW); qLoss = sum(branchResults.Q_loss_MVAr);
pGen = busResults.P_gen_calculada_MW; qGen = busResults.Q_gen_calculada_MVAr;
vm = busResults.VM_pu;
[vmMin, iMin] = min(vm); [vmMax, iMax] = max(vm);
summary = struct('nBus', caseData.nBus, 'nBranch', caseData.nBranch, 'nGen', caseData.nGen, ...
    'slackBus', caseData.bus.BUS_I(slack(1)), 'minVoltagePU', vmMin, 'maxVoltagePU', vmMax, ...
    'minVoltageBus', caseData.bus.BUS_I(iMin), 'maxVoltageBus', caseData.bus.BUS_I(iMax), ...
    'P_loss_MW', pLoss, 'Q_loss_MVAr', qLoss, 'P_generation_MW', sum(pGen), ...
    'P_demand_MW', sum(caseData.bus.PD), 'Q_generation_MVAr', sum(qGen), 'Q_demand_MVAr', sum(caseData.bus.QD));

result = struct('method', method, 'converged', raw.converged, 'iterations', raw.iterations, ...
    'tolerance', tolerance, 'elapsedSeconds', elapsedSeconds, 'V', raw.V, ...
    'mismatchHistory', raw.history, 'busResults', busResults, 'branchResults', branchResults, ...
    'summary', summary, 'message', raw.message, 'maxMismatch', raw.history(end));
end
