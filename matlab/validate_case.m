function validate_case(caseData)
%VALIDATE_CASE Verifica la estructura básica del caso.
if caseData.baseMVA <= 0
    error('baseMVA debe ser mayor que cero.');
end
if height(caseData.bus) == 0 || height(caseData.branch) == 0
    error('El caso debe tener barras y ramas.');
end
ids = caseData.bus.BUS_I;
if numel(unique(ids)) ~= numel(ids)
    error('Los identificadores de barra deben ser únicos.');
end
types = caseData.bus.TYPE;
if sum(types == 3) ~= 1
    error('Debe existir exactamente una barra Slack (TYPE=3).');
end
if any(~ismember(types, [1,2,3]))
    error('Solo se soportan TYPE=1 (PQ), 2 (PV) y 3 (Slack).');
end
if any(abs(caseData.branch.BR_X) < 1e-14)
    error('No se permiten ramas con reactancia cero.');
end
if any(~ismember(caseData.branch.F_BUS, ids)) || any(~ismember(caseData.branch.T_BUS, ids))
    error('Una rama referencia una barra inexistente.');
end
if any(~ismember(caseData.gen.GEN_BUS, ids))
    error('Un generador referencia una barra inexistente.');
end
% Comparte las mismas comprobaciones con las llamadas directas a solvers.
voltage_setpoints(caseData);
end
